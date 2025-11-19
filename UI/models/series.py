from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

class SeriesPoint(BaseModel):
    timestamp: datetime = Field(description="UTC timestamp of the bucket start")
    avg_temp_c: float = Field(description="Average temperature in Celsius for the bucket")

    def as_response(self) -> dict:
        return {"timestamp": self.timestamp.isoformat() + "Z", "avg_temp_c": round(self.avg_temp_c, 2)}

class DailyPoint(BaseModel):
    date: str = Field(description="ISO date YYYY-MM-DD (UTC day)")
    avg_temp_c: float = Field(description="Average temperature in Celsius for the day")

    def as_response(self) -> dict:
        return {"date": self.date, "avg_temp_c": round(self.avg_temp_c, 2)}
