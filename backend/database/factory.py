"""
Database Factory - Creates appropriate database adapter based on configuration
"""

from core.config import settings
from database.interface import DatabaseInterface

def get_database_adapter() -> DatabaseInterface:
    """
    Factory function to get the appropriate database adapter
    Change DATABASE_TYPE in .env to switch databases easily
    """
    database_type = settings.DATABASE_TYPE.lower()
    
    if database_type == "mongodb":
        from database.mongodb_adapter import MongoDBAdapter
        return MongoDBAdapter()
    else:
        raise ValueError(f"Unsupported database type: {database_type}")

db_adapter: DatabaseInterface = None

async def initialize_database():
    """Initialize the database connection"""
    global db_adapter
    db_adapter = get_database_adapter()
    await db_adapter.connect()

async def close_database():
    """Close the database connection"""
    global db_adapter
    if db_adapter:
        await db_adapter.disconnect()

def get_db() -> DatabaseInterface:
    """Get the current database adapter instance"""
    global db_adapter
    if db_adapter is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return db_adapter
