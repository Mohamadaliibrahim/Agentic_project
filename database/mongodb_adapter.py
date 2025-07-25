from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime

from core.config import settings
from database.interface import DatabaseInterface

class MongoDBAdapter(DatabaseInterface):
    """MongoDB implementation - stores data as flexible JSON in original tables"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.mongodb_url = settings.MONGODB_URL
        self.database_name = settings.DATABASE_NAME
    
    def _to_json_document(self, data: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
        """Convert data to pure JSON document for storage - only essential data"""
        # Store only the actual data, no wrapper or type fields
        return data.copy()
    
    def _from_json_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from JSON document (remove only MongoDB internal fields)"""
        if doc:
            # Remove only MongoDB's internal _id field
            clean_doc = {k: v for k, v in doc.items() if k != '_id'}
            return clean_doc
        return doc
    
    async def connect(self) -> None:
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(self.mongodb_url)
        self.database = self.client[self.database_name]
        await self.create_indexes()
        print(f"Connected to MongoDB: {self.database_name}")
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    async def create_indexes(self) -> None:
        """Create MongoDB indexes for pure JSON storage"""
        # Users table - only essential indexes
        await self.database.users.create_index("id", unique=True)
        await self.database.users.create_index("created_at")
        
        # Chat messages table - only essential indexes  
        await self.database.chat_messages.create_index("id", unique=True)
        await self.database.chat_messages.create_index("user_id")  # For fast user lookups
        await self.database.chat_messages.create_index("date")  # For sorting
        
        print("Database indexes created for pure JSON storage")
    
    # User operations - Pure JSON storage in users table
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user stored as pure JSON in users table"""
        json_doc = self._to_json_document(user_data, "user")
        
        result = await self.database.users.insert_one(json_doc)
        
        return self._from_json_document(json_doc)
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID from users table with pure JSON data"""
        doc = await self.database.users.find_one({"id": user_id})
        return self._from_json_document(doc) if doc else None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from users table with pure JSON data"""
        users = []
        async for doc in self.database.users.find():
            users.append(self._from_json_document(doc))
        return users
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and all their messages from original tables"""
        # First delete all messages for this user from chat_messages table
        await self.database.chat_messages.delete_many({"user_id": user_id})
        
        # Then delete the user from users table
        result = await self.database.users.delete_one({"id": user_id})
        return result.deleted_count > 0
    
    async def count_user_messages(self, user_id: str) -> int:
        """Count messages for a user in chat_messages table"""
        return await self.database.chat_messages.count_documents({"user_id": user_id})
    
    # Message operations - Pure JSON storage in chat_messages table
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat message stored as pure JSON in chat_messages table"""
        json_doc = self._to_json_document(message_data, "message")
        
        result = await self.database.chat_messages.insert_one(json_doc)
        
        return self._from_json_document(json_doc)
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by ID from chat_messages table with pure JSON data"""
        doc = await self.database.chat_messages.find_one({"id": message_id})
        return self._from_json_document(doc) if doc else None
    
    async def get_user_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a user from chat_messages table with pure JSON data"""
        messages = []
        async for doc in self.database.chat_messages.find({"user_id": user_id}).sort("date", 1):
            messages.append(self._from_json_document(doc))
        return messages
    
    async def update_message(self, message_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a message in chat_messages table with pure JSON data"""
        # Get current document
        doc = await self.database.chat_messages.find_one({"id": message_id})
        if not doc:
            return None
        
        # Update the document directly (pure JSON)
        current_data = self._from_json_document(doc)
        current_data.update(update_data)
        
        # Update with pure JSON data
        result = await self.database.chat_messages.update_one(
            {"id": message_id},
            {"$set": current_data}
        )
        
        if result.modified_count > 0:
            return current_data
        return None
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message from chat_messages table"""
        result = await self.database.chat_messages.delete_one({"id": message_id})
        return result.deleted_count > 0
    
    async def delete_user_messages(self, user_id: str) -> int:
        """Delete all messages for a user from chat_messages table"""
        result = await self.database.chat_messages.delete_many({"user_id": user_id})
        return result.deleted_count

    async def get_all_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from chat_messages table with pure JSON data"""
        messages = []
        async for doc in self.database.chat_messages.find().sort("date", 1):
            messages.append(self._from_json_document(doc))
        return messages
