"""Application settings and environment configuration for Weather gRPC app.

Loads essential service credentials and connection strings from `.env` using
Pydantic's settings management. Fields mirror the provided `.env` file.

Available settings:
	- OPENWEATHER_API_KEY: API key for OpenWeather requests
	- GRPC_API_KEY: Shared secret for gRPC client/server auth (x-api-key metadata)
	- MONGO_URI: MongoDB connection string

Example:
	from core.settings import settings
	if not settings.OPENWEATHER_API_KEY:
		raise RuntimeError("OPENWEATHER_API_KEY missing")
	repo_uri = settings.MONGO_URI
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "settings"]


class Settings(BaseSettings):
    """Strongly typed environment-backed settings for the Weather gRPC app.

    Required (must be supplied via environment / .env):
      - OPENWEATHER_API_KEY
      - GRPC_API_KEY
      - MONGO_URI

    Optional (sensible defaults provided here; override in .env if needed):
      - MONGO_APP_DB
      - GRPC_PORT
      - GRPC_ADDRESS
      - OPENWEATHER_URL
    """

    # Required secrets / connection strings (no code defaults)
    OPENWEATHER_API_KEY: str
    GRPC_API_KEY: str
    MONGO_URI: str

    MONGO_APP_DB: str
    GRPC_PORT: int
    GRPC_ADDRESS: str
    OPENWEATHER_URL: str

    APP_ENV: str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    def require_openweather_key(self) -> str:
        """Return the OpenWeather API key or raise a clear error."""
        if not self.OPENWEATHER_API_KEY:
            raise RuntimeError("OPENWEATHER_API_KEY is not set in environment")
        return self.OPENWEATHER_API_KEY

    def require_grpc_key(self) -> str:
        """Return the gRPC shared API key or raise."""
        if not self.GRPC_API_KEY:
            raise RuntimeError("GRPC_API_KEY is not set in environment")
        return self.GRPC_API_KEY

    def require_mongo_uri(self) -> str:
        """Return Mongo connection URI or raise."""
        if not self.MONGO_URI:
            raise RuntimeError("MONGO_URI is not set in environment")
        return self.MONGO_URI


settings = Settings()

