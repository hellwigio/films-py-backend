import logging
from datetime import UTC, datetime
from typing import Any

from pymongo.errors import PyMongoError

from src.config import settings
from src.exceptions.search import SearchHistoryUnavailableError
from src.mongo import get_mongo_db
from src.schemas.films.search_statistic import SearchType, StatisticsOrder

logger = logging.getLogger(__name__)


class SearchHistoryService:
    def _collection(self):
        db = get_mongo_db()
        if db is None:
            raise SearchHistoryUnavailableError

        return db[settings.SEARCH_QUERIES_COLLECTION]

    async def record(
        self,
        search_type: SearchType,
        params: dict[str, str | list[str]],
        results_count: int,
    ) -> None:
        try:
            collection = self._collection()
            await collection.insert_one(
                {
                    "timestamp": datetime.now(UTC),
                    "search_type": search_type,
                    "params": params,
                    "results_count": results_count,
                }
            )
        except (PyMongoError, SearchHistoryUnavailableError) as exc:
            # Сбой журнала не должен ломать успешно выполненный поиск в MySQL.
            logger.error("Could not save search history: %s", exc)

    async def get_statistics(
        self,
        order: StatisticsOrder,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        effective_limit = limit or settings.SEARCH_STATISTICS_LIMIT
        collection = self._collection()

        try:
            cursor = collection.aggregate(self._pipeline(order, effective_limit))
            return await cursor.to_list(length=effective_limit)
        except PyMongoError as exc:
            logger.error("Could not read search statistics: %s", exc)
            raise SearchHistoryUnavailableError from exc

    @staticmethod
    def _pipeline(order: StatisticsOrder, limit: int) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {"$sort": {"timestamp": -1}},
            {
                "$group": {
                    "_id": {
                        "search_type": "$search_type",
                        "params": "$params",
                    },
                    "timestamp": {"$first": "$timestamp"},
                    "results_count": {"$first": "$results_count"},
                    "frequency": {"$sum": 1},
                }
            },
        ]

        if order == "frequency":
            pipeline.append({"$sort": {"frequency": -1, "timestamp": -1}})
        else:
            pipeline.append({"$sort": {"timestamp": -1}})

        pipeline.extend(
            [
                {"$limit": limit},
                {
                    "$project": {
                        "_id": 0,
                        "timestamp": 1,
                        "search_type": "$_id.search_type",
                        "params": "$_id.params",
                        "results_count": 1,
                        "frequency": 1,
                    }
                },
            ]
        )
        return pipeline
