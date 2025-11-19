from __future__ import annotations

from typing import Any, Dict
from datetime import datetime

from db.mongo_repository import MongoRepository

class CurrentWeatherService:
    """Provide transformation of latest observation into enriched response structure."""
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    def get_current(self, city: str) -> Dict[str, Any] | None:
        doc = self.repo.get_latest_observation(city)
        if not doc:
            return None
        raw: Dict[str, Any] = doc.get("raw", {}) if isinstance(doc.get("raw"), dict) else {}
        main = raw.get("main", {})
        wind = raw.get("wind", {})
        sys = raw.get("sys", {})
        weather_list = raw.get("weather", []) or []
        weather0 = weather_list[0] if weather_list else {}
        clouds = raw.get("clouds", {})
        coord = raw.get("coord", {})
        visibility = raw.get("visibility")
        ts = raw.get("dt")
        sunrise = sys.get("sunrise")
        sunset = sys.get("sunset")

        def ts_to_iso(sec: int | None) -> str | None:
            if not isinstance(sec, int):
                return None
            return datetime.utcfromtimestamp(sec).isoformat() + "Z"

        return {
            "city": doc.get("city") or raw.get("name") or city,
            "observation_time_iso": doc.get("observation_time").isoformat() + "Z" if isinstance(doc.get("observation_time"), datetime) else None,
            "source_timestamp_iso": ts_to_iso(ts),
            "coords": {"lat": coord.get("lat"), "lon": coord.get("lon")},
            "weather": {
                "id": weather0.get("id"),
                "main": weather0.get("main"),
                "description": weather0.get("description"),
                "icon": weather0.get("icon"),
                "icon_url": f"https://openweathermap.org/img/wn/{weather0.get('icon')}@2x.png" if weather0.get("icon") else None,
            },
            "temperature": {
                "temp_c": main.get("temp"),
                "feels_like_c": main.get("feels_like"),
                "min_c": main.get("temp_min"),
                "max_c": main.get("temp_max"),
            },
            "pressure": {
                "hpa": main.get("pressure"),
                "sea_level_hpa": main.get("sea_level"),
                "ground_level_hpa": main.get("grnd_level"),
            },
            "humidity_pct": main.get("humidity"),
            "visibility_m": visibility,
            "wind": {
                "speed_ms": wind.get("speed"),
                "deg": wind.get("deg"),
            },
            "cloud_coverage_pct": clouds.get("all"),
            "sun": {
                "sunrise_iso": ts_to_iso(sunrise),
                "sunset_iso": ts_to_iso(sunset),
            },
            "country": sys.get("country"),
        }
