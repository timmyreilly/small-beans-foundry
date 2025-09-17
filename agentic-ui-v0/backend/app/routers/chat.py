from fastapi import APIRouter, HTTPException
from app.models.models import ChatRequest, ChatResponse
from app.services.session import session_service
from app.services.agent import agent_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import multi-agent service with error handling
try:
    from app.services.multi_agent import multi_agent_service
    MULTI_AGENT_AVAILABLE = True
    logger.info("Multi-agent service loaded successfully")
except ImportError as e:
    logger.warning(f"Multi-agent service not available: {e}")
    multi_agent_service = None
    MULTI_AGENT_AVAILABLE = False


# Initialize telemetry tracer and meter
try:
    from app.config.telemetry import telemetry_config
    tracer = telemetry_config.get_tracer(__name__)
    meter = telemetry_config.get_meter(__name__)
    
    # Create metrics
    chat_requests_counter = meter.create_counter(
        name="chat_requests_total",
        description="Total number of chat requests",
        unit="1"
    )
    
    chat_response_time_histogram = meter.create_histogram(
        name="chat_response_time_seconds",
        description="Time taken to process chat requests",
        unit="s"
    )
    
    session_operations_counter = meter.create_counter(
        name="session_operations_total",
        description="Total number of session operations",
        unit="1"
    )
    
    logger.info("Telemetry instrumentation loaded for chat router")
except Exception as e:
    logger.warning(f"Telemetry not available for chat router: {e}")
    tracer = None
    chat_requests_counter = None
    chat_response_time_histogram = None
    session_operations_counter = None

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint using single AutoGen agent"""
    start_time = datetime.now()
    
    # Start telemetry span
    if tracer:
        with tracer.start_span("chat_request") as span:
            span.set_attribute("session_id", request.session_id or "new")
            span.set_attribute("message_length", len(request.message))
            return await _process_chat_with_telemetry(request, span, start_time)
    else:
        return await _process_chat_internal(request, start_time)

async def _process_chat_with_telemetry(request: ChatRequest, span, start_time: datetime):
    """Process chat with telemetry tracking"""
    try:
        result = await _process_chat_internal(request, start_time)
        
        # Record success metrics
        if chat_requests_counter:
            chat_requests_counter.add(1, {"status": "success"})
        
        if chat_response_time_histogram:
            response_time = (datetime.now() - start_time).total_seconds()
            chat_response_time_histogram.record(response_time, {"status": "success"})
        
        span.set_attribute("response_length", len(result.response))
        span.set_attribute("response_time_seconds", (datetime.now() - start_time).total_seconds())
        span.set_attribute("final_session_id", result.session_id)
        span.set_attribute("status", "success")
        
        return result
        
    except HTTPException as e:
        # Record HTTP error metrics
        if chat_requests_counter:
            chat_requests_counter.add(1, {"status": "http_error", "status_code": str(e.status_code)})
        
        if chat_response_time_histogram:
            response_time = (datetime.now() - start_time).total_seconds()
            chat_response_time_histogram.record(response_time, {"status": "http_error"})
        
        span.set_attribute("status", "http_error")
        span.set_attribute("status_code", e.status_code)
        span.set_attribute("error_detail", str(e.detail))
        raise
        
    except Exception as e:
        # Record system error metrics
        if chat_requests_counter:
            chat_requests_counter.add(1, {"status": "system_error"})
        
        if chat_response_time_histogram:
            response_time = (datetime.now() - start_time).total_seconds()
            chat_response_time_histogram.record(response_time, {"status": "system_error"})
        
        span.record_exception(e)
        span.set_attribute("status", "system_error")
        span.set_attribute("error_type", type(e).__name__)
        raise

async def _process_chat_internal(request: ChatRequest, start_time: datetime):
    """Internal chat processing logic"""
    try:
        # Get or create session
        try:
            session = session_service.get_or_create_session(
                request.session_id, 
                request.user_details
            )
            
            if session_operations_counter:
                session_operations_counter.add(1, {"operation": "get_or_create_session"})
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Session error: {str(e)}")
        
        # Add user message to session
        user_message = session_service.add_message(
            session.id, 
            request.message, 
            "user"
        )
        
        if session_operations_counter:
            session_operations_counter.add(1, {"operation": "add_user_message"})
        
        # Get conversation history for context
        conversation_context = session_service.get_conversation_context(session.id, limit=10)
        
        # Generate AI response using single AutoGen agent
        try:
            ai_response = await agent_service.generate_response(
                conversation_context[:-1],  # Exclude the message we just added
                request.message
            )
        except Exception as e:
            logger.error(f"Agent service error: {e}")
            ai_response = f"I'm having trouble connecting to the AI service. Please try again later. Error: {str(e)}"
        
        # Add AI response to session
        ai_message = session_service.add_message(
            session.id,
            ai_response,
            "assistant"
        )
        
        if session_operations_counter:
            session_operations_counter.add(1, {"operation": "add_ai_message"})
        
        return ChatResponse(
            response=ai_response,
            session_id=session.id,
            message_id=ai_message.id  # ai_message.id is expected to be set, but may be None depending on Message.__init__ implementation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    """Get conversation history for a session"""
    try:
        messages = session_service.get_messages(session_id)
        return {"messages": [{"id": msg.id, "content": msg.content, "role": msg.role, "timestamp": msg.timestamp} for msg in messages]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/chat/multi-agent", response_model=ChatResponse)
async def multi_agent_chat(request: ChatRequest):
    """Multi-agent chat endpoint using researcher and summarizer agents"""
    if not MULTI_AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Multi-agent service is not available. Please use the single agent endpoint."
        )
    
    start_time = datetime.now()
    
    # Start telemetry span
    if tracer:
        with tracer.start_span("multi_agent_chat_request") as span:
            span.set_attribute("session_id", request.session_id or "new")
            span.set_attribute("message_length", len(request.message))
            span.set_attribute("agent_mode", "multi_agent")
            return await _process_multi_agent_chat_with_telemetry(request, span, start_time)
    else:
        return await _process_multi_agent_chat_internal(request, start_time)


async def _process_multi_agent_chat_with_telemetry(request: ChatRequest, span, start_time: datetime):
    """Process multi-agent chat with telemetry tracking"""
    try:
        result = await _process_multi_agent_chat_internal(request, start_time)
        
        # Record success metrics
        if chat_requests_counter:
            chat_requests_counter.add(1, {"status": "success", "agent_mode": "multi_agent"})
        
        if chat_response_time_histogram:
            response_time = (datetime.now() - start_time).total_seconds()
            chat_response_time_histogram.record(response_time, {"status": "success", "agent_mode": "multi_agent"})
        
        span.set_attribute("response_length", len(result.response))
        span.set_attribute("response_time_seconds", (datetime.now() - start_time).total_seconds())
        span.set_attribute("final_session_id", result.session_id)
        span.set_attribute("status", "success")
        
        return result
        
    except HTTPException as e:
        # Record HTTP error metrics
        if chat_requests_counter:
            chat_requests_counter.add(1, {"status": "http_error", "status_code": str(e.status_code), "agent_mode": "multi_agent"})
        
        if chat_response_time_histogram:
            response_time = (datetime.now() - start_time).total_seconds()
            chat_response_time_histogram.record(response_time, {"status": "http_error", "agent_mode": "multi_agent"})
        
        span.set_attribute("status", "http_error")
        span.set_attribute("status_code", e.status_code)
        span.set_attribute("error_detail", str(e.detail))
        raise
        
    except Exception as e:
        # Record system error metrics
        if chat_requests_counter:
            chat_requests_counter.add(1, {"status": "system_error", "agent_mode": "multi_agent"})
        
        if chat_response_time_histogram:
            response_time = (datetime.now() - start_time).total_seconds()
            chat_response_time_histogram.record(response_time, {"status": "system_error", "agent_mode": "multi_agent"})
        
        span.record_exception(e)
        span.set_attribute("status", "system_error")
        span.set_attribute("error_type", type(e).__name__)
        raise


async def _process_multi_agent_chat_internal(request: ChatRequest, start_time: datetime):
    """Internal multi-agent chat processing logic"""
    try:
        # Get or create session
        try:
            session = session_service.get_or_create_session(
                request.session_id, 
                request.user_details
            )
            
            if session_operations_counter:
                session_operations_counter.add(1, {"operation": "get_or_create_session", "agent_mode": "multi_agent"})
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Session error: {str(e)}")
        
        # Add user message to session
        user_message = session_service.add_message(
            session.id, 
            request.message, 
            "user"
        )
        
        if session_operations_counter:
            session_operations_counter.add(1, {"operation": "add_user_message", "agent_mode": "multi_agent"})
        
        # Get conversation history for context
        conversation_context = session_service.get_conversation_context(session.id, limit=10)
        
        # Generate AI response using multi-agent system
        try:
            if multi_agent_service is None:
                raise ValueError("Multi-agent service is not available")
            ai_response = await multi_agent_service.generate_response(
                conversation_context[:-1],  # Exclude the message we just added
                request.message
            )
        except Exception as e:
            logger.error(f"Multi-agent service error: {e}")
            ai_response = f"I'm having trouble with the multi-agent system. Please try again later. Error: {str(e)}"
        
        # Add AI response to session
        ai_message = session_service.add_message(
            session.id,
            ai_response,
            "assistant"
        )
        
        if session_operations_counter:
            session_operations_counter.add(1, {"operation": "add_ai_message", "agent_mode": "multi_agent"})
        
        return ChatResponse(
            response=ai_response,
            session_id=session.id,
            message_id=ai_message.id or "unknown"  # Handle potential None case
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in multi-agent chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/agent-modes")
async def get_agent_modes():
    """Get available agent modes"""
    modes = [
        {
            "id": "single",
            "name": "Single Agent",
            "description": "Standard AI assistant with general conversation capabilities",
            "available": True
        }
    ]
    
    if MULTI_AGENT_AVAILABLE:
        modes.append({
            "id": "multi",
            "name": "Multi-Agent Research",
            "description": "Collaborative AI team with internet research and summarization capabilities",
            "available": True
        })
    else:
        modes.append({
            "id": "multi",
            "name": "Multi-Agent Research",
            "description": "Collaborative AI team (currently unavailable)",
            "available": False
        })
    
    return {"modes": modes}