"""Pydantic-схемы ответов каталога фильмов."""

from pydantic import BaseModel, ConfigDict


class FilmResponse(BaseModel):
    """Полное публичное представление фильма."""

    id: int
    title: str
    description: str | None
    release_year: int | None
    rental_duration: int
    rental_rate: float
    length: int | None
    replacement_cost: float
    rating: str | None
    genres: list[str]
    features: list[str]

    model_config = ConfigDict(from_attributes=True)


class FilmListResponse(BaseModel):
    """Страница фильмов с метаданными пагинации."""

    items: list[FilmResponse]
    total: int
    page: int
    size: int
    pages: int


class FilmSearchMetaResponse(BaseModel):
    """Допустимые значения и границы фильтров поиска."""

    genres: list[str]
    ratings: list[str]
    features: list[str]
    min_release_year: int | None
    max_release_year: int | None
    min_length: int | None
    max_length: int | None
