# Celestial Ephemeris, Axes Rotation, and Lambert Transfer Windows

`astrox.celestial` provides read-only query APIs for celestial ephemeris and central-body axes rotation, plus inter-body Lambert transfer-window computation: `celestial.ephemeris` computes an ephemeris for a target body over a time window (`start`/`stop` are optional — when omitted, the server selects January 1 to December 31 of the current year), `celestial.cb_axes_rotation` computes the rotation between the coordinate axes of two central bodies, `celestial.mpc_ephemeris` computes minor-planet (MPC data) ephemerides, and `celestial.lambert_transfer_window` samples over departure/arrival time windows and returns each Lambert transfer result. The recommended import style is:

```python
from astrox import celestial
```

All four functions send HTTP POST requests through `astrox.raw.post` and return raw JSON response dictionaries without typed response parsing; the transport status wrapper fields `IsSuccess` and `Message` are removed from the return, and the remaining server fields are preserved. When the server returns an unsuccessful response (`IsSuccess=false`), the HTTP layer raises `astrox.exceptions.AstroxAPIError` (see error handling below). Ephemeris output uses the CZML Position structure: position and velocity are packed in the `cartesianVelocity` array, with each sample being 7 numeric values `[Time, X, Y, Z, dX, dY, dZ]`, where `Time` is the offset in seconds from the reference epoch, positions are in m, and velocities are in m/s. The response declares the coordinate central body in `Position.CentralBody` and the reference frame in `referenceFrame`; the SDK only relays the response's own declarations and makes no claim about the absolute correctness of the server's internal ephemeris kernel.

## Target-body ephemeris

### `celestial.ephemeris`

```python
celestial.ephemeris(
    *,
    target_name: str,
    start: str | None = None,
    stop: str | None = None,
    observer_name: str | None = None,
    observer_frame: str | None = None,
    step_s: float | None = None,
) -> dict[str, Any]
```

Computes an ephemeris for a target body over a time window and returns a raw JSON response dictionary. `start` and `stop` are optional; when omitted, the server selects January 1 to December 31 of the current year as the window.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `target_name` | `TargetName` | Target body name, e.g. `Moon`, `Mars` (the server supports `Moon`, `Mars`, `Venus`, `Mercury`, `Jupiter`, `Saturn`, `Uranus`, `Neptune`, and others) |
| `start` | `Start` | Analysis start time (UTC, `yyyy-MM-ddTHH:mm:ssZ`). Optional; the server default is January 1 of the current year |
| `stop` | `Stop` | Analysis stop time (UTC). Optional; the server default is December 31 of the current year |
| `observer_name` | `ObserverName` | Observer name, e.g. `Earth`; the server default is `Sun` |
| `observer_frame` | `ObserverFrame` | Observer frame, server options `FIXED`, `INERTIAL`, `MeanEclpJ2000`, `J2000`, default `MeanEclpJ2000` |
| `step_s` | `Step` | Sample step, in s, server default 86400 s |

`target_name` is the only required request field of this function; `start` and `stop` are optional — when omitted they are not sent to ASTROX and the server selects January 1 to December 31 of the current year as the window. Other optional fields that are not supplied are likewise not sent to ASTROX, and the server retains its default values.

```python
from astrox import celestial

start = "2026-01-01T00:00:00.000Z"
stop = "2026-01-02T00:00:00.000Z"

for frame in ("J2000", "MeanEclpJ2000"):
    ephemeris = celestial.ephemeris(
        target_name="Moon",
        start=start,
        stop=stop,
        observer_name="Earth",
        observer_frame=frame,
        step_s=43200.0,
    )
    samples = ephemeris["Position"]["cartesianVelocity"]
    print(f"Moon {frame}: {len(samples) // 7} state samples")
```

The response contains `Position` and `Period` (orbital period, unit s per the server documentation). The `Position` keys are `CentralBody`, `referenceFrame`, `epoch`, `interval`, `interpolationAlgorithm`, `interpolationDegree`, and `cartesianVelocity`; the number of samples depends on `Step` and the window length.

## Central-body axes rotation

### `celestial.cb_axes_rotation`

```python
celestial.cb_axes_rotation(
    *,
    from_central_body: str,
    to_central_body: str,
    epoch: str,
    from_frame: str | None = None,
    to_frame: str | None = None,
    order: int | None = None,
) -> dict[str, Any]
```

Computes the rotation from the coordinate axes of the source central body to those of the target central body at a given epoch and returns a raw JSON response dictionary.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `from_central_body` | `FromCbName` | Source central body name, e.g. `Earth` |
| `to_central_body` | `ToCbName` | Target central body name, e.g. `Moon` |
| `epoch` | `Epoch` | Epoch time (UTC) |
| `from_frame` | `FromCbFrame` | Source frame, server options `FIXED`, `INERTIAL`, `J2000`, `ICRF`, `MeanEclpJ2000`, default `INERTIAL` |
| `to_frame` | `ToCbFrame` | Target frame, same options, default `FIXED` |
| `order` | `Order` | Rotation motion order: `0` returns the quaternion only, `1` returns the quaternion and angular velocity; passed through as an integer |

`order` is preserved as an integer and lowered to the server as-is; the SDK does not rewrite the branch. The `Rotation` field of the response is a numeric array: with `order=0` it has length 4 (quaternion `[qx, qy, qz, qw]`), and with `order=1` it has length 7 (quaternion plus angular-velocity components, unit rad/s per the server documentation). Verified numeric semantics include: for the same central body on both sides with `INERTIAL` frames on both sides, the server returns the identity quaternion with zero angular velocity at `order=1`; the Earth `INERTIAL`→`FIXED` quaternion and angular velocity; and the Earth→Moon `INERTIAL`→`FIXED` angular velocity at `order=1`. The Earth→Moon `INERTIAL`→`FIXED` quaternion is unresolved, and other combinations are unverified, so verify their meaning yourself before use.

```python
rotation = celestial.cb_axes_rotation(
    from_central_body="Earth",
    to_central_body="Moon",
    epoch="2026-01-01T00:00:00.000Z",
    from_frame="INERTIAL",
    to_frame="INERTIAL",
    order=1,
)

print(f"Earth→Moon rotation: {len(rotation['Rotation'])} values")
```

The example only demonstrates the request style and response structure; it does not mean that the numeric semantics of the Earth→Moon quaternion have been verified.

## Minor-planet MPC ephemeris

### `celestial.mpc_ephemeris`

```python
celestial.mpc_ephemeris(
    *,
    target_name: str,
    observer_frame: str | None = None,
    start: str | None = None,
    stop: str | None = None,
) -> dict[str, Any]
```

Queries an MPC minor-planet ephemeris by asteroid name or number and returns a raw JSON response dictionary.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `target_name` | `TargetName` | Asteroid name or number, e.g. `Ceres`, `99942` |
| `observer_frame` | `ObserverFrame` | Heliocentric frame, server options `FIXED`, `INERTIAL`, `MeanEclpJ2000`, `J2000`, default `MeanEclpJ2000` |
| `start` | `Start` | Start time (UTC); defaults to the orbital epoch and cannot be earlier than the orbital epoch (server rule) |
| `stop` | `Stop` | Stop time (UTC); defaults to 1 year after `Start` |

This route fetches orbital elements from the external MPC data source (element epoch in MJD TDT), which the server propagates heliocentrically with a fixed 1-day step, and outputs a heliocentric CZML Position structure. The response contains `OrbitElements` (orbital elements with keys `EpochMjdTdt`, `PeriTimeMjdTdt`, `Q`, `SemimajorAxis`, `Eccentricity`, `Inclination`, `Raan`, `ArgOfPeriapsis`, `MeanAnomaly`) and `Position` (CZML structure, same as `ephemeris`). The orbital-element values come from external MPC data, are owned by that external data source, and may change with MPC updates. When `start`/`stop` are omitted, the server uses the orbital-epoch default window (`start` is the orbital epoch and `stop` is one year after it); an explicit fixed window depends on the orbital epoch at query time, and once the external MPC orbital epoch updates, a previously fixed window may fall before the new epoch and be rejected by the server, so prefer omitting the window parameters or following the current epoch.

```python
mpc = celestial.mpc_ephemeris(target_name="Ceres")

print(f"Ceres MPC ephemeris: {len(mpc['Position']['cartesianVelocity']) // 7} state samples")
```

## Minor-planet MPC orbital elements

### `celestial.mpc_orbital_elements` and `celestial.MpcOrbitalElements`

```python
celestial.mpc_orbital_elements(
    *,
    epoch_mjd_tdt: float | None = None,
    periapsis_time_mjd_tdt: float | None = None,
    periapsis_distance_au: float | None = None,
    semi_major_axis_au: float | None = None,
    eccentricity: float | None = None,
    inclination_deg: float | None = None,
    raan_deg: float | None = None,
    argument_of_periapsis_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
) -> MpcOrbitalElements
```

Builds a heliocentric MPC orbital-element fragment. When either the departure or arrival endpoint is an asteroid, pass the fragment to the corresponding `departure_elements` or `arrival_elements` argument of `lambert_transfer_window`. The factory function returns the immutable (frozen) named dataclass `celestial.MpcOrbitalElements`; all fields are optional, and fields that are not supplied do not appear in the `to_wire()` fragment. The SDK only performs the type checks required for lowering (fields must be numeric) and does not perform physical-validity validation.

| Field | Wire key | Unit |
| --- | --- | --- |
| `epoch_mjd_tdt` | `EpochMjdTdt` | MJD TDT |
| `periapsis_time_mjd_tdt` | `PeriTimeMjdTdt` | MJD TDT |
| `periapsis_distance_au` | `Q` | AU |
| `semi_major_axis_au` | `SemimajorAxis` | AU |
| `eccentricity` | `Eccentricity` | — |
| `inclination_deg` | `Inclination` | deg |
| `raan_deg` | `Raan` | deg |
| `argument_of_periapsis_deg` | `ArgOfPeriapsis` | deg |
| `mean_anomaly_deg` | `MeanAnomaly` | deg |

```python
from astrox import celestial

elements = celestial.mpc_orbital_elements(
    epoch_mjd_tdt=61000.0,
    periapsis_time_mjd_tdt=60900.0,
    periapsis_distance_au=0.6740515,
    semi_major_axis_au=0.9898367,
    eccentricity=0.3190276,
    inclination_deg=0.79379,
    raan_deg=209.81829,
    argument_of_periapsis_deg=100.88187,
    mean_anomaly_deg=120.0,
)

print(elements.to_wire())
```

`to_wire()` returns the ASTROX `MpcOrbElements` request fragment; the example above prints `{'EpochMjdTdt': 61000.0, 'PeriTimeMjdTdt': 60900.0, 'Q': 0.6740515, 'SemimajorAxis': 0.9898367, 'Eccentricity': 0.3190276, 'Inclination': 0.79379, 'Raan': 209.81829, 'ArgOfPeriapsis': 100.88187, 'MeanAnomaly': 120.0}`. When passed to `lambert_transfer_window`, the server propagates heliocentrically directly with these elements and no longer queries MPC over the network. The independent Kepler propagation of explicit elements is unverified: the element system, reference frame, and time convention are not confirmed, so verify their meaning yourself before use.

## Lambert transfer windows

### `celestial.lambert_transfer_window`

```python
celestial.lambert_transfer_window(
    *,
    departure_body: str,
    arrival_body: str,
    departure_start: str,
    departure_stop: str,
    arrival_start: str,
    arrival_stop: str,
    sun_frame: str | None = None,
    min_time_of_flight_days: int | None = None,
    departure_step_days: float | None = None,
    arrival_step_days: float | None = None,
    departure_elements: MpcOrbitalElements | None = None,
    arrival_elements: MpcOrbitalElements | None = None,
) -> dict[str, Any]
```

Samples over the departure time window and the arrival time window, computes Lambert transfers between bodies, and returns a raw JSON response dictionary. It is not the single-case `orbits.lambert_delta_v` interface: that function takes two `CartesianState` values and a `time_of_flight_s`, calls `/orbit/lambert`, and returns the two triples `(DV1, DV2)`; this function scans the whole grid of departure/arrival time pairs and returns a `TransferResults` list.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `departure_body` | `DepartureCbName` | Departure body name (planet or asteroid), e.g. `Earth` |
| `arrival_body` | `ArrivalCbName` | Arrival body name (planet or asteroid), e.g. `Mars` |
| `departure_start` | `DepartureInterval` | Departure time window start (UTC); combined with `departure_stop` into `"start/stop"` |
| `departure_stop` | `DepartureInterval` | Departure time window end (UTC) |
| `arrival_start` | `ArrivalInterval` | Arrival time window start (UTC); combined with `arrival_stop` into `"start/stop"` |
| `arrival_stop` | `ArrivalInterval` | Arrival time window end (UTC) |
| `sun_frame` | `SunFrameName` | Heliocentric frame, server options `MeanEclpJ2000`, `ICRF`, default `MeanEclpJ2000` |
| `min_time_of_flight_days` | `MinTofDays` | Minimum transfer time, in d, integer; server default 10 |
| `departure_step_days` | `DepartureStepDay` | Departure time sample step, in d; server default 1 |
| `arrival_step_days` | `ArrivalStepDay` | Arrival time sample step, in d; server default 1 |
| `departure_elements` | `DepartureElements` | MPC orbital elements of the departure asteroid (built with `mpc_orbital_elements`); when omitted, the server queries MPC over the network |
| `arrival_elements` | `ArrivalElements` | MPC orbital elements of the arrival asteroid; when omitted, the server queries MPC over the network |

`departure_body`, `arrival_body`, and the four time strings are the required request fields of this function; `DepartureInterval`/`ArrivalInterval` is a single `"start/stop"` string, e.g. `"2028-06-01T00:00:00Z/2028-06-03T00:00:00Z"`. Other optional parameters that are not supplied are not sent to ASTROX, and the server retains its default values.

```python
from astrox import celestial

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
)

results = transfer["TransferResults"]
first = results[0]
print(f"{len(results)} transfer results")
print(
    f"First: {first['DepartureTime']} → {first['ArrivalTime']}, "
    f"|DeltaV1|={first['DV1_Mag']:.1f} m/s, |DeltaV2|={first['DV2_Mag']:.1f} m/s"
)
```

The response contains `TransferResults` (an array of transfer results; each element corresponds to one sampled departure/arrival time pair, and the number of results is determined jointly by the two time windows and the sample steps). Each result has the following keys:

| Key | Type | Unit / description |
| --- | --- | --- |
| `DepartureTime` / `ArrivalTime` | string | Departure/arrival time (UTC string) |
| `DeltaV1` / `DeltaV2` | number[3] | Departure/arrival velocity-increment vector, m/s |
| `DV1_Mag` / `DV2_Mag` | number | Departure/arrival velocity-increment magnitude, m/s; verified to be the Euclidean norm of the corresponding `DeltaV` vector |
| `RV1` / `RV2` | number[6] | Position and velocity at departure/arrival (heliocentric) `[x, y, z, vx, vy, vz]`, positions m, velocities m/s |

Verified (supported by independent cross-validation): with `sun_frame="ICRF"`, on the maintained Earth→Mars result grid of 2 departure sample days × 3 arrival sample days, the transfer velocities in `RV1`/`RV2` agree with the independent zero-revolution prograde Lambert solution. Unresolved: the exact coordinate relationship between `MeanEclpJ2000` and ICRF, the physical meaning of `DeltaV` relative to the endpoint-body velocities, and independent Kepler propagation of explicit MPC elements. These branches currently have only request-construction and response-structure evidence, so verify their meaning yourself before use.

## Convention notes

- `ephemeris` `start` and `stop` are optional; when omitted they are not sent to ASTROX and the server selects January 1 to December 31 of the current year as the window.
- Each `cartesianVelocity` sample is `[Time, X, Y, Z, dX, dY, dZ]`, with `Time` in seconds from the reference epoch, positions in m, and velocities in m/s.
- `cb_axes_rotation` passes the integer `order` through as-is; the `Rotation` length corresponds to `order` (`0` → 4, `1` → 7).
- `mpc_ephemeris` relies on the server's orbital-epoch default window when `start`/`stop` are omitted; an explicit fixed window may expire when the external MPC orbital epoch updates.
- The returns of all four functions on this page have the transport-level `IsSuccess` and `Message` removed, and the remaining server fields are preserved; errors are still raised by the HTTP layer (see error handling).
- `lambert_transfer_window` combines `departure_start`/`departure_stop` and `arrival_start`/`arrival_stop` into the `"start/stop"` strings of `DepartureInterval`/`ArrivalInterval` respectively.
- `mpc_orbital_elements` only performs the type checks required for lowering and does not perform physical-validity validation; fields that are not supplied do not appear in the `to_wire()` fragment.
- Optional parameters that are not supplied are not sent to ASTROX; the server retains its default values.
- Validation evidence is recorded on the [celestial validation page](../../../../validation/celestial.md).

A complete runnable example is available at `examples/11_celestial/celestial_queries.py`.

## Error handling

When ASTROX returns an unsuccessful response or the network request fails, the functions in this module raise `astrox.exceptions.AstroxAPIError`. The SDK does not rewrite server error messages. When you need full control over the request payload or want to handle the raw response, use `astrox.raw.post`.
