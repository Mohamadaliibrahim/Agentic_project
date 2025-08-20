"""
Vector Database Management for FAISS
Handles FAISS index creation, storage, and retrieval operations
"""

import os
import pickle
import logging
from typing import Optional, Dict, Any
import numpy as np

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
    
    def load_mapping(self, user_id: str) -> Optional[Dict[str, Any]]:
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
