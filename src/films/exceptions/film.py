"""Ошибки операций с фильмами."""

from films.exceptions.base import EntityNotFoundError


class FilmNotFoundError(EntityNotFoundError):
    """Фильм с указанным идентификатором отсутствует."""

    def __init__(self, film_id: int):
        self.message = f"Film with id {film_id} not found"
        super().__init__(self.message)
