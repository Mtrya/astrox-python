# OpenAPI Fixture Matrix Handoff

This handoff summarizes the PR 10 cross-product matrix work for downstream SDK
implementation. It is intentionally about wire-shape evidence only. It does not
upgrade any matrix to semantic, numerical, or ergonomic SDK compatibility.

## Validation Snapshot

Local validation on 2026-05-13:

- fixture endpoint records: 70
- handled nominal endpoint fixtures: 68
- handled branch-axis fixture records: 307
- live verifier branches: 371
- `uv run python scripts/openapi_fixtures/verify.py`: 371 ok, 0 failed
- `uv run python -m pytest -q tests/test_openapi_fixtures.py`: 43 passed
- `uv run python -m pytest -q tests`: 81 passed

GitHub Actions inspection:

- Latest available `CI` run on `main` at
  `e4bac20fa7940b69ff3c6a08edcd705efca8ed31` passed.
- Latest available scheduled `OpenAPI Fixtures` run on `main` at
  `d6ac384d61443472ed45b731d7b5eb2c86ce7583` passed.
- No pull request or remote CI run was available for local branch
  `openapi-fixture-cross-product-matrices` at this handoff.

## Matrix Contract

`representative N + M` coverage means every row context and every column value
has at least one checked fixture branch. It does not mean every row x column
cell is compatible.

Downstream code must not infer untested cross-products from representative
fixtures. If a wrapper wants to promise a specific combination, add or reuse a
fixture for that exact endpoint/context/cell first.

## Resolved Representative Matrices

### AccessComputeV2 Position Pairs

Rows are `FromObjectPath.Position.$type` values. Columns are
`ToObjectPath.Position.$type` values.

The fixtures cover every discovered From variant once and every To variant once
using stable opposite-side defaults. This is `N + M` evidence, not full
`From x To` coverage.

Do not assume that arbitrary pairs such as `HPOP -> Ballistic`,
`CzmlPosition -> SimpleAscent`, or other unlisted pair cells work.

### AccessComputeV2 Entity Options

Rows are Access sides: `FromObjectPath` and `ToObjectPath`. Columns are option
values across orientation, sensor, sensor pointing, constraints, lighting, and
occultation bodies.

The fixtures cover both sides and every discovered option value at least once.
Some values are checked on one side only, and some branches are stable
failure-only wire shapes.

Do not assume every side x option value cell works. Do not assume option-family
cross-products such as orientation plus sensor plus constraints unless a
fixture records that exact payload.

### ChainCompute AllObjects

The row context is the `AllObjects` entity consumer. Columns are Position,
Orientation, Sensor, SensorPointing, Constraints, Lighting, and
OccultationBodies option values.

The fixtures cover representative option values on the current shortest
ChainCompute payload. This does not prove arbitrary chain topology,
multi-object group behavior, or option-family cross-products.

### Lighting Endpoint x Position

Lighting fixtures are endpoint-specific. `/Lighting/LightingTimes` and
`/Lighting/SolarIntensity` both have checked Position branches for the listed
Position variants, including advanced variants.

This is stronger than the PR 10 `N + M` minimum inside the Lighting family, but
it does not make those Position payloads reusable for Access, Coverage,
Astrogator, ChainCompute, or any other endpoint family.

### Coverage Grid And Asset Rows

Coverage grid evidence is representative:

- `/Coverage/GetGridPoints` covers all four grid variants.
- `/Coverage/ComputeCoverage` covers all four grid variants.
- FOM GridStats, FOM GridStatsOverTime, FOM ValueByGridPoint,
  FOM ValueByGridPointAtTime, and Coverage report rows are represented by their
  checked `LatitudeBounds` fixtures.

Coverage asset evidence is representative:

- `/Coverage/ComputeCoverage` carries the option-value evidence for Position,
  Orientation, Sensor, SensorPointing, Constraints, Lighting, and
  OccultationBodies.
- FOM GridStats, FOM GridStatsOverTime, FOM ValueByGridPoint,
  FOM ValueByGridPointAtTime, and Coverage report rows each have one checked
  non-default `Assets.Position.$type=TwoBody` representative.

Do not assume every Coverage/FOM/report endpoint accepts every grid or asset
option. In particular, FOM/report rows do not inherit the full
`ComputeCoverage` asset option set.

## Still Blocked Or Unverified

The following are intentionally not resolved by PR 10 representative matrix
coverage:

- Full `N x M` cells for Access position pairs.
- Full side x option x position combinations for Access.
- Full chain topology, multi-object, and option-family combinations for
  ChainCompute.
- Full Coverage endpoint x grid and endpoint x asset option cells.
- FOM ResponseTime blockers already recorded in `STATUS.md`.
- Non-matrix nominal blockers such as `/Rocket/RocketGuid`,
  `/InterfaceClass`, `/OrbitSystem/CentralBodyFrame`, and multipart archive
  upload.

Any downstream wrapper should expose these as raw or explicitly caveated
surfaces until exact fixture evidence exists.
