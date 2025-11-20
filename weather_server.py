import time
import logging
from concurrent import futures
from datetime import datetime, UTC
from typing import Optional

import grpc
import requests

import proto.weather_pb2 as weather_pb2
import proto.weather_pb2_grpc as weather_pb2_grpc
from db.mongo_repository import MongoRepository
from pydantic import BaseModel, Field

from core.settings import settings

logger = logging.getLogger("weather_server")
logging.basicConfig(level=settings.resolved_log_level(), format="%(asctime)s %(levelname)s %(name)s - %(message)s")

OPENWEATHER_KEY = settings.OPENWEATHER_API_KEY
GRPC_API_KEY = settings.GRPC_API_KEY
MONGO_URI = settings.MONGO_URI

class WeatherNormalized(BaseModel):
    city: str
    temp_c: float
    humidity_pct: Optional[int] = Field(default=None)
    conditions: Optional[str] = Field(default=None)
    wind_speed_ms: Optional[float] = Field(default=None)
    fetched_at: datetime

class ApiKeyInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        meta = dict(handler_call_details.invocation_metadata)
        if meta.get('x-api-key') != GRPC_API_KEY:
            def unary_unauthed(request, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid API key')
            return grpc.unary_unary_rpc_method_handler(unary_unauthed)
        return continuation(handler_call_details)

class WeatherService(weather_pb2_grpc.WeatherServiceServicer):
    """Implements only the current weather RPC per requirements.

    Responsibilities:
    - Validate input city
    - Fetch upstream data (OpenWeatherMap)
    - Normalize & persist
    - Return required fields (city, temp, humidity, conditions, wind speed, timestamp)
    """
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    def GetCurrentWeather(self, request, context):  # noqa: N802 (proto requires this name)
        city = request.city.strip()
        if not city:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, 'City required')
        if not OPENWEATHER_KEY:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, 'OPENWEATHER_API_KEY not set')
        params = {'q': city, 'appid': OPENWEATHER_KEY, 'units': 'metric'}
        try:
            resp = requests.get(settings.OPENWEATHER_URL, params=params, timeout=8)
        except requests.RequestException as e:
            context.abort(grpc.StatusCode.UNAVAILABLE, f'HTTP error: {e}')
        if resp.status_code == 404:
            context.abort(grpc.StatusCode.NOT_FOUND, 'City not found')
        if resp.status_code != 200:
            context.abort(grpc.StatusCode.INTERNAL, f'Upstream error {resp.status_code}')
        try:
            data = resp.json()
        except ValueError:
            context.abort(grpc.StatusCode.INTERNAL, 'Invalid JSON from upstream')
        normalized = WeatherNormalized(
            city=data.get('name', city),
            temp_c=data.get('main', {}).get('temp'),
            humidity_pct=data.get('main', {}).get('humidity'),
            conditions=(data.get('weather') or [{}])[0].get('description'),
            wind_speed_ms=(data.get('wind') or {}).get('speed'),
            fetched_at=datetime.now(UTC)
        )
        # Persist minimal required observation with graceful failure handling
        try:
            self.repo.insert_observation({
                'city': normalized.city,
                'provider': 'openweathermap',
                'observation_time': normalized.fetched_at,
                'fetched_at': normalized.fetched_at,
                'temp_c': normalized.temp_c,
                'humidity_pct': normalized.humidity_pct,
                'wind_speed_ms': normalized.wind_speed_ms,
                'conditions': normalized.conditions,
                'raw': data
            })
        except Exception as persist_err:
            logger.warning("Failed to persist observation: %s", persist_err, exc_info=True)
            pass
        return weather_pb2.GetWeatherResponse(
            city=normalized.city,
            temp_c=normalized.temp_c or 0.0,
            humidity_pct=normalized.humidity_pct or 0,
            conditions=normalized.conditions or '',
            wind_speed_ms=normalized.wind_speed_ms or 0.0,
            fetched_at_iso=normalized.fetched_at.isoformat()
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), interceptors=[ApiKeyInterceptor()])
    weather_pb2_grpc.add_WeatherServiceServicer_to_server(WeatherService(MongoRepository(MONGO_URI)), server)
    port = str(settings.GRPC_PORT)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info('gRPC WeatherService running on port %s', port)
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
 