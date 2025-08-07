"""
Message Routes
Chat message management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from core import crud
from data_validation import ChatMessageResponse, ChatMessageUpdate, ChatRequest, ChatResponse
from pymongo.errors import PyMongoError, DuplicateKeyError, ServerSelectionTimeoutError
from bson.errors import InvalidId

router = APIRouter()

def handle_database_exceptions(e: Exception, operation: str = "operation"):
    """
    Centralized exception handler for database operations
    """
    if isinstance(e, HTTPException):
        raise e
    elif isinstance(e, InvalidId):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format provided"
        )
    elif isinstance(e, ServerSelectionTimeoutError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection timeout. Please try again later."
        )
    elif isinstance(e, DuplicateKeyError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate data detected. Please try again with different values."
        )
    elif isinstance(e, PyMongoError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Database error occurred while {operation}"
        )
    elif isinstance(e, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data provided: {str(e)}"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while {operation}"
        )

@router.post("/chat", tags=["Messages"])
async def chat_endpoint(
    chat_request: ChatRequest, 
    chat_id: Optional[str] = Query(None, description="Optional chat ID for continuing existing conversations")
) -> ChatResponse:
    """ Enhanced chat endpoint - saves conversation to database with page-based chat IDs """
    try:
        user = await crud.get_user(chat_request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {chat_request.user_id} not found"
            )
        from data_validation import ChatMessageCreate
        message_data = ChatMessageCreate(
            user_id=chat_request.user_id,
            user_message=chat_request.message,
            chat_id=chat_id  # Pass the chat_id from query parameter (or None for new page)
        )
        
        saved_message = await crud.create_chat_message(message_data)
        
        return ChatResponse(
            user_message=chat_request.message,
            bot_response=saved_message.assistant_message,
            message_id=saved_message.message_id,
            chat_id=saved_message.chat_id,  # Return the chat_id (created or provided)
            timestamp=saved_message.date
        )
    except ValueError as e:
        if "does not exist" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid data provided: {str(e)}"
            )
    except Exception as e:
        handle_database_exceptions(e, "processing your message")

@router.get("/users/{user_id}/messages", response_model=List[ChatMessageResponse], tags=["Messages"])
async def get_user_messages(user_id: str):
    """ Get all chat messages for a specific user """
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    try:
        messages = await crud.get_user_chat_messages(user_id)
        return messages
    except Exception as e:
        handle_database_exceptions(e, "retrieving messages")

@router.get("/chat/{chat_id}/messages", response_model=List[ChatMessageResponse], tags=["Messages"])
async def get_chat_messages(chat_id: str):
    """ Get all messages for a specific chat ID (page) """
    try:
        messages = await crud.get_chat_messages_by_chat_id(chat_id)
        return messages
    except Exception as e:
        handle_database_exceptions(e, "retrieving chat messages")

@router.get("/messages/{message_id}", response_model=ChatMessageResponse, tags=["Messages"])
async def get_message(message_id: str):
    """ Get a specific message by ID """
    try:
        message = await crud.get_chat_message(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message ID: {str(e)}"
        )
    except Exception as e:
        handle_database_exceptions(e, "retrieving message")

@router.put("/messages/{message_id}", response_model=ChatMessageResponse, tags=["Messages"])
async def update_message(message_id: str, update_data: ChatMessageUpdate):
    """ Update a specific message """
    try:
        message = await crud.get_chat_message(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        updated_message = await crud.update_chat_message(message_id, update_data)
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message"
            )
        return updated_message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
        handle_database_exceptions(e, "updating message")

@router.delete("/messages/{message_id}", tags=["Messages"])
async def delete_message(message_id: str):
    """ Delete a specific message """
    try:
        message = await crud.get_chat_message(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        success = await crud.delete_chat_message(message_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete message"
            )
        return {"message": "Message deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message ID: {str(e)}"
        )
    except Exception as e:
        handle_database_exceptions(e, "deleting message")

@router.delete("/users/{user_id}/messages", tags=["Messages"])
async def delete_user_messages(user_id: str):
    """ Delete all messages for a specific user """
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    try:
        deleted_count = await crud.delete_user_chat_messages(user_id)
        return {
            "message": f"Deleted {deleted_count} messages for user {user_id}",
            "deleted_count": deleted_count
        }
    except Exception as e:
        handle_database_exceptions(e, "deleting user messages")

@router.delete("/chat/{chat_id}/messages", tags=["Messages"])
async def delete_chat_messages(chat_id: str):
    """ Delete all messages for a specific chat ID (page) """
    try:
        deleted_count = await crud.delete_chat_messages_by_chat_id(chat_id)
        return {
            "message": f"Deleted {deleted_count} messages for chat {chat_id}",
            "deleted_count": deleted_count
        }
    except Exception as e:
        handle_database_exceptions(e, "deleting chat messages")