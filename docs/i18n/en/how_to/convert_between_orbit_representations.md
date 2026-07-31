# Convert between orbit representations

This page solves a specific task: use `astrox.orbits` to convert an orbit from one representation to another. Currently supported conversions are between Keplerian elements, Cartesian state, and Kozai-Izsak mean elements.

## Two decisions to make

1. **Source representation determines which function to call**:
   - You have Keplerian elements and want Cartesian state → use `orbits.keplerian_to_cartesian`.
   - You have Cartesian state and want Keplerian elements → use `orbits.cartesian_to_keplerian`.
   - You have osculating elements and want Kozai-Izsak mean elements → use `orbits.kozai_izsak_mean_elements`.
   - If your input is a two-line element set (TLE), the SDK currently has no standalone TLE ↔ elements/state conversion function; just propagate with `propagator.sgp4`. See [How to propagate an orbit](propagate_an_orbit.md).
2. **Whether to specify the gravitational parameter**: `keplerian_to_cartesian` accepts the central-body gravitational parameter via `gravitational_parameter_m3_s2`; when omitted, the ASTROX server uses its default. `cartesian_to_keplerian` currently always uses the ASTROX default Earth gravitational parameter.

## Complete example

Save the following code as `convert_between_orbit_representations.py`:

```python
import astrox
from astrox import orbits

astrox.configure(base_url="http://astrox.cn:8765")

EARTH_MU_M3_S2 = 398600441500000.0

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=15.0,
    true_anomaly_deg=45.0,
)

print("原始开普勒根数:")
print(f"  半长轴 a={orbit.semi_major_axis_m:.3f} m")
print(f"  偏心率 e={orbit.eccentricity:.6f}")
print(f"  倾角 i={orbit.inclination_deg:.3f} deg")
print(f"  升交点赤经 RAAN={orbit.raan_deg:.3f} deg")
print(f"  近地点幅角 ω={orbit.argument_of_periapsis_deg:.3f} deg")
print(f"  真近点角 ν={orbit.true_anomaly_deg:.3f} deg")

cartesian = orbits.keplerian_to_cartesian(
    orbit,
    gravitational_parameter_m3_s2=EARTH_MU_M3_S2,
)
print("\n转换为笛卡尔状态:")
print(f"  位置 (m): x={cartesian.x_m:.3f}, y={cartesian.y_m:.3f}, z={cartesian.z_m:.3f}")
print(f"  速度 (m/s): vx={cartesian.vx_m_s:.6f}, vy={cartesian.vy_m_s:.6f}, vz={cartesian.vz_m_s:.6f}")

round_trip = orbits.cartesian_to_keplerian(cartesian)
print("\n从笛卡尔状态转换回开普勒根数:")
print(f"  半长轴 a={round_trip.semi_major_axis_m:.3f} m")
print(f"  偏心率 e={round_trip.eccentricity:.6f}")
print(f"  倾角 i={round_trip.inclination_deg:.3f} deg")
print(f"  升交点赤经 RAAN={round_trip.raan_deg:.3f} deg")
print(f"  近地点幅角 ω={round_trip.argument_of_periapsis_deg:.3f} deg")
print(f"  真近点角 ν={round_trip.true_anomaly_deg:.3f} deg")

mean = orbits.kozai_izsak_mean_elements(orbit)
print("\n密切根数 -> Kozai-Izsak 平均根数:")
print(f"  半长轴 a={mean.semi_major_axis_m:.3f} m")
print(f"  偏心率 e={mean.eccentricity:.6f}")
print(f"  倾角 i={mean.inclination_deg:.3f} deg")
print(f"  升交点赤经 RAAN={mean.raan_deg:.3f} deg")
print(f"  近地点幅角 ω={mean.argument_of_perigee_deg:.3f} deg")
print(f"  平近点角 M={mean.mean_anomaly_deg:.3f} deg")
print(f"  纬度幅角 u={mean.argument_of_latitude_deg:.3f} deg")
print(f"  近地点经度 Π={mean.longitude_of_perigee_deg:.3f} deg")
print(f"  平经度 L={mean.mean_longitude_deg:.3f} deg")
```

## Run

```bash
python convert_between_orbit_representations.py
```

## Actual output

```text
原始开普勒根数:
  半长轴 a=6778137.000 m
  偏心率 e=0.001000
  倾角 i=28.500 deg
  升交点赤经 RAAN=15.000 deg
  近地点幅角 ω=0.000 deg
  真近点角 ν=45.000 deg

转换为笛卡尔状态:
  位置 (m): x=3536889.576, y=5305259.458, z=2285340.036
  速度 (m/s): vx=-6472.840331, vy=3206.067962, vz=2591.048776

从笛卡尔状态转换回开普勒根数:
  半长轴 a=6778136.995 m
  偏心率 e=0.001000
  倾角 i=28.500 deg
  升交点赤经 RAAN=15.000 deg
  近地点幅角 ω=360.000 deg
  真近点角 ν=45.000 deg

密切根数 -> Kozai-Izsak 平均根数:
  半长轴 a=6778136.238 m
  偏心率 e=0.000851
  倾角 i=28.500 deg
  升交点赤经 RAAN=14.964 deg
  近地点幅角 ω=-61.373 deg
  平近点角 M=106.310 deg
  纬度幅角 u=45.030 deg
  近地点经度 Π=313.591 deg
  平经度 L=59.900 deg
```

## What just happened

`orbits.keplerian(...)` constructs a `KeplerianElements` object that only contains the six classical elements: semi-major axis, eccentricity, inclination, right ascension of the ascending node, argument of periapsis, and true anomaly. It has no epoch.

`orbits.keplerian_to_cartesian` sends the Keplerian elements to ASTROX at `/OrbitConvert/Kepler2RV` and returns a `CartesianState` with fields `x_m / y_m / z_m` (meters) and `vx_m_s / vy_m_s / vz_m_s` (meters per second). `gravitational_parameter_m3_s2` is optional; this example passes the Earth gravitational parameter, and when omitted the server uses its default.

`orbits.cartesian_to_keplerian` sends the Cartesian state to ASTROX at `/OrbitConvert/RV2Kepler` and returns `KeplerianElements`. This function currently always uses the ASTROX default Earth gravitational parameter. Note: when eccentricity is near zero, the argument of periapsis may jump near 0°/360° because of the angular ambiguity of near-circular orbits; this is not a conversion error.

`orbits.kozai_izsak_mean_elements` sends the osculating elements to ASTROX at `/OrbitConvert/GetKozaiIzsakMeanElements` and returns `MeanKeplerianElements`. In addition to the six classical elements, it also contains derived quantities such as argument of latitude, longitude of perigee, and mean longitude.

## Quick reference

| Your input | Desired output | Function to use |
| --- | --- | --- |
| Keplerian elements | Cartesian state | `orbits.keplerian_to_cartesian` |
| Cartesian state | Keplerian elements | `orbits.cartesian_to_keplerian` |
| Osculating elements | Kozai-Izsak mean elements | `orbits.kozai_izsak_mean_elements` |
| Two-line element set (TLE) | Position/velocity samples | `propagator.sgp4` (see [How to propagate an orbit](propagate_an_orbit.md)) |

## Learn more

- For full signatures, unit tables, and return-value conventions of the constructors and conversion functions, see the [orbits manual](../manual/orbits/README.md).
- For verification status, cross-validation evidence, and known residuals for each branch, see the [Orbits validation page](../../../validation/orbits.md).
- A complete runnable example is available at `examples/02_orbits/conversions.py`.
