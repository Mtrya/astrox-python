# astrox-python

Python SDK for the ASTROX Web API.

## Installation

```bash
pip install astrox-python
```

Requires Python 3.10 or later.

## Quickstart

Propagate a simple Keplerian orbit with J2 perturbations:

```python
from astrox import orbits, propagator

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)

period_s, position = propagator.j2(
    start="2026-01-01T00:00:00Z",
    stop="2026-01-01T01:00:00Z",
    orbit_epoch="2026-01-01T00:00:00Z",
    orbit=orbit,
)
```

## Documentation

- SDK guides and API notes: [`docs/sdk/`](./docs/sdk/)
- Runnable examples: [`examples/`](./examples/)

## Development

Install from a checkout:

```bash
uv sync --group dev
uv build --no-build-isolation
uv run python -m pytest -q tests/sdk
```

## License

MIT — see [LICENSE](./LICENSE).
