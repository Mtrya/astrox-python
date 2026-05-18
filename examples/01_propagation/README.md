# Orbit Propagation Examples

This directory contains runnable propagation examples. The curated propagator examples use this public SDK style:

```python
from astrox import orbits, propagator
```

The user-facing guide is [docs/sdk/propagator.md](../../docs/sdk/propagator.md). It documents arguments, units, return values, and caveats for `orbits.keplerian(...)`, `propagator.j2(...)`, `propagator.two_body(...)`, and the curated ballistic functions.

## Curated Propagator Examples

| Example | Public API shown |
| --- | --- |
| `propagator_reference.py` | One compact pass through `orbits.keplerian(...)`, `propagator.j2(...)`, `propagator.two_body(...)`, and `propagator.ballistic_delta_v(...)` |
| `j2_classical.py` | J2 propagation from Classical Keplerian elements |
| `two_body_classical.py` | Two-body propagation from Classical Keplerian elements |
| `ballistic_delta_v.py` | Ballistic `DeltaV` branch |
| `ballistic_min_ecc.py` | Ballistic `DeltaV_MinEcc` branch |
| `ballistic_apogee_alt.py` | Ballistic `ApogeeAlt` branch |
| `ballistic_time_of_flight.py` | Ballistic `TimeOfFlight` branch |

Run an example from this directory:

```bash
python propagator_reference.py
python j2_classical.py
python two_body_classical.py
python ballistic_delta_v.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.

## Output Shape

The curated propagator functions return `(period_s, position)`. `period_s` is the server period value. `position` is a `propagator.PropagatorPosition` dataclass with `central_body`, `epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`, and `cartesian_velocity`.

## Legacy Examples

Some older examples in this directory still cover SDK surfaces outside this curated propagator interface, such as SGP4, HPOP, simple ascent, and batch propagation. Those examples are not the pattern for new curated SDK work until those areas are migrated and documented.
