from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SearchType = Literal["keyword", "genre__years_range"]
StatisticsOrder = Literal["frequency", "latest"]


class SearchStatisticItem(BaseModel):
    timestamp: datetime
    search_type: SearchType
    params: dict[str, str | list[str]]
    results_count: int = Field(ge=0)
    frequency: int = Field(ge=1)


class SearchStatisticsResponse(BaseModel):
    items: list[SearchStatisticItem]
