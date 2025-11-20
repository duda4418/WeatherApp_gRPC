"""Simple FastAPI app to serve temperature series for charting.
Matches requirement: provide UI chart of temperature fluctuations over time.

Endpoint:
  GET /api/series?city=London&minutes=60&bucket=5
Returns JSON: {"city": "London", "points": [{"timestamp": "2025-11-17T10:00:00Z", "avg_temp_c": 12.3}, ...]}

To run:
  uvicorn chart_api:app --reload --port 8000

Static UI (index.html) will fetch this endpoint and render a chart.
"""
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
from core.settings import settings

from UI.api.routers.series import router as series_router
from UI.api.routers.daily import router as daily_router
from UI.api.routers.current import router as current_router

settings.configure_logging()
logger = logging.getLogger("ui.chart")
app = FastAPI(title="Weather Chart API", version="1.0.0")

STATIC_DIR = Path(__file__).parent / 'static'
INDEX_FILE = STATIC_DIR / 'index.html'

@app.get('/', include_in_schema=False)
def root():
  if not INDEX_FILE.exists():
    logger.error("Missing static index file at %s", INDEX_FILE)
    return JSONResponse(status_code=404, content={"detail": "index.html not found"})
  return FileResponse(str(INDEX_FILE))

# Attach routers providing /api/series and /api/daily
app.include_router(series_router)
app.include_router(daily_router)
app.include_router(current_router)
