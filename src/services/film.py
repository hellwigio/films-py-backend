import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.exceptions.film import FilmNotFoundError
from src.exceptions.search import SearchParametersError
from src.models.film import Category, Film
from src.query_builders.film_query_builder import FilmQueryBuilder
from src.schemas.films.film_filter import FilmFilter


class FilmService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_films(self, filter: FilmFilter, page: int, size: int = 10):
        await self._validate_search_values(filter)
        query = FilmQueryBuilder(filter).build()
        count_query = select(func.count()).select_from(query.order_by(None).subquery())
        total = await self.db.scalar(count_query) or 0

        result = await self.db.execute(
            query.options(selectinload(Film.categories))
            .limit(size)
            .offset((page - 1) * size)
        )

        return {
            "items": result.scalars().all(),
            "total": total,
            "page": page,
            "size": size,
            "pages": math.ceil(total / size) if total else 0,
        }

    async def _validate_search_values(self, filter: FilmFilter) -> None:
        if filter.genres:
            genres_result = await self.db.execute(
                select(Category.name).where(Category.name.in_(filter.genres))
            )
            existing_genres = set(genres_result.scalars().all())
            unknown_genres = [
                genre for genre in filter.genres if genre not in existing_genres
            ]
            if unknown_genres:
                raise SearchParametersError(
                    f"Неизвестные жанры: {', '.join(unknown_genres)}. "
                    "Выберите жанры из search-meta."
                )

        if filter.year_from is None and filter.year_to is None:
            return

        min_year, max_year = (
            await self.db.execute(
                select(func.min(Film.release_year), func.max(Film.release_year))
            )
        ).one()
        if min_year is None or max_year is None:
            return

        if filter.year_from is not None and filter.year_from < min_year:
            raise SearchParametersError(
                f"Минимальный год в базе — {min_year}. Исправьте диапазон."
            )
        if filter.year_to is not None and filter.year_to > max_year:
            raise SearchParametersError(
                f"Максимальный год в базе — {max_year}. Исправьте диапазон."
            )

    async def get_search_meta(self):
        genres_result = await self.db.execute(
            select(Category.name).order_by(Category.name)
        )
        ratings_result = await self.db.execute(
            select(Film.rating)
            .where(Film.rating.is_not(None))
            .distinct()
            .order_by(Film.rating)
        )
        years_result = await self.db.execute(
            select(func.min(Film.release_year), func.max(Film.release_year))
        )
        min_release_year, max_release_year = years_result.one()
        length_result = await self.db.execute(
            select(func.min(Film.length), func.max(Film.length))
        )
        min_length, max_length = length_result.one()

        features_result = await self.db.execute(
            select(Film.special_features)
            .where(Film.special_features.is_not(None))
            .where(Film.special_features != "")
        )
        all_features: set[str] = set()
        for row in features_result.scalars().all():
            for f in row.split(","):
                stripped = f.strip()
                if stripped:
                    all_features.add(stripped)

        return {
            "genres": list(genres_result.scalars().all()),
            "ratings": list(ratings_result.scalars().all()),
            "features": sorted(all_features),
            "min_release_year": min_release_year,
            "max_release_year": max_release_year,
            "min_length": min_length,
            "max_length": max_length,
        }

    async def get_film(self, film_id: int) -> Film:
        query = (
            select(Film)
            .where(Film.id == film_id)
            .options(selectinload(Film.categories))
        )
        res = await self.db.execute(query)
        film = res.scalar_one_or_none()

        if film is None:
            raise FilmNotFoundError(film_id)

        return film
