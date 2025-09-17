import asyncio
import json
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from autogen_core import (
    FunctionCall,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import FunctionTool, Tool
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel

from app.models.models import Message
from app.config.azure import azure_config
from app.config.telemetry import telemetry_config

logger = logging.getLogger(__name__)

# Initialize telemetry tracer and meter
try:
    tracer = telemetry_config.get_tracer(__name__)
    meter = telemetry_config.get_meter(__name__)
    
    # Multi-agent specific metrics
    multi_agent_conversation_counter = meter.create_counter(
        name="multi_agent_conversations_total",
        description="Total number of multi-agent conversations",
        unit="1"
    )
    
    agent_handoff_counter = meter.create_counter(
        name="agent_handoffs_total",
        description="Total number of agent handoffs",
        unit="1"
    )
    
    web_search_counter = meter.create_counter(
        name="web_searches_total",
        description="Total number of web searches performed",
        unit="1"
    )
    
    logger.info("Multi-agent telemetry instrumentation loaded")
except Exception as e:
    logger.warning(f"Telemetry not available for multi-agent service: {e}")
    tracer = None
    multi_agent_conversation_counter = None
    agent_handoff_counter = None
    web_search_counter = None


# Message Protocol for Multi-Agent Communication
class UserTask(BaseModel):
    context: List[LLMMessage]
    session_id: str


class AgentResponse(BaseModel):
    reply_to_topic_type: str
    context: List[LLMMessage]
    session_id: str


class WebSearchRequest(BaseModel):
    query: str
    context: List[LLMMessage]
    session_id: str


class SummarizationRequest(BaseModel):
    content: str
    context: List[LLMMessage]
    session_id: str


# Internet Tools for Research Agent
def web_search(query: str) -> str:
    """Simulate web search functionality. In production, integrate with real search APIs."""
    # This is a mock implementation - in production you would use a real search API
    # like Bing Search API, Google Custom Search, or SerpAPI
    
    mock_results = {
        "ai": "Artificial Intelligence (AI) is a broad field of computer science focused on creating intelligent machines capable of performing tasks that typically require human intelligence.",
        "machine learning": "Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.",
        "openai": "OpenAI is an AI research laboratory consisting of the for-profit corporation OpenAI LP and its parent company, the non-profit OpenAI Inc.",
        "autogen": "AutoGen is a framework that enables the development of LLM applications using multiple agents that can converse with each other to solve tasks.",
        "python": "Python is a high-level, interpreted programming language known for its simplicity and readability, widely used in AI and machine learning.",
        "default": f"Search results for '{query}': Found relevant information about {query}. This includes recent developments, key concepts, and practical applications in the field."
    }
    
    # Simple keyword matching for mock results
    query_lower = query.lower()
    for keyword, result in mock_results.items():
        if keyword in query_lower:
            if web_search_counter:
                web_search_counter.add(1, {"query_type": keyword})
            return result
    
    if web_search_counter:
        web_search_counter.add(1, {"query_type": "general"})
    return mock_results["default"]


def fetch_url_content(url: str) -> str:
    """Simulate fetching content from a URL. In production, implement actual web scraping."""
    # Mock implementation - in production use requests, beautifulsoup, or similar
    mock_content = f"Content from {url}: This is sample content that would be extracted from the webpage. In a real implementation, this would contain the actual text content from the specified URL."
    return mock_content


# Tools
web_search_tool = FunctionTool(
    web_search, 
    description="Search the internet for information on any topic. Provide a clear search query."
)

fetch_url_tool = FunctionTool(
    fetch_url_content,
    description="Fetch and extract content from a specific URL."
)


# Handoff Tools
def transfer_to_summarizer() -> str:
    return "SummarizerAgent"


def transfer_to_researcher() -> str:
    return "ResearcherAgent"


transfer_to_summarizer_tool = FunctionTool(
    transfer_to_summarizer,
    description="Transfer task to the summarizer agent for content summarization and analysis."
)

transfer_to_researcher_tool = FunctionTool(
    transfer_to_researcher,
    description="Transfer task to the researcher agent for internet research and information gathering."
)


class MultiAgent(RoutedAgent):
    """Base class for multi-agent system agents with handoff capabilities."""
    
    def __init__(
        self,
        description: str,
        system_message: SystemMessage,
        model_client: ChatCompletionClient,
        tools: List[Tool],
        delegate_tools: List[Tool],
        agent_topic_type: str,
        agent_name: str,
    ) -> None:
        super().__init__(description)
        self._system_message = system_message
        self._model_client = model_client
        self._tools = dict([(tool.name, tool) for tool in tools])
        self._tool_schema = [tool.schema for tool in tools]
        self._delegate_tools = dict([(tool.name, tool) for tool in delegate_tools])
        self._delegate_tool_schema = [tool.schema for tool in delegate_tools]
        self._agent_topic_type = agent_topic_type
        self._agent_name = agent_name

    def _clean_response_content(self, content: str) -> str:
        """Clean and sanitize response content from AutoGen agent"""
        if not content:
            return "I apologize, but I couldn't generate a response."
        
        content = str(content)
        
        # Remove common AutoGen formatting artifacts
        if content.startswith("TextMessage("):
            content = content[12:]
            if content.endswith(")"):
                content = content[:-1]
        
        # Handle escaped characters
        try:
            if content.startswith('"') and content.endswith('"'):
                content = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            content = content.replace('\\n', '\n')
            content = content.replace('\\t', '\t')
            content = content.replace('\\r', '\r')
            content = content.replace('\\"', '"')
            content = content.replace("\\'", "'")
            content = content.replace('\\\\', '\\')
        
        content = content.strip()
        if ((content.startswith('"') and content.endswith('"')) or 
            (content.startswith("'") and content.endswith("'"))):
            content = content[1:-1]
        
        content = ' '.join(content.split())
        
        return content if content else "I apologize, but I couldn't generate a response."

    @message_handler
    async def handle_task(self, message: UserTask, ctx: MessageContext) -> None:
        """Handle incoming user tasks with telemetry tracking."""
        start_time = datetime.now()
        
        if tracer:
            with tracer.start_span(f"{self._agent_name}_handle_task") as span:
                span.set_attribute("agent_name", self._agent_name)
                span.set_attribute("session_id", message.session_id)
                span.set_attribute("context_length", len(message.context))
                await self._process_task_with_telemetry(message, ctx, span)
        else:
            await self._process_task_internal(message, ctx)

    async def _process_task_with_telemetry(self, message: UserTask, ctx: MessageContext, span) -> None:
        """Process task with telemetry tracking."""
        try:
            await self._process_task_internal(message, ctx)
            span.set_attribute("status", "success")
            
            if multi_agent_conversation_counter:
                multi_agent_conversation_counter.add(1, {
                    "agent": self._agent_name,
                    "status": "success"
                })
                
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("status", "error")
            
            if multi_agent_conversation_counter:
                multi_agent_conversation_counter.add(1, {
                    "agent": self._agent_name,
                    "status": "error"
                })
            raise

    async def _process_task_internal(self, message: UserTask, ctx: MessageContext) -> None:
        """Internal task processing logic."""
        # Send the task to the LLM
        llm_result = await self._model_client.create(
            messages=[self._system_message] + message.context,
            tools=self._tool_schema + self._delegate_tool_schema,
            cancellation_token=ctx.cancellation_token,
        )
        
        logger.info(f"{self._agent_name}: {llm_result.content}")
        
        # Process the LLM result
        while isinstance(llm_result.content, list) and all(isinstance(m, FunctionCall) for m in llm_result.content):
            tool_call_results: List[FunctionExecutionResult] = []
            delegate_targets: List[tuple] = []
            
            # Process each function call
            for call in llm_result.content:
                arguments = json.loads(call.arguments)
                
                if call.name in self._tools:
                    # Execute the tool directly
                    result = await self._tools[call.name].run_json(arguments, ctx.cancellation_token)
                    result_as_str = self._tools[call.name].return_value_as_string(result)
                    tool_call_results.append(
                        FunctionExecutionResult(
                            call_id=call.id, 
                            content=result_as_str, 
                            is_error=False, 
                            name=call.name
                        )
                    )
                    
                elif call.name in self._delegate_tools:
                    # Execute delegate tool to get target agent topic
                    result = await self._delegate_tools[call.name].run_json(arguments, ctx.cancellation_token)
                    topic_type = self._delegate_tools[call.name].return_value_as_string(result)
                    
                    # Create context for delegate agent
                    delegate_messages = list(message.context) + [
                        AssistantMessage(content=[call], source=self._agent_name),
                        FunctionExecutionResultMessage(
                            content=[
                                FunctionExecutionResult(
                                    call_id=call.id,
                                    content=f"Transferred to {topic_type}. Please continue the conversation.",
                                    is_error=False,
                                    name=call.name,
                                )
                            ]
                        ),
                    ]
                    
                    delegate_targets.append((
                        topic_type, 
                        UserTask(context=delegate_messages, session_id=message.session_id)
                    ))
                    
                    # Track handoff
                    if agent_handoff_counter:
                        agent_handoff_counter.add(1, {
                            "from_agent": self._agent_name,
                            "to_agent": topic_type
                        })
                else:
                    raise ValueError(f"Unknown tool: {call.name}")
            
            if len(delegate_targets) > 0:
                # Delegate tasks to other agents
                for topic_type, task in delegate_targets:
                    logger.info(f"{self._agent_name}: Delegating to {topic_type}")
                    await self.publish_message(
                        task, 
                        topic_id=TopicId(topic_type, source=message.session_id)
                    )
                return
            
            if len(tool_call_results) > 0:
                logger.info(f"{self._agent_name}: Tool results: {tool_call_results}")
                # Make another LLM call with the results
                message.context.extend([
                    AssistantMessage(content=llm_result.content, source=self._agent_name),
                    FunctionExecutionResultMessage(content=tool_call_results),
                ])
                
                llm_result = await self._model_client.create(
                    messages=[self._system_message] + message.context,
                    tools=self._tool_schema + self._delegate_tool_schema,
                    cancellation_token=ctx.cancellation_token,
                )
                logger.info(f"{self._agent_name}: {llm_result.content}")
        
        # Task completed, send final response back to coordinator
        assert isinstance(llm_result.content, str)
        message.context.append(AssistantMessage(content=llm_result.content, source=self._agent_name))
        
        # In multi-agent, we send back to the coordinator rather than user
        await self.publish_message(
            AgentResponse(
                context=message.context, 
                reply_to_topic_type=self._agent_topic_type,
                session_id=message.session_id
            ),
            topic_id=TopicId("MultiAgentCoordinator", source=message.session_id),
        )


class MultiAgentService:
    """Multi-agent service that orchestrates researcher and summarizer agents."""
    
    def __init__(self):
        self._runtime: Optional[SingleThreadedAgentRuntime] = None
        self._model_client: Optional[AzureAIChatCompletionClient] = None
        self._session_responses: Dict[str, List[Message]] = {}
        logger.debug("MultiAgentService initialized")

    async def _initialize_runtime(self):
        """Initialize the multi-agent runtime and register agents."""
        if self._runtime is None:
            try:
                if not azure_config.is_configured():
                    raise ValueError(
                        "Azure configuration is incomplete. Please check environment variables."
                    )

                logger.info("Initializing multi-agent system")

                # Create model client
                self._model_client = AzureAIChatCompletionClient(
                    model=azure_config.get_deployment_name(),
                    endpoint=azure_config.get_project_endpoint(),
                    credential=AzureKeyCredential(azure_config.get_api_key()),
                    model_info={
                        "json_output": False,
                        "function_calling": True,
                        "vision": False,
                        "family": "unknown",
                        "structured_output": False,
                    },
                )

                # Create runtime
                self._runtime = SingleThreadedAgentRuntime()

                # Register Research Agent (with internet access)
                researcher_agent_type = await MultiAgent.register(
                    self._runtime,
                    type="ResearcherAgent",
                    factory=lambda: MultiAgent(
                        description="An AI agent specialized in internet research and information gathering.",
                        system_message=SystemMessage(
                            content="""You are a research specialist AI agent with access to internet search capabilities. 
                            Your role is to:
                            1. Search for current and accurate information on user queries
                            2. Gather data from multiple sources when needed
                            3. Provide comprehensive research findings
                            4. Transfer complex information to the summarizer when the user needs a concise summary
                            
                            Always search for information before responding. Be thorough in your research and cite your findings clearly.
                            If the user asks for a summary of the information you've gathered, transfer the task to the summarizer agent."""
                        ),
                        model_client=self._model_client,
                        tools=[web_search_tool, fetch_url_tool],
                        delegate_tools=[transfer_to_summarizer_tool],
                        agent_topic_type="ResearcherAgent",
                        agent_name="ResearcherAgent",
                    ),
                )

                # Register Summarizer Agent (no internet access)
                summarizer_agent_type = await MultiAgent.register(
                    self._runtime,
                    type="SummarizerAgent",
                    factory=lambda: MultiAgent(
                        description="An AI agent specialized in content summarization and analysis.",
                        system_message=SystemMessage(
                            content="""You are a summarization specialist AI agent. Your role is to:
                            1. Analyze and summarize complex information provided by other agents
                            2. Extract key points and insights from detailed content
                            3. Present information in clear, concise formats
                            4. Transfer users back to the researcher if they need additional information not available in the current context
                            
                            You do not have internet access. Work only with the information provided in the conversation context.
                            Focus on creating clear, actionable summaries that highlight the most important points."""
                        ),
                        model_client=self._model_client,
                        tools=[],  # No internet tools
                        delegate_tools=[transfer_to_researcher_tool],
                        agent_topic_type="SummarizerAgent",
                        agent_name="SummarizerAgent",
                    ),
                )

                # Register Coordinator Agent (handles responses back to user)
                coordinator_agent_type = await RoutedAgent.register(
                    self._runtime,
                    type="MultiAgentCoordinator",
                    factory=lambda: MultiAgentCoordinator(self),
                )

                # Add subscriptions
                await self._runtime.add_subscription(
                    TypeSubscription(topic_type="ResearcherAgent", agent_type=researcher_agent_type.type)
                )
                await self._runtime.add_subscription(
                    TypeSubscription(topic_type="SummarizerAgent", agent_type=summarizer_agent_type.type)
                )
                await self._runtime.add_subscription(
                    TypeSubscription(topic_type="MultiAgentCoordinator", agent_type=coordinator_agent_type.type)
                )

                # Start runtime
                self._runtime.start()
                
                logger.info("Multi-agent system initialized successfully")

            except Exception as e:
                logger.error(f"Error initializing multi-agent system: {e}", exc_info=True)
                raise

    async def generate_response(self, messages: List[Message], user_message: str) -> str:
        """Generate a response using the multi-agent system."""
        try:
            await self._initialize_runtime()
            
            if not self._runtime:
                raise ValueError("Multi-agent runtime not initialized")

            # Create session ID for this conversation
            session_id = str(uuid.uuid4())
            
            # Convert conversation history to AutoGen messages format
            autogen_messages = []
            
            # Add recent conversation context (last 10 messages)
            recent_messages = messages[-10:] if len(messages) > 10 else messages
            
            for msg in recent_messages:
                autogen_messages.append(
                    UserMessage(content=msg.content, source=msg.role) if msg.role == 'user'
                    else AssistantMessage(content=msg.content, source=msg.role)
                )
            
            # Add current user message
            autogen_messages.append(UserMessage(content=user_message, source="user"))
            
            # Initialize session response storage
            self._session_responses[session_id] = []
            
            # Start with researcher agent (default entry point)
            task = UserTask(context=autogen_messages, session_id=session_id)
            
            logger.info(f"Starting multi-agent conversation for session {session_id}")
            
            # Publish task to researcher agent
            await self._runtime.publish_message(
                task,
                topic_id=TopicId("ResearcherAgent", source=session_id)
            )
            
            # Wait for completion with timeout
            max_wait_time = 30  # seconds
            wait_interval = 0.1
            total_waited = 0
            
            while session_id not in self._session_responses or not self._session_responses[session_id]:
                if total_waited >= max_wait_time:
                    logger.warning(f"Timeout waiting for multi-agent response for session {session_id}")
                    return "I'm sorry, but the multi-agent system is taking longer than expected. Please try again."
                
                await asyncio.sleep(wait_interval)
                total_waited += wait_interval
            
            # Get the final response
            final_messages = self._session_responses[session_id]
            if final_messages:
                final_response = final_messages[-1].content
                
                # Cleanup session
                del self._session_responses[session_id]
                
                return final_response
            else:
                return "I apologize, but I couldn't generate a response using the multi-agent system."
                
        except Exception as e:
            logger.error(f"Error in multi-agent response generation: {e}", exc_info=True)
            return f"I'm having trouble with the multi-agent system. Please try again later. Error: {str(e)}"

    async def close(self):
        """Clean up resources."""
        logger.info("Closing multi-agent service")
        try:
            if self._runtime:
                await self._runtime.stop()
                logger.debug("Multi-agent runtime stopped")
            
            if self._model_client:
                # Note: AzureAIChatCompletionClient may not have a close method
                logger.debug("Multi-agent model client cleaned up")
                
        except Exception as e:
            logger.error(f"Error closing multi-agent service: {e}", exc_info=True)


class MultiAgentCoordinator(RoutedAgent):
    """Coordinator agent that receives responses from other agents and sends them back to the user."""
    
    def __init__(self, service: MultiAgentService):
        super().__init__("Multi-agent coordinator")
        self._service = service

    @message_handler
    async def handle_agent_response(self, message: AgentResponse, ctx: MessageContext) -> None:
        """Handle responses from other agents and store them for the user."""
        try:
            # Extract the final assistant message
            final_response = ""
            for msg in reversed(message.context):
                if hasattr(msg, 'source') and msg.source in ['ResearcherAgent', 'SummarizerAgent']:
                    final_response = msg.content
                    break
            
            if not final_response:
                final_response = "I apologize, but I couldn't generate a proper response."
            
            # Store response for the session
            response_message = Message(
                role="assistant",
                content=final_response,
                timestamp=datetime.now()
            )
            
            if message.session_id not in self._service._session_responses:
                self._service._session_responses[message.session_id] = []
            
            self._service._session_responses[message.session_id].append(response_message)
            
            logger.info(f"Coordinator stored response for session {message.session_id}")
            
        except Exception as e:
            logger.error(f"Error in coordinator handling response: {e}", exc_info=True)
            # Store error response
            error_message = Message(
                role="assistant",
                content=f"I encountered an error processing the response: {str(e)}",
                timestamp=datetime.now()
            )
            
            if message.session_id not in self._service._session_responses:
                self._service._session_responses[message.session_id] = []
            
            self._service._session_responses[message.session_id].append(error_message)


# Global service instance
multi_agent_service = MultiAgentService()