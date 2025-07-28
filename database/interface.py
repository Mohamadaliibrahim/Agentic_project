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
