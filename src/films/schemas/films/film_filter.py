"""Валидация, нормализация и журналирование фильтров фильмов."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from films.schemas.films.search_statistic import SearchType

FilmOrder = Literal["title", "-title", "release_year", "-release_year"]


class FilmFilter(BaseModel):
    """Нормализованные параметры поиска фильмов."""

    keyword: str | None = None
    title: str | None = None
    genres: list[str] = Field(default_factory=list)
    ratings: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    year: int | None = Field(default=None, ge=1800)
    year_from: int | None = Field(default=None, ge=1800)
    year_to: int | None = Field(default=None, ge=1800)
    length_from: int | None = Field(default=None, ge=0)
    length_to: int | None = Field(default=None, ge=0)

    order_by: FilmOrder = "title"

    @field_validator("keyword", "title", mode="before")
    @classmethod
    def strip_text_filter(cls, value: str | None) -> str | None:
        """Удалить крайние и повторяющиеся пробелы текстового фильтра."""

        if value is None:
            return None

        normalized = " ".join(value.strip().split())
        return normalized or None

    @field_validator("genres", "ratings", "features")
    @classmethod
    def normalize_list_filters(cls, values: list[str]) -> list[str]:
        """Очистить, дедуплицировать и стабильно отсортировать список."""

        normalized = [" ".join(value.strip().split()) for value in values]
        return sorted(dict.fromkeys(value for value in normalized if value))

    @model_validator(mode="after")
    def validate_year_range(self) -> "FilmFilter":
        """Согласовать одиночный год и проверить числовые диапазоны."""

        if self.keyword and self.title:
            raise ValueError("Укажите только один параметр: keyword или title")

        if self.year is not None:
            self.year_from = self.year
            self.year_to = self.year

        if (self.year_from is None) != (self.year_to is None):
            raise ValueError("Укажите обе границы: year_from и year_to")

        if (
            self.year_from is not None
            and self.year_to is not None
            and self.year_from > self.year_to
        ):
            raise ValueError("year_from должен быть меньше или равен year_to")

        if (
            self.length_from is not None
            and self.length_to is not None
            and self.length_from > self.length_to
        ):
            raise ValueError("length_from должен быть меньше или равен length_to")

        return self

    def search_event(
        self,
    ) -> tuple[SearchType, dict[str, str | list[str]]] | None:
        """Построить каноническое событие для истории поиска."""

        keyword = self.keyword or self.title
        has_years = self.year_from is not None and self.year_to is not None
        has_non_keyword_filters = any(
            (
                self.genres,
                self.ratings,
                self.features,
                has_years,
                self.length_from is not None,
                self.length_to is not None,
            )
        )
        if not keyword and not has_non_keyword_filters:
            return None

        params: dict[str, str | list[str]] = {}
        if keyword:
            params["keyword"] = keyword.lower()

        if self.genres:
            if len(self.genres) == 1:
                params["genre"] = self.genres[0]
            else:
                params["genres"] = self.genres

        if has_years:
            years_range = (
                str(self.year_from)
                if self.year_from == self.year_to
                else f"{self.year_from}-{self.year_to}"
            )
            params["years_range"] = years_range

        if self.ratings:
            params["ratings"] = sorted(self.ratings)
        if self.features:
            params["features"] = sorted(self.features)
        if self.length_from is not None:
            params["length_from"] = str(self.length_from)
        if self.length_to is not None:
            params["length_to"] = str(self.length_to)

        search_type = (
            "keyword" if keyword and not has_non_keyword_filters else "filters"
        )
        return search_type, params
