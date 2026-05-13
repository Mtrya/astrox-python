# OpenAPI Fixture Status

This file tracks the fixture corpus for observed ASTROX wire contracts.

Source spec: `openapi/astrox.openapi.yaml`

Current checked-in fixture coverage:

- fixture endpoint records: 50
- handled nominal endpoint fixtures: 48
- handled branch-axis fixtures: 190

Legend:

- `[ ]` not handled by a checked-in fixture yet
- `[x]` handled by a checked-in fixture
- `nominal` means a smallest valid request for the endpoint, without optional
  branch-changing fields unless they are required

This inventory is intentionally more cautious than OpenAPI. A discovered branch
axis is only a candidate until a fixture record actually verifies that the live
server accepts that branch and returns the expected wire shape.

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
    and two-asset corrections return empty HTTP 500 with no content type.
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
    return empty HTTP 500 with no content type.
- [x] `/Coverage/FOM/ValueByGridPointAtTime/RevisitTime` nominal
- [x] `/Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage` nominal
- [x] `/Coverage/GetGridPoints` nominal
- [x] `/Coverage/Report/CoverageByAsset` nominal
- [x] `/Coverage/Report/PercentCoverage` nominal

### Interface

- [ ] `/InterfaceClass` nominal

### Landing Zone

- [ ] `/LandingZone` nominal

### Lighting

- [x] `/Lighting/LightingTimes` nominal
- [ ] `/Lighting/SolarAER` nominal
- [x] `/Lighting/SolarIntensity` nominal

### Orbit Convert

- [ ] `/OrbitConvert/CalGEOYMLambertDv` nominal
- [ ] `/OrbitConvert/GetKozaiIzsakMeanElements` nominal
- [ ] `/OrbitConvert/Kepler2LLAAtAscendNode` nominal
- [x] `/OrbitConvert/Kepler2RV` nominal
- [x] `/OrbitConvert/RV2Kepler` nominal

### Orbit System

- [ ] `/OrbitSystem/CentralBodyFrame` nominal
- [ ] `/OrbitSystem/EarthMoonLibration` nominal
- [ ] `/OrbitSystem/EarthMoonLibration2` nominal

### Orbit Wizard

- [ ] `/OrbitWizard/GEO` nominal
- [ ] `/OrbitWizard/Molniya` nominal
- [ ] `/OrbitWizard/SSO` nominal
- [x] `/OrbitWizard/Walker` nominal

### Propagator

- [x] `/Propagator/Ballistic` nominal
- [x] `/Propagator/HPOP` nominal
- [ ] `/Propagator/J2` nominal
- [ ] `/Propagator/MultiJ2` nominal
- [ ] `/Propagator/MultiSgp4` nominal
- [ ] `/Propagator/MultiTwoBody` nominal
- [ ] `/Propagator/SimpleAscent` nominal
- [ ] `/Propagator/TwoBody` nominal
- [ ] `/Propagator/sgp4` nominal

### Rocket

- [ ] `/Rocket/RocketGuid` nominal
  - blocked: all documented root `$type` values (`CZ2CD`, `KZ1A`,
    `CZ7A`, `CZ3BC`, `CZ4BC`) return empty HTTP 500 responses with no content
    type for minimal, example-derived, and fully populated schema-shaped
    payload probes. Invalid discriminator values return structured HTTP 400,
    so the server appears to recognize the documented discriminator names
    before failing inside endpoint execution.
- [x] `/Rocket/RocketLanding` nominal failure-only wire shape
- [x] `/Rocket/RocketSegmentFA` nominal failure-only wire shape

### Terrain

- [ ] `/Terrain/AzElMask` nominal
- [ ] `/Terrain/AzElMaskSimple` nominal

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
  - [x] public `missing_file_and_api_key` validation error

### Other

- [ ] `/ziyou` nominal

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
- [ ] `MainSequence.$type=Follow`
  - blocked: minimal `Follow` plus targeted `Entities` leader probes using J2
    and AstrogatorMCS-shaped positions still return `Start Stop` construction
    errors for the leader position, so the required leader context remains
    unclear.
- [x] `MainSequence.$type=ManeuverFinite`
- [x] `MainSequence.$type=ManeuverImpulsive`
- [x] `MainSequence.$type=InitialState`
- [ ] `MainSequence.$type=TargetSequence`
  - blocked: minimal `TargetSequence` and DifferentialCorrector-shaped
    `Profiles`/`Segments` probes return internal `Operators`/`Variables`
    empty-list errors; the accepted target-operator construction is unclear.
- [x] `MainSequence.$type=Propagate`
- [x] `MainSequence.$type=Stop`
Result branches below verify accepted request/response wire shape on a minimal
`InitialState` segment. They do not assert that every selector yields a
non-empty named result in that minimal context.

- [ ] `MainSequence.Results.$type=BPlane`
  - blocked: minimal `InitialState` and `Propagate` result probes return an
    empty response with no content type.
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
  - blocked: `Follow` construction still fails before `JoiningConditions` are
    reached, even with SitePosition, CzmlPosition, and fully windowed J2 leader
    entity probes.

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

Required branch axes for each endpoint above:

Unchecked endpoint-family matrix rows below are deferred deliberately. They
would require endpoint-by-endpoint fixture records before they could be marked
handled without overclaiming reusable Coverage payload coverage.

- [ ] `Grid.*` covers all Coverage Grid Variants (deferred: only
  `/Coverage/GetGridPoints` has all grid variants checked; this does not prove
  every Coverage/FOM/report endpoint accepts every grid payload.)
- [ ] `Assets.Position.*` covers all Position Variants (deferred:
  endpoint-family-wide asset position coverage would be a cross-product matrix,
  not a single reusable branch.)
- [ ] `Assets.Orientation.*` covers all Entity Orientation Variants (deferred:
  no Coverage-family fixture currently proves all asset orientation variants.)
- [ ] `Assets.Sensor.*` covers all Entity Sensor Variants (deferred: no
  Coverage-family fixture currently proves all asset sensor variants.)
- [ ] `Assets.SensorPointing.*` covers all Sensor Pointing Variants (deferred:
  no Coverage-family fixture currently proves all asset sensor-pointing
  variants.)
- [ ] `Assets.Constraints.*` covers all Coverage Constraint Variants (deferred:
  grid-point constraints are checked separately and do not imply asset
  constraint coverage.)
- [ ] `Assets.Lighting=DirectSun` (deferred: no Coverage-family fixture
  currently proves asset lighting constraints.)
- [ ] `Assets.Lighting=Penumbra` (deferred: no Coverage-family fixture
  currently proves asset lighting constraints.)
- [ ] `Assets.Lighting=Umbra` (deferred: no Coverage-family fixture currently
  proves asset lighting constraints.)
- [ ] `Assets.OccultationBodies=explicit` (deferred: no Coverage-family
  fixture currently proves asset occultation-body handling.)
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
properties before execution. A full schema-shaped payload currently reaches an
empty HTTP 500 with no content type, so `/InterfaceClass` nominal remains
unchecked.

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

- [x] `Position.$type=SitePosition`
- [x] `Position.$type=J2`
- [x] `Position.$type=SGP4`
- [x] `Position.$type=TwoBody`
- [ ] `Position.$type=AstrogatorMCS` deferred
- [ ] `Position.$type=HPOP` deferred
- [ ] `Position.$type=SimpleAscent` deferred
- [ ] `Position.$type=Ballistic` deferred
- [ ] `Position.$type=CentralBody` deferred
- [ ] `Position.$type=CzmlPositions` deferred
- [ ] `Position.$type=CzmlPosition` deferred

Unchecked Lighting position variants remain deferred because endpoint-specific
live fixtures have not verified them yet; PR 09 only checked explicit
occultation bodies on already-working position payloads.

- [x] `OccultationBodies=explicit`

### `/Lighting/SolarIntensity`

- [x] `Position.$type=SitePosition`
- [x] `Position.$type=J2`
- [x] `Position.$type=SGP4`
- [x] `Position.$type=TwoBody`
- [ ] `Position.$type=AstrogatorMCS` deferred
- [ ] `Position.$type=HPOP` deferred
- [ ] `Position.$type=SimpleAscent` deferred
- [ ] `Position.$type=Ballistic` deferred
- [ ] `Position.$type=CentralBody` deferred
- [ ] `Position.$type=CzmlPositions` deferred
- [ ] `Position.$type=CzmlPosition` deferred
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

- [ ] `$type=CZ2CD` blocked: empty HTTP 500 with no content type.
- [ ] `$type=KZ1A` blocked: empty HTTP 500 with no content type.
- [ ] `$type=CZ7A` blocked: empty HTTP 500 with no content type.
- [ ] `$type=CZ3BC` blocked: empty HTTP 500 with no content type.
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

- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=J2`
- [x] `FromObjectPath.Position.$type=J2 -> ToObjectPath.Position.$type=SitePosition`
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=SGP4`
- [ ] other `FromObjectPath.Position.* -> ToObjectPath.Position.*` pairs
  deferred: exhaustive position-pair cross-product coverage is out of scope.
- [ ] `FromObjectPath.Orientation.*` covers all Entity Orientation Variants
  deferred: no AccessComputeV2 fixture proves the full orientation matrix.
- [ ] `FromObjectPath.Sensor.*` covers all Entity Sensor Variants deferred: no
  AccessComputeV2 fixture proves the full sensor matrix.
- [ ] `FromObjectPath.SensorPointing.*` covers all Sensor Pointing Variants
  deferred: no AccessComputeV2 fixture proves the full sensor-pointing matrix.
- [ ] `FromObjectPath.Constraints.*` covers all Coverage Constraint Variants
  deferred: no AccessComputeV2 fixture proves the full constraint matrix.
- [ ] `FromObjectPath.Lighting=DirectSun` deferred: no AccessComputeV2 fixture
  proves from-object lighting constraints.
- [ ] `FromObjectPath.Lighting=Penumbra` deferred: no AccessComputeV2 fixture
  proves from-object lighting constraints.
- [ ] `FromObjectPath.Lighting=Umbra` deferred: no AccessComputeV2 fixture
  proves from-object lighting constraints.
- [ ] `FromObjectPath.OccultationBodies=explicit` deferred: no AccessComputeV2
  fixture proves from-object occultation bodies.
- [ ] `ToObjectPath.Position.*` covers all Position Variants deferred:
  exhaustive position-pair cross-product coverage is out of scope.
- [ ] `ToObjectPath.Orientation.*` covers all Entity Orientation Variants
  deferred: no AccessComputeV2 fixture proves the full orientation matrix.
- [ ] `ToObjectPath.Sensor.*` covers all Entity Sensor Variants deferred: no
  AccessComputeV2 fixture proves the full sensor matrix.
- [ ] `ToObjectPath.SensorPointing.*` covers all Sensor Pointing Variants
  deferred: no AccessComputeV2 fixture proves the full sensor-pointing matrix.
- [ ] `ToObjectPath.Constraints.*` covers all Coverage Constraint Variants
  deferred: no AccessComputeV2 fixture proves the full constraint matrix.
- [ ] `ToObjectPath.Lighting=DirectSun` deferred: no AccessComputeV2 fixture
  proves to-object lighting constraints.
- [ ] `ToObjectPath.Lighting=Penumbra` deferred: no AccessComputeV2 fixture
  proves to-object lighting constraints.
- [ ] `ToObjectPath.Lighting=Umbra` deferred: no AccessComputeV2 fixture
  proves to-object lighting constraints.
- [ ] `ToObjectPath.OccultationBodies=explicit` deferred: no AccessComputeV2
  fixture proves to-object occultation bodies.
- [x] `ComputeAER=true`
- [x] `UseLightTimeDelay=true`

### `/access/ChainCompute`

- [x] `AllObjects.$type=EntityPath`
- [x] `AllObjects.$type=EntityPathGroup` failure-only wire shape
- [ ] `AllObjects.Position.*` covers all Position Variants deferred:
  ChainCompute has not verified every position variant in the chain context.
- [ ] `AllObjects.Orientation.*` covers all Entity Orientation Variants
  deferred: ChainCompute has not verified the full orientation matrix.
- [ ] `AllObjects.Sensor.*` covers all Entity Sensor Variants deferred:
  ChainCompute has not verified the full sensor matrix.
- [ ] `AllObjects.SensorPointing.*` covers all Sensor Pointing Variants
  deferred: ChainCompute has not verified the full sensor-pointing matrix.
- [ ] `AllObjects.Constraints.*` covers all Coverage Constraint Variants
  deferred: ChainCompute has not verified the full constraint matrix.
- [ ] `AllObjects.Lighting=DirectSun` deferred: ChainCompute has not verified
  all-object lighting constraints.
- [ ] `AllObjects.Lighting=Penumbra` deferred: ChainCompute has not verified
  all-object lighting constraints.
- [ ] `AllObjects.Lighting=Umbra` deferred: ChainCompute has not verified
  all-object lighting constraints.
- [ ] `AllObjects.OccultationBodies=explicit` deferred: ChainCompute has not
  verified all-object occultation bodies.
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
- [ ] `/LandingZone`
- [ ] `/Lighting/SolarAER`
- [ ] `/OrbitConvert/CalGEOYMLambertDv`
- [ ] `/OrbitConvert/GetKozaiIzsakMeanElements`
- [ ] `/OrbitConvert/Kepler2LLAAtAscendNode`
- [x] `/OrbitConvert/Kepler2RV`
- [x] `/OrbitConvert/RV2Kepler`
- [ ] `/OrbitSystem/CentralBodyFrame`
- [ ] `/OrbitSystem/EarthMoonLibration`
- [ ] `/OrbitSystem/EarthMoonLibration2`
- [ ] `/OrbitWizard/GEO`
- [ ] `/OrbitWizard/Molniya`
- [ ] `/OrbitWizard/SSO`
- [ ] `/Propagator/J2`
- [ ] `/Propagator/MultiJ2`
- [ ] `/Propagator/MultiSgp4`
- [ ] `/Propagator/MultiTwoBody`
- [ ] `/Propagator/SimpleAscent`
- [ ] `/Propagator/TwoBody`
- [ ] `/Propagator/sgp4`
- [ ] `/Terrain/AzElMask`
- [ ] `/Terrain/AzElMaskSimple`
- [x] `/WeatherForecast`
- [x] `/facility`
- [x] `/satcat`
- [x] `/ssc`
- [ ] `/ssc/admin/upload-database-archive`
- [x] `/orbit/lambert`
- [ ] `/ziyou`

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
