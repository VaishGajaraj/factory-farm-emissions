"""Project configuration and constants (Python-first)

This file centralizes small configuration items to avoid hardcoding in scripts.
No heavy dependencies are used.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class BoundingBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    @property
    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.min_lon, self.min_lat, self.max_lon, self.max_lat)


# Chesapeake Bay watershed coverage (broad bbox incl. Delmarva)
CHESAPEAKE_BBOX = BoundingBox(
    min_lon=-77.8,
    min_lat=36.5,
    max_lon=-74.5,
    max_lat=40.3,
)

# Default analysis window (months)
DEFAULT_MONTH_WINDOW: int = 12

# Optional defaults for AWS (for later IMI runs)
AWS_DEFAULT_REGION: str = "us-east-1"
