"""Simple FastAPI app to serve temperature series for charting.
Matches requirement: provide UI chart of temperature fluctuations over time.

Endpoint:
  GET /api/series?city=London&minutes=60&bucket=5
Returns JSON: {"city": "London", "points": [{"timestamp": "2025-11-17T10:00:00Z", "avg_temp_c": 12.3}, ...]}

To run:
  uvicorn chart_api:app --reload --port 8000

Static UI (index.html) will fetch this endpoint and render a chart.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from db.mongo_repository import MongoRepository
from core.settings import settings

repo = MongoRepository(settings.MONGO_URI)

app = FastAPI(title="Weather Chart API", version="1.0.0")

@app.get('/', include_in_schema=False)
def root():
    return FileResponse('static/index.html')

@app.get('/api/series')
def series(city: str = Query(..., min_length=1), minutes: int = Query(60, ge=1, le=1440), bucket: int = Query(5, ge=1, le=60)):
    # Compute time window
    end = datetime.utcnow().replace(tzinfo=timezone.utc)
    start = end - timedelta(minutes=minutes)
    # Use repository bucketing if available
    observations: List[Dict] = repo.get_temperature_series(city, start.replace(tzinfo=None), end.replace(tzinfo=None), bucket_minutes=bucket)
    if not observations:
        # Try raw observations fallback
        raw = repo.get_observations(city, start.replace(tzinfo=None), end.replace(tzinfo=None))
        if not raw:
            raise HTTPException(status_code=404, detail="No data for city/time range")
        observations = [{"timestamp": d["observation_time"], "avg_temp_c": d.get("temp_c", 0)} for d in raw]
    points = [
        {"timestamp": (o["timestamp"].isoformat() + 'Z'), "avg_temp_c": round(o["avg_temp_c"], 2)}
        for o in observations
    ]
    return {"city": city, "points": points, "bucket_minutes": bucket, "window_minutes": minutes}

@app.get('/api/daily')
def daily(city: str = Query(..., min_length=1), days: int = Query(7, ge=1, le=60)):
        """Return average temperature per day for the last `days` days.

        Response JSON:
            {"city": "London", "points": [{"date": "2025-11-19", "avg_temp_c": 11.3}, ...], "window_days": 7}
        """
        series = repo.get_daily_series(city, days)
        if not series:
                raise HTTPException(status_code=404, detail="No daily data for city")
        # Already date isoformat + avg_temp_c provided
        points = [{"date": s["date"], "avg_temp_c": round(s["avg_temp_c"], 2)} for s in series]
        return {"city": city, "points": points, "window_days": days}
