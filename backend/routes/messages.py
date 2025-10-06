"""
Message Routes
Chat message management endpoints with comprehensive session-based logging
"""

from fastapi import APIRouter, HTTPException, status, Query, Path
from typing import List, Optional
from core import crud
from core.logger import (
    get_logger, log_debug_session, log_info_session, 
    log_timing, log_prompt, log_error_session
)
from data_validation import (
    ChatMessageResponse, ChatMessageUpdate, ChatRequest, ChatResponse,
    DocumentQueryRequest, DocumentQueryResponse, ChatCollectionResponse, ChatCollectionItem,
    ChatMessageItem, ChatMessagesResponse, SourceChunk, ChatTitleUpdate
)
from database.factory import get_db
from pymongo.errors import PyMongoError, DuplicateKeyError, ServerSelectionTimeoutError
from bson.errors import InvalidId
from datetime import datetime
import uuid

logger = get_logger("routes.messages")
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
        
        # Generate unique session ID for tracking this message through all stages
        session_id = str(uuid.uuid4())[:8]
        
        # Record message sending timestamp
        message_sent_timestamp = datetime.utcnow()
        
        # === COMPREHENSIVE USER MESSAGE LOGGING ===
        log_info_session(session_id, "messages.py", f"NEW USER MESSAGE | User: {request.user_id} | Query: '{request.query}' | Length: {len(request.query)} chars")
        log_timing(session_id, "message_start", 0.0, "User message received")
        
        # Generate chat_id if not provided (new conversation)
        chat_id = chat_id if chat_id else str(uuid.uuid4())
        
        if not chat_id:
            log_debug_session(session_id, "messages.py", f"Generated new chat ID: {chat_id}")
        else:
            log_debug_session(session_id, "messages.py", f"Using existing chat ID: {chat_id}")
        
        # Get conversation history for this chat to provide context
        log_debug_session(session_id, "messages.py", "Retrieving conversation history...")
        history_start = datetime.utcnow()
        
        conversation_history = []
        if chat_id:  # If existing chat, get previous messages
            db = get_db()
            previous_messages = await db.get_messages_by_chat_id(chat_id)
            conversation_history = previous_messages
            history_duration = (datetime.utcnow() - history_start).total_seconds()
            log_timing(session_id, "conversation_history", history_duration, f"Retrieved {len(conversation_history)} messages")
            log_info_session(session_id, "messages.py", f"Found {len(conversation_history)} previous messages in conversation")
        else:
            log_info_session(session_id, "messages.py", "No previous conversation history - this is a new chat")
        
        # Query documents using RAG - searches across all user documents
        log_info_session(session_id, "messages.py", f"Starting RAG document search for query: '{request.query}'")
        rag_start_time = datetime.utcnow()
        
        rag_result = await rag_service.query_documents(
            query=request.query,
            user_id=request.user_id,
            session_id=session_id  # Pass session ID for tracking
        )
        
        rag_end_time = datetime.utcnow()
        rag_duration = (rag_end_time - rag_start_time).total_seconds()
        log_timing(session_id, "rag_search", rag_duration, f"Found {rag_result.get('context_used', 0)} chunks")
        log_info_session(session_id, "messages.py", f"RAG search completed in {rag_duration:.3f}s - {rag_result.get('context_used', 0)} chunks found")
        
        # Log first chunk details for timing analysis
        source_chunks = rag_result.get('source_chunks', [])
        if source_chunks:
            first_chunk = source_chunks[0]
            log_timing(session_id, "first_chunk", rag_duration, f"First chunk: {first_chunk.get('filename', 'Unknown')} | Score: {first_chunk.get('similarity_score', 0):.3f}")
            log_debug_session(session_id, "messages.py", f"Document sources found: {len(source_chunks)} chunks")
            for i, chunk in enumerate(source_chunks[:3], 1):  # Log first 3 chunks
                log_debug_session(session_id, "messages.py", f"Source {i}: {chunk.get('filename', 'Unknown')} (similarity: {chunk.get('similarity_score', 0):.3f})")
        else:
            log_error_session(session_id, "No relevant document sources found for this query")
        
        # Enhance the RAG response with conversation context if available
        rag_result = await rag_service.query_documents(
            query=request.query,
            user_id=request.user_id,  # Removed document_id - searches all user documents
            session_id=session_id
        )
        
        # Enhance the RAG response with conversation context if available
        if conversation_history:
            log_debug_session(session_id, "messages.py", f"Enhancing response with {len(conversation_history)} conversation messages")
            enhance_start = datetime.utcnow()
            
            # Build conversation context for the AI
            context_messages = []
            for i, msg in enumerate(conversation_history[-5:], 1):  # Last 5 exchanges for context
                user_msg = msg.get('user_message', '')
                ai_msg = msg.get('assistant_message', '')
                context_messages.append(f"Previous Q: {user_msg}")
                context_messages.append(f"Previous A: {ai_msg}")
                log_debug_session(session_id, "messages.py", f"Context {i}: User='{user_msg[:30]}...' | AI='{ai_msg[:30]}...'")
            
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
            
            log_debug_session(session_id, "messages.py", f"Prepared enhanced prompt with {len(enhanced_prompt)} characters")
            log_debug_session(session_id, "messages.py", f"Sending enhanced query to Mistral AI with conversation context")
            mistral_start_time = datetime.utcnow()
            
            from core.mistral_service import mistral_service
            enhanced_answer = await mistral_service.generate_response(
                user_message=enhanced_prompt,
                user_id=request.user_id,
                conversation_history=conversation_history,
                session_id=session_id  # Pass session ID
            )
            
            mistral_end_time = datetime.utcnow()
            mistral_duration = (mistral_end_time - mistral_start_time).total_seconds()
            log_timing(session_id, "mistral_enhanced", mistral_duration, f"Enhanced response: {len(enhanced_answer)} chars")
            
            # Log the final result only (avoid duplicates)
            log_prompt(session_id, request.query, enhanced_answer, "rag-enhanced")
            
            if len(enhanced_answer) > len(rag_result['answer']) * 0.8:
                log_info_session(session_id, "messages.py", "Using enhanced AI response (significantly longer/better)")
                rag_result['answer'] = enhanced_answer
            else:
                log_debug_session(session_id, "messages.py", "Using original RAG response (enhanced response not significantly better)")
                
            enhance_duration = (datetime.utcnow() - enhance_start).total_seconds()
            log_timing(session_id, "context_enhancement", enhance_duration, "Conversation context processing")
        else:
            log_info_session(session_id, "messages.py", "No conversation history available - using direct RAG response")
            # Log the basic RAG result
            log_prompt(session_id, request.query, rag_result['answer'], "rag-direct")
        
        answer_received_timestamp = datetime.utcnow()
        total_processing_time = (answer_received_timestamp - message_sent_timestamp).total_seconds()
        
        logger.info("PREPARING TO SAVE MESSAGE TO DATABASE...")
        logger.info(f"Total processing time: {total_processing_time:.3f} seconds")
        
        db = get_db()
        next_message_id = await db.get_next_message_id_for_chat(chat_id)
        logger.info(f"Generated message ID: {next_message_id}")
        
        source_info = ""
        sources_list = []
        if rag_result.get('source_chunks'):
            source_info = f" [Sources: {len(rag_result['source_chunks'])} document chunks]"
            logger.info(f"Adding source information: {len(rag_result['source_chunks'])} chunks")
            sources_list = [
                SourceChunk(
                    document=chunk.get('filename', 'unknown'),
                    chunk=chunk.get('text_preview', chunk.get('text', ''))[:100] + "..." if len(chunk.get('text_preview', chunk.get('text', ''))) > 100 else chunk.get('text_preview', chunk.get('text', '')),
                    relevance_score=chunk.get('similarity_score', 0.0)
                )
                for chunk in rag_result['source_chunks'][:3]
            ]
        else:
            logger.warning("No source chunks to include in response")

        final_answer = rag_result['answer'] + source_info
        logger.info(f"Final answer length: {len(final_answer)} characters")
        
        message_data = {
            "message_id": str(next_message_id),
            "user_id": request.user_id,
            "chat_id": chat_id,
            "date": datetime.utcnow(),
            "user_message": request.query,
            "assistant_message": final_answer,
            "query_type": "document_query",
            "source_chunks": rag_result.get('source_chunks', []),
            "message_sent_timestamp": message_sent_timestamp,
            "answer_received_timestamp": answer_received_timestamp
        }
        
        logger.info("SAVING MESSAGE TO DATABASE...")
        logger.info(f"Message data: User='{request.query[:50]}...' | AI='{final_answer[:50]}...'")
        db_save_start = datetime.utcnow()
        
        await db.create_message(message_data)
        
        db_save_end = datetime.utcnow()
        db_save_duration = (db_save_end - db_save_start).total_seconds()
        logger.info(f"MESSAGE SAVED TO DATABASE in {db_save_duration:.3f} seconds")

        logger.info("UPDATING/CREATING CHAT COLLECTION...")
        existing_collections = await db.get_chat_collections_by_user(request.user_id)
        existing_chat = next((c for c in existing_collections if c.get('chat_id') == chat_id), None)
        
        if existing_chat:
            # For existing chats, only update metadata, NOT the title
            logger.info(f"Updating existing chat collection for chat_id: {chat_id} (preserving title)")
            await db.update_chat_collection_item(chat_id, {
                "last_message_date": datetime.utcnow(),
                "message_count": next_message_id
            })
        else:
            # For NEW chats, set the title based on the FIRST message
            logger.info(f"Creating new chat collection for chat_id: {chat_id} with title from first message")
            chat_collection_data = {
                "chat_id": chat_id,
                "user_id": request.user_id,
                "chat_title": request.query[:50] + ("..." if len(request.query) > 50 else ""),
                "creation_date": datetime.utcnow(),
                "last_message_date": datetime.utcnow(),
                "message_count": next_message_id,
                "query_type": "document_query"
            }
            logger.info(f"New chat collection data: Title='{chat_collection_data['chat_title']}'")
            await db.store_chat_collection_item(chat_collection_data)
        
        logger.info("PREPARING RESPONSE FOR CLIENT...")
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
        
        final_timestamp = datetime.utcnow()
        complete_duration = (final_timestamp - message_sent_timestamp).total_seconds()
        
        logger.info("MESSAGE PROCESSING COMPLETED SUCCESSFULLY")
        logger.info(f"Total end-to-end time: {complete_duration:.3f} seconds")
        logger.info(f"Returning {len(messages)} messages to client")
        logger.info(f"User message: '{request.query}'")
        logger.info(f"AI response length: {len(rag_result['answer'])} characters")
        logger.info(f"Sources included: {len(sources_list)}")
        logger.info("=" * 80)
        
        return ChatMessagesResponse(messages=messages)
        
    except Exception as e:
        logger.error("ERROR IN MESSAGE PROCESSING")
        logger.error(f"Error details: {str(e)}")
        logger.error(f"User ID: {request.user_id if 'request' in locals() else 'Unknown'}")
        logger.error(f"Query: {request.query if 'request' in locals() else 'Unknown'}")
        logger.error("=" * 80, exc_info=True)
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
        logger.info(f"Updating message {message_id} with data: {update_data}")
        
        message = await crud.get_chat_message(message_id)
        if not message:
            logger.warning(f"Message not found: {message_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        logger.info(f"Found message: {message}")
        
        updated_message = await crud.update_chat_message(message_id, update_data)
        if not updated_message:
            logger.error(f"Failed to update message {message_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message"
            )
        
        logger.info(f"Successfully updated message: {updated_message}")
        return updated_message
    except ValueError as e:
        logger.error(f"ValueError updating message {message_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating message {message_id}: {str(e)}", exc_info=True)
        handle_database_exceptions(e, "updating message")

@router.put("/{message_id}/regenerate", response_model=ChatMessageResponse, tags=["Messages"])
async def update_message_and_regenerate(message_id: str, update_data: ChatMessageUpdate):
    """ Update a message and regenerate the AI response """
    try:
        logger.info(f"Updating message {message_id} and regenerating response with data: {update_data}")
        
        # Get the current message
        message = await crud.get_chat_message(message_id)
        if not message:
            logger.warning(f"Message not found: {message_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Update the user message part
        updated_message = await crud.update_chat_message(message_id, update_data)
        if not updated_message:
            logger.error(f"Failed to update message {message_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update message"
            )
        
        # Now regenerate AI response for the updated message
        # Get conversation history (all messages before this one in the same chat)
        from core.mistral_service import mistral_service
        from database.factory import get_db
        
        db = get_db()
        chat_messages = await db.get_messages_by_chat_id(updated_message.chat_id)
        
        # Filter messages that come before the current message (by message_id)
        conversation_history = []
        current_msg_id = int(message_id)
        
        for msg in chat_messages:
            if int(msg["message_id"]) < current_msg_id:
                conversation_history.append(msg)
        
        # Generate new AI response
        new_ai_response = await mistral_service.generate_response(
            user_message=update_data.user_message,
            user_id=updated_message.user_id,
            conversation_history=conversation_history,
            session_id="update_message"  # Using generic session for message updates
        )
        
        # Update the message with the new AI response
        final_update = {"assistant_message": new_ai_response}
        final_message = await crud.update_chat_message(message_id, final_update)
        
        if not final_message:
            logger.error(f"Failed to update AI response for message {message_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update AI response"
            )
        
        logger.info(f"Successfully updated message and regenerated response: {final_message}")
        return final_message
        
    except ValueError as e:
        logger.error(f"ValueError updating message {message_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating message {message_id}: {str(e)}", exc_info=True)
        handle_database_exceptions(e, "updating message with regeneration")

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