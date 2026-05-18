"""Python interface for the ASTROX Web API.

Functions are organized by domain modules and can use package-level
configuration without requiring explicit client management:

    from astrox.coverage import compute_coverage
    from astrox.propagator import propagate_j2

    astrox.configure(base_url="http://custom:8765", timeout=120)
    result = propagate_j2(...)

For advanced configuration, instantiate Client directly:

    client = astrox.Client(timeout=60)
    result = compute_coverage(..., session=client)

Raw route access is available for advanced callers:

    result = astrox.raw.post("/Propagator/J2", json={...})
"""

from astrox import orbits
from astrox._http import Client, configure, get_session, raw

__version__ = "0.1.0"

__all__ = [
    "Client",
    "configure",
    "get_session",
    "orbits",
    "raw",
]
