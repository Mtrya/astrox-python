# Orbits

`astrox.orbits` provides public APIs for orbit description, orbit conversion, orbit wizards, Lambert transfer, and reference frame conversion. It is recommended to import as follows:

```python
from astrox import orbits
```

This page is organized by concept, return-value conventions, function-family reference, and examples. All public parameters use `snake_case`; parameters with units use explicit suffixes such as `_m`, `_deg`, and `_s`. Optional parameters that are not provided are not sent to ASTROX, and the server retains their default values. If you need the complete raw ASTROX response dictionary, use `astrox.raw`.

> The examples on this page are runnable snippets that require a configured ASTROX service address: set the environment variable `ASTROX_BASE_URL`, or call `astrox.configure(base_url=...)` at the beginning of the script. Complete runnable scripts are in `examples/02_orbits/`.

## Orbit Value Objects

Orbit descriptions in `astrox.orbits` are carried by frozen dataclasses; constructors send only the fields explicitly provided by the caller.

### `orbits.KeplerianElements` / `orbits.keplerian(...)`

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

`orbits.keplerian(...)` returns an `orbits.KeplerianElements` frozen dataclass with the following fields:

| Field | Unit | Description |
| --- | --- | --- |
| `semi_major_axis_m` | m | Semi-major axis |
| `eccentricity` | — | Eccentricity |
| `inclination_deg` | deg | Inclination |
| `argument_of_periapsis_deg` | deg | Argument of periapsis |
| `raan_deg` | deg | Right ascension of the ascending node |
| `true_anomaly_deg` | deg | True anomaly |

### `orbits.CartesianState` / `orbits.cartesian_state(...)`

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

`orbits.cartesian_state(...)` returns an `orbits.CartesianState` frozen dataclass with the following fields:

| Field | Unit | Description |
| --- | --- | --- |
| `x_m` | m | X-axis position |
| `y_m` | m | Y-axis position |
| `z_m` | m | Z-axis position |
| `vx_m_s` | m/s | X-axis velocity |
| `vy_m_s` | m/s | Y-axis velocity |
| `vz_m_s` | m/s | Z-axis velocity |

### `orbits.MeanKeplerianElements`

`orbits.MeanKeplerianElements` is the frozen dataclass returned by `kozai_izsak_mean_elements(...)`, representing Kozai-Izsak mean elements, with the following fields:

| Field | Unit | Description |
| --- | --- | --- |
| `semi_major_axis_m` | m | Semi-major axis |
| `eccentricity` | — | Eccentricity |
| `inclination_deg` | deg | Inclination |
| `argument_of_perigee_deg` | deg | Argument of perigee |
| `raan_deg` | deg | Right ascension of the ascending node |
| `mean_anomaly_deg` | deg | Mean anomaly |
| `argument_of_latitude_deg` | deg | Argument of latitude |
| `longitude_of_perigee_deg` | deg | Longitude of perigee |
| `mean_longitude_deg` | deg | Mean longitude |

## Orbit Conversions

### `orbits.keplerian_to_cartesian`

```python
orbits.keplerian_to_cartesian(
    orbit: KeplerianElements,
    *,
    gravitational_parameter_m3_s2: float | None = None,
) -> CartesianState
```

Converts Keplerian elements to a Cartesian state. `gravitational_parameter_m3_s2` is an optional gravitational parameter; when not provided, ASTROX uses its default value.

| Parameter | Unit | Description |
| --- | --- | --- |
| `orbit` | — | `orbits.KeplerianElements` instance |
| `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter |

```python
state = orbits.keplerian_to_cartesian(
    orbit,
    gravitational_parameter_m3_s2=398600441500000.0,
)

print(state.x_m, state.y_m, state.z_m)
print(state.vx_m_s, state.vy_m_s, state.vz_m_s)
```

### `orbits.cartesian_to_keplerian`

```python
orbits.cartesian_to_keplerian(state: CartesianState) -> KeplerianElements
```

Converts a Cartesian state to Keplerian elements. ASTROX uses its default Earth gravitational parameter for the conversion.

| Parameter | Description |
| --- | --- |
| `state` | `orbits.CartesianState` instance |

```python
elements = orbits.cartesian_to_keplerian(state)
print(elements.semi_major_axis_m, elements.eccentricity)
```

### `orbits.lla_at_ascending_node`

```python
orbits.lla_at_ascending_node(
    orbit: KeplerianElements,
    *,
    orbit_epoch: str,
) -> tuple[float, float, float]
```

Returns the longitude, latitude, and altitude at the ascending node of the orbit at the given epoch, in the order `(longitude_deg, latitude_deg, height_m)`.

| Parameter | Description |
| --- | --- |
| `orbit` | `orbits.KeplerianElements` instance |
| `orbit_epoch` | Orbit epoch string |

```python
longitude_deg, latitude_deg, height_m = orbits.lla_at_ascending_node(
    orbit,
    orbit_epoch="2024-01-01T00:00:00.000Z",
)
```

### `orbits.kozai_izsak_mean_elements`

```python
orbits.kozai_izsak_mean_elements(orbit: KeplerianElements) -> MeanKeplerianElements
```

Converts instantaneous Keplerian elements to Kozai-Izsak mean elements.

| Parameter | Description |
| --- | --- |
| `orbit` | `orbits.KeplerianElements` instance |

```python
mean_elements = orbits.kozai_izsak_mean_elements(orbit)
print(mean_elements.semi_major_axis_m, mean_elements.mean_anomaly_deg)
```

## Orbit Wizards

Orbit wizards generate Keplerian elements from common design constraints. GEO, Molniya, and SSO return a tuple `(elements_tod, elements_inertial)`, where TOD is the true equator and true equinox result at the epoch, and inertial is the corresponding ASTROX inertial reference frame output.

### `orbits.geo`

```python
orbits.geo(
    *,
    orbit_epoch: str,
    inclination_deg: float,
    subsatellite_longitude_deg: float,
) -> tuple[KeplerianElements, KeplerianElements]
```

Generates geostationary orbit (GEO) elements.

| Parameter | Unit | Description |
| --- | --- | --- |
| `orbit_epoch` | — | Orbit epoch string |
| `inclination_deg` | deg | Inclination |
| `subsatellite_longitude_deg` | deg | Subsatellite longitude |

```python
elements_tod, elements_inertial = orbits.geo(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    inclination_deg=10.0,
    subsatellite_longitude_deg=120.0,
)
```

### `orbits.molniya`

```python
orbits.molniya(
    *,
    orbit_epoch: str,
    perigee_altitude_km: float,
    apogee_longitude_deg: float,
    argument_of_periapsis_deg: float,
) -> tuple[KeplerianElements, KeplerianElements]
```

Generates Molniya orbit elements.

| Parameter | Unit | Description |
| --- | --- | --- |
| `orbit_epoch` | — | Orbit epoch string |
| `perigee_altitude_km` | km | Perigee altitude |
| `apogee_longitude_deg` | deg | Apogee longitude |
| `argument_of_periapsis_deg` | deg | Argument of periapsis |

```python
elements_tod, elements_inertial = orbits.molniya(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    perigee_altitude_km=600.0,
    apogee_longitude_deg=100.0,
    argument_of_periapsis_deg=270.0,
)
```

### `orbits.sso`

```python
orbits.sso(
    *,
    orbit_epoch: str,
    altitude_km: float,
    local_time_of_descending_node_hours: float,
) -> tuple[KeplerianElements, KeplerianElements]
```

Generates sun-synchronous orbit (SSO) elements.

| Parameter | Unit | Description |
| --- | --- | --- |
| `orbit_epoch` | — | Orbit epoch string |
| `altitude_km` | km | Altitude |
| `local_time_of_descending_node_hours` | h | Local time of the descending node |

```python
elements_tod, elements_inertial = orbits.sso(
    orbit_epoch="2024-01-01T00:00:00.000Z",
    altitude_km=600.0,
    local_time_of_descending_node_hours=14.5,
)
```

### `orbits.walker_delta` / `orbits.walker_star` / `orbits.walker_custom`

```python
orbits.walker_delta(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]

orbits.walker_star(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_phase_increment: int | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]

orbits.walker_custom(
    *,
    seed_orbit: KeplerianElements,
    num_planes: int,
    num_sats_per_plane: int,
    inter_plane_true_anomaly_increment_deg: float | None = None,
    raan_increment_deg: float | None = None,
) -> tuple[tuple[KeplerianElements, ...], ...]
```

Generates Walker constellations. The outer tuple is indexed by orbital plane, and each inner tuple contains the satellite elements for that plane.

| Parameter | Description |
| --- | --- |
| `seed_orbit` | Seed orbit, an `orbits.KeplerianElements` instance |
| `num_planes` | Number of planes |
| `num_sats_per_plane` | Number of satellites per plane |
| `inter_plane_phase_increment` | Inter-plane phase increment (Delta/Star) |
| `inter_plane_true_anomaly_increment_deg` | True-anomaly increment between adjacent planes (Custom) |
| `raan_increment_deg` | RAAN increment between adjacent planes (Custom) |

```python
seed = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=53.0,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=0.0,
)

walker = orbits.walker_delta(
    seed_orbit=seed,
    num_planes=3,
    num_sats_per_plane=2,
    inter_plane_phase_increment=1,
)

first_plane_first_sat = walker[0][0]
```

## Lambert Transfer

### `orbits.lambert_delta_v`

```python
orbits.lambert_delta_v(
    *,
    departure_state: CartesianState,
    arrival_state: CartesianState,
    time_of_flight_s: float,
    gravitational_parameter_m3_s2: float | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]
```

Solves a single-revolution Lambert transfer between two Cartesian states, returning `(departure_delta_v_m_s, arrival_delta_v_m_s)`. Each delta-v is an `(x, y, z)` tuple in m/s.

| Parameter | Unit | Description |
| --- | --- | --- |
| `departure_state` | — | Cartesian state at departure |
| `arrival_state` | — | Cartesian state at arrival |
| `time_of_flight_s` | s | Time of flight |
| `gravitational_parameter_m3_s2` | m³/s² | Gravitational parameter |

```python
departure_delta_v_m_s, arrival_delta_v_m_s = orbits.lambert_delta_v(
    departure_state=departure_state,
    arrival_state=arrival_state,
    time_of_flight_s=817.4257,
    gravitational_parameter_m3_s2=398600441500000.0,
)
```

### `orbits.geo_ym_lambert_delta_v`

```python
orbits.geo_ym_lambert_delta_v(
    *,
    platform_orbit: KeplerianElements,
    target_orbit: KeplerianElements,
    time_of_flight_s: float,
    platform_gravitational_parameter_m3_s2: float | None = None,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]
```

Computes the GEO-YM Lambert transfer delta-v based on the platform orbit and target orbit. `platform_gravitational_parameter_m3_s2` applies only to the platform orbit; when not provided, ASTROX retains its default value.

| Parameter | Unit | Description |
| --- | --- | --- |
| `platform_orbit` | — | Platform Keplerian elements |
| `target_orbit` | — | Target Keplerian elements |
| `time_of_flight_s` | s | Time of flight |
| `platform_gravitational_parameter_m3_s2` | m³/s² | Platform orbit gravitational parameter |

```python
departure_delta_v_m_s, arrival_delta_v_m_s = orbits.geo_ym_lambert_delta_v(
    platform_orbit=platform_orbit,
    target_orbit=target_orbit,
    time_of_flight_s=3600.0,
    platform_gravitational_parameter_m3_s2=398600441500000.0,
)
```

## Reference Frames and Libration

### `orbits.convert_czml_position`

```python
orbits.convert_czml_position(
    position: components.CzmlPosition,
    *,
    to_central_body: str,
    target_reference_frame: str,
) -> tuple[float, components.CzmlPosition]
```

Converts sampled CZML positions from the current central body and reference frame to another central-body reference frame, returning `(period_s, transformed_position)`.

| Parameter | Description |
| --- | --- |
| `position` | `astrox.components.CzmlPosition` instance |
| `to_central_body` | Target central body |
| `target_reference_frame` | Target reference frame, such as `FIXED`, `INERTIAL`, `J2000` |

```python
from astrox import components, orbits

position = components.czml_position(
    epoch="2024-01-01T00:00:00Z",
    central_body="Earth",
    reference_frame="INERTIAL",
    interpolation_algorithm="LAGRANGE",
    interpolation_degree=7,
    cartesian=[0.0, 7000000.0, 0.0, 0.0],
)

period_s, fixed_position = orbits.convert_czml_position(
    position,
    to_central_body="Earth",
    target_reference_frame="FIXED",
)
```

### `orbits.earth_moon_libration`

```python
orbits.earth_moon_libration(position: components.CzmlPosition) -> components.CzmlPositionSTM
```

Converts sampled CZML positions to the Earth-Moon libration reference frame, returning `astrox.components.CzmlPositionSTM`. This object includes the `components.CzmlPosition` fields plus `unit_quaternion` and `cartesian_translation`.

| Parameter | Description |
| --- | --- |
| `position` | `astrox.components.CzmlPosition` instance |

```python
libration_state = orbits.earth_moon_libration(position)
print(libration_state.central_body, libration_state.reference_frame)
print(libration_state.unit_quaternion)
```

## Return Values

Functions in `astrox.orbits` return parsed SDK value objects or tuples, not raw ASTROX response dictionaries. Constructors and conversion functions return frozen dataclasses; wizards and Lambert functions return nested tuples; `convert_czml_position` returns `(period_s, components.CzmlPosition)`; `earth_moon_libration` returns `components.CzmlPositionSTM`. When an unparsed raw response is needed, use `astrox.raw`.

## Error Handling

All functions raise `astrox.exceptions.AstroxAPIError` when ASTROX returns an unsuccessful response or the network request fails. The SDK does not hide or rewrite server error messages.

## Full Examples

Complete runnable examples are in `examples/02_orbits/`:

- `conversions.py`: mutual conversion between Keplerian elements and Cartesian states, ascending-node longitude/latitude/altitude, and Kozai-Izsak mean elements.
- `wizards.py`: GEO, Molniya, SSO, and Walker constellation generation.
- `lambert_delta_v.py`: Cartesian Lambert and GEO-YM Lambert delta-v.
- `orbit_system.py`: CZML position reference-frame conversion and Earth-Moon libration conversion.
