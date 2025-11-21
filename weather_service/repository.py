"""Repository protocol to enable mocking in WeatherService tests."""

from __future__ import annotations
from typing import Protocol, Dict, Any


class WeatherRepository(Protocol):  # pragma: no cover - structural typing only
    def insert_observation(self, doc: Dict[str, Any]) -> str:  # noqa: D401
        """Persist an observation document."""
        ...
