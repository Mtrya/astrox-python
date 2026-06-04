# Orbit Propagation Examples

This directory contains runnable propagation examples. The curated propagator examples use this public SDK style:

```python
from astrox import orbits, propagator
```

The user-facing guide is [docs/sdk/propagator.md](../../docs/sdk/propagator.md). It documents arguments, units, return values, and caveats for `orbits.keplerian(...)`, `propagator.j2(...)`, `propagator.two_body(...)`, `propagator.multi_j2(...)`, `propagator.multi_two_body(...)`, `propagator.sgp4(...)`, `propagator.multi_sgp4(...)`, `propagator.simple_ascent(...)`, and the curated ballistic functions.

## Curated Propagator Examples

| Example | Public API shown |
| --- | --- |
| `propagator_reference.py` | One compact pass through `orbits.keplerian(...)`, `propagator.j2(...)`, `propagator.two_body(...)`, `propagator.ballistic_delta_v(...)`, `propagator.sgp4(...)`, and `propagator.simple_ascent(...)` |
| `j2_classical.py` | J2 propagation from Classical Keplerian elements |
| `two_body_classical.py` | Two-body propagation from Classical Keplerian elements |
| `batch_propagators.py` | Batch J2, two-body, and SGP4 propagation to one target epoch |
| `sgp4_tle.py` | SGP4 propagation from two-line element data |
| `simple_ascent.py` | Simple ascent propagation from launch point to burnout point |
| `ballistic_delta_v.py` | Ballistic `DeltaV` branch |
| `ballistic_min_ecc.py` | Ballistic `DeltaV_MinEcc` branch |
| `ballistic_apogee_alt.py` | Ballistic `ApogeeAlt` branch |
| `ballistic_time_of_flight.py` | Ballistic `TimeOfFlight` branch |

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/01_propagation/propagator_reference.py
uv run python examples/01_propagation/j2_classical.py
uv run python examples/01_propagation/two_body_classical.py
uv run python examples/01_propagation/batch_propagators.py
uv run python examples/01_propagation/sgp4_tle.py
uv run python examples/01_propagation/simple_ascent.py
uv run python examples/01_propagation/ballistic_delta_v.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.

## Output Shape

The single-result curated propagator functions return `(period_s, position)`. `period_s` is the server period value. `position` is a `propagator.PropagatorPosition` dataclass with `central_body`, `epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`, and `cartesian_velocity`. Batch propagator functions return `tuple[orbits.KeplerianElements, ...]`.

For SGP4 examples, ASTROX reports `position.reference_frame` as `INERTIAL`. Compare those coordinates as GCRF/GCRS-style inertial states, not raw TEME states from low-level SGP4 libraries.
