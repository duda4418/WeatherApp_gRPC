"""Factories for test data objects (simplified to plain functions)."""

from __future__ import annotations
from datetime import datetime, timedelta, UTC


def raw_openweather_payload(city: str = "Berlin", temp: float = 12.34):
    return {
        "name": city,
        "main": {"temp": temp, "humidity": 55},
        "weather": [{"description": "clear sky", "icon": "01d"}],
        "wind": {"speed": 3.2},
        "dt": int(datetime.now(UTC).timestamp()),
        "sys": {"country": "DE", "sunrise": int(datetime.now(UTC).timestamp()), "sunset": int(datetime.now(UTC).timestamp())},
        "coord": {"lat": 52.52, "lon": 13.405},
        "visibility": 10000,
        "clouds": {"all": 10},
    }


def observation_doc(city="Berlin", temp=10.0, minutes_ago=0):
    ts = datetime.now(UTC) - timedelta(minutes=minutes_ago)
    return {
        "city": city,
        "observation_time": ts,
        "fetched_at": ts,
        "temp_c": temp,
        "raw": raw_openweather_payload(city=city, temp=temp),
    }
