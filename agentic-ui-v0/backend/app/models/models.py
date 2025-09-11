from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import uuid4

class UserDetails(BaseModel):
    name: str
    email: str

class Message(BaseModel):
    id: Optional[str] = None
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid4())
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_details: Optional[UserDetails] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_id: str

class Session(BaseModel):
    id: str
    user_details: Optional[UserDetails] = None
    messages: List[Message] = []
    created_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid4())
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now()
        super().__init__(**data)