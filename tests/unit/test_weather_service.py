
from datetime import UTC, datetime
import pytest
import proto.weather_pb2 as weather_pb2
from weather_service.service import WeatherService
from weather_service.errors import UpstreamNotFoundError
from tests.helpers import FakeRepo, FakeProvider, DummyContext


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
