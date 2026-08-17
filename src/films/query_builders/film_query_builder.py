"""Построение SQLAlchemy-запросов для поиска фильмов."""

from sqlalchemy import Select, and_, or_, select

from films.models.film import Category, Film
from films.schemas.films.film_filter import FilmFilter


class FilmQueryBuilder:
    """Собрать SELECT с фильтрами и стабильной сортировкой фильмов."""

    def __init__(self, filter: FilmFilter):
        self.filter = filter

    def build(self) -> Select:
        """Вернуть итоговый SQLAlchemy SELECT."""

        query = select(Film)

        query = self._apply_filter(query)
        query = self._apply_sort(query)

        return query

    def _apply_filter(self, query: Select) -> Select:
        f = self.filter

        title_query = f.keyword or f.title
        if title_query:
            query = query.where(Film.title.ilike(f"%{title_query}%"))

        if f.genres:
            query = query.join(Film.categories).where(Category.name.in_(f.genres))

        if f.ratings:
            query = query.where(Film.rating.in_(f.ratings))

        if f.features:
            query = query.where(
                or_(
                    *(
                        Film.special_features.like(f"%{feature}%")
                        for feature in f.features
                    )
                )
            )

        year_range = None
        if f.year_from is not None and f.year_to is not None:
            year_range = and_(
                Film.release_year >= f.year_from,
                Film.release_year <= f.year_to,
            )

        has_distinct_exact_year = f.year is not None and (
            f.year_from != f.year or f.year_to != f.year
        )
        if year_range is not None and has_distinct_exact_year:
            query = query.where(or_(year_range, Film.release_year == f.year))
        elif f.year is not None:
            query = query.where(Film.release_year == f.year)
        elif year_range is not None:
            query = query.where(year_range)

        if f.length_from is not None:
            query = query.where(Film.length >= f.length_from)

        if f.length_to is not None:
            query = query.where(Film.length <= f.length_to)

        return query.distinct()

    def _apply_sort(self, query: Select) -> Select:
        sort_map = {
            "title": Film.title,
            "release_year": Film.release_year,
        }

        f = self.filter.order_by

        if f.startswith("-"):
            return query.order_by(sort_map[f[1:]].desc(), Film.id.asc())

        query = query.order_by(sort_map[f].asc(), Film.id.asc())
        return query
