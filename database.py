from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bot_database")

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    """ Create database connection """
    db.client = AsyncIOMotorClient(MONGODB_URL)
    db.database = db.client[DATABASE_NAME]
    
    await create_indexes()
    print(f"Connected to MongoDB: {DATABASE_NAME}")

async def close_mongo_connection():
    """ Close database connection """
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance"""
    await db.database.users.create_index("id", unique=True)
    await db.database.users.create_index("created_at")
    
    await db.database.chat_messages.create_index("id", unique=True)
    await db.database.chat_messages.create_index("user_id")
    await db.database.chat_messages.create_index("date")
    
    print("Database indexes created")

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc
    return None

def serialize_docs(docs):
    """Convert list of MongoDB documents to JSON serializable format"""
    return [serialize_doc(doc) for doc in docs]
