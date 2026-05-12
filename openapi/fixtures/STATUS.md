# OpenAPI Fixture Status

This file tracks the fixture corpus for observed ASTROX wire contracts.

Source spec: `openapi/astrox.openapi.yaml`

Current checked-in fixture coverage:

- fixture endpoint records: 25
- handled nominal endpoint fixtures: 24
- handled branch-axis fixtures: 23

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

- [ ] `/Astrogator/RunMCS` nominal

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
- [ ] `/Coverage/FOM/GridStats/CoverageTime` nominal
- [ ] `/Coverage/FOM/GridStats/NumberOfAssets` nominal
- [ ] `/Coverage/FOM/GridStats/ResponseTime` nominal
- [ ] `/Coverage/FOM/GridStats/RevisitTime` nominal
- [ ] `/Coverage/FOM/GridStats/SimpleCoverage` nominal
- [ ] `/Coverage/FOM/GridStatsOverTime/NumberOfAssets` nominal
- [ ] `/Coverage/FOM/GridStatsOverTime/ResponseTime` nominal
- [ ] `/Coverage/FOM/GridStatsOverTime/RevisitTime` nominal
- [ ] `/Coverage/FOM/GridStatsOverTime/SimpleCoverage` nominal
- [ ] `/Coverage/FOM/ValueByGridPoint/CoverageTime` nominal
- [ ] `/Coverage/FOM/ValueByGridPoint/NumberOfAssets` nominal
- [ ] `/Coverage/FOM/ValueByGridPoint/ResponseTime` nominal
- [ ] `/Coverage/FOM/ValueByGridPoint/RevisitTime` nominal
- [ ] `/Coverage/FOM/ValueByGridPoint/SimpleCoverage` nominal
- [ ] `/Coverage/FOM/ValueByGridPointAtTime/NumberOfAssets` nominal
- [ ] `/Coverage/FOM/ValueByGridPointAtTime/ResponseTime` nominal
- [ ] `/Coverage/FOM/ValueByGridPointAtTime/RevisitTime` nominal
- [ ] `/Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage` nominal
- [ ] `/Coverage/GetGridPoints` nominal
- [ ] `/Coverage/Report/CoverageByAsset` nominal
- [ ] `/Coverage/Report/PercentCoverage` nominal

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
- [ ] `/OrbitWizard/Walker` nominal

### Propagator

- [x] `/Propagator/Ballistic` nominal
- [ ] `/Propagator/HPOP` nominal
- [ ] `/Propagator/J2` nominal
- [ ] `/Propagator/MultiJ2` nominal
- [ ] `/Propagator/MultiSgp4` nominal
- [ ] `/Propagator/MultiTwoBody` nominal
- [ ] `/Propagator/SimpleAscent` nominal
- [ ] `/Propagator/TwoBody` nominal
- [ ] `/Propagator/sgp4` nominal

### Rocket

- [ ] `/Rocket/RocketGuid` nominal
- [ ] `/Rocket/RocketLanding` nominal
- [ ] `/Rocket/RocketSegmentFA` nominal

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

## Reusable Branch Value Sets

These sets are reused by many endpoint branch axes below.

### Position Variants

- [ ] `Position.$type=J2`
- [ ] `Position.$type=SitePosition`
- [ ] `Position.$type=AstrogatorMCS`
- [ ] `Position.$type=HPOP`
- [ ] `Position.$type=SimpleAscent`
- [ ] `Position.$type=Ballistic`
- [ ] `Position.$type=SGP4`
- [ ] `Position.$type=CentralBody`
- [ ] `Position.$type=CzmlPositions`
- [ ] `Position.$type=CzmlPosition`
- [ ] `Position.$type=TwoBody`

### Coverage Grid Variants

- [ ] `Grid.$type=CbLatLonBounds`
- [ ] `Grid.$type=Global`
- [ ] `Grid.$type=LatitudeBounds`
- [ ] `Grid.$type=LatLonBounds`

### Coverage Sensor Variants

- [ ] `GridPointSensor.$type=Conic`
- [ ] `GridPointSensor.$type=Rectangular`

### Coverage Constraint Variants

- [ ] `GridPointConstraints.$type=AzElMask`
- [ ] `GridPointConstraints.$type=Range`
- [ ] `GridPointConstraints.$type=ElevationAngle`

### Entity Orientation Variants

- [ ] `Orientation.$type=FixedAtEpoch`
- [ ] `Orientation.$type=Composite`
- [ ] `Orientation.$type=Fixed`
- [ ] `Orientation.$type=VNC`
- [ ] `Orientation.$type=AlignedAndConstrained`
- [ ] `Orientation.$type=LVLH`
- [ ] `Orientation.$type=VVLH`
- [ ] `Orientation.$type=CzmlOrientation`

### Entity Sensor Variants

- [ ] `Sensor.$type=Conic`
- [ ] `Sensor.$type=Rectangular`

### Sensor Pointing Variants

- [ ] `SensorPointing.$type=Fixed`

### Stopping Condition Variants

- [ ] `StopCondition.$type=Apoapsis`
- [ ] `StopCondition.$type=Duration`
- [ ] `StopCondition.$type=Epoch`
- [ ] `StopCondition.$type=Periapsis`
- [ ] `StopCondition.$type=Scalar`

### State Element Variants

- [ ] `Element.$type=Cartesian`
- [ ] `Element.$type=Keplerian`
- [ ] `Element.$type=Spherical`

### Attitude Control Variants

- [ ] `AttitudeControl.$type=AntiVelocityVector`
- [ ] `AttitudeControl.$type=Attitude`
- [ ] `AttitudeControl.$type=VelocityVector`
- [ ] `AttitudeControl.$type=ThrustVector`

### CalcScalar Variants

- [ ] `CalcScalar.$type=BPlane`
- [ ] `CalcScalar.$type=Epoch`
- [ ] `CalcScalar.$type=Relative`
- [ ] `CalcScalar.$type=Duration`
- [ ] `CalcScalar.$type=Cartographic`
- [ ] `CalcScalar.$type=SphericalElement`
- [ ] `CalcScalar.$type=DeltaSpherical`
- [ ] `CalcScalar.$type=ModifiedKeplerianElement`
- [ ] `CalcScalar.$type=PointElement`
- [ ] `CalcScalar.$type=KeplerianElement`

## Endpoint Branch Axes

### `/Astrogator/RunMCS`

- [ ] `MainSequence.$type=Sequence`
- [ ] `MainSequence.$type=Follow`
- [ ] `MainSequence.$type=ManeuverFinite`
- [ ] `MainSequence.$type=ManeuverImpulsive`
- [ ] `MainSequence.$type=InitialState`
- [ ] `MainSequence.$type=TargetSequence`
- [ ] `MainSequence.$type=Propagate`
- [ ] `MainSequence.$type=Stop`
- [ ] `MainSequence.Results.$type.*` covers all CalcScalar variants
- [ ] `MainSequence.StopConditions.$type.*` covers all stopping condition variants
- [ ] `MainSequence.JoiningConditions.$type.*` covers all stopping condition variants
- [ ] `MainSequence.AttitudeControl.$type.*` covers all Attitude Control Variants
- [ ] `MainSequence.InitialState.Element.$type.*` covers all State Element Variants
- [ ] `Entities.Position.*` covers all Position Variants
- [ ] `Entities.Orientation.*` covers all Entity Orientation Variants
- [ ] `Entities.Sensor.*` covers all Entity Sensor Variants
- [ ] `Entities.SensorPointing.*` covers all Sensor Pointing Variants
- [ ] `Entities.Constraints.*` covers all Coverage Constraint Variants
- [ ] `Entities.Lighting=DirectSun`
- [ ] `Entities.Lighting=Penumbra`
- [ ] `Entities.Lighting=Umbra`
- [ ] `Entities.OccultationBodies=explicit`
- [ ] `Propagators.NumericalIntegrator.$type=RKF7th8th`
- [ ] `Propagators.GravityModel.$type=GravityField`
- [ ] `Propagators.GravityModel.$type=TwoBody`
- [ ] `Propagators.AtmosphericModel.$type=JacchiaRoberts`
- [ ] `Propagators.SRPModel.$type=SRPSpherical`
- [ ] `EngineModels.$type=EngineConstAcc`
- [ ] `EngineModels.$type=EngineConstant`
- [ ] `ComputeCzmlPositions=true`

### `/CAT/CA_ComputeV3`

- [ ] `Targets=null` database-backed target lookup

### `/CAT/CA_ComputeV4`

- [ ] `Targets=null` database-backed target lookup

### `/CAT/DebrisBreakup`

- [x] `ComputeLifeOfTime=true`

### `/CAT/DebrisBreakupSimple`

- [x] `ComputeLifeOfTime=true`

### `/CAT/GetTLE`

- [x] `IsMeanElements=true`

### `/city`

- [ ] `typeOfCity=PopulatedPlace`
- [ ] `typeOfCity=AdministrationCenter`
- [ ] `typeOfCity=NationalCapital`
- [ ] `typeOfCity=TerritorialCapital`

### `/celestial/ephemeris`

- [ ] `ObserverFrame=FIXED`
- [ ] `ObserverFrame=INERTIAL`
- [ ] `ObserverFrame=MeanEclpJ2000`
- [ ] `ObserverFrame=J2000`

### `/celestial/mpc`

- [ ] `ObserverFrame=FIXED`
- [ ] `ObserverFrame=INERTIAL`
- [ ] `ObserverFrame=MeanEclpJ2000`
- [ ] `ObserverFrame=J2000`

### `/celestial/transfer`

- [ ] `SunFrameName=MeanEclpJ2000`
- [ ] `SunFrameName=ICRF`

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

- [ ] `Grid.*` covers all Coverage Grid Variants
- [ ] `Assets.Position.*` covers all Position Variants
- [ ] `Assets.Orientation.*` covers all Entity Orientation Variants
- [ ] `Assets.Sensor.*` covers all Entity Sensor Variants
- [ ] `Assets.SensorPointing.*` covers all Sensor Pointing Variants
- [ ] `Assets.Constraints.*` covers all Coverage Constraint Variants
- [ ] `Assets.Lighting=DirectSun`
- [ ] `Assets.Lighting=Penumbra`
- [ ] `Assets.Lighting=Umbra`
- [ ] `Assets.OccultationBodies=explicit`
- [ ] `GridPointSensor.*` covers all Coverage Sensor Variants
- [ ] `GridPointConstraints.*` covers all Coverage Constraint Variants
- [ ] `FilterType=AtLeastN`
- [ ] `FilterType=ExactlyN`
- [ ] `ContainAssetAccessResults=true`
- [ ] `ContainCoveragePoints=true`

Additional FOM endpoint branch axes:

- [ ] `ComputeType=TotalTimeAbove`
- [ ] `ComputeType=Maximum`
- [ ] `ComputeType=Minimum`
- [ ] `ComputeType=Average`

### `/Coverage/GetGridPoints`

- [ ] `Grid.*` covers all Coverage Grid Variants

### `/InterfaceClass`

- [ ] `AgVAAttitudeControlFinite.$type=AntiVelocityVector`
- [ ] `AgVAAttitudeControlFinite.$type=Attitude`
- [ ] `AgVAAttitudeControlFinite.$type=VelocityVector`
- [ ] `AgVAAttitudeControlFinite.$type=ThrustVector`
- [ ] `AgVAAttitudeControlFiniteAttitude.CoordType=EulerAngles`
- [ ] `AgVAAttitudeControlFiniteAttitude.CoordType=Quaternion`
- [ ] `AgVAAttitudeControlFiniteThrustVector.CoordType=Cartesian`
- [ ] `AgVAAttitudeControlFiniteThrustVector.CoordType=Spherical`
- [ ] `AgVAAttitudeControlImpulsive.$type=AntiVelocityVector`
- [ ] `AgVAAttitudeControlImpulsive.$type=Attitude`
- [ ] `AgVAAttitudeControlImpulsive.$type=VelocityVector`
- [ ] `AgVAAttitudeControlImpulsive.$type=ThrustVector`
- [ ] `AgVAAttitudeControlImpulsiveAttitude.CoordType=EulerAngles`
- [ ] `AgVAAttitudeControlImpulsiveAttitude.CoordType=Quaternion`
- [ ] `AgVAAttitudeControlImpulsiveThrustVector.CoordType=Cartesian`
- [ ] `AgVAAttitudeControlImpulsiveThrustVector.CoordType=Spherical`
- [ ] `AgVAStoppingConditionElement.$type=Apoapsis`
- [ ] `AgVAStoppingConditionElement.$type=Duration`
- [ ] `AgVAStoppingConditionElement.$type=Epoch`
- [ ] `AgVAStoppingConditionElement.$type=Periapsis`
- [ ] `AgVAStoppingConditionElement.$type=Scalar`
- [ ] `AgVAElement.$type=Cartesian`
- [ ] `AgVAElement.$type=Keplerian`
- [ ] `AgVAElement.$type=Spherical`
- [ ] `CalcScalar.$type.*` covers all CalcScalar variants

### `/Lighting/LightingTimes`

- [x] `Position.$type=SitePosition`
- [x] `Position.$type=J2`
- [x] `Position.$type=SGP4`
- [x] `Position.$type=TwoBody`
- [ ] `Position.$type=AstrogatorMCS`
- [ ] `Position.$type=HPOP`
- [ ] `Position.$type=SimpleAscent`
- [ ] `Position.$type=Ballistic`
- [ ] `Position.$type=CentralBody`
- [ ] `Position.$type=CzmlPositions`
- [ ] `Position.$type=CzmlPosition`

Unchecked Lighting position variants remain deferred because phase 1 did not
establish reusable payload patterns for them, and no endpoint-specific live
fixture has verified them yet.

- [ ] `OccultationBodies=explicit`

### `/Lighting/SolarIntensity`

- [x] `Position.$type=SitePosition`
- [x] `Position.$type=J2`
- [x] `Position.$type=SGP4`
- [x] `Position.$type=TwoBody`
- [ ] `Position.$type=AstrogatorMCS`
- [ ] `Position.$type=HPOP`
- [ ] `Position.$type=SimpleAscent`
- [ ] `Position.$type=Ballistic`
- [ ] `Position.$type=CentralBody`
- [ ] `Position.$type=CzmlPositions`
- [ ] `Position.$type=CzmlPosition`
- [ ] `OccultationBodies=explicit`

### `/Propagator/Ballistic`

- [x] `BallisticType=DeltaV`
- [x] `BallisticType=DeltaV_MinEcc`
- [x] `BallisticType=ApogeeAlt`
- [x] `BallisticType=TimeOfFlight`

### `/Propagator/HPOP`

- [ ] `HpopPropagator.NumericalIntegrator.$type=RKF7th8th`
- [ ] `HpopPropagator.GravityModel.$type=GravityField`
- [ ] `HpopPropagator.GravityModel.$type=TwoBody`
- [ ] `HpopPropagator.AtmosphericModel.$type=JacchiaRoberts`
- [ ] `HpopPropagator.SRPModel.$type=SRPSpherical`
- [ ] `HpopPropagator.SRPModel.ShadowModel=DualCone`
- [ ] `HpopPropagator.SRPModel.ShadowModel=Cylindrical`
- [ ] `HpopPropagator.SRPModel.SunPosition=Apparent`
- [ ] `HpopPropagator.SRPModel.SunPosition=True`

### `/OrbitWizard/Walker`

- [ ] `WalkerType=Delta`
- [ ] `WalkerType=Star`
- [ ] `WalkerType=Custom`

### `/Rocket/RocketGuid`

- [ ] `$type=CZ2CD`
- [ ] `$type=KZ1A`
- [ ] `$type=CZ7A`
- [ ] `$type=CZ3BC`
- [ ] `$type=CZ4BC`

### `/Rocket/RocketLanding`

- [ ] `IsOptimize=true`
- [ ] `VariableX0=Phicx20`
- [ ] `VariableX0=Psicx20`
- [ ] `VariableX0=Dt2`
- [ ] `VariableX0=Height4`
- [ ] `VariableLowerBound=Phicx20`
- [ ] `VariableLowerBound=Psicx20`
- [ ] `VariableLowerBound=Dt2`
- [ ] `VariableLowerBound=Height4`
- [ ] `VariableUpperBound=Phicx20`
- [ ] `VariableUpperBound=Psicx20`
- [ ] `VariableUpperBound=Dt2`
- [ ] `VariableUpperBound=Height4`

### `/Rocket/RocketSegmentFA`

- [ ] `UseMcsProfile=true`

### `/access/AccessComputeV2`

- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=J2`
- [x] `FromObjectPath.Position.$type=J2 -> ToObjectPath.Position.$type=SitePosition`
- [x] `FromObjectPath.Position.$type=SitePosition -> ToObjectPath.Position.$type=SGP4`
- [ ] other `FromObjectPath.Position.* -> ToObjectPath.Position.*` pairs
- [ ] `FromObjectPath.Orientation.*` covers all Entity Orientation Variants
- [ ] `FromObjectPath.Sensor.*` covers all Entity Sensor Variants
- [ ] `FromObjectPath.SensorPointing.*` covers all Sensor Pointing Variants
- [ ] `FromObjectPath.Constraints.*` covers all Coverage Constraint Variants
- [ ] `FromObjectPath.Lighting=DirectSun`
- [ ] `FromObjectPath.Lighting=Penumbra`
- [ ] `FromObjectPath.Lighting=Umbra`
- [ ] `FromObjectPath.OccultationBodies=explicit`
- [ ] `ToObjectPath.Position.*` covers all Position Variants
- [ ] `ToObjectPath.Orientation.*` covers all Entity Orientation Variants
- [ ] `ToObjectPath.Sensor.*` covers all Entity Sensor Variants
- [ ] `ToObjectPath.SensorPointing.*` covers all Sensor Pointing Variants
- [ ] `ToObjectPath.Constraints.*` covers all Coverage Constraint Variants
- [ ] `ToObjectPath.Lighting=DirectSun`
- [ ] `ToObjectPath.Lighting=Penumbra`
- [ ] `ToObjectPath.Lighting=Umbra`
- [ ] `ToObjectPath.OccultationBodies=explicit`
- [x] `ComputeAER=true`
- [x] `UseLightTimeDelay=true`

### `/access/ChainCompute`

- [x] `AllObjects.$type=EntityPath`
- [x] `AllObjects.$type=EntityPathGroup` failure-only wire shape
- [ ] `AllObjects.Position.*` covers all Position Variants
- [ ] `AllObjects.Orientation.*` covers all Entity Orientation Variants
- [ ] `AllObjects.Sensor.*` covers all Entity Sensor Variants
- [ ] `AllObjects.SensorPointing.*` covers all Sensor Pointing Variants
- [ ] `AllObjects.Constraints.*` covers all Coverage Constraint Variants
- [ ] `AllObjects.Lighting=DirectSun`
- [ ] `AllObjects.Lighting=Penumbra`
- [ ] `AllObjects.Lighting=Umbra`
- [ ] `AllObjects.OccultationBodies=explicit`
- [ ] `EntityPathGroup.FromAccess_Restriction=AnyOf`
- [ ] `EntityPathGroup.FromAccess_Restriction=AtLeastN`
- [ ] `EntityPathGroup.ToAccess_Restriction=AnyOf`
- [ ] `EntityPathGroup.ToAccess_Restriction=AtLeastN`
- [ ] `Connections=null`
- [ ] `Connections=explicit`
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
