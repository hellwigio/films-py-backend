"""Управление подключением к MongoDB для истории поиска."""

import logging
from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConfigurationError, PyMongoError

from films.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MongoConnection:
    """Связанные MongoDB-клиент и выбранная база данных."""

    client: AsyncIOMotorClient
    database: AsyncIOMotorDatabase


async def connect_mongo() -> MongoConnection | None:
    """Подключиться к MongoDB и подготовить индексы истории поиска."""

    if not settings.MONGO_URL:
        return None

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
        return None

    return MongoConnection(client=client, database=db)


def close_mongo(connection: MongoConnection | None) -> None:
    """Закрыть MongoDB-клиент, если подключение было установлено."""

    if connection is not None:
        connection.client.close()
