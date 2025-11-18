"""Simple ingestion loop to produce multiple observations for charting.
Calls the existing gRPC WeatherService at a fixed interval, persisting each result in Mongo via the server.

Usage (PowerShell):
  $env:GRPC_API_KEY="your_key"
  python ingest_weather.py --city London --interval 120 --address localhost:50051

Stop with Ctrl+C.
"""
import time
import argparse
import grpc
from datetime import datetime
import weather_pb2
import weather_pb2_grpc

from core.settings import settings

API_KEY = settings.GRPC_API_KEY or "changeme"
DEFAULT_ADDRESS = settings.GRPC_ADDRESS


def fetch_once(stub, city: str):
    meta = [("x-api-key", API_KEY)]
    try:
        resp = stub.GetCurrentWeather(weather_pb2.GetWeatherRequest(city=city), metadata=meta)
        print(f"[{datetime.utcnow().isoformat()}] Stored weather: {resp.city} {resp.temp_c:.1f}°C {resp.humidity_pct}% {resp.conditions}")
    except grpc.RpcError as e:
        print(f"[ERROR] gRPC {e.code().name}: {e.details()}")


def main():
    parser = argparse.ArgumentParser(description="Weather ingestion loop")
    parser.add_argument("--city", required=True, help="City to ingest")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between ingests (default 300)")
    parser.add_argument("--address", default=DEFAULT_ADDRESS, help="gRPC server host:port")
    args = parser.parse_args()

    channel = grpc.insecure_channel(args.address)
    stub = weather_pb2_grpc.WeatherServiceStub(channel)

    print(f"Starting ingestion for city '{args.city}' every {args.interval}s against {args.address} (Ctrl+C to stop)")
    try:
        while True:
            fetch_once(stub, args.city)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopping ingestion.")


if __name__ == "__main__":
    main()
