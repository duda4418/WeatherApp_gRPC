"""Legacy entrypoint kept for backward compatibility.

Delegates to `weather_service.server.serve`. Prefer importing from
`weather_service.server` directly going forward.
"""

from weather_service.server import serve  # noqa: F401

if __name__ == "__main__":  # pragma: no cover
    serve()
 