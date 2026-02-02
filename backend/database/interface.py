"""
Database Interface - Abstract base class for database operations
This allows easy switching between different database types (MongoDB, PostgreSQL, MySQL, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class DatabaseInterface(ABC):
    """Abstract interface for database operations"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the database"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the database"""
        pass
    
    @abstractmethod
    async def create_indexes(self) -> None:
        """Create database indexes for performance"""
        pass
    
    @abstractmethod
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        pass
    
    @abstractmethod
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        pass
    
    @abstractmethod
    async def count_user_messages(self, user_id: str) -> int:
        """Count messages for a user"""
        pass
    
    @abstractmethod
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat message"""
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by ID"""
        pass
    
    @abstractmethod
    async def get_user_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a user"""
        pass
    
    @abstractmethod
    async def get_messages_by_chat_id(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific chat ID (page)"""
        pass
    
    @abstractmethod
    async def get_next_message_id_for_chat(self, chat_id: str) -> int:
        """Get the next sequential message ID for a specific chat"""
        pass
    
    @abstractmethod
    async def update_message(self, message_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a message"""
        pass
    
    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        pass
    
    @abstractmethod
    async def delete_user_messages(self, user_id: str) -> int:
        """Delete all messages for a user, return count of deleted messages"""
        pass

    @abstractmethod
    async def get_all_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from all users"""
        pass

    @abstractmethod
    async def get_user_chats_collection(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chats for a user with basic info for collection view"""
        pass

    @abstractmethod
    async def store_chat_collection_item(self, chat_data: Dict[str, Any]) -> str:
        """Store chat collection item in dedicated table"""
        pass

    @abstractmethod
    async def update_chat_collection_item(self, chat_id: str, update_data: Dict[str, Any]) -> bool:
        """Update chat collection item"""
        pass

    @abstractmethod
    async def get_chat_collections_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat collections for a user from dedicated table"""
        pass

    @abstractmethod
    async def delete_chat_collection_item(self, chat_id: str) -> bool:
        """Delete chat collection item"""
        pass

    # Document storage methods
    @abstractmethod
    async def store_document(self, document_data: Dict[str, Any]) -> str:
        """Store document metadata"""
        pass
    
    @abstractmethod
    async def store_document_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Store document chunks with embeddings"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        pass
    
    @abstractmethod
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        pass
    
    @abstractmethod
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks"""
        pass
