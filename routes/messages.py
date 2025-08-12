"""
Message Routes
Chat message management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import List, Optional
from core import crud
from data_validation import (
    ChatMessageResponse, ChatMessageUpdate, ChatRequest, ChatResponse
)
from pymongo.errors import PyMongoError, DuplicateKeyError, ServerSelectionTimeoutError
from bson.errors import InvalidId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/messages", tags=["Messages"])

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

# Original API endpoints

@router.post("/chat", tags=["Messages"])
async def chat_endpoint(
    chat_request: ChatRequest, 
    chat_id: Optional[str] = Query(None, description="Optional chat ID for continuing existing conversations")
) -> ChatResponse:
    """ 
    Enhanced chat endpoint with RAG integration and conversation memory
    
    This endpoint:
    1. First tries to find relevant documents using RAG
    2. If documents found, uses RAG + conversation memory for response
    3. If no documents found, uses regular chat with conversation memory
    4. Stores all conversations in the same table with proper metadata
    5. Maintains conversation memory across both chat and document queries
    """
    try:
        user = await crud.get_user(chat_request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {chat_request.user_id} not found"
            )
        
        from database.factory import get_db
        from core.rag_service import rag_service
        from core.mistral_service import mistral_service
        import uuid
        
        # Generate chat_id if not provided (new conversation)
        chat_id = chat_id if chat_id else str(uuid.uuid4())
        
        db = get_db()
        
        # Get conversation history for this chat to provide context
        conversation_history = []
        if chat_id:  # If existing chat, get previous messages
            conversation_history = await db.get_messages_by_chat_id(chat_id)
        
        # Try to query user documents first (RAG functionality)
        rag_result = None
        try:
            rag_result = await rag_service.query_documents(
                query=chat_request.message,
                user_id=chat_request.user_id  # Removed document_id - searches all user documents
            )
        except Exception as e:
            logger.warning(f"RAG query failed, falling back to regular chat: {str(e)}")
        
        assistant_message = ""
        query_type = "chat"
        source_chunks = []
        
        if rag_result and rag_result.get('context_used', 0) > 0:
            # We have document context - use RAG with conversation memory
            query_type = "chat_with_rag"
            source_chunks = rag_result.get('source_chunks', [])
            
            # Build conversation context
            context_messages = []
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 exchanges for context
                    context_messages.append(f"Previous Q: {msg.get('user_message', '')}")
                    context_messages.append(f"Previous A: {msg.get('assistant_message', '')}")
            
            conversation_context = "\n".join(context_messages) if context_messages else "No previous conversation."
            
            # Enhanced prompt for RAG with conversation context
            enhanced_prompt = f"""You are a helpful AI assistant that answers questions based on provided document context and conversation history.

Conversation History:
{conversation_context}

Document Context:
{rag_result.get('context_used', 0)} relevant document chunks found.
Document Information: {rag_result['answer']}

Current Question: {chat_request.message}

Instructions:
- Use both the document context and conversation history to answer
- If the user asks about previous questions or answers, reference the conversation history
- If asking about relationships between current and previous topics, explain connections
- Be contextual and helpful
- If the current question is about something in the conversation history, prioritize that information

Answer:"""
            
            # Generate enhanced response using Mistral with full context
            assistant_message = await mistral_service.generate_response(
                user_message=enhanced_prompt,
                user_id=chat_request.user_id,
                conversation_history=conversation_history
            )
            
            # If enhanced answer is not significantly better, use original RAG answer
            if len(assistant_message.strip()) < 10:
                assistant_message = rag_result['answer']
        
        else:
            # No document context - use regular chat with conversation memory
            query_type = "chat"
            assistant_message = await mistral_service.generate_response(
                user_message=chat_request.message,
                user_id=chat_request.user_id,
                conversation_history=conversation_history
            )
        
        # Get the next sequential message ID for this chat
        next_message_id = await db.get_next_message_id_for_chat(chat_id)
        
        # Store the conversation in database with metadata
        message_data = {
            "message_id": str(next_message_id),
            "user_id": chat_request.user_id,
            "chat_id": chat_id,
            "date": datetime.utcnow(),
            "user_message": chat_request.message,
            "assistant_message": assistant_message,
            "query_type": query_type,  # Mark the type of query
        }
        
        # Add source chunks if we have them from RAG
        if source_chunks:
            message_data["source_chunks"] = source_chunks
        
        await db.create_message(message_data)
        
        return ChatResponse(
            user_message=chat_request.message,
            bot_response=assistant_message,
            message_id=str(next_message_id),
            chat_id=chat_id,
            timestamp=datetime.utcnow()
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