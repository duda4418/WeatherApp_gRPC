"""Server bootstrap wiring for Weather gRPC service only."""

from __future__ import annotations

import logging
import time
from concurrent import futures

import grpc

from core.settings import settings
from db.mongo_repository import MongoRepository
import proto.weather_pb2_grpc as weather_pb2_grpc
from weather_service.interceptors import ApiKeyInterceptor
from weather_service.service import WeatherService
from weather_service.providers.openweather_client import OpenWeatherClient

logger = logging.getLogger("weather_service.server")


def serve(*, port: int | None = None, repo=None, provider=None) -> None:  # noqa: D401
    """Start the gRPC server with injected dependencies (optional overrides)."""
    settings.configure_logging()  # ensure logging configured once
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[ApiKeyInterceptor()],
    )
    repo = repo or MongoRepository(settings.MONGO_URI)
    provider = provider or OpenWeatherClient()
    weather_pb2_grpc.add_WeatherServiceServicer_to_server(WeatherService(repo, provider), server)
    run_port = port or settings.GRPC_PORT
    server.add_insecure_port(f"[::]:{run_port}")
    server.start()
    logger.info("gRPC WeatherService running on port %s", run_port)
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":  # pragma: no cover
    serve()
