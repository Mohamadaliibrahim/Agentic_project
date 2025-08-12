"""
Document Routes
API endpoints for document upload, processing, and RAG querying
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Query
from pydantic import BaseModel
from data_validation import DocumentQueryRequest, DocumentQueryResponse

from core.document_processor import document_processor
from core.embedding_service import embedding_service
from database.factory import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    total_chunks: int
    message: str

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    file_type: str
    total_chunks: int
    upload_date: str
    file_size: int

@router.post("/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload and process a document (PDF, CSV, Word, TXT)
    
    The document will be:
    1. Processed and split into chunks
    2. Embedded using our embedding service
    3. Stored in the database for later querying
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.txt', '.csv', '.docx', '.doc'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum allowed size is 10MB."
            )
        
        # Process document using the new vector storage approach (like rag_testing notebook)
        document_result = await document_processor.process_and_store_document(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id
        )
        
        return DocumentUploadResponse(
            document_id=document_result["document_id"],
            filename=document_result["filename"],
            file_type=document_result["file_type"],
            total_chunks=document_result["total_chunks"],
            message=document_result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@router.get("/documents", response_model=List[DocumentInfo], tags=["Documents"])
async def get_user_documents(user_id: str = Query(...)):
    """Get all documents uploaded by a user"""
    try:
        db = get_db()
        documents = await db.get_user_documents(user_id)
        
        return [
            DocumentInfo(
                document_id=doc["document_id"],
                filename=doc["filename"],
                file_type=doc["file_type"],
                total_chunks=doc["total_chunks"],
                upload_date=doc["upload_date"],
                file_size=doc["file_size"]
            )
            for doc in documents
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

@router.get("/documents/{document_id}", response_model=DocumentInfo, tags=["Documents"])
async def get_document_info(document_id: str):
    """Get information about a specific document"""
    try:
        db = get_db()
        document = await db.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentInfo(
            document_id=document["document_id"],
            filename=document["filename"],
            file_type=document["file_type"],
            total_chunks=document["total_chunks"],
            upload_date=document["upload_date"],
            file_size=document["file_size"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document info: {str(e)}"
        )

@router.delete("/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    try:
        db = get_db()
        # Check if document exists
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete document and chunks
        success = await db.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
        return {"message": f"Document '{document['filename']}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/documents/{document_id}/chunks", tags=["Documents"])
async def get_document_chunks(document_id: str):
    """Get all chunks for a specific document (for debugging/inspection)"""
    try:
        db = get_db()
        # Check if document exists
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get chunks (without embeddings for readability)
        chunks = await db.get_document_chunks(document_id)
        
        # Remove embeddings from response for readability
        simplified_chunks = []
        for chunk in chunks:
            simplified_chunk = {
                "chunk_id": chunk["chunk_id"],
                "chunk_index": chunk["chunk_index"],
                "text_preview": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "word_count": chunk["word_count"],
                "character_count": chunk["character_count"]
            }
            simplified_chunks.append(simplified_chunk)
        
        return {
            "document_id": document_id,
            "filename": document["filename"],
            "total_chunks": len(chunks),
            "chunks": simplified_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document chunks: {str(e)}"
        )

@router.post("/documents/query", response_model=DocumentQueryResponse, tags=["Documents"])
async def query_documents(
    request: DocumentQueryRequest,
    chat_id: Optional[str] = Query(None, description="Optional chat ID for continuing existing conversations")
):
    """
    Query documents with RAG and conversation memory
    
    This endpoint allows users to ask questions about their uploaded documents.
    It supports conversation memory by tracking chat_id, so users can ask
    follow-up questions and reference previous parts of the conversation.
    
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
            
            # Generate enhanced response using Mistral with conversation context
            from core.mistral_service import mistral_service
            enhanced_answer = await mistral_service.generate_response(
                user_message=enhanced_prompt,
                user_id=request.user_id,
                conversation_history=conversation_history
            )
            
            # Use enhanced answer if it's significantly different
            if len(enhanced_answer) > len(rag_result['answer']) * 0.8:
                rag_result['answer'] = enhanced_answer
        
        # Store this query and response in the messages table for conversation memory
        db = get_db()
        next_message_id = await db.get_next_message_id_for_chat(chat_id)
        
        # Prepare source chunks information for storage
        source_info = ""
        if rag_result.get('source_chunks'):
            source_info = f" [Sources: {len(rag_result['source_chunks'])} document chunks]"
        
        message_data = {
            "message_id": str(next_message_id),
            "user_id": request.user_id,
            "chat_id": chat_id,
            "date": datetime.utcnow(),
            "user_message": request.query,
            "assistant_message": rag_result['answer'] + source_info,
            "query_type": "document_query",  # Mark this as a document query
            "source_chunks": rag_result.get('source_chunks', [])  # Store source chunks
        }
        
        await db.create_message(message_data)
        
        return DocumentQueryResponse(
            answer=rag_result['answer'],
            source_chunks=rag_result.get('source_chunks', []),
            query=request.query,
            context_used=rag_result.get('context_used', 0),
            chat_id=chat_id,
            message_id=str(next_message_id)
        )
        
    except Exception as e:
        logger.error(f"Error in document query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}"
        )
