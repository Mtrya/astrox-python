"""Python interface for the ASTROX Web API.

Functions are organized by domain modules and can use package-level
configuration without requiring explicit client management:

    from astrox import orbits, propagator

    astrox.configure(base_url="http://custom:8765", timeout=120)
    orbit = orbits.keplerian(...)
    period_s, position = propagator.j2(
        start="2026-01-01T00:00:00Z",
        stop="2026-01-01T01:00:00Z",
        orbit_epoch="2026-01-01T00:00:00Z",
        orbit=orbit,
    )

For advanced configuration, instantiate Client directly:

    client = astrox.Client(timeout=60)

Raw route access is available for advanced callers:

    result = astrox.raw.post("/Propagator/J2", json={...})
"""

from astrox import orbits, propagator
from astrox._http import Client, configure, get_session, raw

__version__ = "0.1.0"

__all__ = [
    "Client",
    "configure",
    "get_session",
    "orbits",
    "propagator",
    "raw",
]
