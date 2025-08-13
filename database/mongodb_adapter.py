from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any

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
        return data.copy()
    
    def _from_json_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from JSON document (remove only MongoDB internal fields)"""
        if doc:
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
        await self.database.users.create_index("id", unique=True)
        await self.database.users.create_index("created_at")
        
        # Handle field migration from "id" to "message_id" for existing data
        await self.migrate_message_id_field()
        
        # Create compound unique index on (chat_id, message_id) to allow sequential numbering per chat
        await self.database.chat_messages.create_index([("chat_id", 1), ("message_id", 1)], unique=True)
        await self.database.chat_messages.create_index("user_id")
        
        # Document indexes
        await self.database.documents.create_index("document_id", unique=True)
        await self.database.documents.create_index("user_id")
        await self.database.documents.create_index("upload_date")
        
        # Document chunks indexes
        await self.database.document_chunks.create_index([("document_id", 1), ("chunk_index", 1)], unique=True)
        await self.database.document_chunks.create_index("user_id")
        await self.database.document_chunks.create_index("chunk_id", unique=True)
        
        await self.database.chat_messages.create_index("chat_id")  # Index for page-based conversations
        await self.database.chat_messages.create_index("date")
        
        # Chat collections indexes
        await self.database.chat_collections.create_index("chat_id", unique=True)
        await self.database.chat_collections.create_index("user_id")
        await self.database.chat_collections.create_index("creation_date")
        
        print("Database indexes created for pure JSON storage")
    
    async def migrate_message_id_field(self) -> None:
        """Migrate existing messages from 'id' field to 'message_id' field and fix indexes"""
        # First, try to drop the old id index if it exists
        try:
            await self.database.chat_messages.drop_index("id_1")
            print("Dropped old 'id' index")
        except Exception as e:
            print(f"No old 'id' index to drop or error dropping it: {e}")
        
        # Drop the old global unique message_id index if it exists
        try:
            await self.database.chat_messages.drop_index("message_id_1")
            print("Dropped old global unique 'message_id' index")
        except Exception as e:
            print(f"No old 'message_id' index to drop or error dropping it: {e}")
        
        # Check if migration is needed by looking for documents with 'id' but no 'message_id'
        old_docs = await self.database.chat_messages.find({"id": {"$exists": True}, "message_id": {"$exists": False}}).to_list(None)
        
        if old_docs:
            print(f"Migrating {len(old_docs)} messages from 'id' to 'message_id' field...")
            
            # Update each document
            for doc in old_docs:
                await self.database.chat_messages.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {"message_id": doc["id"]},
                        "$unset": {"id": ""}
                    }
                )
            
            print(f"Successfully migrated {len(old_docs)} messages")
        else:
            print("No message field migration needed")
    
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
        await self.database.chat_messages.delete_many({"user_id": user_id})
        
        result = await self.database.users.delete_one({"id": user_id})
        return result.deleted_count > 0
    
    async def count_user_messages(self, user_id: str) -> int:
        """Count messages for a user in chat_messages table"""
        return await self.database.chat_messages.count_documents({"user_id": user_id})
    
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat message stored as pure JSON in chat_messages table"""
        json_doc = self._to_json_document(message_data, "message")
        
        result = await self.database.chat_messages.insert_one(json_doc)
        
        return self._from_json_document(json_doc)
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by ID from chat_messages table with pure JSON data"""
        doc = await self.database.chat_messages.find_one({"message_id": message_id})
        return self._from_json_document(doc) if doc else None
    
    async def get_user_messages(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a user from chat_messages table with pure JSON data"""
        messages = []
        async for doc in self.database.chat_messages.find({"user_id": user_id}).sort("date", 1):
            messages.append(self._from_json_document(doc))
        return messages
    
    async def get_messages_by_chat_id(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a specific chat ID (page) from chat_messages table"""
        messages = []
        # Sort by message_id as integer to maintain proper sequential order (1, 2, 3...)
        pipeline = [
            {"$match": {"chat_id": chat_id}},
            {"$addFields": {
                "message_id_int": {"$toInt": "$message_id"}
            }},
            {"$sort": {"message_id_int": 1}}
        ]
        
        async for doc in self.database.chat_messages.aggregate(pipeline):
            # Remove the temporary field before returning
            if "message_id_int" in doc:
                del doc["message_id_int"]
            messages.append(self._from_json_document(doc))
        return messages
    
    async def get_next_message_id_for_chat(self, chat_id: str) -> int:
        """Get the next sequential message ID for a specific chat"""
        # Get the current highest message_id for this chat_id (as integer)
        pipeline = [
            {"$match": {"chat_id": chat_id}},
            {"$addFields": {
                "message_id_int": {
                    "$cond": {
                        "if": {"$type": "$message_id"},
                        "then": {"$toInt": "$message_id"},
                        "else": 0
                    }
                }
            }},
            {"$sort": {"message_id_int": -1}},
            {"$limit": 1}
        ]
        
        cursor = self.database.chat_messages.aggregate(pipeline)
        docs = await cursor.to_list(length=1)
        
        if docs and docs[0].get("message_id_int"):
            current_max = docs[0]["message_id_int"]
            return current_max + 1
        else:
            # No messages in this chat yet, start with 1
            return 1
    
    async def update_message(self, message_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a message in chat_messages table with pure JSON data"""
        doc = await self.database.chat_messages.find_one({"message_id": message_id})
        if not doc:
            return None
        
        current_data = self._from_json_document(doc)
        current_data.update(update_data)
        
        result = await self.database.chat_messages.update_one(
            {"message_id": message_id},
            {"$set": current_data}
        )
        
        if result.modified_count > 0:
            return current_data
        return None
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message from chat_messages table"""
        result = await self.database.chat_messages.delete_one({"message_id": message_id})
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

    async def get_user_chats_collection(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chats for a user with basic info for collection view"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"date": 1}},  # Sort by date to get first message
            {"$group": {
                "_id": "$chat_id",
                "chat_id": {"$first": "$chat_id"},
                "first_message": {"$first": "$user_message"},
                "creation_date": {"$first": "$date"}
            }},
            {"$sort": {"creation_date": -1}}  # Sort chats by newest first
        ]
        
        chats = []
        cursor = self.database.chat_messages.aggregate(pipeline)
        async for doc in cursor:
            chats.append({
                "chat_id": doc["chat_id"],
                "first_message": doc["first_message"],
                "creation_date": doc["creation_date"]
            })
        return chats

    async def store_chat_collection_item(self, chat_data: Dict[str, Any]) -> str:
        """Store chat collection item in dedicated chat_collections table"""
        doc_json = self._to_json_document(chat_data, "chat_collection")
        await self.database.chat_collections.insert_one(doc_json)
        return chat_data["chat_id"]

    async def update_chat_collection_item(self, chat_id: str, update_data: Dict[str, Any]) -> bool:
        """Update chat collection item in chat_collections table"""
        try:
            # Remove any None values and prepare update document
            update_doc = {k: v for k, v in update_data.items() if v is not None}
            if not update_doc:
                return False
            
            result = await self.database.chat_collections.update_one(
                {"chat_id": chat_id},
                {"$set": update_doc}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def get_chat_collections_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat collections for a user from dedicated chat_collections table"""
        collections = []
        async for doc in self.database.chat_collections.find({"user_id": user_id}).sort("creation_date", -1):
            collections.append(self._from_json_document(doc))
        return collections

    async def delete_chat_collection_item(self, chat_id: str) -> bool:
        """Delete chat collection item from chat_collections table"""
        try:
            result = await self.database.chat_collections.delete_one({"chat_id": chat_id})
            return result.deleted_count > 0
        except Exception:
            return False

    # Document storage methods
    async def store_document(self, document_data: Dict[str, Any]) -> str:
        """Store document metadata in documents table"""
        doc_json = self._to_json_document(document_data, "document")
        result = await self.database.documents.insert_one(doc_json)
        return document_data["document_id"]
    
    async def store_document_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Store document chunks with embeddings in document_chunks table"""
        try:
            chunks_json = [self._to_json_document(chunk, "chunk") for chunk in chunks]
            await self.database.document_chunks.insert_many(chunks_json)
            return True
        except Exception:
            return False
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by document_id"""
        doc = await self.database.documents.find_one({"document_id": document_id})
        return self._from_json_document(doc) if doc else None
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        documents = []
        async for doc in self.database.documents.find({"user_id": user_id}).sort("upload_date", -1):
            documents.append(self._from_json_document(doc))
        return documents
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document"""
        chunks = []
        async for chunk in self.database.document_chunks.find({"document_id": document_id}).sort("chunk_index", 1):
            chunks.append(self._from_json_document(chunk))
        return chunks
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document and all its chunks"""
        try:
            # Delete chunks first
            await self.database.document_chunks.delete_many({"document_id": document_id})
            # Delete document metadata
            result = await self.database.documents.delete_one({"document_id": document_id})
            return result.deleted_count > 0
        except Exception:
            return False
