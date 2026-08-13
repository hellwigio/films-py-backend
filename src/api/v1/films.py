from enum import IntEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.schemas.films.film import (
    FilmListResponse,
    FilmResponse,
    FilmSearchMetaResponse,
)
from src.schemas.films.film_filter import FilmFilter
from src.schemas.films.search_statistic import (
    SearchStatisticsResponse,
    StatisticsOrder,
)
from src.services.film import FilmService
from src.services.search_history import SearchHistoryService

films_router = APIRouter()


class FilmPageSize(IntEnum):
    TEN = 10
    TWELVE = 12
    TWENTY_FOUR = 24
    THIRTY_SIX = 36
    FORTY_EIGHT = 48


def get_film_service(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> FilmService:
    return FilmService(db)


def get_search_history_service() -> SearchHistoryService:
    return SearchHistoryService()


def get_film_filter(
    keyword: str | None = None,
    title: str | None = None,
    genre: Annotated[list[str] | None, Query()] = None,
    ratings: Annotated[list[str] | None, Query()] = None,
    features: Annotated[list[str] | None, Query()] = None,
    year: Annotated[int | None, Query(ge=1800)] = None,
    year_from: Annotated[int | None, Query(ge=1800)] = None,
    year_to: Annotated[int | None, Query(ge=1800)] = None,
    length_from: Annotated[int | None, Query(ge=0)] = None,
    length_to: Annotated[int | None, Query(ge=0)] = None,
    order_by: str = "title",
) -> FilmFilter:
    try:
        return FilmFilter(
            keyword=keyword,
            title=title,
            genres=genre or [],
            ratings=ratings or [],
            features=features or [],
            year=year,
            year_from=year_from,
            year_to=year_to,
            length_from=length_from,
            length_to=length_to,
            order_by=order_by,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@films_router.get("/search-meta", response_model=FilmSearchMetaResponse)
async def get_search_meta(
    service: Annotated[FilmService, Depends(get_film_service)],
):
    return await service.get_search_meta()


@films_router.get("/search-statistics", response_model=SearchStatisticsResponse)
async def get_search_statistics(
    search_history_service: Annotated[
        SearchHistoryService, Depends(get_search_history_service)
    ],
    order: StatisticsOrder = "frequency",
    limit: Annotated[int, Query(ge=1, le=5)] = 5,
):
    items = await search_history_service.get_statistics(order=order, limit=limit)

    return {"items": items}


@films_router.get("/popular-searches", response_model=SearchStatisticsResponse)
async def get_popular_searches(
    search_history_service: Annotated[
        SearchHistoryService, Depends(get_search_history_service)
    ],
):
    """Обратная совместимость: пять запросов по частоте."""
    items = await search_history_service.get_statistics(order="frequency", limit=5)
    return {"items": items}


@films_router.get("/", response_model=FilmListResponse)
async def get_films(
    service: Annotated[FilmService, Depends(get_film_service)],
    search_history_service: Annotated[
        SearchHistoryService, Depends(get_search_history_service)
    ],
    filter: Annotated[FilmFilter, Depends(get_film_filter)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: FilmPageSize = FilmPageSize.TEN,
):
    result = await service.get_films(filter, page=page, size=int(size))

    search_event = filter.search_event()
    if search_event and page == 1:
        search_type, params = search_event
        await search_history_service.record(
            search_type=search_type,
            params=params,
            results_count=result["total"],
        )

    return result


@films_router.get("/{film_id}", response_model=FilmResponse)
async def get_film(
    film_id: int,
    service: Annotated[FilmService, Depends(get_film_service)],
):
    return await service.get_film(film_id)
