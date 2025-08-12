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
    user_message: str
    chat_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """Model for chat message response"""
    message_id: str
    user_id: str
    chat_id: str
    date: datetime
    user_message: str
    assistant_message: str

class ChatMessageUpdate(BaseModel):
    """Model for updating a chat message"""
    user_message: Optional[str] = None

class ChatRequest(BaseModel):
    """Model for chat request"""
    user_id: str
    message: str

class ChatResponse(BaseModel):
    """Model for chat response"""
    user_message: str
    bot_response: str
    message_id: str
    chat_id: str
    timestamp: datetime

class DocumentQueryRequest(BaseModel):
    """Model for document query request - searches all user documents"""
    query: str
    user_id: str
    # document_id removed - now searches across all user documents
    # chat_id moved to query parameter

class DocumentQueryResponse(BaseModel):
    """Model for document query response"""
    answer: str
    source_chunks: list
    query: str
    context_used: int
    chat_id: str  # Return chat_id for conversation tracking
    message_id: str  # Return message_id for tracking

class ChatRequest(BaseModel):
    """Model for sending a chat message"""
    message: str
    user_id: str
