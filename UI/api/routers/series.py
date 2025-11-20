from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from db.mongo_repository import MongoRepository
from core.settings import settings
from UI.services.weather_series_service import WeatherSeriesService

repo = MongoRepository(settings.MONGO_URI)
service = WeatherSeriesService(repo)

router = APIRouter(prefix="/api", tags=["series"])

@router.get("/series")
def get_series(
    city: str = Query(..., min_length=1),
    minutes: int = Query(60, ge=1, le=1440),
    bucket: int = Query(5, ge=1, le=60),
):
    points = service.get_bucketed_series(city, minutes, bucket)
    if not points:
        raise HTTPException(status_code=404, detail="No data for city/time range")
    return {
        "city": city,
        "points": [p.as_response() for p in points],
        "bucket_minutes": bucket,
        "window_minutes": minutes,
    }
