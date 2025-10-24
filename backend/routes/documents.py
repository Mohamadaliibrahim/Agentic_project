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

from core.config import settings
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
        
        # Validate file size
        max_size = settings.MAX_UPLOAD_SIZE_BYTES
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB."
            )
        
        # Process document using the new vector storage approach (like rag_testing notebook)
        document_result = await document_processor.process_and_store_document(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id,
            file_size=file_size
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
        error_message = str(e)
        
        # Provide specific error codes based on the error type
        if "authentication failed" in error_message.lower() or "mistral api authentication" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"AI Service Authentication Error: {error_message}"
            )
        elif "embedding" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embedding Service Error: {error_message}"
            )
        elif "database" in error_message.lower() or "mongodb" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database Service Error: {error_message}"
            )
        elif "timeout" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Request Timeout: {error_message}"
            )
        elif "rate limit" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate Limited: {error_message}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process document: {error_message}"
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
                upload_date=doc["upload_date"].isoformat() if hasattr(doc["upload_date"], 'isoformat') else str(doc["upload_date"]),
                file_size=doc.get("file_size", 0)  # Default to 0 if file_size is missing
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
            upload_date=document["upload_date"].isoformat() if hasattr(document["upload_date"], 'isoformat') else str(document["upload_date"]),
            file_size=document.get("file_size", 0)  # Default to 0 if file_size is missing
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
