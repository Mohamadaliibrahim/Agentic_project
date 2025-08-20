"""
CRUD operations for chunks using the new vector database system
These functions handle saving and retrieving document chunks
"""

import logging
from typing import List, Dict, Any, Optional
from database.factory import get_db

logger = logging.getLogger(__name__)

async def save_chunks(file_id: str, chunk_list: List[str]) -> bool:
    """
    Save chunks to the database
    
    Args:
        file_id: Document/file identifier
        chunk_list: List of text chunks
        
    Returns:
        bool: Success status
    """
    try:
        db = get_db()
        
        chunks_with_metadata = []
        for i, chunk_text in enumerate(chunk_list):
            chunk_data = {
                "chunk_id": f"{file_id}_chunk_{i}",
                "document_id": file_id,
                "chunk_index": i,
                "text": chunk_text,
                "word_count": len(chunk_text.split()),
                "character_count": len(chunk_text),
                "embedding": None
            }
            chunks_with_metadata.append(chunk_data)
        
        # Save to database
        success = await db.store_document_chunks(chunks_with_metadata)
        
        if success:
            logger.info(f"Saved {len(chunk_list)} chunks for file {file_id}")
        else:
            logger.error(f"Failed to save chunks for file {file_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error saving chunks for file {file_id}: {e}")
        return False

async def get_chunks_by_file_id(file_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve chunks by file/document ID
    
    Args:
        file_id: Document/file identifier
        
    Returns:
        List of chunk dictionaries
    """
    try:
        db = get_db()
        chunks = await db.get_document_chunks(file_id)
        
        logger.info(f"Retrieved {len(chunks)} chunks for file {file_id}")
        return chunks
        
    except Exception as e:
        logger.error(f"Error retrieving chunks for file {file_id}: {e}")
        return []

async def update_chunk_embeddings(file_id: str, embeddings: List[List[float]]) -> bool:
    """
    Update chunks with their embeddings
    
    Args:
        file_id: Document/file identifier
        embeddings: List of embedding vectors
        
    Returns:
        bool: Success status
    """
    try:
        db = get_db()
        chunks = await db.get_document_chunks(file_id)
        
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) doesn't match embedding count ({len(embeddings)})")
        
        # Update each chunk with its embedding
        updated_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
            updated_chunks.append(chunk)
        
        # Store updated chunks
        success = await db.store_document_chunks(updated_chunks)
        
        if success:
            logger.info(f"Updated {len(embeddings)} chunk embeddings for file {file_id}")
        else:
            logger.error(f"Failed to update chunk embeddings for file {file_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error updating chunk embeddings for file {file_id}: {e}")
        return False

async def get_all_user_chunks(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all chunks for a specific user
    
    Args:
        user_id: User identifier
        
    Returns:
        List of chunk dictionaries
    """
    try:
        db = get_db()
        
        # Get all documents for the user
        documents = await db.get_user_documents(user_id)
        
        all_chunks = []
        for doc in documents:
            chunks = await db.get_document_chunks(doc["document_id"])
            all_chunks.extend(chunks)
        
        logger.info(f"Retrieved {len(all_chunks)} total chunks for user {user_id}")
        return all_chunks
        
    except Exception as e:
        logger.error(f"Error retrieving chunks for user {user_id}: {e}")
        return []

async def delete_chunks_by_file_id(file_id: str) -> bool:
    """
    Delete all chunks for a specific file
    
    Args:
        file_id: Document/file identifier
        
    Returns:
        bool: Success status
    """
    try:
        db = get_db()
        success = await db.delete_document(file_id)
        
        if success:
            logger.info(f"Deleted chunks for file {file_id}")
        else:
            logger.error(f"Failed to delete chunks for file {file_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error deleting chunks for file {file_id}: {e}")
        return False
