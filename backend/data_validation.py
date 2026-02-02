"""
Data Validation Models
This module contains all Pydantic models for request/response validation
"""

from pydantic import BaseModel
from typing import Optional, List
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

class DocumentQueryResponse(BaseModel):
    """Model for document query response"""
    answer: str
    source_chunks: list
    query: str
    context_used: int
    chat_id: str
    message_id: str

class SourceChunk(BaseModel):
    """Model for source chunk information in chat responses"""
    document: str
    chunk: str
    relevance_score: float

class ChatMessageItem(BaseModel):
    """Model for individual chat message in new format"""
    content: str
    userType: str
    timestamp: datetime
    sources: Optional[List[SourceChunk]] = None

class ChatMessagesResponse(BaseModel):
    """Model for chat messages response in new format"""
    messages: list[ChatMessageItem]
    chat_id: Optional[str] = None

class ChatCollectionItem(BaseModel):
    """Model for individual chat in collection"""
    chatId: str
    chatTitle: str
    creation: datetime

class ChatCollectionResponse(BaseModel):
    """Model for chat collection response"""
    chats: list[ChatCollectionItem]

class ChatTitleUpdate(BaseModel):
    """Model for updating chat title"""
    title: str
