"""
RAG utilities:
- chunk_text: split long text into chunks with overlap
- embed_texts: pluggable embedding function (provide real impl)
- index_management: index creation/search using faiss (if available)
- simple_search: perform nearest neighbor search and return context chunks
"""
from typing import List, Tuple, Callable, Dict, Any
import numpy as np
import uuid

from database.factory import get_db

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        RecursiveCharacterTextSplitter = None
import os
import pickle
import logging

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

class VectorDB:
    """Vector database implementation using FAISS for similarity search"""
    
    def __init__(self, storage_dir: str = "vector_storage"):
        self.storage_dir = storage_dir
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self):
        """Create storage directory if it doesn't exist"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def create_faiss_index(self, dim: int):
        """Create a new FAISS index for the given dimension"""
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is not available. Install with: pip install faiss-cpu")
        
        index = faiss.IndexFlatL2(dim)
        logger.info(f"Created FAISS index with dimension {dim}")
        return index
    
    def save_faiss_index(self, index, user_id: str):
        """Save FAISS index to disk"""
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is not available")
        
        index_path = os.path.join(self.storage_dir, f"{user_id}_index.faiss")
        faiss.write_index(index, index_path)
        logger.info(f"Saved FAISS index for user {user_id}")
    
    def load_faiss_index(self, user_id: str):
        """Load FAISS index from disk"""
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is not available")
        
        index_path = os.path.join(self.storage_dir, f"{user_id}_index.faiss")
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"No index found for user {user_id}")
        
        index = faiss.read_index(index_path)
        logger.info(f"Loaded FAISS index for user {user_id}")
        return index
    
    def save_mapping(self, mapping: Dict[str, Any], user_id: str):
        """Save chunk ID to text mapping"""
        mapping_path = os.path.join(self.storage_dir, f"{user_id}_mapping.pkl")
        with open(mapping_path, 'wb') as f:
            pickle.dump(mapping, f)
        logger.info(f"Saved mapping for user {user_id} with {len(mapping)} entries")
    
    def load_mapping(self, user_id: str):
        """Load chunk ID to text mapping"""
        mapping_path = os.path.join(self.storage_dir, f"{user_id}_mapping.pkl")
        if not os.path.exists(mapping_path):
            logger.warning(f"No mapping found for user {user_id}")
            return None
        
        with open(mapping_path, 'rb') as f:
            mapping = pickle.load(f)
        logger.info(f"Loaded mapping for user {user_id} with {len(mapping)} entries")
        return mapping
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all vector data for a user"""
        try:
            index_path = os.path.join(self.storage_dir, f"{user_id}_index.faiss")
            mapping_path = os.path.join(self.storage_dir, f"{user_id}_mapping.pkl")
            
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(mapping_path):
                os.remove(mapping_path)
            
            logger.info(f"Deleted vector data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vector data for user {user_id}: {e}")
            return False

vector_db = VectorDB()

async def save_chunks(file_id: str, chunk_list: List[str]) -> bool:
    """
    Save chunks to the database
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
    """
    try:
        db = get_db()
        chunks = await db.get_document_chunks(file_id)
        
        logger.info(f"Retrieved {len(chunks)} chunks for file {file_id}")
        return chunks
        
    except Exception as e:
        logger.error(f"Error retrieving chunks for file {file_id}: {e}")
        return []

def chunk_text(text: str) -> List[str]:
    """
    Split text into overlapping chunks using RecursiveCharacterTextSplitter
    
    Args:
        text: Input text to chunk
        
    Returns:
        List of text chunks
    """
    if not RecursiveCharacterTextSplitter:
        raise ImportError("RecursiveCharacterTextSplitter not available. Install langchain or langchain-text-splitters")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(text)
    return chunks

def embed_texts(texts: List[str], embed_fn: Callable[[List[str]], List[List[float]]]) -> np.ndarray:
    """
    embed_fn should accept List[str] and return List[List[float]] (float vectors).
    This function returns a numpy array of shape (n, dim).
    """
    vects = embed_fn(texts)
    arr = np.asarray(vects, dtype=np.float32)
    return arr

def build_or_update_index(user_id: str, texts: List[str], embed_fn: Callable[[List[str]], List[List[float]]]):
    """
    Build or update FAISS index for a user with new texts
    
    Args:
        user_id: User identifier
        texts: List of text chunks to index
        embed_fn: Function to generate embeddings
        
    Returns:
        Dict with indexing results
    """
    embeddings = embed_texts(texts, embed_fn)
    dim = embeddings.shape[1]

    idx = None
    try:
        idx = vector_db.load_faiss_index(user_id)
    except Exception:
        idx = None

    mapping = vector_db.load_mapping(user_id) or {}

    if idx is None:
        try:
            idx = vector_db.create_faiss_index(dim)
        except Exception as e:
            raise RuntimeError("FAISS unavailable or failed to create index: " + str(e))

    start_id = len(mapping)
    ids = []
    for i, txt in enumerate(texts):
        new_id = str(uuid.uuid4())
        mapping[new_id] = {"text": txt}
        ids.append(new_id)

    idx.add(embeddings)
    vector_db.save_faiss_index(idx, user_id)
    vector_db.save_mapping(mapping, user_id)

    return {"indexed": len(texts), "mapping_size": len(mapping)}

def search_index(user_id: str, query: str, embed_fn: Callable[[List[str]], List[List[float]]], k: int = 5) -> List[Tuple[str, float]]:
    """
    Search the FAISS index for similar texts
    
    Args:
        user_id: User identifier
        query: Query text
        embed_fn: Function to generate embeddings
        k: Number of results to return
        
    Returns:
        List of (text, score) tuples
    """
    q_emb = np.asarray(embed_fn([query]), dtype=np.float32)
    try:
        idx = vector_db.load_faiss_index(user_id)
    except:
        return []
    
    if idx is None:
        return []

    D, I = idx.search(q_emb, k)
    mapping = vector_db.load_mapping(user_id)
    
    if mapping is None:
        return []
    
    results = []
    for score, idx_pos in zip(D[0], I[0]):
        keys = list(mapping.keys())
        if idx_pos < len(keys):
            key = keys[idx_pos]
            results.append((mapping[key]["text"], float(score)))
    return results

async def process_and_index_document(file_id: str, text: str, user_id: str, embed_fn: Callable[[List[str]], List[List[float]]]) -> Dict[str, Any]:
    """
    Process a document: chunk it, save chunks, generate embeddings, and index
    
    Args:
        file_id: Document identifier
        text: Document text content
        user_id: User identifier
        embed_fn: Function to generate embeddings
        
    Returns:
        Processing results
    """
    chunks = chunk_text(text)
    
    await save_chunks(file_id, chunks)
    
    index_result = build_or_update_index(user_id, chunks, embed_fn)
    
    return {
        "file_id": file_id,
        "chunks_created": len(chunks),
        "index_result": index_result
    }

async def query_user_documents(user_id: str, query: str, embed_fn: Callable[[List[str]], List[List[float]]], k: int = 5) -> Dict[str, Any]:
    """
    Query a user's indexed documents
    
    Args:
        user_id: User identifier
        query: Query text
        embed_fn: Function to generate embeddings
        k: Number of results to return
        
    Returns:
        Query results with context
    """
    results = search_index(user_id, query, embed_fn, k)
    
    if not results:
        return {
            "query": query,
            "results": [],
            "context": "No relevant documents found."
        }
    
    context_parts = []
    for i, (text, score) in enumerate(results):
        context_parts.append(f"[Result {i+1}, Score: {score:.3f}]\n{text}")
    
    context = "\n\n".join(context_parts)
    
    return {
        "query": query,
        "results": results,
        "context": context,
        "num_results": len(results)
    }
