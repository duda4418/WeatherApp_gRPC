from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from db.mongo_repository import MongoRepository
from core.settings import settings
from UI.services.weather_series_service import WeatherSeriesService

repo = MongoRepository(settings.MONGO_URI)
service = WeatherSeriesService(repo)

router = APIRouter(prefix="/api", tags=["daily"])

@router.get("/daily")
def get_daily(
    city: str = Query(..., min_length=1),
    days: int = Query(7, ge=1, le=60),
):
    points = service.get_daily_series(city, days)
    if not points:
        raise HTTPException(status_code=404, detail="No daily data for city")
    return {
        "city": city,
        "points": [p.as_response() for p in points],
        "window_days": days,
    }
