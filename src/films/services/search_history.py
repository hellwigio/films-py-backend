"""Запись поисковых событий и агрегация статистики в MongoDB."""

import logging
from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from films.config import settings
from films.exceptions.search import SearchHistoryUnavailableError
from films.schemas.films.search_statistic import SearchType, StatisticsOrder

logger = logging.getLogger(__name__)


class SearchHistoryService:
    """Работать с коллекцией истории поиска без глобального состояния."""

    def __init__(
        self,
        database: AsyncIOMotorDatabase | None,
        collection_name: str | None = None,
    ) -> None:
        self.database = database
        self.collection_name = collection_name or settings.SEARCH_QUERIES_COLLECTION

    def _collection(self):
        if self.database is None:
            raise SearchHistoryUnavailableError

        return self.database[self.collection_name]

    async def record(
        self,
        search_type: SearchType,
        params: dict[str, str | list[str]],
        results_count: int,
    ) -> None:
        """Сохранить поисковое событие, не прерывая поиск при сбое MongoDB."""

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
        """Вернуть уникальные запросы, отсортированные по выбранному режиму."""

        effective_limit = limit or settings.SEARCH_STATISTICS_LIMIT
        collection = self._collection()

        try:
            cursor = collection.aggregate(self._pipeline(order, effective_limit))
            return await cursor.to_list(length=effective_limit)
        except PyMongoError as exc:
            logger.error("Could not read search statistics: %s", exc)
            raise SearchHistoryUnavailableError from exc

    @staticmethod
    def _search_type_expression() -> dict[str, Any]:
        """Собрать канонический тип из фактически сохранённых параметров."""

        def has_param(name: str) -> dict[str, Any]:
            return {"$ne": [{"$type": f"$params.{name}"}, "missing"]}

        has_years_range = has_param("years_range")
        years_range_has_separator = {
            "$regexMatch": {
                "input": {"$ifNull": ["$params.years_range", ""]},
                "regex": "-",
            }
        }
        components = [
            (has_param("keyword"), "keyword"),
            ({"$or": [has_param("genre"), has_param("genres")]}, "genre"),
            (
                {
                    "$or": [
                        has_param("year"),
                        {
                            "$and": [
                                has_years_range,
                                {"$not": [years_range_has_separator]},
                            ]
                        },
                    ]
                },
                "year",
            ),
            (
                {"$and": [has_years_range, years_range_has_separator]},
                "years_range",
            ),
            (has_param("ratings"), "rating"),
            (has_param("features"), "feature"),
            (has_param("length_from"), "length_from"),
            (has_param("length_to"), "length_to"),
        ]
        parts = [
            {"$cond": [condition, [component], []]}
            for condition, component in components
        ]

        return {
            "$reduce": {
                "input": {"$concatArrays": parts},
                "initialValue": "",
                "in": {
                    "$cond": [
                        {"$eq": ["$$value", ""]},
                        "$$this",
                        {"$concat": ["$$value", "__", "$$this"]},
                    ]
                },
            }
        }

    @staticmethod
    def _pipeline(order: StatisticsOrder, limit: int) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {"$sort": {"timestamp": -1}},
            {"$set": {"search_type": SearchHistoryService._search_type_expression()}},
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
