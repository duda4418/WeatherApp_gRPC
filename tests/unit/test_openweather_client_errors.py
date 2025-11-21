
import pytest
import requests
from weather_service.providers.openweather_client import OpenWeatherClient
from weather_service.errors import (
    UpstreamNotFoundError,
    UpstreamHttpError,
    UpstreamInvalidResponse,
    UpstreamRequestError,
)
from tests.helpers import DummyResp


def test_404_raises_not_found(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResp(status_code=404)
    monkeypatch.setattr(requests, "get", fake_get)
    client = OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(UpstreamNotFoundError):
        client.get_current("Berlin")


def test_500_raises_http_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResp(status_code=500)
    monkeypatch.setattr(requests, "get", fake_get)
    client = OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(UpstreamHttpError):
        client.get_current("Berlin")


def test_connection_error_maps_to_request_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        raise requests.RequestException("boom")
    monkeypatch.setattr(requests, "get", fake_get)
    client = OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(UpstreamRequestError):
        client.get_current("Berlin")


def test_invalid_json_raises_invalid_response(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResp(status_code=200, json_error=True)
    monkeypatch.setattr(requests, "get", fake_get)
    client = OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(UpstreamInvalidResponse):
        client.get_current("Berlin")


def test_missing_main_section_raises_invalid_response(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return DummyResp(status_code=200, json_data={"weather": [{}]})
    monkeypatch.setattr(requests, "get", fake_get)
    client = OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(UpstreamInvalidResponse):
        client.get_current("Berlin")
