
import pytest
import grpc
import proto.weather_pb2 as weather_pb2
from weather_service.service import WeatherService
from weather_service.errors import (
    UpstreamNotFoundError,
    UpstreamRequestError,
    UpstreamHttpError,
    UpstreamInvalidResponse,
)
from tests.helpers import DummyContext, RepoPersistFail, RepoOK, make_provider


@pytest.mark.parametrize("error, expected_code", [
    (UpstreamNotFoundError("x"), grpc.StatusCode.NOT_FOUND),
    (UpstreamRequestError("x"), grpc.StatusCode.UNAVAILABLE),
    (UpstreamHttpError(500, "x"), grpc.StatusCode.INTERNAL),
    (UpstreamInvalidResponse("x"), grpc.StatusCode.INTERNAL),
])
def test_error_mapping_aborts_with_correct_code(error, expected_code):
    svc = WeatherService(RepoOK(), make_provider(error=error))
    ctx = DummyContext()
    with pytest.raises(RuntimeError):
        svc.GetCurrentWeather(weather_pb2.GetWeatherRequest(city="Berlin"), ctx)
    assert ctx.aborted[0] == expected_code


def test_empty_city_aborts_invalid_argument():
    svc = WeatherService(RepoOK(), make_provider())
    ctx = DummyContext()
    with pytest.raises(RuntimeError):
        svc.GetCurrentWeather(weather_pb2.GetWeatherRequest(city="   "), ctx)
    assert ctx.aborted[0] == grpc.StatusCode.INVALID_ARGUMENT


def test_persistence_failure_logs_warning(caplog):
    svc = WeatherService(RepoPersistFail(), make_provider())
    ctx = DummyContext()
    resp = svc.GetCurrentWeather(weather_pb2.GetWeatherRequest(city="Paris"), ctx)
    assert resp.city == "Paris"
    assert any("Failed to persist observation" in r.message for r in caplog.records)


def test_diacritic_normalization():
    svc = WeatherService(RepoOK(), make_provider())
    ctx = DummyContext()
    resp = svc.GetCurrentWeather(weather_pb2.GetWeatherRequest(city="Constanța"), ctx)
    assert resp.city == "Constanta"
    assert svc.repo.inserted[0]["city"] == "Constanta"
