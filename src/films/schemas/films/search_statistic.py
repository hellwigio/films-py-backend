"""Схемы документов и ответов статистики поисковых запросов."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ``genre__years_range`` remains readable for documents written by older releases.
SearchType = Literal["keyword", "filters", "genre__years_range"]
StatisticsOrder = Literal["frequency", "latest"]


class SearchStatisticItem(BaseModel):
    """Агрегированная статистика одного уникального запроса."""

    timestamp: datetime
    search_type: SearchType
    params: dict[str, str | list[str]]
    results_count: int = Field(ge=0)
    frequency: int = Field(ge=1)


class SearchStatisticsResponse(BaseModel):
    """Список агрегированных поисковых запросов."""

    items: list[SearchStatisticItem]
