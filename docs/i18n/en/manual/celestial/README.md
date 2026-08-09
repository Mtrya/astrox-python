# Celestial Ephemeris and Axes Rotation

`astrox.celestial` provides read-only query APIs for celestial ephemeris and central-body axes rotation: `celestial.ephemeris` computes an ephemeris for a target body over an explicit time window, `celestial.cb_axes_rotation` computes the rotation between the coordinate axes of two central bodies, and `celestial.mpc_ephemeris` computes minor-planet (MPC data) ephemerides. The recommended import style is:

```python
from astrox import celestial
```

All three functions send HTTP POST requests through `astrox.raw.post` and return ASTROX raw JSON response dictionaries without typed response parsing. Ephemeris output uses the CZML Position structure: position and velocity are packed in the `cartesianVelocity` array, with each sample being 7 numeric values `[Time, X, Y, Z, dX, dY, dZ]`, where `Time` is the offset in seconds from the reference epoch, positions are in m, and velocities are in m/s. The response declares the coordinate central body in `Position.CentralBody` and the reference frame in `referenceFrame`; the SDK only relays the response's own declarations and makes no claim about the absolute correctness of the server's internal ephemeris kernel.

## Target-body ephemeris

### `celestial.ephemeris`

```python
celestial.ephemeris(
    *,
    target_name: str,
    start: str,
    stop: str,
    observer_name: str | None = None,
    observer_frame: str | None = None,
    step_s: float | None = None,
) -> dict[str, Any]
```

Computes an ephemeris for a target body over an explicit time window and returns a raw JSON response dictionary.

| Parameter | Wire parameter | Description |
| --- | --- | --- |
| `target_name` | `TargetName` | Target body name, e.g. `Moon`, `Mars` (the server supports `Moon`, `Mars`, `Venus`, `Mercury`, `Jupiter`, `Saturn`, `Uranus`, `Neptune`, and others) |
| `start` | `Start` | Analysis start time (UTC, `yyyy-MM-ddTHH:mm:ssZ`). Explicitly required on the curated surface; the server default is January 1 of the current year, but passing an explicit window is the supported usage |
| `stop` | `Stop` | Analysis stop time (UTC). Explicitly required on the curated surface; the server default is December 31 of the current year |
| `observer_name` | `ObserverName` | Observer name, e.g. `Earth`; the server default is `Sun` |
| `observer_frame` | `ObserverFrame` | Observer frame, server options `FIXED`, `INERTIAL`, `MeanEclpJ2000`, `J2000`, default `MeanEclpJ2000` |
| `step_s` | `Step` | Sample step, in s, server default 86400 s |

`start` and `stop` are the only two required request fields of this function; optional fields that are not supplied are not sent to ASTROX and the server retains its default values.

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
    print(f"Moon {frame}: {ephemeris['IsSuccess']}, {len(samples) // 7} state samples")
```

The response contains `IsSuccess`, `Message`, `Position`, and `Period` (orbital period, unit s per the server documentation). The `Position` keys are `CentralBody`, `referenceFrame`, `epoch`, `interval`, `interpolationAlgorithm`, `interpolationDegree`, and `cartesianVelocity`; the number of samples depends on `Step` and the window length.

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

`order` is preserved as an integer and lowered to the server as-is; the SDK does not rewrite the branch. The `Rotation` field of the response is a numeric array: with `order=0` it has length 4 (quaternion `[qx, qy, qz, qw]`), and with `order=1` it has length 7 (quaternion plus angular-velocity components, unit rad/s per the server documentation). For the same central body on both sides with `INERTIAL` frames on both sides, the server returns the identity quaternion with zero angular velocity; transformation values for arbitrary central-body/frame combinations are outside the SDK-maintained scope, so verify their meaning yourself before use.

```python
rotation = celestial.cb_axes_rotation(
    from_central_body="Earth",
    to_central_body="Moon",
    epoch="2026-01-01T00:00:00.000Z",
    from_frame="INERTIAL",
    to_frame="INERTIAL",
    order=1,
)

print(f"Earth→Moon rotation: {rotation['IsSuccess']}, {len(rotation['Rotation'])} values")
```

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

This route fetches orbital elements from the external MPC data source (element epoch in MJD TDT), which the server propagates heliocentrically with a fixed 1-day step, and outputs a heliocentric CZML Position structure. The response contains `IsSuccess`, `Message`, `OrbitElements` (orbital elements with keys `EpochMjdTdt`, `PeriTimeMjdTdt`, `Q`, `SemimajorAxis`, `Eccentricity`, `Inclination`, `Raan`, `ArgOfPeriapsis`, `MeanAnomaly`), and `Position` (CZML structure, same as `ephemeris`). The orbital-element values come from external MPC data, are owned by that external data source, and may change with MPC updates; choose query windows after the asteroid's orbital epoch, because windows earlier than the orbital epoch may be rejected by the server.

```python
mpc = celestial.mpc_ephemeris(
    target_name="Ceres",
    start="2026-01-01T00:00:00.000Z",
    stop="2026-01-02T00:00:00.000Z",
)

print(f"Ceres MPC ephemeris: {mpc['IsSuccess']}, {mpc['Message']}")
```

## Convention notes

- `ephemeris` requires `start` and `stop` explicitly on the curated surface and does not rely on the server's annual default window.
- Each `cartesianVelocity` sample is `[Time, X, Y, Z, dX, dY, dZ]`, with `Time` in seconds from the reference epoch, positions in m, and velocities in m/s.
- `cb_axes_rotation` passes the integer `order` through as-is; the `Rotation` length corresponds to `order` (`0` → 4, `1` → 7).
- Optional parameters that are not supplied are not sent to ASTROX; the server retains its default values.
- Validation evidence is recorded on the [celestial validation page](../../../../validation/celestial.md).

A complete runnable example is available at `examples/11_celestial/celestial_queries.py`.

## Error handling

When ASTROX returns an unsuccessful response or the network request fails, the functions in this module raise `astrox.exceptions.AstroxAPIError`. The SDK does not rewrite server error messages. When you need full control over the request payload or want to handle the raw response, use `astrox.raw.post`.
