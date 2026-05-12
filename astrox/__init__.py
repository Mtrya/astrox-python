"""Python client for the ASTROX Web API.

This package provides a functional Python interface to the ASTROX aerospace
computation API. Functions are organized by domain (coverage, propagator, etc.)
and can be imported directly:

    from astrox.coverage import compute_coverage
    from astrox.propagator import propagate_j2
    from astrox.models import EntityPath, Cartesian

Configuration is optional - the library works out of the box:

    # Zero-config usage
    result = compute_coverage(start="...", stop="...", grid={...}, assets=[...])

    # Global configuration
    import astrox
    astrox.configure(base_url="http://custom:8765", timeout=120)

    # Explicit session (advanced)
    session = astrox.HTTPClient(timeout=60)
    result = compute_coverage(..., session=session)
"""

from astrox._http import HTTPClient, configure, get_session

__version__ = "0.1.0"

__all__ = [
    "HTTPClient",
    "configure",
    "get_session",
]
