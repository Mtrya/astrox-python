# Position Payload Patterns

This note records reusable `Position.$type` payload shapes for future fixture
work. These are patterns, not global coverage claims: each endpoint still needs
its own live fixture before `STATUS.md` can mark that endpoint branch handled.

Source evidence:

- OpenAPI schema `IEntityPosition` / `IEntityPosition2` declares the same
  discriminator property, `$type`, and maps eleven position variants.
- OpenAPI component schemas list required fields for the phase-1 variants:
  `IEntityPositionEntityPositionSite`, `IEntityPositionEntityPositionJ2`,
  `IEntityPositionEntityPositionSGP4`, and
  `IEntityPositionEntityPositionTwoBody`.
- Live probes on 2026-05-13 against `/Lighting/SolarIntensity` returned
  `HTTP 200`, `IsSuccess=true`, and non-empty `Datas` arrays for the four
  patterns below. The checked-in endpoint-scoped evidence is
  `openapi/fixtures/lighting/solar_intensity.yaml`.
- Live probes on 2026-05-13 against `/Lighting/LightingTimes` returned
  `HTTP 200`, `IsSuccess=true`, and interval/duration response objects for the
  same four patterns. The checked-in endpoint-scoped evidence is
  `openapi/fixtures/lighting/lighting_times.yaml`.

## Shared Rules

- Include `$type` exactly as documented by the OpenAPI discriminator mapping.
- For Access and Lighting probes with a top-level analysis window, omit nested
  `Start` / `Stop` from J2, SGP4, and TwoBody positions unless an
  endpoint-specific fixture needs explicit ephemeris bounds.
- Do not rely on OpenAPI defaults for required fields; include the required
  fields explicitly in fixtures.
- Do not assume a pattern accepted by one endpoint is accepted everywhere.

## SitePosition

Required by OpenAPI:

- `$type: SitePosition`
- `cartographicDegrees`

Observed reusable payload:

```yaml
Position:
  $type: SitePosition
  CentralBody: Earth
  cartographicDegrees:
    - 120.0
    - 31.0
    - 10.0
```

`/Lighting/SolarIntensity` returns site-shaped data items for this branch,
including `ApparentSolarAzimuth`, `ApparentSolarElevation`, and
`TerrainElevation`.

## J2

Required by OpenAPI:

- `$type: J2`
- `OrbitEpoch`
- `OrbitalElements`

Observed reusable payload:

```yaml
Position:
  $type: J2
  Step: 600.0
  OrbitEpoch: "2024-01-01T00:00:00.000Z"
  OrbitalElements:
    - 6778137.0
    - 0.001
    - 28.5
    - 0.0
    - 0.0
    - 0.0
```

## SGP4

Required by OpenAPI:

- `$type: SGP4`
- `TLEs`

Observed reusable payload:

```yaml
Position:
  $type: SGP4
  Step: 600.0
  TLEs:
    - 1 25544U 98067A   21120.54791667  .00001391  00000-0  33245-4 0  9993
    - 2 25544  51.6443 206.1695 0002829  89.9572  27.6891 15.48915315281553
```

For fixture reuse, align the outer endpoint analysis window with the TLE epoch
window unless a later endpoint-specific probe proves a wider window is stable.

## TwoBody

Required by OpenAPI:

- `$type: TwoBody`
- `OrbitEpoch`
- `OrbitalElements`

Observed reusable payload:

```yaml
Position:
  $type: TwoBody
  Step: 600.0
  OrbitEpoch: "2024-01-01T00:00:00.000Z"
  OrbitalElements:
    - 6778137.0
    - 0.001
    - 28.5
    - 0.0
    - 0.0
    - 0.0
```

## Deferred Variants

`AstrogatorMCS`, `HPOP`, `SimpleAscent`, `Ballistic`, `CentralBody`,
`CzmlPositions`, and `CzmlPosition` remain unclaimed here and unchecked in
endpoint `STATUS.md` entries. Some need more context, previously generated
ephemeris-like data, or endpoint-specific semantics before their payloads should
be reused.
