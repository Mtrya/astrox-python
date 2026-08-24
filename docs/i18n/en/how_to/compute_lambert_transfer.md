# Compute a Lambert transfer window between bodies

This page solves a specific task: given a departure body, an arrival body, and their departure/arrival time windows, scan the windows for transfer opportunities and read out each Lambert transfer's departure/arrival times, velocity increments, and transfer orbit states.

## Complete example

The script below computes an Earth→Mars transfer window departing in June 2028 and arriving in April 2029, using the ICRF frame. Save the code as `compute_lambert_transfer.py`:

```python
import astrox
from astrox import celestial

astrox.configure(base_url="http://astrox.cn:8765")

transfer = celestial.lambert_transfer_window(
    departure_body="Earth",
    arrival_body="Mars",
    departure_start="2028-06-01T00:00:00Z",
    departure_stop="2028-06-03T00:00:00Z",
    arrival_start="2029-04-01T00:00:00Z",
    arrival_stop="2029-04-03T00:00:00Z",
    sun_frame="ICRF",
    min_time_of_flight_days=10,
    departure_step_days=2.0,
    arrival_step_days=1.0,
    # this window's departure hyperbolic excess speed is about 15 km/s, above
    # the server MaxDepartureDV default (10000 m/s); widen the bound explicitly
    # to keep the results
    max_departure_delta_v_m_s=20000,
)

results = transfer["TransferResults"]
print(f"Returned {len(results)} transfer results")

for result in results:
    print(
        f"Departure {result['DepartureTime']} → arrival {result['ArrivalTime']}: "
        f"|DeltaV1|={result['DV1_Mag']:.1f} m/s, "
        f"|DeltaV2|={result['DV2_Mag']:.1f} m/s, "
        f"TOF={result['TimeOfFlightDays']:.0f} d"
    )
```

## Run it

```bash
python compute_lambert_transfer.py
```

## Decisions to make

1. **Choose the departure and arrival bodies**: `departure_body`/`arrival_body` accept server-supported body names (e.g. `Earth`, `Mars`, `Ceres`) and MPC numbers or names (e.g. `2015 XF261`). When the matching `*_elements` argument is omitted for an asteroid, the server queries the MPC elements over the network.
2. **Set the two time windows**: `departure_start`/`departure_stop` and `arrival_start`/`arrival_stop` each define a UTC time window, which the SDK combines into the `"start/stop"` string of `DepartureInterval`/`ArrivalInterval` respectively. `departure_step_days` and `arrival_step_days` (unit d) control the sample step within each window; the number of results is roughly the product of the two windows' sample counts — the 2 departure days × 3 arrival days in the example produce 6 results. `min_time_of_flight_days` (unit d, integer) filters out combinations whose transfer time is too short; the server default is 10.
3. **Choose the output reference frame**: the server default for `sun_frame` is `MeanEclpJ2000`; the transfer velocities of the `ICRF` branch agree with an independent zero-revolution prograde Lambert solution, and the endpoint position directions have also been identified as ICRF axes, while the exact relationship between `MeanEclpJ2000` and ICRF is not yet independently confirmed, so pass `sun_frame="ICRF"` explicitly when you need numbers with an identified frame.
4. **Adjust the filter bounds as needed**: since 2026-08-20 the server filters cases by `max_departure_delta_v_m_s`/`max_arrival_delta_v_m_s` (defaults 10000 m/s each, the departure/arrival hyperbolic excess speed magnitudes) and `max_time_of_flight_days` (default 500 d), returning an empty list when everything is out of bounds; widen the bounds explicitly when scanning large-ΔV or very long transfer windows — the Earth→Mars window in the example is such a case.

## Reading the results

Each result object contains:

- `DepartureTime`/`ArrivalTime`: departure/arrival times (UTC strings).
- `DeltaV1`/`DeltaV2`: departure/arrival velocity-increment vectors (departure/arrival hyperbolic excess velocity vectors, m/s); `DV1_Mag`/`DV2_Mag` are their Euclidean norms (m/s). The physical meaning of `DeltaV` relative to the endpoint bodies' velocities is not yet independently confirmed, so verify it yourself when you need a strict physical interpretation.
- `RV1`/`RV2`: heliocentric position and velocity at departure/arrival `[x, y, z, vx, vy, vz]` (positions m, velocities m/s); under the ICRF branch the transfer velocities agree with the independent Lambert solution, and the endpoint position directions match the ICRF axes.
- `TimeOfFlightDays`: time of flight (d), verified to be the exact day difference between the arrival and departure times.
- `ArrivalLightAngle`: Sun lighting angle at arrival (deg), verified to be the angle between `DeltaV2` and the `RV2` position vector.

## Asteroids and explicit MPC elements

To skip the server's MPC network query, you can pass orbital elements explicitly:

```python
elements = celestial.mpc_orbital_elements(
    epoch_mjd_tdt=61000.0,
    periapsis_distance_au=0.6740515,
    semi_major_axis_au=0.9898367,
    eccentricity=0.3190276,
    inclination_deg=0.79379,
    raan_deg=209.81829,
    argument_of_periapsis_deg=100.88187,
    mean_anomaly_deg=120.0,
)

transfer = celestial.lambert_transfer_window(
    departure_body="Earth",
    arrival_body="2015 XF261",
    departure_start="2028-06-01T00:00:00Z",
    departure_stop="2028-06-03T00:00:00Z",
    arrival_start="2029-04-01T00:00:00Z",
    arrival_stop="2029-04-03T00:00:00Z",
    sun_frame="ICRF",
    arrival_elements=elements,
)
```

Note: independent Kepler propagation of explicit MPC elements in the transfer route is not yet verified, and the element system and time convention are unconfirmed (the `reference_frame` option does not change the arrival states of that route); this branch is callable and its response structure is recorded by live snapshots, but verify the numeric semantics yourself. The `target_elements` branch of `mpc_ephemeris` is verified (see the celestial manual).

## Learn more

- The full parameter tables of `lambert_transfer_window` and `mpc_orbital_elements`, and the `TransferResults` field descriptions, are in the [celestial manual](../manual/celestial/README.md).
- For the single-transfer velocity increment `orbits.lambert_delta_v`, see the [orbits manual](../manual/orbits/README.md).
- The validation status, known residuals, and cross-validation evidence per branch are on the [celestial validation page](../../../validation/celestial.md).
