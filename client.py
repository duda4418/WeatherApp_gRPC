import argparse
from typing import Optional
import grpc
import proto.weather_pb2 as weather_pb2
import proto.weather_pb2_grpc as weather_pb2_grpc

from core.settings import settings

API_KEY = settings.GRPC_API_KEY or 'changeme'
DEFAULT_ADDRESS = settings.GRPC_ADDRESS


def get_current(stub, city: str):
    metadata = [('x-api-key', API_KEY)]
    resp = stub.GetCurrentWeather(weather_pb2.GetWeatherRequest(city=city), metadata=metadata)
    print(f"Weather for {resp.city}:\n  Temp: {resp.temp_c:.1f} °C\n  Humidity: {resp.humidity_pct}%\n  Conditions: {resp.conditions}\n  Wind: {resp.wind_speed_ms:.1f} m/s\n  Fetched: {resp.fetched_at_iso}")


def get_series(stub, city: str, start: str, end: str, bucket: int):
    metadata = [('x-api-key', API_KEY)]
    resp = stub.GetTemperatureSeries(weather_pb2.GetSeriesRequest(city=city, start_iso=start, end_iso=end, bucket_minutes=bucket), metadata=metadata)
    print(f"Series for {resp.city} (bucket {bucket}m):")
    for p in resp.points:
        print(f"  {p.timestamp_iso}: {p.avg_temp_c:.2f} °C")


def prompt_city_if_missing(arg_city: Optional[str]) -> str:
    if arg_city:
        return arg_city
    # Interactive prompt per requirements
    while True:
        entered = input("Enter city name: ").strip()
        if entered:
            return entered
        print("City cannot be empty. Please try again.")


def main():
    parser = argparse.ArgumentParser(description='Weather gRPC client')
    parser.add_argument('city', nargs='?', help='City name (optional; will prompt if omitted)')
    parser.add_argument('--address', default=DEFAULT_ADDRESS, help='Server address host:port')
    args = parser.parse_args()

    city = prompt_city_if_missing(args.city)

    channel = grpc.insecure_channel(args.address)
    stub = weather_pb2_grpc.WeatherServiceStub(channel)

    try:
        get_current(stub, city)
    except grpc.RpcError as e:
        status = e.code()
        detail = e.details() or ''
        print(f"Error fetching weather (status={status.name}): {detail}")

if __name__ == '__main__':
    main()
