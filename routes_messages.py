from fastapi import APIRouter, HTTPException, status
from typing import List
import crud
from models import ChatMessageResponse, ChatMessageUpdate, ChatRequest, ChatResponse
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
async def chat_endpoint(chat_request: ChatRequest) -> ChatResponse:
    """ Enhanced chat endpoint - saves conversation to database with auto-generated response """
    try:
        user = await crud.get_user(chat_request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {chat_request.user_id} not found"
            )
        from models import ChatMessageCreate
        message_data = ChatMessageCreate(
            user_id=chat_request.user_id,
            user_msg=chat_request.message
        )
        
        saved_message = await crud.create_chat_message(message_data)
        
        return ChatResponse(
            user_message=chat_request.message,
            bot_response=saved_message.assistant_msg,
            message_id=saved_message.id,
            timestamp=saved_message.date
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

@router.get("/messages/{message_id}", response_model=ChatMessageResponse, tags=["Messages"])
async def get_chat_message(message_id: str):
    """ Get a specific chat message by ID """
    try:
        message = await crud.get_chat_message(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found"
            )
        return message
    except Exception as e:
        handle_database_exceptions(e, "retrieving the message")

@router.put("/messages/{message_id}", response_model=ChatMessageResponse, tags=["Messages"])
async def update_chat_message(message_id: str, update_data: ChatMessageUpdate):
    """ Update a chat message """
    existing_message = await crud.get_chat_message(message_id)
    if not existing_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with ID {message_id} not found"
        )
    
    update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    no_changes = True
    for field, new_value in update_dict.items():
        current_value = getattr(existing_message, field, None)
        if current_value != new_value:
            no_changes = False
            break
    
    if no_changes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No changes detected. The provided values are identical to the current message content."
        )
    
    try:
        updated_message = await crud.update_chat_message(message_id, update_dict)
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found"
            )
        return updated_message
    except Exception as e:
        handle_database_exceptions(e, "updating the message")

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Messages"])
async def delete_chat_message(message_id: str):
    """ Delete a specific chat message """
    try:
        message = await crud.get_chat_message(message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {message_id} not found"
            )
        
        success = await crud.delete_chat_message(message_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or already deleted"
            )
    except Exception as e:
        handle_database_exceptions(e, "deleting the message")

@router.delete("/users/{user_id}/messages", status_code=status.HTTP_204_NO_CONTENT, tags=["Messages"])
async def delete_user_messages(user_id: str):
    """ Delete all chat messages for a specific usern """
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    try:
        deleted_count = await crud.delete_user_chat_messages(user_id)
        return {"detail": f"Deleted {deleted_count} messages"}
    except Exception as e:
        handle_database_exceptions(e, "deleting messages")
