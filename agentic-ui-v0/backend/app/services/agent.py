import asyncio
import os
import logging
from typing import List, Optional
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential
from app.models.models import Message
from app.config.azure import azure_config
from datetime import datetime, timezone, timedelta
from app.config.telemetry import telemetry_config

logger = logging.getLogger(__name__)

# Initialize telemetry tracer and meter
try:
    tracer = telemetry_config.get_tracer(__name__)
    meter = telemetry_config.get_meter(__name__)
    
    # Create metrics
    conversation_counter = meter.create_counter(
        name="agent_conversations_total",
        description="Total number of agent conversations",
        unit="1"
    )
    
    response_time_histogram = meter.create_histogram(
        name="agent_response_time_seconds",
        description="Time taken to generate agent responses",
        unit="s"
    )
    
    message_length_histogram = meter.create_histogram(
        name="agent_message_length_chars",
        description="Length of messages processed by agent",
        unit="chars"
    )
    
    logger.info("Telemetry instrumentation loaded for agent service")
except Exception as e:
    logger.warning(f"Telemetry not available for agent service: {e}")
    tracer = None
    conversation_counter = None
    response_time_histogram = None
    message_length_histogram = None

class SingleAgentService:
    def __init__(self):
        self._model_client: Optional[AzureAIChatCompletionClient] = None
        self._assistant_agent: Optional[AssistantAgent] = None
        logger.debug("SingleAgentService initialized")

    def _clean_response_content(self, content: str) -> str:
        """Clean and sanitize response content from AutoGen agent"""
        if not content:
            return "I apologize, but I couldn't generate a response."
        
        # Convert to string if it's not already
        content = str(content)
        
        # Remove common AutoGen formatting artifacts
        # Remove TextMessage wrapper if present
        if content.startswith("TextMessage("):
            content = content[12:]  # Remove "TextMessage("
            if content.endswith(")"):
                content = content[:-1]  # Remove trailing ")"
        
        # Handle escaped characters properly
        import json
        try:
            # Try to parse as JSON string to handle escaping
            if content.startswith('"') and content.endswith('"'):
                content = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, manually handle common escape sequences
            content = content.replace('\\n', '\n')
            content = content.replace('\\t', '\t')
            content = content.replace('\\r', '\r')
            content = content.replace('\\"', '"')
            content = content.replace("\\'", "'")
            content = content.replace('\\\\', '\\')
        
        # Remove any remaining quotes that might wrap the entire content
        content = content.strip()
        if ((content.startswith('"') and content.endswith('"')) or 
            (content.startswith("'") and content.endswith("'"))):
            content = content[1:-1]
        
        # Final cleanup - remove excessive whitespace
        content = ' '.join(content.split())
        
        return content if content else "I apologize, but I couldn't generate a response."

    async def _initialize_agent(self):
        """Initialize the single AutoGen agent"""
        if self._assistant_agent is None:
            try:
                if not azure_config.is_configured():
                    raise ValueError(
                        "Azure configuration is incomplete. Please check environment variables."
                    )

                logger.info("Initializing single AutoGen agent")

                # Create AzureAIChatCompletionClient
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

                # Create single AssistantAgent
                self._assistant_agent = AssistantAgent(
                    name="helpful_assistant",
                    model_client=self._model_client,
                    description="A helpful AI assistant for general conversations",
                    system_message="You are a helpful and friendly AI assistant. Provide clear, concise, and helpful responses to user questions. Be conversational and engaging while remaining professional.",
                )

                logger.info(f"Single agent initialized successfully with model: {azure_config.get_deployment_name()}")

            except Exception as e:
                logger.error(f"Error initializing single agent: {e}", exc_info=True)
                raise

    async def generate_response(self, messages: List[Message], user_message: str) -> str:
        """Generate a response using the single AutoGen agent"""
        start_time = datetime.now()
        
        # Start telemetry span
        if tracer:
            with tracer.start_span("agent_generate_response") as span:
                span.set_attribute("user_message_length", len(user_message))
                span.set_attribute("conversation_context_length", len(messages))
                return await self._generate_response_with_telemetry(messages, user_message, span, start_time)
        else:
            return await self._generate_response_internal(messages, user_message, start_time)
    
    async def _generate_response_with_telemetry(self, messages: List[Message], user_message: str, span, start_time: datetime) -> str:
        """Internal method with telemetry tracking"""
        try:
            result = await self._generate_response_internal(messages, user_message, start_time)
            
            # Record success metrics
            if conversation_counter:
                conversation_counter.add(1, {"status": "success", "agent_type": "autogen_assistant"})
            
            if response_time_histogram:
                response_time = (datetime.now() - start_time).total_seconds()
                response_time_histogram.record(response_time, {"status": "success"})
            
            if message_length_histogram:
                message_length_histogram.record(len(result), {"message_type": "response"})
                message_length_histogram.record(len(user_message), {"message_type": "request"})
            
            span.set_attribute("response_length", len(result))
            span.set_attribute("response_time_seconds", (datetime.now() - start_time).total_seconds())
            span.set_attribute("status", "success")
            
            return result
            
        except Exception as e:
            # Record error metrics
            if conversation_counter:
                conversation_counter.add(1, {"status": "error", "agent_type": "autogen_assistant"})
            
            if response_time_histogram:
                response_time = (datetime.now() - start_time).total_seconds()
                response_time_histogram.record(response_time, {"status": "error"})
            
            span.record_exception(e)
            span.set_attribute("status", "error")
            span.set_attribute("error_type", type(e).__name__)
            raise
    
    async def _generate_response_internal(self, messages: List[Message], user_message: str, start_time: datetime) -> str:
        """Internal response generation logic"""
        try:
            logger.debug("Starting single agent response generation")
            await self._initialize_agent()

            if not self._assistant_agent:
                raise ValueError("Single agent not initialized")

            # Convert conversation history to AutoGen messages format
            autogen_messages = []

            # Add recent conversation context (last 10 messages)
            recent_messages = messages[-10:] if len(messages) > 10 else messages
            logger.debug(f"Processing {len(recent_messages)} recent messages for context")

            for msg in recent_messages:
                autogen_messages.append(
                    TextMessage(
                        content=msg.content,
                        source=msg.role,  # 'user' or 'assistant'
                    )
                )

            # Add the current user message
            autogen_messages.append(TextMessage(content=user_message, source="user"))

            logger.debug(f"Sending {len(autogen_messages)} messages to single agent")

            # Generate response using AssistantAgent
            result = await self._assistant_agent.on_messages(
                autogen_messages, CancellationToken()
            )

            logger.debug(f"Raw AutoGen result type: {type(result)}")
            logger.debug(f"Raw AutoGen result: {str(result)[:200]}...")

            # Extract the response content
            if hasattr(result, "messages") and result.messages:
                logger.debug("Successfully received response from single agent")
                # Get the last message from the assistant
                for msg in reversed(result.messages):
                    if hasattr(msg, "source") and msg.source == self._assistant_agent.name:
                        raw_content = msg.content
                        logger.debug(f"Raw message content: {repr(raw_content)}")
                        return self._clean_response_content(raw_content)
                    elif hasattr(msg, "content"):
                        raw_content = msg.content
                        logger.debug(f"Raw message content (no source): {repr(raw_content)}")
                        return self._clean_response_content(raw_content)

            # Fallback: convert result to string and clean it
            response_text = str(result) if result else "I apologize, but I couldn't generate a response."
            
            # Clean up response if it contains unwanted formatting
            if "TextMessage" in response_text or "content=" in response_text:
                import re
                # Try to extract content from TextMessage format with proper escaping handling
                # Look for content within quotes, handling escaped quotes properly
                content_match = re.search(r"content=['\"](.+?)['\"](?:,|\s|$)", response_text, re.DOTALL)
                if content_match:
                    return self._clean_response_content(content_match.group(1))
                
                # Alternative pattern for different quote styles
                content_match = re.search(r"content:\s*['\"](.+?)['\"]", response_text, re.DOTALL)
                if content_match:
                    return self._clean_response_content(content_match.group(1))

            return self._clean_response_content(response_text)

        except Exception as e:
            logger.error(f"Error generating single agent response: {e}", exc_info=True)
            return f"I'm having trouble connecting to the AI service. Please try again later. Error: {str(e)}"

    async def close(self):
        """Clean up resources"""
        logger.info("Closing single agent service")
        try:
            if self._model_client:
                logger.debug("Cleaned up AzureAIChatCompletionClient")
        except Exception as e:
            logger.error(f"Error closing single agent service: {e}", exc_info=True)

# Global service instance
agent_service = SingleAgentService()