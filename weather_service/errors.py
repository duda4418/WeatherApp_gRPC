"""Typed exception classes enabling clean mapping to gRPC status codes."""

class UpstreamNotFoundError(Exception):
    """Raised when a city (or resource) is not found upstream (404)."""


class UpstreamHttpError(Exception):
    """Generic non-200/404 HTTP error from upstream service."""
    def __init__(self, status_code: int, message: str | None = None):
        super().__init__(message or f"Upstream HTTP error {status_code}")
        self.status_code = status_code


class UpstreamInvalidResponse(Exception):
    """Raised when upstream returns invalid JSON or structure."""


class UpstreamRequestError(Exception):
    """Raised when an underlying request/network error occurs."""
