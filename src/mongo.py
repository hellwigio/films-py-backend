import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConfigurationError, PyMongoError

from src.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    global _client, _db

    if not settings.MONGO_URL:
        return

    client = AsyncIOMotorClient(
        settings.MONGO_URL,
        connectTimeoutMS=2_000,
        serverSelectionTimeoutMS=2_000,
    )

    try:
        db = client.get_default_database()
        await db.command("ping")
        collection = db[settings.SEARCH_QUERIES_COLLECTION]
        await collection.create_index([("timestamp", -1)])
        await collection.create_index([("search_type", 1), ("timestamp", -1)])
    except (PyMongoError, ConfigurationError) as exc:
        client.close()
        logger.error(
            "MongoDB is unavailable; film search will work without history: %s",
            exc,
        )
        return

    _client = client
    _db = db


async def close_mongo() -> None:
    global _client, _db

    if _client is not None:
        _client.close()

    _client = None
    _db = None


def get_mongo_db() -> AsyncIOMotorDatabase | None:
    return _db
