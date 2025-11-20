"""Application settings and environment configuration for Weather gRPC app.

Loads essential service credentials and connection strings from `.env` using
Pydantic's settings management. Fields mirror the provided `.env` file.

Available settings:
    - OPENWEATHER_API_KEY: API key for OpenWeather requests
    - GRPC_API_KEY: Shared secret for gRPC client/server auth (x-api-key metadata)
    - MONGO_URI: MongoDB connection string
    - LOG_LEVEL: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Example:
    from core.settings import settings
    settings.configure_logging()  # sets root logging per LOG_LEVEL
    logger = logging.getLogger(__name__)
    logger.info("Started")
"""

from __future__ import annotations
import logging


from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

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
    LOG_LEVEL: str = "INFO"  # Override in .env (e.g., DEBUG, WARNING)
    
    @field_validator("LOG_LEVEL")
    def _validate_log_level(cls, v: str) -> str:  # noqa: D401
        """Ensure LOG_LEVEL is one of the standard logging level names."""
        if not v:
            return "INFO"
        name = v.upper()
        if name not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError(f"Invalid LOG_LEVEL '{v}'. Expected one of DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return name

    def resolved_log_level(self) -> int:
        """Return numeric logging level from LOG_LEVEL string with fallback to INFO."""
        return getattr(logging, self.LOG_LEVEL, logging.INFO)

    def configure_logging(self, *, force: bool = False) -> None:
        """Initialize basic logging configuration once for the application.

        Call early (e.g., at process entry) so modules obtaining loggers after
        import inherit the desired level and format.

        Parameters
        ----------
        force: bool
            If True, reconfigure even if handlers already exist (passes force to
            logging.basicConfig). Use cautiously; default False preserves existing handlers.
        """
        logging.basicConfig(
            level=self.resolved_log_level(),
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
            force=force,
        )


settings = Settings()

