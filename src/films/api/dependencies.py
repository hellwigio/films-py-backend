"""FastAPI-зависимости сервисов и параметров поиска."""

from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from films.config import settings
from films.database import get_async_session
from films.schemas.films.film_filter import FilmFilter, FilmOrder
from films.services.film import FilmService
from films.services.search_history import SearchHistoryService


async def get_film_service(
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> FilmService:
    """Создать сервис фильмов для текущей SQLAlchemy-сессии."""

    return FilmService(db)


async def get_search_history_service(request: Request) -> SearchHistoryService:
    """Создать сервис истории из MongoDB-состояния приложения."""

    return SearchHistoryService(
        database=getattr(request.app.state, "mongo_db", None),
        collection_name=settings.SEARCH_QUERIES_COLLECTION,
    )


async def get_film_filter(
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
    order_by: FilmOrder = "title",
) -> FilmFilter:
    """Собрать и дополнительно провалидировать фильтры query string."""

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
