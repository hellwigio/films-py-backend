"""Команда очистки коллекции поисковой истории MongoDB."""

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

from films.config import settings

MONGO_TIMEOUT_MS = 2_000


async def main() -> None:
    """Удалить все документы из настроенной коллекции истории."""

    if not settings.MONGO_URL:
        raise SystemExit("MONGO_URL is not set")

    client = AsyncIOMotorClient(
        settings.MONGO_URL,
        connectTimeoutMS=MONGO_TIMEOUT_MS,
        serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
    )

    try:
        db = client.get_default_database()
        await db.command("ping")
        result = await db[settings.SEARCH_QUERIES_COLLECTION].delete_many({})
    except PyMongoError as exc:
        raise SystemExit(f"MongoDB is not available: {exc}") from exc
    finally:
        client.close()

    print(f"Deleted search history: {result.deleted_count}")


if __name__ == "__main__":
    asyncio.run(main())
