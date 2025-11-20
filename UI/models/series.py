from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SeriesPoint(BaseModel):
    timestamp: datetime = Field(description="UTC timestamp of the bucket start")
    avg_temp_c: float = Field(description="Average temperature in Celsius for the bucket")
    icon: Optional[str] = Field(default=None, description="Representative weather icon code for the bucket")

    def as_response(self) -> dict:
        icon_url = f"https://openweathermap.org/img/wn/{self.icon}@2x.png" if self.icon else None
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "avg_temp_c": round(self.avg_temp_c, 2),
            "icon": self.icon,
            "icon_url": icon_url,
        }

class DailyPoint(BaseModel):
    date: str = Field(description="ISO date YYYY-MM-DD (UTC day)")
    avg_temp_c: float = Field(description="Average temperature in Celsius for the day")
    icon: Optional[str] = Field(default=None, description="Representative weather icon code for the day")

    def as_response(self) -> dict:
        icon_url = f"https://openweathermap.org/img/wn/{self.icon}@2x.png" if self.icon else None
        return {"date": self.date, "avg_temp_c": round(self.avg_temp_c, 2), "icon": self.icon, "icon_url": icon_url}
