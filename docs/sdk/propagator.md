# Propagator

This page documents the curated ASTROX Python propagator interface for Classical Keplerian orbits, J2 and two-body propagation, batch propagation, SGP4 propagation from TLE data, simple ascent propagation, and ballistic trajectories. The intended import style is:

```python
from astrox import orbits, propagator
```

The curated functions documented here use SDK-owned dataclasses and ordinary scalar keyword arguments. They are not generated transport-model constructors, and they do not ask users to hand-build ASTROX request dictionaries for ordinary use. Raw access remains available through `astrox.raw` for advanced callers who need lower-level API control.

These functions describe the Python interface, units, and return values.

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

## Batch J2 And Two-Body

`propagator.multi_j2(...)` and `propagator.multi_two_body(...)` propagate multiple Classical Keplerian states to one target epoch and return `tuple[orbits.KeplerianElements, ...]`.

Required arguments are `epoch` and `states`. `epoch` is the target epoch to which all inputs are propagated. `states` is a sequence of two-item sequences: `(orbit_epoch, orbit)`, where `orbit_epoch` is a time string and `orbit` is an `orbits.KeplerianElements` instance. Empty `states` is valid and returns an empty tuple when ASTROX returns an empty batch result.

Both functions accept optional shared `gravitational_parameter_m3_s2`; when supplied, the SDK writes the same value into every input state. `propagator.multi_j2(...)` does not expose `j2_normalized_value` or `ref_distance_m`; the batch ASTROX route owns those J2 constants.

```python
states = [
    ("2024-01-01T00:00:00.000Z", orbit_a),
    ("2024-01-01T00:03:00.000Z", orbit_b),
]

elements = propagator.multi_two_body(
    epoch="2024-01-01T00:10:00.000Z",
    states=states,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

ASTROX raw batch responses include `GravitationalParameter` on each returned element. The curated SDK returns `orbits.KeplerianElements` and omits that field because live behavior shows it is not a reliable echo of the propagation parameter used for the result. Use `astrox.raw` when you need the full raw envelope.

See `examples/01_propagation/batch_propagators.py` for a runnable source example.

## SGP4

`propagator.sgp4(...)` propagates a satellite from two-line element data and returns `(period_s, position)`.

Required arguments are `start`, `stop`, and `tle_lines`. `tle_lines` is a two-item sequence containing TLE line 1 and TLE line 2. Optional arguments are `step_s` and `satellite_number`; both are omitted unless supplied, so the server keeps ownership of its defaults.

```python
period_s, position = propagator.sgp4(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    step_s=300.0,
    satellite_number="25544",
    tle_lines=(
        "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
        "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
    ),
)
```

See `examples/01_propagation/sgp4_tle.py` and `examples/01_propagation/propagator_reference.py` for runnable source examples.

When comparing SGP4 results with another tool, match the TLE, epoch, time scale, reference frame, and units. ASTROX reports this SGP4 output as `INERTIAL`; for the checked ISS TLE sample, that frame matches Skyfield's GCRS/GCRF-style state, not raw TEME output from a low-level SGP4 propagator. If another tool starts from TEME, transform the state to GCRF/GCRS before comparing coordinates.

## Batch SGP4

`propagator.multi_sgp4(...)` propagates multiple TLE sets to one target epoch and returns `tuple[orbits.KeplerianElements, ...]`.

Required arguments are `epoch` and `tle_sets`. `epoch` is the target epoch to which all TLEs are propagated. `tle_sets` is a sequence of two-line TLE sequences, each containing line 1 and line 2. The SDK lowers each public TLE pair to ASTROX's newline-joined batch format. Empty `tle_sets` is valid and returns an empty tuple when ASTROX returns an empty batch result.

```python
elements = propagator.multi_sgp4(
    epoch="2024-01-01T00:10:00.000Z",
    tle_sets=[
        (
            "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
            "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
        ),
    ],
)
```

Satellite identity is supplied by the TLE lines. The batch ASTROX route does not expose a validated satellite-number selector through the curated SDK.

See `examples/01_propagation/batch_propagators.py` for a runnable source example.

## Simple Ascent

`propagator.simple_ascent(...)` propagates a simple ascent curve from a launch point to a burnout point and returns `(period_s, position)`.

Required arguments are `start`, `stop`, `launch_latitude_deg`, `launch_longitude_deg`, `launch_altitude_m`, `burnout_velocity_m_s`, `burnout_latitude_deg`, `burnout_longitude_deg`, and `burnout_altitude_m`. Optional arguments are `step_s` and `central_body`; both are omitted unless supplied.

```python
period_s, position = propagator.simple_ascent(
    start="2024-01-01T03:00:00.000Z",
    stop="2024-01-01T03:02:00.000Z",
    step_s=30.0,
    central_body="Earth",
    launch_latitude_deg=40.9575,
    launch_longitude_deg=100.2912,
    launch_altitude_m=1000.0,
    burnout_velocity_m_s=7800.0,
    burnout_latitude_deg=41.3,
    burnout_longitude_deg=101.0,
    burnout_altitude_m=200000.0,
)
```

See `examples/01_propagation/simple_ascent.py` and `examples/01_propagation/propagator_reference.py` for runnable source examples.

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

The single-result curated propagator functions return a success-path tuple:

```python
period_s, position = propagator.two_body(...)
```

`period_s` is the server `Period` value. `position` is a frozen `propagator.PropagatorPosition` dataclass with `central_body`, `epoch`, `reference_frame`, `interpolation_algorithm`, `interpolation_degree`, and `cartesian_velocity`.

For SGP4 results, `position.reference_frame == "INERTIAL"` should be interpreted as GCRF/GCRS-style inertial coordinates for external comparisons.

The batch propagator functions return immutable tuples of `orbits.KeplerianElements`:

```python
elements = propagator.multi_two_body(...)
```

When ASTROX reports an unsuccessful response, the curated function raises `astrox.exceptions.AstroxAPIError` with the server message. When you need the full raw response envelope, use the lower-level `astrox.raw` API.
