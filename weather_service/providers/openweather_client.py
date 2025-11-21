"""Client wrapper for OpenWeatherMap HTTP API."""

from __future__ import annotations
from typing import Any, Dict
from datetime import UTC, datetime
import requests

from core.settings import settings
from weather_service.errors import (
    UpstreamNotFoundError,
    UpstreamHttpError,
    UpstreamInvalidResponse,
    UpstreamRequestError,
)


class OpenWeatherClient:
    """Thin HTTP client for current weather endpoint (metric units)."""

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, timeout: int = 8):
        self._api_key = api_key or settings.OPENWEATHER_API_KEY
        self._base_url = base_url or settings.OPENWEATHER_URL
        self._timeout = timeout

    def get_current(self, city: str) -> Dict[str, Any]:  # noqa: D401
        if not self._api_key:
            raise RuntimeError("OPENWEATHER_API_KEY not set")
        params = {"q": city, "appid": self._api_key, "units": "metric"}
        try:
            resp = requests.get(self._base_url, params=params, timeout=self._timeout)
        except requests.RequestException as e:  # network / timeout
            raise UpstreamRequestError(str(e)) from e
        if resp.status_code == 404:
            raise UpstreamNotFoundError(f"City '{city}' not found")
        if resp.status_code != 200:
            raise UpstreamHttpError(resp.status_code)
        try:
            data = resp.json()
        except ValueError as e:
            raise UpstreamInvalidResponse("Invalid JSON from OpenWeather") from e
        # Basic invariant sanity check
        if "main" not in data:
            raise UpstreamInvalidResponse("Missing 'main' section in response")
        # Attach retrieval timestamp for convenience
        data.setdefault("_fetched_at", datetime.now(UTC).isoformat())
        return data
