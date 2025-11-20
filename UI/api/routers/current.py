from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from core.settings import settings
from db.mongo_repository import MongoRepository
from UI.services.current_weather_service import CurrentWeatherService

repo = MongoRepository(settings.MONGO_URI)
service = CurrentWeatherService(repo)

router = APIRouter(prefix="/api", tags=["current"])

@router.get("/current")
def get_current(city: str = Query(..., min_length=1)):
    data = service.get_current(city)
    if not data:
        raise HTTPException(status_code=404, detail="No current observation for city")
    return data
