"""Weather service package encapsulating gRPC logic, providers, models.

Modules:
    server: gRPC server bootstrap only.
    service: WeatherService business logic implementation.
    interceptors: gRPC interceptors (API key auth).
    models: Pydantic domain models.
    providers: Upstream provider clients (OpenWeather).
    errors: Typed exceptions for mapping to gRPC status codes.
"""

from .service import WeatherService  # re-export for convenience
from .server import serve  # convenience entrypoint

__all__ = ["WeatherService", "serve"]
