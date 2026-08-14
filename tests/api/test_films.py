import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.exceptions import RequestValidationError
from pydantic import TypeAdapter

from films.api.dependencies import (
    get_film_filter,
    get_film_service,
    get_search_history_service,
)
from films.api.v1.films import (
    FilmPageSize,
    get_films,
    get_search_statistics,
)
from films.main import app


async def asgi_get(path: str, query: str = "") -> tuple[int, dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    request_delivered = False
    wait_for_response = asyncio.Event()

    async def receive() -> dict[str, Any]:
        nonlocal request_delivered
        if not request_delivered:
            request_delivered = True
            return {"type": "http.request", "body": b"", "more_body": False}

        await wait_for_response.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": query.encode(),
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 50000),
            "server": ("test", 80),
        },
        receive,
        send,
    )

    status = next(
        message["status"]
        for message in messages
        if message["type"] == "http.response.start"
    )
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return status, json.loads(body)


class FakeFilmService:
    def __init__(self) -> None:
        self.last_filter = None

    async def get_films(self, _filter, page: int, size: int):
        self.last_filter = _filter
        return {
            "items": [],
            "total": 23,
            "page": page,
            "size": size,
            "pages": 3,
        }


class FakeSearchHistoryService:
    def __init__(self) -> None:
        self.records = []
        self.statistics_calls = []

    async def record(self, **document) -> None:
        self.records.append(document)

    async def get_statistics(self, order: str, limit: int):
        self.statistics_calls.append((order, limit))
        return [
            {
                "timestamp": datetime(2025, 5, 1, 15, 34, tzinfo=UTC),
                "search_type": "keyword",
                "params": {"keyword": "matrix"},
                "results_count": 3,
                "frequency": 2,
            }
        ]


@pytest.fixture
def services():
    history = FakeSearchHistoryService()
    return FakeFilmService(), history


def test_keyword_search_records_full_count_only_on_first_page(services) -> None:
    film_service, history = services
    film_filter = asyncio.run(get_film_filter(keyword="  The   Matrix  "))

    result = asyncio.run(get_films(film_service, history, film_filter, page=1, size=10))

    assert result["total"] == 23
    assert history.records == [
        {
            "search_type": "keyword",
            "params": {"keyword": "the matrix"},
            "results_count": 23,
        }
    ]

    asyncio.run(get_films(film_service, history, film_filter, page=2, size=10))
    assert len(history.records) == 1


def test_genre_year_search_is_recorded(services) -> None:
    film_service, history = services
    film_filter = asyncio.run(
        get_film_filter(
            genre=["Action", "Comedy"],
            year_from=2001,
            year_to=2010,
        )
    )

    asyncio.run(get_films(film_service, history, film_filter, page=1, size=10))

    assert history.records[0]["search_type"] == "filters"
    assert history.records[0]["params"] == {
        "genres": ["Action", "Comedy"],
        "years_range": "2001-2010",
    }


def test_combined_filters_are_recorded_without_reset(services) -> None:
    film_service, history = services
    film_filter = asyncio.run(
        get_film_filter(
            keyword="Academy",
            genre=["Action", "Comedy"],
            year_from=2000,
            year_to=2020,
        )
    )

    asyncio.run(get_films(film_service, history, film_filter, page=1, size=10))

    assert history.records[0] == {
        "search_type": "filters",
        "params": {
            "keyword": "academy",
            "genres": ["Action", "Comedy"],
            "years_range": "2000-2020",
        },
        "results_count": 23,
    }


@pytest.mark.parametrize(
    "params",
    [
        {"genre": ["Action"], "year_from": 2010, "year_to": 2000},
        {"order_by": "unknown"},
    ],
)
def test_invalid_search_parameters_are_reported(params) -> None:
    with pytest.raises(RequestValidationError):
        asyncio.run(get_film_filter(**params))


@pytest.mark.parametrize("order", ["frequency", "latest"])
def test_statistics_modes(services, order: str) -> None:
    _film_service, history = services

    response = asyncio.run(get_search_statistics(history, order=order, limit=5))

    assert history.statistics_calls == [(order, 5)]
    assert response["items"][0]["results_count"] == 3


def test_application_exposes_required_routes() -> None:
    paths = {route.path for route in app.routes}

    assert "/v1/films/" in paths
    assert "/v1/films/search-meta" in paths
    assert "/v1/films/search-statistics" in paths


def test_supported_page_size_is_passed_to_service(services) -> None:
    film_service, history = services
    film_filter = asyncio.run(get_film_filter(keyword="academy"))

    result = asyncio.run(get_films(film_service, history, film_filter, page=1, size=24))

    assert result["size"] == 24


def test_page_size_is_parsed_from_query_string() -> None:
    page_size_adapter = TypeAdapter(FilmPageSize)

    assert page_size_adapter.validate_python("12") is FilmPageSize.TWELVE


def test_http_layer_parses_repeated_filters_and_serializes_response() -> None:
    film_service = FakeFilmService()
    history = FakeSearchHistoryService()

    async def override_film_service():
        return film_service

    async def override_history_service():
        return history

    app.dependency_overrides[get_film_service] = override_film_service
    app.dependency_overrides[get_search_history_service] = override_history_service

    async def make_request():
        return await asgi_get("/v1/films/", "genre=Comedy&genre=Action&size=12")

    try:
        status, body = asyncio.run(make_request())
    finally:
        app.dependency_overrides.clear()

    assert status == 200
    assert body["size"] == 12
    assert film_service.last_filter.genres == ["Action", "Comedy"]
    assert history.records[0]["search_type"] == "filters"


def test_http_layer_returns_422_for_incomplete_year_range() -> None:
    film_service = FakeFilmService()
    history = FakeSearchHistoryService()

    async def override_film_service():
        return film_service

    async def override_history_service():
        return history

    app.dependency_overrides[get_film_service] = override_film_service
    app.dependency_overrides[get_search_history_service] = override_history_service

    async def make_request():
        return await asgi_get("/v1/films/", "year_from=2001")

    try:
        status, _body = asyncio.run(make_request())
    finally:
        app.dependency_overrides.clear()

    assert status == 422
    assert film_service.last_filter is None
