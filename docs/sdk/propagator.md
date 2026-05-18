# Propagator SDK Reference Slice

This page documents the first curated ASTROX Python SDK slice. It covers the public orbit value object and the fixture-backed propagator functions added for PR 02. The intended import style is:

```python
from astrox import orbits, propagator
```

The curated functions documented here use SDK-owned dataclasses and ordinary scalar keyword arguments. They are not generated Pydantic model constructors, and they do not ask users to hand-build ASTROX wire dictionaries for ordinary use. Raw route access remains available through `astrox.raw` for advanced callers who need the transport envelope or an endpoint branch that has not yet been curated.

## Evidence Level

This slice is fixture-backed for wire shape. The checked fixtures cover `/Propagator/J2`, `/Propagator/TwoBody`, and `/Propagator/Ballistic` nominal behavior plus the verified ballistic branch modes `DeltaV`, `DeltaV_MinEcc`, `ApogeeAlt`, and `TimeOfFlight`. Unit tests prove the curated functions assemble those payload shapes and can construct the documented success-path return values from server-shaped responses.

This is not semantic or physics validation. The docs and examples do not claim that the returned trajectory is numerically correct for mission use; they only document the public SDK boundary and the verified request/response shape.

## Orbit Input

Create Classical Keplerian orbital elements with `orbits.keplerian(...)`:

```python
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)
```

`orbits.keplerian(...)` returns a frozen `orbits.KeplerianElements` dataclass. The six public fields are `semi_major_axis_m`, `eccentricity`, `inclination_deg`, `argument_of_periapsis_deg`, `raan_deg`, and `true_anomaly_deg`. The orbit epoch is intentionally separate because the ASTROX propagator endpoints receive `OrbitEpoch` separately from the `OrbitalElements` list.

Use `orbit.to_wire()` only when you need to inspect the ASTROX request fragment. It lowers the object to the exact Classical `OrbitalElements` order used by the wire API: semi-major axis in meters, eccentricity, inclination in degrees, argument of periapsis in degrees, RAAN in degrees, and true anomaly in degrees.

## J2 And Two-Body

`propagator.j2(...)` and `propagator.two_body(...)` accept a `KeplerianElements` object and return `(period_s, position)`.

Required arguments for both functions are `start`, `stop`, `orbit_epoch`, and `orbit`. `start`, `stop`, and `orbit_epoch` are passed to ASTROX as time strings. The `orbit` argument must be a `KeplerianElements` instance; raw lists and raw dictionaries are intentionally not part of this curated call style.

Optional arguments shared by both functions are `step_s`, `central_body`, `gravitational_parameter_m3_s2`, and `coord_system`. `propagator.j2(...)` also accepts `j2_normalized_value` and `ref_distance_m`. Optional arguments are omitted from the request unless supplied, so the server keeps ownership of its defaults.

The SDK adds `CoordType: "Classical"` from the orbit object and sends `OrbitalElements` from `orbit.to_wire()`.

```python
period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
    step_s=300.0,
    coord_system="Inertial",
    gravitational_parameter_m3_s2=398600441500000.0,
    j2_normalized_value=0.000484165143790815,
    ref_distance_m=6378137.0,
)
```

See `examples/01_propagation/j2_classical.py`, `examples/01_propagation/two_body_classical.py`, and `examples/01_propagation/pr02_reference_slice.py` for runnable source examples.

## Ballistic Branches

`/Propagator/Ballistic` has one nominal curated function and four branch-specific functions. The branch-specific functions are separate because the branch changes the meaning and unit of the value argument.

| Function | Extra required value | ASTROX branch |
| --- | --- | --- |
| `propagator.ballistic(...)` | none | nominal, no `BallisticType` |
| `propagator.ballistic_delta_v(...)` | `delta_v_m_s` | `DeltaV` |
| `propagator.ballistic_delta_v_min_ecc(...)` | `delta_v_m_s` | `DeltaV_MinEcc` |
| `propagator.ballistic_apogee_altitude(...)` | `apogee_altitude_m` | `ApogeeAlt` |
| `propagator.ballistic_time_of_flight(...)` | `time_of_flight_s` | `TimeOfFlight` |

All five functions require `start`, `impact_latitude_deg`, and `impact_longitude_deg`. Optional shared arguments are `stop`, `step_s`, `central_body`, `gravitational_parameter_m3_s2`, `launch_latitude_deg`, `launch_longitude_deg`, `launch_altitude_m`, and `impact_altitude_m`. Optional arguments are omitted unless supplied.

```python
period_s, position = propagator.ballistic_delta_v(
    start="2024-01-01T12:00:00.000Z",
    impact_latitude_deg=30.0,
    impact_longitude_deg=-70.0,
    launch_latitude_deg=28.5721,
    launch_longitude_deg=-80.648,
    launch_altitude_m=10.0,
    impact_altitude_m=0.0,
    delta_v_m_s=3000.0,
    step_s=30.0,
)
```

See `examples/01_propagation/ballistic_delta_v.py`, `examples/01_propagation/ballistic_min_ecc.py`, `examples/01_propagation/ballistic_apogee_alt.py`, `examples/01_propagation/ballistic_time_of_flight.py`, and `examples/01_propagation/pr02_reference_slice.py` for runnable source examples.

## Return Value

The curated PR 02 propagator functions return a success-path tuple:

```python
period_s, position = propagator.two_body(...)
```

`period_s` is the server `Period` value. `position` is a frozen `propagator.PropagatorPosition` dataclass with `central_body`, `epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`, and `cartesian_velocity`.

When ASTROX returns `IsSuccess` as false, the curated function raises `ValueError` with the server `Message`. When you need the full raw response envelope, call the raw route layer directly, for example `astrox.raw.post("/Propagator/J2", json=payload)`.
