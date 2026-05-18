# Propagator

This page documents the curated ASTROX Python propagator interface for Classical Keplerian orbits, J2 and two-body propagation, and ballistic trajectories. The intended import style is:

```python
from astrox import orbits, propagator
```

The curated functions documented here use SDK-owned dataclasses and ordinary scalar keyword arguments. They are not generated Pydantic model constructors, and they do not ask users to hand-build ASTROX request dictionaries for ordinary use. Raw access remains available through `astrox.raw` for advanced callers who need lower-level API control.

These functions are documented for the SDK behaviors covered by the current test and fixture suite. They describe the Python interface, units, return values, and caveats; they are not a claim that ASTROX propagation results are numerically validated for mission use.

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

`orbits.keplerian(...)` returns a frozen `orbits.KeplerianElements` dataclass. The six public fields are `semi_major_axis_m`, `eccentricity`, `inclination_deg`, `argument_of_periapsis_deg`, `raan_deg`, and `true_anomaly_deg`. The orbit epoch is intentionally separate because propagation calls receive `orbit_epoch` separately from the orbital element values.

Use `orbit.to_wire()` only when you need to inspect the ASTROX request fragment. It lowers the object to the Classical element order used by ASTROX: semi-major axis in meters, eccentricity, inclination in degrees, argument of periapsis in degrees, RAAN in degrees, and true anomaly in degrees.

## J2 And Two-Body

`propagator.j2(...)` and `propagator.two_body(...)` accept a `KeplerianElements` object and return `(period_s, position)`.

Required arguments for both functions are `start`, `stop`, `orbit_epoch`, and `orbit`. `start`, `stop`, and `orbit_epoch` are passed to ASTROX as time strings. The `orbit` argument must be a `KeplerianElements` instance; raw lists and raw dictionaries are intentionally not part of this curated call style.

Optional arguments shared by both functions are `step_s`, `central_body`, `gravitational_parameter_m3_s2`, and `coord_system`. `propagator.j2(...)` also accepts `j2_normalized_value` and `ref_distance_m`. Optional arguments are omitted from the request unless supplied, so the server keeps ownership of its defaults.

The SDK derives the Classical coordinate type from the orbit object and sends the ordered orbital elements from `orbit.to_wire()`.

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

See `examples/01_propagation/j2_classical.py`, `examples/01_propagation/two_body_classical.py`, and `examples/01_propagation/propagator_reference.py` for runnable source examples.

## Ballistic Branches

Ballistic propagation has one nominal curated function and four value-specific functions. The value-specific functions are separate because each one gives a different meaning and unit to its extra argument.

| Function | Extra required value |
| --- | --- |
| `propagator.ballistic(...)` | none |
| `propagator.ballistic_delta_v(...)` | `delta_v_m_s` |
| `propagator.ballistic_delta_v_min_ecc(...)` | `delta_v_m_s` |
| `propagator.ballistic_apogee_altitude(...)` | `apogee_altitude_m` |
| `propagator.ballistic_time_of_flight(...)` | `time_of_flight_s` |

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

See `examples/01_propagation/ballistic_delta_v.py`, `examples/01_propagation/ballistic_min_ecc.py`, `examples/01_propagation/ballistic_apogee_alt.py`, `examples/01_propagation/ballistic_time_of_flight.py`, and `examples/01_propagation/propagator_reference.py` for runnable source examples.

## Return Value

The curated propagator functions return a success-path tuple:

```python
period_s, position = propagator.two_body(...)
```

`period_s` is the server `Period` value. `position` is a frozen `propagator.PropagatorPosition` dataclass with `central_body`, `epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`, and `cartesian_velocity`.

When ASTROX reports an unsuccessful response, the curated function raises `ValueError` with the server message. When you need the full raw response envelope, use the lower-level `astrox.raw` API.
