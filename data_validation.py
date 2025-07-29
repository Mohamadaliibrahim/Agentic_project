"""
Data Validation Models
This module contains all Pydantic models for request/response validation
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Model for creating a new user"""
    pass

class UserResponse(BaseModel):
    """Model for user response"""
    id: str
    created_at: datetime
    total_chats: Optional[int] = 0

class UserUpdate(BaseModel):
    """Model for updating user (if needed in future)"""
    pass

class ChatMessageCreate(BaseModel):
    """Model for creating a new chat message"""
    user_id: str
    user_msg: str
    chat_id: Optional[str] = None  # Optional chat ID for page-based conversations

class ChatMessageResponse(BaseModel):
    """Model for chat message response"""
    id: str
    user_id: str
    chat_id: str  # Chat ID for page-based conversations
    date: datetime
    user_msg: str
    assistant_msg: str

class ChatMessageUpdate(BaseModel):
    """Model for updating a chat message"""
    user_msg: Optional[str] = None

class ChatRequest(BaseModel):
    """Model for chat request"""
    user_id: str
    message: str
    chat_id: Optional[str] = None  # Optional chat ID for page-based conversations

class ChatResponse(BaseModel):
    """Model for chat response"""
    user_message: str
    bot_response: str
    message_id: str
    chat_id: str  # Return the chat ID (created or provided)
    timestamp: datetime
