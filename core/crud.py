"""
Database CRUD Operations - Database Agnostic
Now works with any database through the abstraction layer
"""

from datetime import datetime
from typing import List, Optional
import uuid

from database.factory import get_db
from data_validation import UserResponse, ChatMessageCreate, ChatMessageResponse
from core.mistral_service import mistral_service

# User CRUD Operations
async def create_user() -> UserResponse:
    """Create a new user"""
    db = get_db()
    
    user_data = {
        "id": str(uuid.uuid4()),  # Generate unique ID
        "created_at": datetime.utcnow(),
    }
    
    await db.create_user(user_data)
    
    # Count total chats for this user
    total_chats = await db.count_user_messages(user_data["id"])
    
    return UserResponse(
        id=user_data["id"],
        created_at=user_data["created_at"],
        total_chats=total_chats
    )

async def get_user(user_id: str) -> Optional[UserResponse]:
    """Get a user by ID"""
    db = get_db()
    user = await db.get_user(user_id)
    if user:
        total_chats = await db.count_user_messages(user_id)
        return UserResponse(
            id=user["id"],
            created_at=user["created_at"],
            total_chats=total_chats
        )
    return None

async def get_all_users() -> List[UserResponse]:
    """Get all users"""
    db = get_db()
    user_list = await db.get_all_users()
    users = []
    for user in user_list:
        total_chats = await db.count_user_messages(user["id"])
        users.append(UserResponse(
            id=user["id"],
            created_at=user["created_at"],
            total_chats=total_chats
        ))
    return users

async def delete_user(user_id: str) -> bool:
    """Delete a user and all their messages"""
    db = get_db()
    return await db.delete_user(user_id)

# Chat Message CRUD Operations
async def validate_chat_id_exists(chat_id: str) -> bool:
    """Check if a chat_id exists in the database"""
    db = get_db()
    messages = await db.get_messages_by_chat_id(chat_id)
    return len(messages) > 0

async def create_chat_message(message_data: ChatMessageCreate) -> ChatMessageResponse:
    """Create a new chat message with AI response from Mistral"""
    db = get_db()
    
    # Generate chat_id if not provided (create new page)
    chat_id = message_data.chat_id if message_data.chat_id else str(uuid.uuid4())
    
    # If chat_id was provided, validate it exists (unless it's a new chat)
    if message_data.chat_id and not await validate_chat_id_exists(message_data.chat_id):
        raise ValueError(f"Chat ID '{message_data.chat_id}' does not exist")
    
    # Get conversation history for context-aware AI response
    conversation_history = []
    if message_data.chat_id:  # If existing chat, get previous messages
        previous_messages = await db.get_messages_by_chat_id(message_data.chat_id)
        conversation_history = previous_messages
    
    # Generate AI response using Mistral AI with conversation context
    ai_response = await mistral_service.generate_response(
        user_message=message_data.user_message,
        user_id=message_data.user_id,
        conversation_history=conversation_history
    )
    
    chat_data = {
        "message_id": str(uuid.uuid4()),
        "user_id": message_data.user_id,
        "chat_id": chat_id,  # Add chat_id for page-based conversations
        "date": datetime.utcnow(),
        "user_message": message_data.user_message,
        "assistant_message": ai_response  # Now using actual AI response from Mistral
    }
    
    await db.create_message(chat_data)
    
    return ChatMessageResponse(
        message_id=chat_data["message_id"],
        user_id=chat_data["user_id"],
        chat_id=chat_data["chat_id"],  # Return the chat_id
        date=chat_data["date"],
        user_message=chat_data["user_message"],
        assistant_message=chat_data["assistant_message"]
    )

async def get_chat_message(message_id: str) -> Optional[ChatMessageResponse]:
    """Get a chat message by ID"""
    db = get_db()
    message = await db.get_message(message_id)
    if message:
        return ChatMessageResponse(
            message_id=message["message_id"],
            user_id=message["user_id"],
            chat_id=message.get("chat_id", ""),  # Handle existing messages without chat_id
            date=message["date"],
            user_message=message["user_message"],
            assistant_message=message["assistant_message"]
        )
    return None

async def get_user_chat_messages(user_id: str) -> List[ChatMessageResponse]:
    """Get all chat messages for a user"""
    db = get_db()
    message_list = await db.get_user_messages(user_id)
    messages = []
    for message in message_list:
        messages.append(ChatMessageResponse(
            message_id=message["message_id"],
            user_id=message["user_id"],
            chat_id=message.get("chat_id", ""),  # Handle existing messages without chat_id
            date=message["date"],
            user_message=message["user_message"],
            assistant_message=message["assistant_message"]
        ))
    return messages

async def get_chat_messages_by_chat_id(chat_id: str) -> List[ChatMessageResponse]:
    """Get all messages for a specific chat ID (page)"""
    db = get_db()
    message_list = await db.get_messages_by_chat_id(chat_id)
    messages = []
    for message in message_list:
        messages.append(ChatMessageResponse(
            message_id=message["message_id"],
            user_id=message["user_id"],
            chat_id=message["chat_id"],
            date=message["date"],
            user_message=message["user_message"],
            assistant_message=message["assistant_message"]
        ))
    return messages

async def update_chat_message(message_id: str, update_data: dict) -> Optional[ChatMessageResponse]:
    """Update a chat message"""
    db = get_db()
    
    # Get the current message
    current_message = await db.get_message(message_id)
    if not current_message:
        return None
    
    # Update with new data
    updated_data = {**current_message, **update_data}
    updated_message = await db.update_message(message_id, updated_data)
    
    if updated_message:
        return ChatMessageResponse(
            message_id=updated_message["message_id"],
            user_id=updated_message["user_id"],
            date=updated_message["date"],
            user_message=updated_message["user_message"],
            assistant_message=updated_message["assistant_message"]
        )
    return None

async def delete_chat_message(message_id: str) -> bool:
    """Delete a chat message"""
    db = get_db()
    return await db.delete_message(message_id)

async def delete_user_chat_messages(user_id: str) -> int:
    """Delete all chat messages for a user and return count of deleted messages"""
    db = get_db()
    return await db.delete_user_messages(user_id)

# Statistics
async def get_user_message_count(user_id: str) -> int:
    """Get the count of messages for a user"""
    db = get_db()
    return await db.count_user_messages(user_id)

async def get_all_messages() -> List[ChatMessageResponse]:
    """Get all chat messages from all users"""
    db = get_db()
    message_list = await db.get_all_messages()
    messages = []
    for message in message_list:
        messages.append(ChatMessageResponse(
            message_id=message["message_id"],
            user_id=message["user_id"],
            date=message["date"],
            user_message=message["user_message"],
            assistant_message=message["assistant_message"]
        ))
    return messages
