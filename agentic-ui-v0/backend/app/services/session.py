from typing import Dict, List, Optional
from app.models.models import Session, Message, UserDetails
import logging

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    def get_or_create_session(self, session_id: Optional[str], user_details: Optional[UserDetails] = None) -> Session:
        """Get an existing session or create a new one"""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            logger.debug(f"Retrieved existing session: {session_id}")
            return session
        
        # Create new session
        session = Session(user_details=user_details)
        self._sessions[session.id] = session
        logger.info(f"Created new session: {session.id}")
        return session
    
    def add_message(self, session_id: str, content: str, role: str) -> Message:
        """Add a message to a session"""
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        message = Message(content=content, role=role)
        self._sessions[session_id].messages.append(message)
        logger.debug(f"Added {role} message to session {session_id}")
        return message
    
    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages from a session"""
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        return self._sessions[session_id].messages
    
    def get_conversation_context(self, session_id: str, limit: int = 10) -> List[Message]:
        """Get recent conversation context"""
        messages = self.get_messages(session_id)
        return messages[-limit:] if len(messages) > limit else messages

# Global service instance
session_service = SessionService()