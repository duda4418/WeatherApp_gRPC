import proto.weather_pb2 as weather_pb2

from weather_service.service import WeatherService


class FakeProvider:
    def get_current(self, city: str):  # minimal subset of expected structure
        return {
            "name": city,
            "main": {"temp": 12.34, "humidity": 55},
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 3.2},
        }


class FakeRepo:
    def __init__(self):
        self.inserted = []

    def insert_observation(self, doc):  # noqa: D401
        self.inserted.append(doc)
        return "fake_id"


def test_get_current_weather_happy_path():
    repo = FakeRepo()
    provider = FakeProvider()
    svc = WeatherService(repo, provider)
    request = weather_pb2.GetWeatherRequest(city="Berlin")

    # gRPC context is not easily mocked; call method directly with a dummy context
    class DummyContext:
        def abort(self, code, message):  # pragma: no cover - should not fire here
            raise AssertionError(f"Unexpected abort {code}: {message}")

    response = svc.GetCurrentWeather(request, DummyContext())
    assert response.city == "Berlin"
    assert response.temp_c == 12.34
    assert response.humidity_pct == 55
    assert response.conditions == "clear sky"
    assert response.wind_speed_ms == 3.2
    assert repo.inserted, "Expected persistence call"


def test_get_current_weather_strips_diacritics():
    repo = FakeRepo()
    provider = FakeProvider()
    svc = WeatherService(repo, provider)
    # City with Romanian diacritic ță
    request = weather_pb2.GetWeatherRequest(city="Constanța")

    class DummyContext:
        def abort(self, code, message):  # pragma: no cover - should not fire here
            raise AssertionError(f"Unexpected abort {code}: {message}")

    response = svc.GetCurrentWeather(request, DummyContext())
    assert response.city == "Constanta"
    assert repo.inserted[0]["city"] == "Constanta"
