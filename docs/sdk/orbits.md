# Orbits

This page documents the curated ASTROX Python orbit conversion and orbit wizard interface. The intended import style is:

```python
from astrox import orbits
```

The functions here use SDK-owned dataclasses and ordinary scalar keyword arguments. They are useful when you need to convert between Classical Keplerian and Cartesian orbit states, derive common orbit designs such as GEO, Molniya, SSO, or Walker constellations, or ask ASTROX for Lambert delta-v estimates.

## Orbit Inputs

Create Classical Keplerian orbital elements with `orbits.keplerian(...)`:

```python
orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=45.0,
)
```

`orbits.keplerian(...)` returns a frozen `orbits.KeplerianElements` dataclass with fields `semi_major_axis_m`, `eccentricity`, `inclination_deg`, `argument_of_periapsis_deg`, `raan_deg`, and `true_anomaly_deg`.

Create Cartesian position and velocity with `orbits.cartesian_state(...)`:

```python
state = orbits.cartesian_state(
    x_m=6114454.0,
    y_m=2870352.0,
    z_m=3308542.0,
    vx_m_s=-3548.0,
    vy_m_s=6463.0,
    vz_m_s=1830.0,
)
```

## Orbit Conversions

`orbits.keplerian_to_cartesian(...)` converts Classical Keplerian elements into a Cartesian state in meters and meters per second:

```python
state = orbits.keplerian_to_cartesian(
    orbit,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

`gravitational_parameter_m3_s2` is optional. When omitted, ASTROX owns the default.

`orbits.cartesian_to_keplerian(...)` converts Cartesian position and velocity into Classical Keplerian elements:

```python
elements = orbits.cartesian_to_keplerian(state)
```

ASTROX interprets `cartesian_to_keplerian(...)` with its default Earth gravitational parameter. Use `gravitational_parameter_m3_s2` only on `keplerian_to_cartesian(...)`; Cartesian states produced with a custom gravitational parameter are not reversible through `cartesian_to_keplerian(...)` with the same custom parameter.

`orbits.lla_at_ascending_node(...)` returns the ascending-node location as `(longitude_deg, latitude_deg, height_m)`:

```python
longitude_deg, latitude_deg, height_m = orbits.lla_at_ascending_node(
    orbit,
    orbit_epoch="2024-01-01T00:00:00.000Z",
)
```

`orbits.kozai_izsak_mean_elements(...)` converts osculating Classical elements into `orbits.MeanKeplerianElements`:

```python
mean_elements = orbits.kozai_izsak_mean_elements(orbit)
```

The returned dataclass fields are `semi_major_axis_m`, `eccentricity`, `inclination_deg`, `argument_of_perigee_deg`, `raan_deg`, `mean_anomaly_deg`, `argument_of_latitude_deg`, `longitude_of_perigee_deg`, and `mean_longitude_deg`.

## Orbit Wizards

The GEO, Molniya, and SSO helpers return `(elements_tod, elements_inertial)`, where both values are `orbits.KeplerianElements`:

```python
elements_tod, elements_inertial = orbits.geo(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    inclination_deg=10.0,
    subsatellite_longitude_deg=120.0,
)
```

TOD means true equator and true equinox of date. The inertial element set is ASTROX's inertial output for the same generated orbit.

Molniya:

```python
elements_tod, elements_inertial = orbits.molniya(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    perigee_altitude_km=600.0,
    apogee_longitude_deg=100.0,
    argument_of_periapsis_deg=270.0,
)
```

SSO:

```python
elements_tod, elements_inertial = orbits.sso(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    altitude_km=600.0,
    local_time_of_descending_node_hours=14.5,
)
```

Walker constellation helpers return nested tuples. The outer tuple is ordered by plane; each inner tuple contains the satellites in that plane.

```python
walker = orbits.walker_delta(
    seed_orbit=orbit,
    num_planes=3,
    num_sats_per_plane=2,
    inter_plane_phase_increment=1,
)

first_satellite = walker[0][0]
```

Use `orbits.walker_delta(...)` for Delta constellations, `orbits.walker_star(...)` for Star constellations, and `orbits.walker_custom(...)` when you want to supply explicit adjacent-plane true-anomaly and RAAN increments:

```python
custom_walker = orbits.walker_custom(
    seed_orbit=orbit,
    num_planes=3,
    num_sats_per_plane=2,
    inter_plane_true_anomaly_increment_deg=30.0,
    raan_increment_deg=60.0,
)
```

## Lambert Delta-V

`orbits.lambert_delta_v(...)` solves a single-revolution Lambert transfer between two Cartesian endpoint states:

```python
departure_delta_v_m_s, arrival_delta_v_m_s = orbits.lambert_delta_v(
    departure_state=departure_state,
    arrival_state=arrival_state,
    time_of_flight_s=817.4257,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

The return value is `(departure_delta_v_m_s, arrival_delta_v_m_s)`. Each delta-v is a three-item tuple `(x, y, z)` in meters per second. `gravitational_parameter_m3_s2` is optional; when omitted, ASTROX owns the default.

`orbits.geo_ym_lambert_delta_v(...)` estimates a Lambert transfer delta-v between a platform orbit and a target orbit over a supplied time of flight:

```python
departure_delta_v_m_s, arrival_delta_v_m_s = orbits.geo_ym_lambert_delta_v(
    platform_orbit=platform_orbit,
    target_orbit=target_orbit,
    time_of_flight_s=3600.0,
    platform_gravitational_parameter_m3_s2=398600441500000.0,
)
```

The GEO-YM helper accepts Keplerian input orbits instead of Cartesian endpoint states. ASTROX advances the target orbit's true anomaly linearly by mean motion times `time_of_flight_s` before solving the Lambert transfer, so its result is not the same as first propagating the target orbit through mean anomaly with Kepler's equation. `platform_gravitational_parameter_m3_s2` is optional; when omitted, ASTROX owns the platform orbit default.

## Frame And Libration Transforms

`orbits.convert_czml_position(...)` transforms a sampled CZML position from one central-body frame to another. The input must be an `entities.CzmlPosition` and the function returns `(period_s, transformed_position)`:

```python
from astrox import entities, orbits

position = entities.czml_position(
    epoch="2024-01-01T00:00:00Z",
    central_body="Earth",
    reference_frame="INERTIAL",
    interpolation_algorithm="LAGRANGE",
    interpolation_degree=7,
    cartesian=[0.0, 7000000.0, 0.0, 0.0, 142.857, 6900000.0, 1000000.0, 0.0],
)

period_s, fixed_position = orbits.convert_czml_position(
    position,
    to_central_body="Earth",
    target_reference_frame="FIXED",
)
```

`to_central_body` and `target_reference_frame` are required. The returned `fixed_position` is an `entities.CzmlPosition` whose `cartesian` samples are in the requested target frame.

Independent cross-validation has calibrated the following `orbits.convert_czml_position(...)` branches against external ephemeris tools. Static input samples at 7 000 km from Earth center are used for all cases.

- **Earth FIXED, INERTIAL, J2000, ICRF**: Earth FIXED matches ITRS (Earth body-fixed). Earth INERTIAL matches GCRS. Earth J2000 matches FK5 mean equator/equinox of J2000.0. Earth ICRF matches ICRS (GCRS-aligned to the precision of these tests). Residuals are at the metre level for the INERTIAL-origin branches and ~10 m for branches that traverse the Earth-orientation model.
- **Moon INERTIAL**: matches the Moon Mean Equator/Equinox J2000 (MMEJ2000) frame. The rotation is built from the IAU lunar pole at J2000 and the line of nodes with Earth's J2000 mean equator; translation is taken from JPL DE440. Residuals are ~50 m.
- **Moon FIXED**: matches the high-precision NAIF ``MOON_ME`` (mean Earth/polar axis, DE440) body-fixed frame. Residuals are ~300 m absolute and ~0.15 arcsec angular.
- **Mars INERTIAL**: matches the SPICE built-in MARSIAU Mars inertial frame, not common J2000/ICRS axes. Residuals are ~135 km absolute, ~0.09 arcsec angular. Predictions use the Mars barycenter because de440.bsp does not provide Mars body centre relative to Earth directly; the barycenter-to-centre offset is much smaller than the residuals.
- **Mars FIXED**: matches the IAU_MARS body-fixed frame orientation only. The absolute residual is ~15 000 km at planetary distance (consistent with using the Mars barycenter), so calibration uses angular separation (~10 arcsec).
- **Sun INERTIAL**: matches common J2000 inertial axes. Residuals are ~235 m.
- **Sun FIXED**: matches the IAU_SUN body-fixed frame. Residuals are ~498 m, ~0.001 arcsec angular.

No other `to_central_body` / `target_reference_frame` combinations have been independently calibrated.

`orbits.earth_moon_libration(...)` transforms a sampled CZML position to the Earth-Moon libration frame. It wires to ``/OrbitSystem/EarthMoonLibration2`` and returns an `entities.CzmlPositionSTM`:

```python
libration_state = orbits.earth_moon_libration(position)
```

Cross-validation shows that the returned `cartesian` samples are the input state expressed in a Moon-centered libration frame whose x-axis points Earth-to-Moon and whose z-axis is aligned with the Earth-Moon orbital angular momentum. Two fields remain unresolved:

- `unit_quaternion` does not match any standard quaternion convention (scalar-first/last, with/without conjugation, for either libration-to-inertial or inertial-to-libration) after a systematic probe. The best residual is ~24.56°. Treat this field as an unvalidated auxiliary orientation.
- `cartesian_translation` is not populated in live responses for the input matrix exercised by validation (varied sample counts, interpolation degrees, reference frames, central bodies, and velocity flags).

See `examples/02_orbits/` for runnable source examples.
