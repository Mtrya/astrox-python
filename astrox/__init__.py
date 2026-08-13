"""Python interface for the ASTROX Web API.

Functions are organized by domain modules and can use package-level
configuration without requiring explicit client management:

    import astrox
    from astrox import access, celestial, catalog, components, coverage, libration, lighting, orbits, propagator, terrain

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

from importlib.metadata import PackageNotFoundError, version

from astrox import (
    access,
    astrogator,
    catalog,
    cat,
    celestial,
    conjunction,
    components,
    coverage,
    libration,
    lighting,
    orbits,
    propagator,
    rocket,
    terrain,
)
from astrox._http import Client, configure, get_session, raw

try:
    __version__ = version("astrox-python")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "Client",
    "configure",
    "get_session",
    "access",
    "astrogator",
    "catalog",
    "cat",
    "celestial",
    "conjunction",
    "coverage",
    "components",
    "libration",
    "lighting",
    "orbits",
    "propagator",
    "rocket",
    "terrain",
    "raw",
]
