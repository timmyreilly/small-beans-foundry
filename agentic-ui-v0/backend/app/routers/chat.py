from fastapi import APIRouter, HTTPException
from app.models.models import ChatRequest, ChatResponse
from app.services.session import session_service
from app.services.agent import agent_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint using single AutoGen agent"""
    try:
        # Get or create session
        try:
            session = session_service.get_or_create_session(
                request.session_id, 
                request.user_details
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Session error: {str(e)}")
        
        # Add user message to session
        user_message = session_service.add_message(
            session.id, 
            request.message, 
            "user"
        )
        
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
        
        return ChatResponse(
            response=ai_response,
            session_id=session.id,
            message_id=ai_message.id
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