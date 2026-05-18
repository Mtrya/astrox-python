# Orbit Propagation Examples

This directory contains runnable propagation examples. The documented PR 02 reference slice is the curated public SDK style to follow for new examples:

```python
from astrox import orbits, propagator
```

The user-facing guide for this slice is [docs/sdk/propagator.md](../../docs/sdk/propagator.md). It documents the evidence level, arguments, units, return values, and caveats for `orbits.keplerian(...)`, `propagator.j2(...)`, `propagator.two_body(...)`, and the curated ballistic functions.

## PR 02 Reference Slice

| Example | Public API shown |
| --- | --- |
| `pr02_reference_slice.py` | One compact pass through `orbits.keplerian(...)`, `propagator.j2(...)`, `propagator.two_body(...)`, and `propagator.ballistic_delta_v(...)` |
| `j2_classical.py` | J2 propagation from Classical Keplerian elements |
| `two_body_classical.py` | Two-body propagation from Classical Keplerian elements |
| `ballistic_delta_v.py` | Ballistic `DeltaV` branch |
| `ballistic_min_ecc.py` | Ballistic `DeltaV_MinEcc` branch |
| `ballistic_apogee_alt.py` | Ballistic `ApogeeAlt` branch |
| `ballistic_time_of_flight.py` | Ballistic `TimeOfFlight` branch |

Run an example from this directory:

```bash
python pr02_reference_slice.py
python j2_classical.py
python two_body_classical.py
python ballistic_delta_v.py
```

These examples call the ASTROX API through the package default client configuration. They are validated in this repository for syntax/import style and are backed by fixture-shaped unit tests; running them end to end still requires access to a compatible ASTROX server.

## PR 02 Output Shape

The curated PR 02 propagator functions return `(period_s, position)`. `period_s` is the server `Period` value. `position` is a `propagator.PropagatorPosition` dataclass with `central_body`, `epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`, and `cartesian_velocity`.

## Legacy Examples

Some older examples in this directory still cover SDK surfaces outside the PR 02 reference slice, such as SGP4, HPOP, simple ascent, and batch propagation. Those examples are not the pattern for new curated SDK work until their endpoint families are migrated and documented.
