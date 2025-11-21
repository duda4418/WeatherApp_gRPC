"""Domain models for Weather service (Pydantic)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WeatherNormalized(BaseModel):
    city: str
    temp_c: float | None
    humidity_pct: Optional[int] = Field(default=None)
    conditions: Optional[str] = Field(default=None)
    wind_speed_ms: Optional[float] = Field(default=None)
    fetched_at: datetime
