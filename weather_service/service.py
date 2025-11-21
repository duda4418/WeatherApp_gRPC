"""Business logic implementation of WeatherService gRPC servicer."""

from __future__ import annotations

import logging
import unicodedata
from datetime import UTC, datetime

import grpc

import proto.weather_pb2 as weather_pb2
import proto.weather_pb2_grpc as weather_pb2_grpc
from weather_service.models import WeatherNormalized
from weather_service.errors import (
    UpstreamNotFoundError,
    UpstreamHttpError,
    UpstreamInvalidResponse,
    UpstreamRequestError,
)

logger = logging.getLogger("weather_service.service")


class WeatherService(weather_pb2_grpc.WeatherServiceServicer):
    def __init__(self, repo, provider): 
        # Store repository and provider references for later use
        self.repo = repo
        self.provider = provider

    def GetCurrentWeather(self, request, context): 
        city = request.city.strip()
        if not city:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "City required")
        try:
            data = self.provider.get_current(city)
        except UpstreamNotFoundError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, str(e))
        except UpstreamRequestError as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, f"HTTP error: {e}")
        except UpstreamHttpError as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Upstream error {e.status_code}")
        except UpstreamInvalidResponse as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

        # Normalize / strip diacritics from city name for persistence consistency
        upstream_city = data.get("name", city)
        ascii_city = unicodedata.normalize("NFKD", upstream_city).encode("ascii", "ignore").decode("ascii")

        normalized = WeatherNormalized(
            city=ascii_city or upstream_city,
            temp_c=data.get("main", {}).get("temp"),
            humidity_pct=data.get("main", {}).get("humidity"),
            conditions=(data.get("weather") or [{}])[0].get("description"),
            wind_speed_ms=(data.get("wind") or {}).get("speed"),
            fetched_at=datetime.now(UTC),
        )
        try:
            self.repo.insert_observation({
                "city": normalized.city,
                "provider": "openweathermap",
                "observation_time": normalized.fetched_at,
                "fetched_at": normalized.fetched_at,
                "temp_c": normalized.temp_c,
                "humidity_pct": normalized.humidity_pct,
                "wind_speed_ms": normalized.wind_speed_ms,
                "conditions": normalized.conditions,
                "raw": data,
            })
        except Exception as persist_err:  
            logger.warning("Failed to persist observation: %s", persist_err, exc_info=True)
        return weather_pb2.GetWeatherResponse(
            city=normalized.city,
            temp_c=normalized.temp_c or 0.0,
            humidity_pct=normalized.humidity_pct or 0,
            conditions=normalized.conditions or "",
            wind_speed_ms=normalized.wind_speed_ms or 0.0,
            fetched_at_iso=normalized.fetched_at.isoformat(),
        )
