from datetime import UTC, datetime
import pytest
import proto.weather_pb2 as weather_pb2
from weather_service.service import WeatherService
from weather_service.errors import UpstreamNotFoundError


class FakeRepo:
    def __init__(self):
        self.inserted = []
    def insert_observation(self, doc):
        self.inserted.append(doc)
        return "id"


class FakeProvider:
    def __init__(self, data=None, error=None):
        self._data = data
        self._error = error
    def get_current(self, city):
        if self._error:
            raise self._error
        return self._data or {
            "name": city,
            "main": {"temp": 11.1, "humidity": 50},
            "weather": [{"description": "few clouds"}],
            "wind": {"speed": 2.5},
        }


class DummyContext:
    def __init__(self):
        self.aborted = None
    def abort(self, code, message):
        self.aborted = (code, message)
        raise RuntimeError(f"aborted: {code} {message}")


def test_weather_service_happy_path():
    repo = FakeRepo()
    provider = FakeProvider()
    svc = WeatherService(repo, provider)
    req = weather_pb2.GetWeatherRequest(city="Constanța")
    ctx = DummyContext()
    resp = svc.GetCurrentWeather(req, ctx)
    assert resp.city == "Constanta"  # normalization
    assert repo.inserted[0]["city"] == "Constanta"
    assert resp.temp_c == pytest.approx(11.1)


def test_weather_service_not_found_maps_status():
    repo = FakeRepo()
    provider = FakeProvider(error=UpstreamNotFoundError("missing"))
    svc = WeatherService(repo, provider)
    req = weather_pb2.GetWeatherRequest(city="X")
    ctx = DummyContext()
    with pytest.raises(RuntimeError):
        svc.GetCurrentWeather(req, ctx)
    assert ctx.aborted is not None
