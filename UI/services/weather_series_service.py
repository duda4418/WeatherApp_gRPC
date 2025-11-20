from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from db.mongo_repository import MongoRepository
from UI.models.series import SeriesPoint, DailyPoint

class WeatherSeriesService:
    """Application layer for producing temperature time series.

    Wraps repository queries and fallback logic, returning typed models.
    """
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    def get_bucketed_series(self, city: str, minutes: int, bucket: int) -> List[SeriesPoint]:
        end = datetime.utcnow().replace(tzinfo=timezone.utc)
        start = end - timedelta(minutes=minutes)
        # repository expects naive datetimes (assumed UTC)
        observations = self.repo.get_temperature_series(city, start.replace(tzinfo=None), end.replace(tzinfo=None), bucket_minutes=bucket)
        if not observations:
            raw = self.repo.get_observations(city, start.replace(tzinfo=None), end.replace(tzinfo=None))
            if not raw:
                return []
            observations = [
                {"timestamp": data["observation_time"], "avg_temp_c": data.get("temp_c", 0.0)}
                for data in raw
            ]
        points: List[SeriesPoint] = [
            SeriesPoint(
                timestamp=obs["timestamp"],
                avg_temp_c=obs.get("avg_temp_c", 0.0),
                icon=obs.get("icon")
            )
            for obs in observations
        ]
        return points

    def get_daily_series(self, city: str, days: int) -> List[DailyPoint]:
        series = self.repo.get_daily_series(city, days)
        if not series:
            return []
        return [
            DailyPoint(
                date=day["date"],
                avg_temp_c=day.get("avg_temp_c", 0.0),
                icon=day.get("icon")
            )
            for day in series
        ]
