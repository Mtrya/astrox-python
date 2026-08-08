# Two-Line Elements and Debris Analysis

`astrox.cat` provides public APIs for two-line element set (TLE) generation, orbital lifetime estimation, and space debris breakup simulation. The recommended import style is:

```python
from astrox import cat, orbits
```

This page is organized by function family: generate a TLE from Keplerian elements with `cat.generate_tle`, then estimate the orbital lifetime with `cat.estimate_tle_lifetime`, or generate debris through the three breakup-simulation functions. All TLE inputs and outputs use the `orbits.Tle` value object from the [orbits manual](../orbits/README.md).

## Two-line element generation

### `cat.generate_tle`

```python
cat.generate_tle(
    *,
    name: str,
    catalog_number: str,
    epoch: str,
    bstar: float,
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_perigee_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
    is_mean_elements: bool | None = None,
) -> Tle
```

Generates a two-line element set from Keplerian elements in the TEME reference frame, returning an `orbits.Tle` instance.

| Parameter | Unit | Description |
| --- | --- | --- |
| `name` | — | Space object name |
| `catalog_number` | — | Catalog number (NORAD number) |
| `epoch` | — | Orbit epoch string (UTC) |
| `bstar` | — | B* drag coefficient |
| `semi_major_axis_km` | km | Semi-major axis |
| `eccentricity` | — | Eccentricity |
| `inclination_deg` | deg | Inclination (TEME) |
| `argument_of_perigee_deg` | deg | Argument of perigee (TEME) |
| `raan_deg` | deg | Right ascension of the ascending node (TEME) |
| `true_anomaly_deg` | deg | True anomaly (TEME) |
| `is_mean_elements` | — | Whether the input is mean elements; `True` means mean elements, `False` or omitted means instantaneous elements |

```python
tle = cat.generate_tle(
    name="probe",
    catalog_number="25545",
    epoch="2024-01-01T00:00:00.000Z",
    bstar=0.0001,
    semi_major_axis_km=6778.0,
    eccentricity=0.0005,
    inclination_deg=51.6,
    argument_of_perigee_deg=60.0,
    raan_deg=340.0,
    true_anomaly_deg=0.0,
)

print(tle.line1)
print(tle.line2)
```

The generated result can be used directly with `propagator.sgp4`, `conjunction`, and the lifetime estimation and breakup simulation functions below.

## Orbital lifetime estimation

### `cat.estimate_tle_lifetime`

```python
cat.estimate_tle_lifetime(
    *,
    epoch: str,
    tle: Tle,
    sm: float | None = None,
    mass: float | None = None,
) -> TleLifetimeResult
```

Estimates the orbital lifetime of a given TLE. `sm` and `mass` are parameters of the server-side lifetime model; when omitted, the server retains its default values.

| Parameter | Description |
| --- | --- |
| `epoch` | Epoch string for the lifetime computation |
| `tle` | `orbits.Tle` instance of the target satellite |
| `sm` | Server-side lifetime model parameter (optional) |
| `mass` | Satellite mass (optional) |

`TleLifetimeResult` is a parsed frozen dataclass:

| Field | Type | Description |
| --- | --- | --- |
| `is_success` | `bool` | Whether the call succeeded |
| `message` | `str` | Server message |
| `life_years` | `float` | Orbital lifetime, in years |

```python
result = cat.estimate_tle_lifetime(
    epoch="2024-01-01T00:00:00.000Z",
    tle=tle,
)

print(result.life_years)
```

`life_years` includes server fallback values and cannot be used as an accurate lifetime prediction. Currently only the monotonic direction of the lifetime under changing parameter ratios has been verified; absolute lifetime values are unverified.

## Debris breakup simulation

The three functions simulate debris produced by the breakup of a mother satellite and all return `DebrisBreakupResult`. They simulate the breakup event itself and return the debris TLEs and orbital parameters; the debris orbital periods and perigee/apogee altitudes have been cross-checked against the orbital invariants of independent SGP4 states, but the scientific validity of the debris breakup model itself is outside the verified scope.

### `cat.simulate_debris_breakup_simple`

```python
cat.simulate_debris_breakup_simple(
    *,
    mother_tle: Tle,
    epoch: str,
    count: int | None = None,
    ssc_prefix: str | None = None,
    delta_v_m_s: float | None = None,
    area_to_mass_ratio_m2_kg: float | None = None,
    min_azimuth_deg: float | None = None,
    max_azimuth_deg: float | None = None,
    min_elevation_deg: float | None = None,
    max_elevation_deg: float | None = None,
    compute_lifetime: bool | None = None,
) -> DebrisBreakupResult
```

All debris pieces use the same relative speed and area-to-mass ratio; azimuth/elevation are generated uniformly within the given ranges.

| Parameter | Unit | Description |
| --- | --- | --- |
| `mother_tle` | — | `orbits.Tle` instance of the mother satellite |
| `epoch` | — | Breakup time string (UTC) |
| `count` | — | Number of debris pieces, should be less than 1000 |
| `ssc_prefix` | — | Debris catalog-number prefix, e.g. `"AF"` |
| `delta_v_m_s` | m/s | Debris speed magnitude relative to the mother satellite |
| `area_to_mass_ratio_m2_kg` | m²/kg | Debris area-to-mass ratio |
| `min_azimuth_deg` | deg | Minimum azimuth |
| `max_azimuth_deg` | deg | Maximum azimuth |
| `min_elevation_deg` | deg | Minimum elevation |
| `max_elevation_deg` | deg | Maximum elevation |
| `compute_lifetime` | — | Whether to compute the debris orbital lifetimes |

The azimuth and elevation ranges are defined by the server in the VVLH axes of the TEME reference frame.

```python
result = cat.simulate_debris_breakup_simple(
    mother_tle=tle,
    epoch="2024-01-01T00:00:00.000Z",
    count=50,
    ssc_prefix="AF",
    delta_v_m_s=400.0,
    area_to_mass_ratio_m2_kg=0.002,
)

print(len(result.debris_tles), result.periods_min[:3])
```

### `cat.simulate_debris_breakup`

```python
cat.simulate_debris_breakup(
    *,
    mother_tle: Tle,
    epoch: str,
    impulses: Sequence[DebrisImpulse],
    ssc_prefix: str | None = None,
    area_to_mass_ratio_m2_kg: float | None = None,
    compute_lifetime: bool | None = None,
) -> DebrisBreakupResult
```

Gives the breakup parameters for each debris piece individually. `impulses` is a sequence of `DebrisImpulse`, one per debris piece:

| Field | Unit | Description |
| --- | --- | --- |
| `azimuth_deg` | deg | Azimuth |
| `elevation_deg` | deg | Elevation |
| `delta_v_m_s` | m/s | Speed magnitude relative to the mother satellite |
| `area_to_mass_ratio_m2_kg` | m²/kg | Area-to-mass ratio |

```python
impulses = [
    cat.DebrisImpulse(
        azimuth_deg=90.0,
        elevation_deg=1.0,
        delta_v_m_s=400.0,
        area_to_mass_ratio_m2_kg=0.002,
    ),
    cat.DebrisImpulse(
        azimuth_deg=120.0,
        elevation_deg=0.0,
        delta_v_m_s=300.0,
        area_to_mass_ratio_m2_kg=0.01,
    ),
]

result = cat.simulate_debris_breakup(
    mother_tle=tle,
    epoch="2024-01-01T00:00:00.000Z",
    impulses=impulses,
    ssc_prefix="AF",
)
```

### `cat.simulate_debris_breakup_nasa`

```python
cat.simulate_debris_breakup_nasa(
    *,
    mother_tle: Tle,
    epoch: str,
    ssc_prefix: str | None = None,
    total_mass: float | None = None,
    minimum_characteristic_length: float | None = None,
) -> DebrisBreakupResult
```

Generates debris using the NASA breakup-model branch. `total_mass` is the total mass of the mother satellite and `minimum_characteristic_length` is the minimum characteristic length of the debris; the units and value constraints of both follow the server-side model convention, and the SDK only forwards them.

```python
result = cat.simulate_debris_breakup_nasa(
    mother_tle=tle,
    epoch="2024-01-01T00:00:00.000Z",
    ssc_prefix="AF",
    total_mass=100.0,
    minimum_characteristic_length=0.1,
)
```

### Return value `DebrisBreakupResult`

| Field | Type | Description |
| --- | --- | --- |
| `is_success` | `bool` | Whether the call succeeded |
| `message` | `str` | Server message |
| `debris_tles` | `tuple[Tle, ...]` | TLEs of all debris pieces |
| `impulses` | `tuple[DebrisImpulse, ...]` | Breakup parameters of each debris piece |
| `life_years` | `tuple[float, ...]` | Orbital lifetime of each debris piece, in years; the server falls back to 25 years when lifetime is not computed or the computation fails |
| `altitude_of_perigee_km` | `tuple[float, ...]` | Perigee altitude of each debris piece, in km |
| `altitude_of_apogee_km` | `tuple[float, ...]` | Apogee altitude of each debris piece, in km |
| `periods_min` | `tuple[float, ...]` | Orbital period of each debris piece, in min |

Each array corresponds to `debris_tles` by debris position, but the SDK does not enforce equal array lengths; lengths follow the server response. Like the lifetime estimation, `life_years` includes server fallback values and cannot be used as an accurate lifetime prediction.

## Verified scope

- The instantaneous-elements branch of `generate_tle` (`is_mean_elements` omitted or `False`) is consistent with an independent TEME Keplerian state; the mean-elements branch (`True`) is unverified.
- The debris periods, perigee altitudes, and apogee altitudes returned by the three breakup-simulation branches are consistent with the orbital invariants of independent SGP4 states of the debris.
- The debris breakup model itself (the physical plausibility of debris counts, velocity distribution, and mass distribution) and the lifetime values are unverified.

## Convention notes

- Optional parameters are not sent to ASTROX when omitted; the server retains its default values.
- The azimuth/elevation ranges of the breakup simulation are defined in the VVLH axes of the TEME reference frame (simple branch).

A complete runnable example is available at `examples/09_cat/cat_workflows.py`.

## Error handling

When ASTROX returns an unsuccessful response or the network request fails, the functions in this module raise `astrox.exceptions.AstroxAPIError`. The SDK does not rewrite server error messages. When you need full control over the request payload or want to handle the raw response, use `astrox.raw.post`.
