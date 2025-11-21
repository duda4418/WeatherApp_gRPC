import types
import pytest
import weather_service.providers.openweather_client as ow


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, raise_json=False):
        self.status_code = status_code
        self._json = json_data or {}
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("bad json")
        return self._json


def test_openweather_success(monkeypatch):
    payload = {"main": {}, "name": "Berlin"}
    def fake_get(url, params, timeout):
        return DummyResponse(200, payload)
    monkeypatch.setattr("weather_service.providers.openweather_client.requests.get", fake_get)
    client = ow.OpenWeatherClient(api_key="k", base_url="http://x")
    out = client.get_current("Berlin")
    assert out["name"] == "Berlin"
    assert "_fetched_at" in out


@pytest.mark.parametrize("status,exc_type", [
    (404, ow.UpstreamNotFoundError),
    (500, ow.UpstreamHttpError),
])
def test_openweather_http_errors(monkeypatch, status, exc_type):
    def fake_get(url, params, timeout):
        return DummyResponse(status, {"main": {}})
    monkeypatch.setattr("weather_service.providers.openweather_client.requests.get", fake_get)
    client = ow.OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(exc_type):
        client.get_current("Berlin")


def test_openweather_invalid_json(monkeypatch):
    def fake_get(url, params, timeout):
        return DummyResponse(200, json_data={"bad": 1}, raise_json=True)
    monkeypatch.setattr("weather_service.providers.openweather_client.requests.get", fake_get)
    client = ow.OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(ow.UpstreamInvalidResponse):
        client.get_current("Berlin")


def test_openweather_missing_main(monkeypatch):
    def fake_get(url, params, timeout):
        return DummyResponse(200, json_data={"name": "Berlin"})
    monkeypatch.setattr("weather_service.providers.openweather_client.requests.get", fake_get)
    client = ow.OpenWeatherClient(api_key="k", base_url="http://x")
    with pytest.raises(ow.UpstreamInvalidResponse):
        client.get_current("Berlin")
