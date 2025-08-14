"""
Message Routes
Chat message management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import List, Optional
from core import crud
from data_validation import (
    ChatMessageResponse, ChatMessageUpdate, ChatRequest, ChatResponse,
    DocumentQueryRequest, DocumentQueryResponse, ChatCollectionResponse, ChatCollectionItem,
    ChatMessageItem, ChatMessagesResponse, SourceChunk, ChatTitleUpdate
)
from database.factory import get_db
from pymongo.errors import PyMongoError, DuplicateKeyError, ServerSelectionTimeoutError
from bson.errors import InvalidId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat/message", tags=["Messages"])

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

@router.post("", response_model=ChatMessagesResponse, tags=["Messages"])
async def chat_message(
    request: DocumentQueryRequest,
    chat_id: Optional[str] = Query(None, description="Optional chat ID for continuing existing conversations")
):
    """
    Query documents with RAG and conversation memory
    
    This endpoint allows users to ask questions about their uploaded documents.
    It supports conversation memory by tracking chat_id, so users can ask
    follow-up questions and reference previous parts of the conversation.
    
    Returns messages in new format with timestamps for tracking LLM response times.
    
    Example conversation:
    1. "What is machine learning?" -> Returns answer with new chat_id
    2. "How is it different from AI?" -> Uses same chat_id, references previous Q&A
    3. "What was my first question?" -> Can answer "What is machine learning?"
    """
    try:
        from core.rag_service import rag_service
        from core import crud
        import uuid
        from datetime import datetime
        
        # Record message sending timestamp
        message_sent_timestamp = datetime.utcnow()
        
        # Generate chat_id if not provided (new conversation)
        chat_id = chat_id if chat_id else str(uuid.uuid4())
        
        # Get conversation history for this chat to provide context
        conversation_history = []
        if chat_id:  # If existing chat, get previous messages
            db = get_db()
            previous_messages = await db.get_messages_by_chat_id(chat_id)
            conversation_history = previous_messages
        
        # Query documents using RAG - searches across all user documents
        rag_result = await rag_service.query_documents(
            query=request.query,
            user_id=request.user_id  # Removed document_id - searches all user documents
        )
        
        # Enhance the RAG response with conversation context if available
        if conversation_history:
            # Build conversation context for the AI
            context_messages = []
            for msg in conversation_history[-5:]:  # Last 5 exchanges for context
                context_messages.append(f"Previous Q: {msg.get('user_message', '')}")
                context_messages.append(f"Previous A: {msg.get('assistant_message', '')}")
            
            conversation_context = "\n".join(context_messages)
            
            # Enhanced prompt that includes conversation history
            enhanced_prompt = f"""You are answering questions about documents. Use the conversation history to provide contextually relevant responses.

Conversation History:
{conversation_context}

Document Context:
{rag_result.get('context_used', 0)} relevant document chunks found.

Current Question: {request.query}

Document Information: {rag_result['answer']}

Instructions:
- Answer the current question using both the document context and conversation history
- If the user asks about previous questions or answers, reference the conversation history
- If asking about relationships between current and previous topics, explain the connections
- Be specific and helpful

Answer:"""
            
            from core.mistral_service import mistral_service
            enhanced_answer = await mistral_service.generate_response(
                user_message=enhanced_prompt,
                user_id=request.user_id,
                conversation_history=conversation_history
            )
            
            if len(enhanced_answer) > len(rag_result['answer']) * 0.8:
                rag_result['answer'] = enhanced_answer
        
        answer_received_timestamp = datetime.utcnow()
        
        db = get_db()
        next_message_id = await db.get_next_message_id_for_chat(chat_id)
        
        source_info = ""
        sources_list = []
        if rag_result.get('source_chunks'):
            source_info = f" [Sources: {len(rag_result['source_chunks'])} document chunks]"
            sources_list = [
                SourceChunk(
                    document=chunk.get('filename', 'unknown'),
                    chunk=chunk.get('text_preview', chunk.get('text', ''))[:100] + "..." if len(chunk.get('text_preview', chunk.get('text', ''))) > 100 else chunk.get('text_preview', chunk.get('text', '')),
                    relevance_score=chunk.get('similarity_score', 0.0)
                )
                for chunk in rag_result['source_chunks'][:3]
            ]
        
        message_data = {
            "message_id": str(next_message_id),
            "user_id": request.user_id,
            "chat_id": chat_id,
            "date": datetime.utcnow(),
            "user_message": request.query,
            "assistant_message": rag_result['answer'] + source_info,
            "query_type": "document_query",
            "source_chunks": rag_result.get('source_chunks', []),
            "message_sent_timestamp": message_sent_timestamp,
            "answer_received_timestamp": answer_received_timestamp
        }
        
        await db.create_message(message_data)
        

        chat_collection_data = {
            "chat_id": chat_id,
            "user_id": request.user_id,
            "chat_title": request.query[:50] + ("..." if len(request.query) > 50 else ""),
            "creation_date": datetime.utcnow(),
            "last_message_date": datetime.utcnow(),
            "message_count": next_message_id,
            "query_type": "document_query"
        }
        
        existing_collections = await db.get_chat_collections_by_user(request.user_id)
        existing_chat = next((c for c in existing_collections if c.get('chat_id') == chat_id), None)
        
        if existing_chat:
            await db.update_chat_collection_item(chat_id, {
                "last_message_date": datetime.utcnow(),
                "message_count": next_message_id
            })
        else:
            await db.store_chat_collection_item(chat_collection_data)
        
        messages = [
            ChatMessageItem(
                content=request.query,
                userType="user",
                timestamp=message_sent_timestamp,
                sources=[]
            ),
            ChatMessageItem(
                content=rag_result['answer'],
                userType="bot",
                timestamp=answer_received_timestamp,
                sources=sources_list
            )
        ]
        
        return ChatMessagesResponse(messages=messages)
        
    except Exception as e:
        logger.error(f"Error in document query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}"
        )

@router.get("/collection", response_model=ChatCollectionResponse, tags=["Messages"])
async def get_chat_collection(user_id: str = Query(..., description="User ID to get chats for")):
    """
    Get all chats for a given user
    
    Returns a list of chat objects containing:
    - chatId: Unique chat identifier
    - chatTitle: Title/first message of the chat
    - creation: Chat creation timestamp
    """
    try:
        db = get_db()
        
        chats_data = await db.get_chat_collections_by_user(user_id)
        
        chat_items = []
        for chat_data in chats_data:
            chat_item = ChatCollectionItem(
                chatId=chat_data['chat_id'],
                chatTitle=chat_data['chat_title'],
                creation=chat_data['creation_date']
            )
            chat_items.append(chat_item)
        
        return ChatCollectionResponse(chats=chat_items)
        
    except Exception as e:
        logger.error(f"Error getting chat collection for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat collection: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=List[ChatMessageResponse], tags=["Messages"])
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

@router.get("/chat/{chat_id}", response_model=List[ChatMessageResponse], tags=["Messages"])
async def get_chat_messages(chat_id: str):
    """ Get all messages for a specific chat ID (page) """
    try:
        messages = await crud.get_chat_messages_by_chat_id(chat_id)
        return messages
    except Exception as e:
        handle_database_exceptions(e, "retrieving chat messages")

@router.get("/{message_id}", response_model=ChatMessageResponse, tags=["Messages"])
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

@router.put("/{message_id}", response_model=ChatMessageResponse, tags=["Messages"])
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

@router.delete("/{message_id}", tags=["Messages"])
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

@router.delete("/users/{user_id}", tags=["Messages"])
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

@router.delete("/chat/{chat_id}", tags=["Messages"])
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

@router.put("/chat/{chat_id}/title", tags=["Messages"])
async def update_chat_title(chat_id: str, title_update: ChatTitleUpdate):
    """ Update the title of a chat """
    try:
        db = get_db()
        
        # Update the chat title in the chat_collections
        result = await db.update_chat_collection_item(chat_id, {
            "chat_title": title_update.title
        })
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with ID {chat_id} not found"
            )
        
        return {
            "message": "Chat title updated successfully",
            "chat_id": chat_id,
            "new_title": title_update.title
        }
    except HTTPException:
        # Re-raise HTTPExceptions as they are
        raise
    except Exception as e:
        logger.error(f"Error updating chat title: {str(e)}")
        handle_database_exceptions(e, "updating chat title")