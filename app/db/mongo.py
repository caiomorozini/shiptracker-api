"""
MongoDB connection configuration
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import get_app_settings

settings = get_app_settings()

mongo_client: Optional[AsyncIOMotorClient] = None
mongo_db: Optional[AsyncIOMotorDatabase] = None


def get_mongodb_url() -> str:
    """Build MongoDB connection URL"""
    if settings.mongo_username and settings.mongo_password:
        return (
            f"mongodb://{settings.mongo_username}:"
            f"{settings.mongo_password}@"
            f"{settings.mongo_hostname}:{settings.mongo_port}/"
            f"{settings.mongo_database}?authSource=admin"
        )
    return f"mongodb://{settings.mongo_hostname}:{settings.mongo_port}/{settings.mongo_database}"


async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongo_client, mongo_db
    mongo_client = AsyncIOMotorClient(get_mongodb_url())
    mongo_db = mongo_client[settings.mongo_database]


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()


def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if mongo_db is None:
        raise Exception("MongoDB not connected. Call connect_to_mongo() first.")
    return mongo_db


# MongoDB Collections
def get_tracking_events_archive():
    """Get tracking events archive collection"""
    return get_database().tracking_events_archive


def get_analytics_snapshots():
    """Get analytics snapshots collection"""
    return get_database().analytics_snapshots


def get_integration_logs():
    """Get integration logs collection"""
    return get_database().integration_logs


def get_automation_history():
    """Get automation history collection"""
    return get_database().automation_history


def get_client_interactions():
    """Get client interactions collection"""
    return get_database().client_interactions


async def get_carrier_raw_responses():
    """Get carrier raw responses collection"""
    return get_database().carrier_raw_responses

    """Testa a conexão com MongoDB."""
    try:
        await client.admin.command('ping')
        logger.info("MongoDB is alive!")
        return True
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return False
