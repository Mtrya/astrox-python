# OpenAPI Fixture Status

This file tracks the fixture corpus for observed ASTROX wire contracts.

Source spec: `openapi/astrox.openapi.yaml`

Current checked-in fixture coverage:

- fixture endpoint records: 70
- handled nominal endpoint fixtures: 68
- handled branch-axis fixtures: 274

Legend:

- `[ ]` not handled by a checked-in fixture yet
- `[x]` handled by a checked-in fixture
- `nominal` means a smallest valid request for the endpoint, without optional
  branch-changing fields unless they are required

This inventory is intentionally more cautious than OpenAPI. A discovered branch
axis is only a candidate until a fixture record actually verifies that the live
server accepts that branch and returns the expected wire shape.

For deferred matrix rows, `representative N + M` means every row context and
every column variant has at least one checked fixture branch. It does not mean
every row x column cell is covered. Any unchecked matrix entry keeps its
unverified cells out of SDK assumptions until a fixture records the exact
endpoint context.

## Required Nominal Fixtures

Every endpoint should eventually have at least one `nominal` fixture record.

### Access

- [x] `/access/AccessComputeV2` nominal
- [x] `/access/ChainCompute` nominal

### Astrogator

- [x] `/Astrogator/RunMCS` nominal

### CAT

- [x] `/CAT/CA_ComputeV3` nominal
- [x] `/CAT/CA_ComputeV4` nominal
- [x] `/CAT/DebrisBreakup` nominal
- [x] `/CAT/DebrisBreakupNASA` nominal
- [x] `/CAT/DebrisBreakupSimple` nominal
- [x] `/CAT/GetTLE` nominal
- [x] `/CAT/LifeTimeTLE` nominal

### Coverage

- [x] `/Coverage/ComputeCoverage` nominal
- [x] `/Coverage/FOM/GridStats/CoverageTime` nominal
- [x] `/Coverage/FOM/GridStats/NumberOfAssets` nominal
- [x] `/Coverage/FOM/GridStats/ResponseTime` nominal
- [x] `/Coverage/FOM/GridStats/RevisitTime` nominal
- [x] `/Coverage/FOM/GridStats/SimpleCoverage` nominal
- [x] `/Coverage/FOM/GridStatsOverTime/NumberOfAssets` nominal
- [ ] `/Coverage/FOM/GridStatsOverTime/ResponseTime` nominal
  - blocked: small Coverage base payload plus targeted `Time`, longer-window,
    `ComputeType=Maximum`, and two-asset corrections return empty HTTP 500
    with no content type. Reprobed on 2026-05-13 with the current base payload.
- [x] `/Coverage/FOM/GridStatsOverTime/RevisitTime` nominal
- [x] `/Coverage/FOM/GridStatsOverTime/SimpleCoverage` nominal
- [x] `/Coverage/FOM/ValueByGridPoint/CoverageTime` nominal
- [x] `/Coverage/FOM/ValueByGridPoint/NumberOfAssets` nominal
- [x] `/Coverage/FOM/ValueByGridPoint/ResponseTime` nominal
- [x] `/Coverage/FOM/ValueByGridPoint/RevisitTime` nominal
- [x] `/Coverage/FOM/ValueByGridPoint/SimpleCoverage` nominal
- [x] `/Coverage/FOM/ValueByGridPointAtTime/NumberOfAssets` nominal
- [ ] `/Coverage/FOM/ValueByGridPointAtTime/ResponseTime` nominal
  - blocked: endpoint requires `Time`, but valid-looking `Time` payloads
    return empty HTTP 500 with no content type. Reprobed on 2026-05-13 with
    baseline, `ComputeType=Maximum`, longer-window, and two-asset payloads.
- [x] `/Coverage/FOM/ValueByGridPointAtTime/RevisitTime` nominal
- [x] `/Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage` nominal
- [x] `/Coverage/GetGridPoints` nominal
- [x] `/Coverage/Report/CoverageByAsset` nominal
- [x] `/Coverage/Report/PercentCoverage` nominal

### Interface

- [ ] `/InterfaceClass` nominal
  - blocked: empty and single-fragment probes return structured HTTP 400
    validation responses listing the current required `InterfaceInput`
    properties. A generated schema-shaped payload covering all 53 current
    top-level `InterfaceInput` properties reaches endpoint execution but still
    returns an empty HTTP 500 with no content type. Reprobed on 2026-05-13.

### Landing Zone

- [x] `/LandingZone` nominal

### Lighting

- [x] `/Lighting/LightingTimes` nominal
- [x] `/Lighting/SolarAER` nominal
- [x] `/Lighting/SolarIntensity` nominal

### Orbit Convert

- [x] `/OrbitConvert/CalGEOYMLambertDv` nominal
- [x] `/OrbitConvert/GetKozaiIzsakMeanElements` nominal
- [x] `/OrbitConvert/Kepler2LLAAtAscendNode` nominal
- [x] `/OrbitConvert/Kepler2RV` nominal
- [x] `/OrbitConvert/RV2Kepler` nominal

### Orbit System

- [ ] `/OrbitSystem/CentralBodyFrame` nominal
  - blocked: endpoint requires `toCb` and `referenceFrame` as POST query
    parameters, which the current fixture format cannot express for a
    route/body fixture. A manual query-param probe with a minimal
    `EntityPositionCzml3` body returns only a structured failure object.
- [x] `/OrbitSystem/EarthMoonLibration` nominal failure-only wire shape
- [x] `/OrbitSystem/EarthMoonLibration2` nominal failure-only wire shape

### Orbit Wizard

- [x] `/OrbitWizard/GEO` nominal
- [x] `/OrbitWizard/Molniya` nominal
- [x] `/OrbitWizard/SSO` nominal
- [x] `/OrbitWizard/Walker` nominal

### Propagator

- [x] `/Propagator/Ballistic` nominal
- [x] `/Propagator/HPOP` nominal
- [x] `/Propagator/J2` nominal
- [x] `/Propagator/MultiJ2` nominal
- [x] `/Propagator/MultiSgp4` nominal
- [x] `/Propagator/MultiTwoBody` nominal
- [x] `/Propagator/SimpleAscent` nominal
- [x] `/Propagator/TwoBody` nominal
- [x] `/Propagator/sgp4` nominal

### Rocket

- [ ] `/Rocket/RocketGuid` nominal
  - blocked: all documented root `$type` values (`CZ2CD`, `KZ1A`,
    `CZ7A`, `CZ3BC`, `CZ4BC`) return empty HTTP 500 responses with no content
    type for minimal payload probes. An example-derived `CZ3BC` payload also
    returns empty HTTP 500. Invalid discriminator values return structured HTTP
    400, so the server recognizes the documented discriminator names before
    failing inside endpoint execution. Reprobed on 2026-05-13.
- [x] `/Rocket/RocketLanding` nominal failure-only wire shape
- [x] `/Rocket/RocketSegmentFA` nominal failure-only wire shape

### Terrain

- [x] `/Terrain/AzElMask` nominal failure-only wire shape
- [x] `/Terrain/AzElMaskSimple` nominal failure-only wire shape

### Celestial

- [x] `/celestial/ephemeris` nominal
- [x] `/celestial/mpc` nominal
- [x] `/celestial/transfer` nominal
- [x] `/orbit/lambert` nominal

### Catalog and Database GET/File Endpoints

- [x] `/WeatherForecast` nominal
- [x] `/city` nominal
- [x] `/facility` nominal
- [x] `/satcat` nominal
- [x] `/ssc` nominal
- [ ] `/ssc/admin/upload-database-archive` nominal
  - blocked: real nominal upload requires `multipart/form-data`, `X-Api-Key`,
    and a ZIP archive. The current verifier cannot express multipart files or
    headers, and public fake-key multipart probes return structured HTTP 401.
  - [x] public `missing_file_and_api_key` validation error

### Other

- [x] `/ziyou` nominal

## Shared Branch Value Vocabulary

These are branch values that appear in multiple endpoint schemas. They are an
inventory, not coverage status: checkboxes only appear under concrete endpoint
or endpoint-family axes below. A value listed here is not reusable handled
coverage until a checked-in fixture verifies it in the specific endpoint context
where it is claimed.

### Position Variants

- `Position.$type=J2`
- `Position.$type=SitePosition`
- `Position.$type=AstrogatorMCS`
- `Position.$type=HPOP`
- `Position.$type=SimpleAscent`
- `Position.$type=Ballistic`
- `Position.$type=SGP4`
- `Position.$type=CentralBody`
- `Position.$type=CzmlPositions`
- `Position.$type=CzmlPosition`
- `Position.$type=TwoBody`

### Coverage Grid Variants

- `Grid.$type=CbLatLonBounds`
- `Grid.$type=Global`
- `Grid.$type=LatitudeBounds`
- `Grid.$type=LatLonBounds`

### Coverage Sensor Variants

- `GridPointSensor.$type=Conic`
- `GridPointSensor.$type=Rectangular`

### Coverage Constraint Variants

- `GridPointConstraints.$type=AzElMask`
- `GridPointConstraints.$type=Range`
- `GridPointConstraints.$type=ElevationAngle`

### Entity Orientation Variants

- `Orientation.$type=FixedAtEpoch`
- `Orientation.$type=Composite`
- `Orientation.$type=Fixed`
- `Orientation.$type=VNC`
- `Orientation.$type=AlignedAndConstrained`
- `Orientation.$type=LVLH`
- `Orientation.$type=VVLH`
- `Orientation.$type=CzmlOrientation`

### Entity Sensor Variants

- `Sensor.$type=Conic`
- `Sensor.$type=Rectangular`

### Sensor Pointing Variants

- `SensorPointing.$type=Fixed`

### Stopping Condition Variants

- `StopCondition.$type=Apoapsis`
- `StopCondition.$type=Duration`
- `StopCondition.$type=Epoch`
- `StopCondition.$type=Periapsis`
- `StopCondition.$type=Scalar`

### State Element Variants

- `Element.$type=Cartesian`
- `Element.$type=Keplerian`
- `Element.$type=Spherical`

### Attitude Control Variants

- `AttitudeControl.$type=AntiVelocityVector`
- `AttitudeControl.$type=Attitude`
- `AttitudeControl.$type=VelocityVector`
- `AttitudeControl.$type=ThrustVector`

### CalcScalar Variants

- `CalcScalar.$type=BPlane`
- `CalcScalar.$type=Epoch`
- `CalcScalar.$type=Relative`
- `CalcScalar.$type=Duration`
- `CalcScalar.$type=Cartographic`
- `CalcScalar.$type=SphericalElement`
- `CalcScalar.$type=DeltaSpherical`
- `CalcScalar.$type=ModifiedKeplerianElement`
- `CalcScalar.$type=PointElement`
- `CalcScalar.$type=KeplerianElement`

## Endpoint Branch Axes

### `/Astrogator/RunMCS`

- [x] `MainSequence.$type=Sequence`
- [x] `MainSequence.$type=Follow` failure-only wire shape
  - reprobed on 2026-05-13: minimal `Follow` plus targeted `Entities` leader
    probes using SitePosition, CzmlPosition, J2, and AstrogatorMCS-shaped
    positions returns a structured `IsSuccess=false` response before creating a
    follow point, so this covers constructor failure shape only.
- [x] `MainSequence.$type=ManeuverFinite`
- [x] `MainSequence.$type=ManeuverImpulsive`
- [x] `MainSequence.$type=InitialState`
- [x] `MainSequence.$type=TargetSequence`
  - reprobed on 2026-05-13: an inactive DifferentialCorrector profile with a
    nominal segment list returns `TargetSequenceResult`; minimal/no-profile and
    active-profile probes still return internal `Operators`/`Variables`
    empty-list errors, so target convergence semantics remain unverified.
- [x] `MainSequence.$type=Propagate`
- [x] `MainSequence.$type=Stop`
Result branches below verify accepted request/response wire shape on a minimal
`InitialState` segment. They do not assert that every selector yields a
non-empty named result in that minimal context.

- [ ] `MainSequence.Results.$type=BPlane`
  - blocked: reprobed on 2026-05-13. Minimal `InitialState` BPlane returns
    empty HTTP 500 with no content type; `Propagate` BPlane returns empty HTTP
    200 with no content type, so neither response is fixture-worthy.
- [x] `MainSequence.Results.$type=Epoch`
- [x] `MainSequence.Results.$type=Relative`
- [x] `MainSequence.Results.$type=Duration`
- [x] `MainSequence.Results.$type=Cartographic`
- [x] `MainSequence.Results.$type=SphericalElement`
- [x] `MainSequence.Results.$type=DeltaSpherical`
- [x] `MainSequence.Results.$type=ModifiedKeplerianElement`
- [x] `MainSequence.Results.$type=PointElement`
- [x] `MainSequence.Results.$type=KeplerianElement`

- [x] `MainSequence.StopConditions.$type=Duration`
- [x] `MainSequence.StopConditions.$type=Epoch`
- [x] `MainSequence.StopConditions.$type=Apoapsis`
- [x] `MainSequence.StopConditions.$type=Periapsis`
- [x] `MainSequence.StopConditions.$type=Scalar` failure-only wire shape

- [ ] `MainSequence.JoiningConditions.$type.*` covers all stopping condition variants
  - blocked: reprobed on 2026-05-13. `Follow` now has a structured
    failure-only fixture, but `Joining=Specify` plus Duration and targeted
    SitePosition, CzmlPosition, J2, and AstrogatorMCS leader probes still fail
    before `JoiningConditions` are evaluated.

Attitude-control branches below are standalone `ManeuverImpulsive` probes. They
do not claim every finite/impulsive maneuver context accepts every attitude
payload shape.

- [x] `MainSequence.AttitudeControl.$type=AntiVelocityVector`
- [x] `MainSequence.AttitudeControl.$type=Attitude`
- [x] `MainSequence.AttitudeControl.$type=VelocityVector`
- [x] `MainSequence.AttitudeControl.$type=ThrustVector`

- [x] `MainSequence.InitialState.Element.$type=Cartesian`
- [x] `MainSequence.InitialState.Element.$type=Keplerian`
- [x] `MainSequence.InitialState.Element.$type=Spherical`
The `Entities.Position.*` branches below are standalone nominal-MCS probes.
They do not claim cross-product coverage with `Follow`, constraints, sensors,
or other `MainSequence` variants.

- [x] `Entities.Position.$type=SitePosition`
- [x] `Entities.Position.$type=J2`
- [x] `Entities.Position.$type=SGP4`
- [x] `Entities.Position.$type=TwoBody`
- [x] `Entities.Position.$type=AstrogatorMCS`
- [x] `Entities.Position.$type=HPOP`
- [x] `Entities.Position.$type=SimpleAscent`
- [x] `Entities.Position.$type=Ballistic`
- [x] `Entities.Position.$type=CentralBody`
- [x] `Entities.Position.$type=CzmlPosition`
- [x] `Entities.Position.$type=CzmlPositions`

The entity-context branches below are standalone nominal-MCS probes with a
single `SitePosition` entity unless noted. They do not claim reusable branch
coverage outside `/Astrogator/RunMCS` or cross-product coverage with every
position or sequence subtype.

- [x] `Entities.Orientation.$type=FixedAtEpoch`
- [x] `Entities.Orientation.$type=Composite`
- [x] `Entities.Orientation.$type=Fixed`
- [x] `Entities.Orientation.$type=VNC`
- [x] `Entities.Orientation.$type=AlignedAndConstrained`
- [x] `Entities.Orientation.$type=LVLH`
- [x] `Entities.Orientation.$type=VVLH`
- [x] `Entities.Orientation.$type=CzmlOrientation`
- [x] `Entities.Sensor.$type=Conic`
- [x] `Entities.Sensor.$type=Rectangular`
- [x] `Entities.SensorPointing.$type=Fixed`
- [x] `Entities.Constraints.$type=AzElMask`
- [x] `Entities.Constraints.$type=Range`
- [x] `Entities.Constraints.$type=ElevationAngle`
- [x] `Entities.Lighting=DirectSun`
- [x] `Entities.Lighting=Penumbra`
- [x] `Entities.Lighting=Umbra`
- [x] `Entities.OccultationBodies=explicit`
- [x] `Propagators.NumericalIntegrator.$type=RKF7th8th`
- [x] `Propagators.GravityModel.$type=GravityField`
- [x] `Propagators.GravityModel.$type=TwoBody`
- [x] `Propagators.AtmosphericModel.$type=JacchiaRoberts`
- [x] `Propagators.SRPModel.$type=SRPSpherical`
- [x] `EngineModels.$type=EngineConstAcc`
- [x] `EngineModels.$type=EngineConstant`
  - note: engine model branches are accepted as standalone root `EngineModels`
    entries on the nominal MCS payload. This does not claim all maneuver
    consumers accept every engine model.
- [x] `ComputeCzmlPositions=true`

### `/CAT/CA_ComputeV3`

- [x] `Targets=null` validation-only wire shape
  - note: live `Targets: null` returns structured HTTP 400 validation
    (`Targets` is required), so this does not confirm database-backed lookup.

### `/CAT/CA_ComputeV4`

- [x] `Targets=null` validation-only wire shape
  - note: live `Targets: null` returns structured HTTP 400 validation
    (`Targets` is required), so this does not confirm database-backed lookup.

### `/CAT/DebrisBreakup`

- [x] `ComputeLifeOfTime=true`

### `/CAT/DebrisBreakupSimple`

- [x] `ComputeLifeOfTime=true`

### `/CAT/GetTLE`

- [x] `IsMeanElements=true`

### `/city`

- [x] `typeOfCity=PopulatedPlace`
- [x] `typeOfCity=AdministrationCenter`
- [x] `typeOfCity=NationalCapital`
- [x] `typeOfCity=TerritorialCapital`

### `/celestial/ephemeris`

- [x] `ObserverFrame=FIXED`
- [x] `ObserverFrame=INERTIAL`
- [x] `ObserverFrame=MeanEclpJ2000`
- [x] `ObserverFrame=J2000`

### `/celestial/mpc`

- [x] `ObserverFrame=FIXED`
- [x] `ObserverFrame=INERTIAL`
- [x] `ObserverFrame=MeanEclpJ2000`
- [x] `ObserverFrame=J2000`

### `/celestial/transfer`

- [x] `SunFrameName=MeanEclpJ2000`
- [x] `SunFrameName=ICRF`

### Coverage Family

The following endpoints currently share the same discovered branch axes:

- `/Coverage/ComputeCoverage`
- `/Coverage/FOM/GridStats/CoverageTime`
- `/Coverage/FOM/GridStats/NumberOfAssets`
- `/Coverage/FOM/GridStats/ResponseTime`
- `/Coverage/FOM/GridStats/RevisitTime`
- `/Coverage/FOM/GridStats/SimpleCoverage`
- `/Coverage/FOM/GridStatsOverTime/NumberOfAssets`
- `/Coverage/FOM/GridStatsOverTime/ResponseTime`
- `/Coverage/FOM/GridStatsOverTime/RevisitTime`
- `/Coverage/FOM/GridStatsOverTime/SimpleCoverage`
- `/Coverage/FOM/ValueByGridPoint/CoverageTime`
- `/Coverage/FOM/ValueByGridPoint/NumberOfAssets`
- `/Coverage/FOM/ValueByGridPoint/ResponseTime`
- `/Coverage/FOM/ValueByGridPoint/RevisitTime`
- `/Coverage/FOM/ValueByGridPoint/SimpleCoverage`
- `/Coverage/FOM/ValueByGridPointAtTime/NumberOfAssets`
- `/Coverage/FOM/ValueByGridPointAtTime/ResponseTime`
- `/Coverage/FOM/ValueByGridPointAtTime/RevisitTime`
- `/Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage`
- `/Coverage/Report/CoverageByAsset`
- `/Coverage/Report/PercentCoverage`

Required branch axes are tracked by endpoint context. These rows do not claim
that a branch fixture under one Coverage endpoint is reusable across every
Coverage/FOM/report endpoint. PR 10 matrix work should use representative
row/column evidence unless a row explicitly says full endpoint x option
coverage was verified.

Grid context:

- [ ] Coverage grid matrix representative rows and columns
  - row contexts: `/Coverage/GetGridPoints`, `/Coverage/ComputeCoverage`, FOM
    GridStats, FOM GridStatsOverTime, FOM ValueByGridPoint, FOM
    ValueByGridPointAtTime, and Coverage report endpoints.
  - column variants: `CbLatLonBounds`, `Global`, `LatitudeBounds`, and
    `LatLonBounds`.
  - deferred: `/Coverage/GetGridPoints` has all grid variants checked, but this
    does not prove every Coverage/FOM/report endpoint accepts every grid
    payload.

`/Coverage/ComputeCoverage` asset context:

- [x] `Assets.Position.$type=J2`
- [x] `Assets.Position.$type=TwoBody`
- [x] `Assets.Position.$type=SGP4`
- [ ] `Assets.Position.*` remaining variants (deferred to PR 10 row-class
  matrix work; `SitePosition` reprobe returned a structured `IsSuccess=false`
  response rather than the nominal success shape.)
- [x] `Assets.Orientation.$type=VVLH`
- [x] `Assets.Orientation.$type=LVLH`
- [x] `Assets.Orientation.$type=VNC`
- [ ] `Assets.Orientation.*` remaining variants (deferred to PR 10; complex
  orientation constructors require endpoint-context probes.)
- [x] `Assets.Sensor.$type=Conic`
- [x] `Assets.Sensor.$type=Rectangular`
- [x] `Assets.SensorPointing.$type=Fixed`
- [x] `Assets.Constraints.$type=Range`
- [x] `Assets.Constraints.$type=ElevationAngle`
- [x] `Assets.Constraints.$type=AzElMask` rejection shape for non-ground asset
- [x] `Assets.Lighting=DirectSun`
- [x] `Assets.Lighting=Penumbra`
- [x] `Assets.Lighting=Umbra`
- [x] `Assets.OccultationBodies=explicit`

Deferred Coverage asset matrix row contexts:

- [ ] FOM GridStats asset row context (deferred to PR 10 representative matrix
  work; no fixture in this endpoint class proves the ComputeCoverage asset
  variants are accepted there.)
- [ ] FOM GridStatsOverTime asset row context (deferred to PR 10
  representative matrix work; includes the still-blocked ResponseTime endpoint.)
- [ ] FOM ValueByGridPoint asset row context (deferred to PR 10 representative
  matrix work.)
- [ ] FOM ValueByGridPointAtTime asset row context (deferred to PR 10
  representative matrix work; includes the still-blocked ResponseTime endpoint.)
- [ ] Coverage report asset row context (deferred to PR 10 representative
  matrix work.)
- [x] `GridPointSensor.*` covers all Coverage Sensor Variants
- [x] `GridPointConstraints.*` covers all Coverage Constraint Variants
- [x] `FilterType=AtLeastN`
- [x] `FilterType=ExactlyN`
- [x] `ContainAssetAccessResults=true`
- [x] `ContainCoveragePoints=true`

Additional FOM endpoint branch axes:

- [x] `ComputeType=TotalTimeAbove`
- [x] `ComputeType=Maximum`
- [x] `ComputeType=Minimum`
- [x] `ComputeType=Average`
  - note: `Minimum` and `Average` are checked on representative
    `NumberOfAssets` GridStats and ValueByGridPoint fixtures. This does not
    claim every FOM endpoint accepts every compute type.

### `/Coverage/GetGridPoints`

- [x] `Grid.$type=CbLatLonBounds`
- [x] `Grid.$type=Global`
- [x] `Grid.$type=LatitudeBounds`
- [x] `Grid.$type=LatLonBounds`

### `/InterfaceClass`

Coordinate branches below are validation-boundary fixtures. Minimal
single-coordinate payloads verify live as structured `application/problem+json`
responses because the server requires many unrelated `InterfaceInput`
properties before execution. A generated payload covering all 53 current
top-level `InterfaceInput` properties reaches an empty HTTP 500 with no content
type, so `/InterfaceClass` nominal remains unchecked. Reprobed on 2026-05-13.

- [x] `AgVAAttitudeControlFinite.$type=AntiVelocityVector` validation-only wire shape
- [x] `AgVAAttitudeControlFinite.$type=Attitude` validation-only wire shape
- [x] `AgVAAttitudeControlFinite.$type=VelocityVector` validation-only wire shape
- [x] `AgVAAttitudeControlFinite.$type=ThrustVector` validation-only wire shape
- [x] `AgVAAttitudeControlFiniteAttitude.CoordType=EulerAngles` validation-only wire shape
- [x] `AgVAAttitudeControlFiniteAttitude.CoordType=Quaternion` validation-only wire shape
- [x] `AgVAAttitudeControlFiniteThrustVector.CoordType=Cartesian` validation-only wire shape
- [x] `AgVAAttitudeControlFiniteThrustVector.CoordType=Spherical` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsive.$type=AntiVelocityVector` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsive.$type=Attitude` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsive.$type=VelocityVector` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsive.$type=ThrustVector` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsiveAttitude.CoordType=EulerAngles` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsiveAttitude.CoordType=Quaternion` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsiveThrustVector.CoordType=Cartesian` validation-only wire shape
- [x] `AgVAAttitudeControlImpulsiveThrustVector.CoordType=Spherical` validation-only wire shape
- [x] `AgVAStoppingConditionElement.$type=Apoapsis` validation-only wire shape
- [x] `AgVAStoppingConditionElement.$type=Duration` validation-only wire shape
- [x] `AgVAStoppingConditionElement.$type=Epoch` validation-only wire shape
- [x] `AgVAStoppingConditionElement.$type=Periapsis` validation-only wire shape
- [x] `AgVAStoppingConditionElement.$type=Scalar` validation-only wire shape
- [x] `AgVAElement.$type=Cartesian` validation-only wire shape
- [x] `AgVAElement.$type=Keplerian` validation-only wire shape
- [x] `AgVAElement.$type=Spherical` validation-only wire shape
- [x] `CalcScalar.$type=BPlane` validation-only wire shape
- [x] `CalcScalar.$type=Cartographic` validation-only wire shape
- [x] `CalcScalar.$type=DeltaSpherical` validation-only wire shape
- [x] `CalcScalar.$type=Duration` validation-only wire shape
- [x] `CalcScalar.$type=Epoch` validation-only wire shape
- [x] `CalcScalar.$type=KeplerianElement` validation-only wire shape
- [x] `CalcScalar.$type=ModifiedKeplerianElement` validation-only wire shape
- [x] `CalcScalar.$type=PointElement` validation-only wire shape
- [x] `CalcScalar.$type=Relative` validation-only wire shape
- [x] `CalcScalar.$type=SphericalElement` validation-only wire shape

### `/Lighting/LightingTimes`

Lighting Position branches are endpoint-specific. They do not claim reusable
Position coverage for Access, Coverage, Astrogator, or other endpoint families.

- [x] `Position.$type=SitePosition`
- [x] `Position.$type=J2`
- [x] `Position.$type=SGP4`
- [x] `Position.$type=TwoBody`
- [x] `Position.$type=AstrogatorMCS`
- [x] `Position.$type=HPOP`
- [x] `Position.$type=SimpleAscent`
- [x] `Position.$type=Ballistic`
- [x] `Position.$type=CentralBody`
- [x] `Position.$type=CzmlPositions`
- [x] `Position.$type=CzmlPosition`
- [x] `OccultationBodies=explicit`

### `/Lighting/SolarIntensity`

Lighting Position branches are endpoint-specific. Together with
`/Lighting/LightingTimes`, the current fixtures cover the Lighting endpoint x
Position matrix cells listed below, but no non-Lighting endpoint inherits this
coverage.

- [x] `Position.$type=SitePosition`
- [x] `Position.$type=J2`
- [x] `Position.$type=SGP4`
- [x] `Position.$type=TwoBody`
- [x] `Position.$type=AstrogatorMCS`
- [x] `Position.$type=HPOP`
- [x] `Position.$type=SimpleAscent`
- [x] `Position.$type=Ballistic`
- [x] `Position.$type=CentralBody`
- [x] `Position.$type=CzmlPositions`
- [x] `Position.$type=CzmlPosition`
- [x] `OccultationBodies=explicit`

### `/Propagator/Ballistic`

- [x] `BallisticType=DeltaV`
- [x] `BallisticType=DeltaV_MinEcc`
- [x] `BallisticType=ApogeeAlt`
- [x] `BallisticType=TimeOfFlight`

### `/Propagator/HPOP`

- [x] `HpopPropagator.NumericalIntegrator.$type=RKF7th8th`
- [x] `HpopPropagator.GravityModel.$type=GravityField`
- [x] `HpopPropagator.GravityModel.$type=TwoBody`
- [x] `HpopPropagator.AtmosphericModel.$type=JacchiaRoberts`
- [x] `HpopPropagator.SRPModel.$type=SRPSpherical`
- [x] `HpopPropagator.SRPModel.ShadowModel=DualCone`
- [x] `HpopPropagator.SRPModel.ShadowModel=Cylindrical`
- [x] `HpopPropagator.SRPModel.SunPosition=Apparent`
- [x] `HpopPropagator.SRPModel.SunPosition=True`

### `/OrbitWizard/Walker`

- [x] `WalkerType=Delta`
- [x] `WalkerType=Star`
- [x] `WalkerType=Custom`

### `/Rocket/RocketGuid`

Reprobed on 2026-05-13: invalid discriminator values return structured HTTP 400
`application/problem+json`, while each documented discriminator below still
reaches an empty HTTP 500 with no content type.

- [ ] `$type=CZ2CD` blocked: empty HTTP 500 with no content type.
- [ ] `$type=KZ1A` blocked: empty HTTP 500 with no content type.
- [ ] `$type=CZ7A` blocked: empty HTTP 500 with no content type.
- [ ] `$type=CZ3BC` blocked: empty HTTP 500 with no content type; an
  example-derived `CZ3BC` payload also returns the same empty HTTP 500.
- [ ] `$type=CZ4BC` blocked: empty HTTP 500 with no content type.

### `/Rocket/RocketLanding`

- [x] `IsOptimize=true` failure-only wire shape

Variable array branches are single-slot probes on the known-good
`IsOptimize=true` payload. They do not claim cross-product coverage across
initial, lower-bound, and upper-bound arrays.

- [x] `VariableX0=Phicx20` failure-only wire shape
- [x] `VariableX0=Psicx20` failure-only wire shape
- [x] `VariableX0=Dt2` failure-only wire shape
- [x] `VariableX0=Height4` failure-only wire shape
- [x] `VariableLowerBound=Phicx20` failure-only wire shape
- [x] `VariableLowerBound=Psicx20` failure-only wire shape
- [x] `VariableLowerBound=Dt2` failure-only wire shape
- [x] `VariableLowerBound=Height4` failure-only wire shape
- [x] `VariableUpperBound=Phicx20` failure-only wire shape
- [x] `VariableUpperBound=Psicx20` failure-only wire shape
- [x] `VariableUpperBound=Dt2` failure-only wire shape
- [x] `VariableUpperBound=Height4` failure-only wire shape

### `/Rocket/RocketSegmentFA`

- [x] `UseMcsProfile=true` failure-only wire shape
  - uncertainty: `UseMcsProfile=true` was live-confirmed only as a boolean
    branch on the same schema-shaped payload. The server returns a
    `RocketSegmentFA` static-initializer failure before validating or executing
    `McsProfiles`, so Astrogator/MCS profile payload semantics remain
    unverified and out of scope for this phase.

### `/access/AccessComputeV2`

Position-pair rows are matrix cells already checked by fixtures. The deferred
entry below is for representative `N + M` row/column coverage, not exhaustive
`FromObjectPath.Position x ToObjectPath.Position` coverage.

- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=J2`
- [x] `FromObjectPath.Position.$type=J2 -> ToObjectPath.Position.$type=SitePosition`
- [x] `FromObjectPath.Position.$type=SGP4 -> ToObjectPath.Position.$type=SitePosition`
- [x] `FromObjectPath.Position.$type=TwoBody -> ToObjectPath.Position.$type=SitePosition`
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=SGP4`
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=TwoBody`
- [x] `FromObjectPath.Position.$type=AstrogatorMCS -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=HPOP -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SimpleAscent -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=Ballistic -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=CentralBody -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=CzmlPosition -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=CzmlPositions -> ToObjectPath.Position.$type=SitePosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=AstrogatorMCS`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=HPOP`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=SimpleAscent`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=Ballistic`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=CentralBody`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=CzmlPosition`
  wire-shape only; `Passes` may be empty
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=CzmlPositions`
  wire-shape only; `Passes` may be empty

Representative AccessComputeV2 Position matrix coverage is now `N + M`: every
currently discovered From position row and every To position column has at
least one checked branch. This does not claim every From x To pair works.

Entity option branches below are side/value evidence on the current Access
baseline. They do not claim cross-products with every Position pair, every
other entity option, or both Access sides unless the side/value branch is
listed explicitly.

- [x] `FromObjectPath.Orientation.$type=VVLH`
- [x] `FromObjectPath.Orientation.$type=LVLH`
- [x] `FromObjectPath.Orientation.$type=VNC`
- [x] `FromObjectPath.Orientation.$type=FixedAtEpoch`
- [x] `FromObjectPath.Orientation.$type=Composite`
- [x] `FromObjectPath.Orientation.$type=Fixed`
- [x] `FromObjectPath.Sensor.$type=Conic`
- [x] `FromObjectPath.Sensor.$type=Rectangular`
- [x] `FromObjectPath.SensorPointing.$type=Fixed`
- [x] `FromObjectPath.Constraints.$type=Range`
- [x] `FromObjectPath.Constraints.$type=ElevationAngle`
- [x] `FromObjectPath.Constraints.$type=AzElMask`
- [x] `FromObjectPath.Lighting=DirectSun`
- [x] `FromObjectPath.Lighting=Penumbra`
- [x] `FromObjectPath.Lighting=Umbra`
- [x] `FromObjectPath.OccultationBodies=explicit`
- [x] `ToObjectPath.Orientation.$type=VVLH`
- [x] `ToObjectPath.Orientation.$type=LVLH`
- [x] `ToObjectPath.Orientation.$type=VNC`
- [x] `ToObjectPath.Orientation.$type=AlignedAndConstrained` failure-only wire shape
- [x] `ToObjectPath.Orientation.$type=CzmlOrientation`

Representative AccessComputeV2 entity option matrix coverage is now `N + M`:
both Access sides and every currently discovered Orientation, Sensor,
SensorPointing, Constraints, Lighting, and OccultationBodies option value have
at least one checked branch. This does not claim every side x option value cell
or every option-family combination works.

- [x] `ToObjectPath.Sensor.$type=Conic`
- [x] `ToObjectPath.Sensor.$type=Rectangular`
- [x] `ToObjectPath.SensorPointing.$type=Fixed`
- [x] `ToObjectPath.Constraints.$type=Range`
- [x] `ToObjectPath.Constraints.$type=ElevationAngle`
- [x] `ToObjectPath.Constraints.$type=AzElMask`
- [x] `ToObjectPath.Lighting=DirectSun`
- [x] `ToObjectPath.Lighting=Penumbra`
- [x] `ToObjectPath.Lighting=Umbra`
- [x] `ToObjectPath.OccultationBodies=explicit`
- [x] `ComputeAER=true`
- [x] `UseLightTimeDelay=true`

### `/access/ChainCompute`

`AllObjects` rows are representative endpoint-context branches. They do not
claim full chain topology, multi-object, or option-family cross-product
coverage.

- [x] `AllObjects.$type=EntityPath`
- [x] `AllObjects.$type=EntityPathGroup` failure-only wire shape
- [x] `AllObjects.Position.$type=SitePosition`
- [x] `AllObjects.Position.$type=J2`
- [x] `AllObjects.Position.$type=SGP4`
- [x] `AllObjects.Position.$type=TwoBody`
- [ ] `AllObjects.Position.*` remaining variants deferred: AstrogatorMCS,
  HPOP, SimpleAscent, Ballistic, CentralBody, CzmlPositions, and CzmlPosition
  need endpoint-specific construction work.
- [x] `AllObjects.Orientation.$type=VVLH`
- [x] `AllObjects.Orientation.$type=LVLH`
- [x] `AllObjects.Orientation.$type=VNC`
- [ ] `AllObjects.Orientation.*` remaining constructors deferred:
  FixedAtEpoch, Composite, Fixed, AlignedAndConstrained, and CzmlOrientation
  need endpoint-context probes.
- [x] `AllObjects.Sensor.$type=Conic`
- [x] `AllObjects.Sensor.$type=Rectangular`
- [x] `AllObjects.SensorPointing.$type=Fixed`
- [x] `AllObjects.Constraints.$type=Range`
- [x] `AllObjects.Constraints.$type=ElevationAngle`
- [x] `AllObjects.Constraints.$type=AzElMask`
- [x] `AllObjects.Lighting=DirectSun`
- [x] `AllObjects.Lighting=Penumbra`
- [x] `AllObjects.Lighting=Umbra`
- [x] `AllObjects.OccultationBodies=explicit`
- [x] `EntityPathGroup.FromAccess_Restriction=AnyOf` failure-only wire shape
- [x] `EntityPathGroup.FromAccess_Restriction=AtLeastN` failure-only wire shape
- [x] `EntityPathGroup.ToAccess_Restriction=AnyOf` failure-only wire shape
- [x] `EntityPathGroup.ToAccess_Restriction=AtLeastN` failure-only wire shape
- [x] `Connections=null`
- [x] `Connections=explicit` failure-only wire shape
- [x] `UseLightTimeDelay=true`

## No Additional Branch Axes Discovered Yet

These endpoints currently only have a required `nominal` fixture in this status
file. This does not prove that no branch-changing options exist; it only means
the current heuristics did not identify branch axes.

- [x] `/CAT/DebrisBreakupNASA`
- [x] `/CAT/LifeTimeTLE`
- [x] `/LandingZone`
- [x] `/Lighting/SolarAER`
- [x] `/OrbitConvert/CalGEOYMLambertDv`
- [x] `/OrbitConvert/GetKozaiIzsakMeanElements`
- [x] `/OrbitConvert/Kepler2LLAAtAscendNode`
- [x] `/OrbitConvert/Kepler2RV`
- [x] `/OrbitConvert/RV2Kepler`
- [ ] `/OrbitSystem/CentralBodyFrame` blocked: POST query params are required
  but not representable in the current route/body fixture format.
- [x] `/OrbitSystem/EarthMoonLibration` failure-only wire shape
- [x] `/OrbitSystem/EarthMoonLibration2` failure-only wire shape
- [x] `/OrbitWizard/GEO`
- [x] `/OrbitWizard/Molniya`
- [x] `/OrbitWizard/SSO`
- [x] `/Propagator/J2`
- [x] `/Propagator/MultiJ2`
- [x] `/Propagator/MultiSgp4`
- [x] `/Propagator/MultiTwoBody`
- [x] `/Propagator/SimpleAscent`
- [x] `/Propagator/TwoBody`
- [x] `/Propagator/sgp4`
- [x] `/Terrain/AzElMask` failure-only wire shape
- [x] `/Terrain/AzElMaskSimple` failure-only wire shape
- [x] `/WeatherForecast`
- [x] `/facility`
- [x] `/satcat`
- [x] `/ssc`
- [ ] `/ssc/admin/upload-database-archive` blocked: multipart upload plus
  `X-Api-Key` is outside the current fixture transport and public credentials.
- [x] `/orbit/lambert`
- [x] `/ziyou`

## Discovery Notes

The removed `scripts/discover_endpoint_branches.py` was useful as a seed but
not reliable enough to be the canonical branch source. It used line-oriented
YAML parsing plus hard-coded field allowlists. It found some important branches,
such as `/Propagator/Ballistic` `BallisticType` values, but missed root
discriminators such as `/Rocket/RocketGuid` `$type`.

Future discovery should preserve the good heuristics while moving them into a
structured OpenAPI traversal:

- parse YAML as structured data, not indentation-sensitive text
- follow `$ref`, `items.$ref`, `anyOf`, `oneOf`, and discriminator mappings
- detect root and property discriminators
- detect real enums
- keep a small explicit allowlist for description-derived pseudo-enums such as
  `BallisticType`
- treat booleans as branch axes, but remember that `false` or omitted/default
  usually belongs to the endpoint's `nominal` fixture
- avoid claiming cross-product coverage until a fixture explicitly covers a
  combination
- never assume that a branch value is constructible until a live fixture proves
  the request is accepted and the response wire shape matches
