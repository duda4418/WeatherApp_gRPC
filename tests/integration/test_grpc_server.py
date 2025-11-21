import grpc
from concurrent import futures
import proto.weather_pb2 as weather_pb2
import proto.weather_pb2_grpc as weather_pb2_grpc
from weather_service.service import WeatherService
from weather_service.interceptors import ApiKeyInterceptor
from tests.factories import raw_openweather_payload


class FakeRepo:
    def __init__(self):
        self.inserted = []
    def insert_observation(self, doc):
        self.inserted.append(doc)
        return "id"


class FakeProvider:
    def get_current(self, city):
        return raw_openweather_payload(city=city)


def test_grpc_round_trip():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2), interceptors=[ApiKeyInterceptor(expected_key="test-grpc")])
    weather_pb2_grpc.add_WeatherServiceServicer_to_server(WeatherService(FakeRepo(), FakeProvider()), server)
    port = server.add_insecure_port("[::]:0")
    server.start()
    try:
        channel = grpc.insecure_channel(f"localhost:{port}")
        stub = weather_pb2_grpc.WeatherServiceStub(channel)
        md = ("x-api-key", "test-grpc")
        resp = stub.GetCurrentWeather(weather_pb2.GetWeatherRequest(city="Berlin"), metadata=[md])
        assert resp.city == "Berlin"
        assert resp.temp_c is not None
    finally:
        server.stop(0)
