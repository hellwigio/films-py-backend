import asyncio
from datetime import datetime

from films.services.search_history import SearchHistoryService


class FakeCollection:
    def __init__(self) -> None:
        self.document = None

    async def insert_one(self, document) -> None:
        self.document = document


class FakeDatabase:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection = collection

    def __getitem__(self, _name: str) -> FakeCollection:
        return self.collection


def test_record_stores_required_document_fields() -> None:
    collection = FakeCollection()

    asyncio.run(
        SearchHistoryService(FakeDatabase(collection)).record(
            search_type="keyword",
            params={"keyword": "matrix"},
            results_count=3,
        )
    )

    assert set(collection.document) == {
        "timestamp",
        "search_type",
        "params",
        "results_count",
    }
    assert isinstance(collection.document["timestamp"], datetime)
    assert collection.document["results_count"] == 3


def test_frequency_pipeline_groups_unique_queries() -> None:
    pipeline = SearchHistoryService._pipeline("frequency", 5)

    assert pipeline[1]["$group"]["frequency"] == {"$sum": 1}
    assert pipeline[2] == {"$sort": {"frequency": -1, "timestamp": -1}}
    assert pipeline[3] == {"$limit": 5}


def test_latest_pipeline_sorts_unique_queries_by_timestamp() -> None:
    pipeline = SearchHistoryService._pipeline("latest", 5)

    assert pipeline[0] == {"$sort": {"timestamp": -1}}
    assert pipeline[2] == {"$sort": {"timestamp": -1}}
    assert pipeline[3] == {"$limit": 5}
