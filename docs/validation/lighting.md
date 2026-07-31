# Lighting Validation Evidence

This page records the cross-validation status of the `astrox.lighting` surface. It is an evidence register, not a usage guide; for API semantics and examples see [`docs/manual/lighting/README.md`](../manual/lighting/README.md). Status values (`verified`, `partial`, `unresolved`, `unverified`) are taken directly from the coverage checklists in the cross-validation scripts listed under each family.

| Family | Cross-validation script | Live snapshot sidecar |
| --- | --- | --- |
| Site Solar AER / Lighting Times / Solar Intensity | [`tests/validation/cross_validation/lighting/test_site_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_site_sun_skyfield.py) | [`tests/validation/live_snapshot/lighting/lighting.snap.json`](../../tests/validation/live_snapshot/lighting/lighting.snap.json) |
| Spacecraft Solar AER / Lighting Times | [`tests/validation/cross_validation/lighting/test_spacecraft_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_spacecraft_sun_skyfield.py) | [`tests/validation/live_snapshot/lighting/lighting.snap.json`](../../tests/validation/live_snapshot/lighting/lighting.snap.json) |
| Spacecraft Solar Intensity | [`tests/validation/cross_validation/lighting/test_spacecraft_solar_intensity_orekit.py`](../../tests/validation/cross_validation/lighting/test_spacecraft_solar_intensity_orekit.py) | [`tests/validation/live_snapshot/lighting/lighting.snap.json`](../../tests/validation/live_snapshot/lighting/lighting.snap.json) |

## Site Lighting Times

Coverage status from [`test_site_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_site_sun_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| Site `lighting_times` | verified for high-altitude/representative cases; low-altitude transition residual unresolved |
| `SunLight` / `Penumbra` / `Umbra` intervals | partial (representative cases verified; low-altitude residual unresolved) |
| Site longitude / latitude / height parameters | partial (Hawaii / Greenwich and a low-altitude calibration case) |
| Start / stop window parameters | partial (day, short, sunrise / sunset windows) |

Comparison path: Skyfield apparent topocentric Sun geometry and WGS84 solar-disk horizon derivation.

Constants and tolerances:

- `EARTH_EQUATORIAL_RADIUS_M = 6378137.0`
- `SUN_RADIUS_KM = 695700.0`
- Transition tolerance: `TRANSITION_ABS_S = 3.0`

Verified transition pairs compare ASTROX interval boundaries against the times when the apparent topocentric Sun center crosses the geometric horizon offset by the solar angular radius:

- Evening full-sun stop and morning full-sun start: `altitude = geometric_horizon + solar_angular_radius`.
- Evening umbra start and morning umbra stop: `altitude = geometric_horizon - solar_angular_radius`.

Unresolved: low-altitude site lighting transitions do not yet match the simple WGS84 geometric-horizon model and remain a strict calibration `xfail` in the script.

Live snapshot sidecar: `lighting.snap.json` records `lighting_times_site`.

## Site Solar AER

Coverage status from [`test_site_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_site_sun_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| Site `solar_aer` | verified for representative topocentric Sun cases |
| `Azimuth` / `Elevation` | verified |
| `Range` | partial (angles verified; broader range residual unresolved) |
| Site longitude / latitude / height parameters | partial |
| Start / stop window / `step_s` parameters | partial |

Comparison path: Skyfield apparent topocentric Sun `altaz` and range.

Constants and tolerances:

- `EARTH_EQUATORIAL_RADIUS_M = 6378137.0`
- `AER_AZIMUTH_ABS_DEG = 1.0e-4`
- `AER_ELEVATION_ABS_DEG = 5.0e-5`
- `AER_RANGE_ABS_KM = 25.0`

Known residual: SolarAER range has a date-dependent residual against Skyfield / Astropy / Orekit topocentric range. `solar_intensity.ApparentSolarRange` matches those engines, so the residual appears SolarAER-specific. This case is kept as a strict calibration `xfail`.

Live snapshot sidecar: `lighting.snap.json` records `solar_aer_site`.

## Site Solar Intensity

Coverage status from [`test_site_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_site_sun_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| Site `solar_intensity` | partial (Quito sunrise verified; Hawaii sunset transition residual unresolved) |
| `Intensity` / `PercentShadow` | partial (stable sunrise case verified; sunset transition residual unresolved) |
| `ApparentSolarRange` | partial |
| `SolarDiskHalfAngle` | partial |
| `SolarGrazingAngle` | partial (stable sunrise case verified; far-from-edge residual unresolved) |
| Site longitude / latitude / height parameters | partial |
| Start / stop window / `step_s` parameters | partial |

Comparison path: Skyfield apparent topocentric Sun geometry, solar angular radius, and visible-disk fraction for a grazing solar disk against the WGS84 geometric horizon.

Constants and tolerances:

- `EARTH_EQUATORIAL_RADIUS_M = 6378137.0`
- `SUN_RADIUS_KM = 695700.0`
- `INTENSITY_ABS = 5.0e-4`
- `SOLAR_DISK_HALF_ANGLE_ABS_DEG = 5.0e-5`
- `GRAZING_ANGLE_ABS_DEG = 1.0e-4`
- `AER_AZIMUTH_ABS_DEG = 1.0e-4` and `AER_ELEVATION_ABS_DEG = 5.0e-5` for `ApparentSolarAzimuth` and `ApparentSolarElevation`
- `AER_RANGE_ABS_KM = 25.0` for `ApparentSolarRange`

Convention note: the site angles returned inside `solar_intensity` are light-delay-only, without aberration. For direct apparent topocentric Sun angles, use `solar_aer`.

Known residual: Hawaii sunset transition residuals, including `SolarGrazingAngle` far from the edge, remain unresolved and are kept as a strict calibration `xfail`.

Live snapshot sidecar: none directly for site solar intensity. `lighting.snap.json` records spacecraft solar intensity snapshots only.

## Spacecraft Lighting Times

Coverage status from [`test_spacecraft_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_spacecraft_sun_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| Spacecraft `lighting_times` from SGP4 | verified for ISS eclipse-cycle intervals |
| `SunLight` / `Penumbra` / `Umbra` intervals | verified against conical Earth / Sun disk transition geometry |
| Spacecraft TLE parameters | partial (ISS SGP4 representative case) |
| Start / stop window parameters | partial (multi-orbit eclipse window) |

Comparison path: Skyfield SGP4 state, apparent Sun vector, and conical Earth-shadow geometry.

Constants and tolerances:

- `EARTH_EQUATORIAL_RADIUS_KM = 6378.137`
- `SUN_RADIUS_KM = 695700.0`
- `LIGHTING_TRANSITION_ABS_S = 3.0`

Verified transition pairs compare ASTROX interval boundaries against the times when the spacecraft-Earth-Sun separation equals:

- Sunlight entry / exit: `separation = earth_angular_radius + sun_angular_radius`.
- Umbra entry / exit: `separation = earth_angular_radius - sun_angular_radius`.

Live snapshot sidecar: `lighting.snap.json` records `lighting_times_sgp4`.

## Spacecraft Solar AER

Coverage status from [`test_spacecraft_sun_skyfield.py`](../../tests/validation/cross_validation/lighting/test_spacecraft_sun_skyfield.py):

| Branch / Field | Status |
| --- | --- |
| Spacecraft `solar_aer` from SGP4 | verified for the documented VVLH front-right-down frame with ASTROX's observed Sun-vector convention |
| `Azimuth` | verified (VVLH convention) |
| `Elevation` | partial (VVLH convention verified; narrow DE421-vs-ASTROX-ephemeris / vector-convention tolerance) |
| `Range` | partial (apparent spacecraft-to-Sun range; retains tolerance) |
| Spacecraft TLE / `step_s` parameters | partial (ISS SGP4 representative case) |

Comparison path: Skyfield SGP4 state, apparent Sun vector, and VVLH front-right-down axes.

Constants and tolerances:

- `EARTH_EQUATORIAL_RADIUS_KM = 6378.137`
- `SUN_RADIUS_KM = 695700.0`
- `SOLAR_AER_AZIMUTH_ABS_DEG = 1.0e-4`
- `SOLAR_AER_ELEVATION_ABS_DEG = 7.0e-4`
- `SOLAR_AER_RANGE_ABS_KM = 25.0`

Known convention mismatch: spacecraft SolarAER uses a mixed-vector convention. The horizontal components (`x`, `y`) of the Sun direction are derived from the apparent geocentric Sun vector projected onto the VVLH forward / right axes; the vertical component (`z`) and the `Range` value use the apparent spacecraft-to-Sun vector projected onto the VVLH down axis. This means azimuth is computed from geocentric-Sun horizontal components while elevation and range are computed from apparent spacecraft-to-Sun vertical / range components. The script encodes this observed ASTROX convention rather than assuming a single physical vector.

Live snapshot sidecar: `lighting.snap.json` records `solar_aer_sgp4`.

## Spacecraft Solar Intensity

Coverage status from [`test_spacecraft_solar_intensity_orekit.py`](../../tests/validation/cross_validation/lighting/test_spacecraft_solar_intensity_orekit.py):

| Branch / Field | Status |
| --- | --- |
| Spacecraft `solar_intensity` from CZML-like inertial state samples | verified |
| `Intensity` | verified (Orekit conical Earth-shadow lighting ratio) |
| Spacecraft position / velocity parameters | partial (general-shadow and partial-shadow samples) |
| Start / stop / sample offset parameters | partial (two fixed case windows) |

Comparison path: Orekit `ConicallyShadowedLightFluxModel` with EME2000 state samples.

Constants and tolerances:

- Orekit WGS84 Earth equatorial radius and Sun radius
- `INTENSITY_ABS = 5.0e-6`

Verified cases:

- `general_shadow`: five samples spanning SunLight, Umbra, and mixed geometric conditions.
- `partial_shadow`: five samples at a fixed position near the edge of the Earth shadow.

Live snapshot sidecar: `lighting.snap.json` records `solar_intensity_j2`, `solar_intensity_two_body`, and `solar_intensity_czml`. No SGP4 solar-intensity snapshot is maintained.
