"""
Document Routes
API endpoints for document upload, processing, and RAG querying
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Query
from pydantic import BaseModel

from core.document_processor import document_processor
from core.embedding_service import embedding_service
from core.rag_service import rag_service
from database.factory import get_db

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

class DocumentQueryRequest(BaseModel):
    query: str
    user_id: str
    document_id: Optional[str] = None

class DocumentQueryResponse(BaseModel):
    answer: str
    source_chunks: List[dict]
    query: str
    context_used: int

class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    text_preview: str
    similarity_score: float

class DocumentQueryHistory(BaseModel):
    query_id: str
    user_id: str
    document_id: Optional[str]
    query_text: str
    response_text: str
    source_chunks: List[dict]
    context_used: int
    query_date: str
    response_quality: str

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
        
        # Process document
        document_info = await document_processor.process_document(
            file_content=file_content,
            filename=file.filename,
            user_id=user_id
        )
        
        # Generate embeddings for chunks
        chunk_texts = [chunk["text"] for chunk in document_info["chunks"]]
        embeddings = await embedding_service.generate_embeddings(chunk_texts)
        
        # Prepare document metadata for storage
        upload_date = datetime.utcnow().isoformat()
        document_metadata = {
            "document_id": document_info["document_id"],
            "filename": document_info["filename"],
            "file_type": document_info["file_type"],
            "user_id": user_id,
            "total_chunks": document_info["total_chunks"],
            "upload_date": upload_date,
            "file_size": file_size,
            "total_characters": document_info["total_characters"]
        }
        
        # Prepare chunks with embeddings for storage
        chunks_with_embeddings = []
        for i, chunk in enumerate(document_info["chunks"]):
            chunk_with_embedding = {
                "chunk_id": chunk["chunk_id"],
                "document_id": document_info["document_id"],
                "filename": document_info["filename"],
                "user_id": user_id,
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "word_count": chunk["word_count"],
                "character_count": chunk["character_count"],
                "embedding": embeddings[i]
            }
            chunks_with_embeddings.append(chunk_with_embedding)
        
        # Store in database
        db = get_db()
        await db.store_document(document_metadata)
        await db.store_document_chunks(chunks_with_embeddings)
        
        return DocumentUploadResponse(
            document_id=document_info["document_id"],
            filename=document_info["filename"],
            file_type=document_info["file_type"],
            total_chunks=document_info["total_chunks"],
            message=f"Document '{file.filename}' uploaded and processed successfully. {document_info['total_chunks']} chunks created."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@router.post("/documents/query", response_model=DocumentQueryResponse, tags=["Documents"])
async def query_documents(request: DocumentQueryRequest):
    """
    Query documents using RAG (Retrieval-Augmented Generation)
    
    Finds relevant document chunks and generates an answer using Mistral AI.
    The query and response are automatically saved to the database.
    """
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Note: user_id is now passed in the request
        user_id = request.user_id
        
        # Perform RAG query
        result = await rag_service.query_documents(
            query=request.query,
            user_id=user_id,
            document_id=request.document_id
        )
        
        # Store the query and response in database
        try:
            query_data = {
                "query_id": str(uuid.uuid4()),
                "user_id": user_id,
                "document_id": request.document_id,
                "query_text": request.query,
                "response_text": result["answer"],
                "source_chunks": result["source_chunks"],
                "context_used": result["context_used"],
                "query_date": datetime.utcnow().isoformat(),
                "response_quality": "success" if result["context_used"] > 0 else "no_context"
            }
            
            db = get_db()
            await db.store_document_query(query_data)
            
        except Exception as e:
            # Log the error but don't fail the query
            print(f"Warning: Failed to store query in database: {str(e)}")
        
        return DocumentQueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query documents: {str(e)}"
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

@router.get("/documents/queries/history", response_model=List[DocumentQueryHistory], tags=["Documents"])
async def get_user_query_history(user_id: str = Query(...)):
    """Get all document query history for a user"""
    try:
        db = get_db()
        queries = await db.get_user_document_queries(user_id)
        
        return [
            DocumentQueryHistory(
                query_id=query["query_id"],
                user_id=query["user_id"],
                document_id=query.get("document_id"),
                query_text=query["query_text"],
                response_text=query["response_text"],
                source_chunks=query.get("source_chunks", []),
                context_used=query.get("context_used", 0),
                query_date=query["query_date"],
                response_quality=query.get("response_quality", "unknown")
            )
            for query in queries
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve query history: {str(e)}"
        )

@router.get("/documents/{document_id}/queries", response_model=List[DocumentQueryHistory], tags=["Documents"])
async def get_document_query_history(document_id: str):
    """Get all queries made for a specific document"""
    try:
        db = get_db()
        # Check if document exists
        document = await db.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        queries = await db.get_document_queries_by_document(document_id)
        
        return [
            DocumentQueryHistory(
                query_id=query["query_id"],
                user_id=query["user_id"],
                document_id=query["document_id"],
                query_text=query["query_text"],
                response_text=query["response_text"],
                source_chunks=query.get("source_chunks", []),
                context_used=query.get("context_used", 0),
                query_date=query["query_date"],
                response_quality=query.get("response_quality", "unknown")
            )
            for query in queries
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document query history: {str(e)}"
        )
