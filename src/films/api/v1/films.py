"""HTTP-маршруты каталога и статистики поиска фильмов."""

from enum import IntEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from films.api.dependencies import (
    get_film_filter,
    get_film_service,
    get_search_history_service,
)
from films.schemas.films.film import (
    FilmListResponse,
    FilmResponse,
    FilmSearchMetaResponse,
)
from films.schemas.films.film_filter import FilmFilter
from films.schemas.films.search_statistic import (
    SearchStatisticsResponse,
    StatisticsOrder,
)
from films.services.film import FilmService
from films.services.search_history import SearchHistoryService

films_router = APIRouter()


class FilmPageSize(IntEnum):
    """Поддерживаемые размеры страницы каталога."""

    TEN = 10
    TWELVE = 12
    TWENTY_FOUR = 24
    THIRTY_SIX = 36
    FORTY_EIGHT = 48


@films_router.get("/search-meta", response_model=FilmSearchMetaResponse)
async def get_search_meta(
    service: Annotated[FilmService, Depends(get_film_service)],
):
    """Вернуть данные, необходимые для построения формы поиска."""

    return await service.get_search_meta()


@films_router.get("/search-statistics", response_model=SearchStatisticsResponse)
async def get_search_statistics(
    search_history_service: Annotated[
        SearchHistoryService, Depends(get_search_history_service)
    ],
    order: StatisticsOrder = "frequency",
    limit: Annotated[int, Query(ge=1, le=5)] = 5,
):
    """Вернуть частые или последние уникальные поисковые запросы."""

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
    track_search: bool = False,
):
    """Вернуть страницу фильмов и при необходимости записать поиск."""

    result = await service.get_films(filter, page=page, size=int(size))

    search_event = filter.search_event()
    if track_search and search_event and page == 1:
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
    """Вернуть один фильм по идентификатору."""

    return await service.get_film(film_id)
