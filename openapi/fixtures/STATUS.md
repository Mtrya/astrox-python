# OpenAPI Fixture Status

This file tracks the fixture corpus for observed ASTROX wire contracts.

Source spec: `openapi/astrox.openapi.yaml`

Status as of this scaffold:

- fixture endpoint records: 0
- handled nominal endpoint fixtures: 0
- handled branch-axis fixtures: 0

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

- [ ] `/access/AccessComputeV2` nominal
- [ ] `/access/ChainCompute` nominal

### Astrogator

- [ ] `/Astrogator/RunMCS` nominal

### CAT

- [ ] `/CAT/CA_ComputeV3` nominal
- [ ] `/CAT/CA_ComputeV4` nominal
- [ ] `/CAT/DebrisBreakup` nominal
- [ ] `/CAT/DebrisBreakupNASA` nominal
- [ ] `/CAT/DebrisBreakupSimple` nominal
- [ ] `/CAT/GetTLE` nominal
- [ ] `/CAT/LifeTimeTLE` nominal

### Coverage

- [ ] `/Coverage/ComputeCoverage` nominal
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

- [ ] `/Lighting/LightingTimes` nominal
- [ ] `/Lighting/SolarAER` nominal
- [ ] `/Lighting/SolarIntensity` nominal

### Orbit Convert

- [ ] `/OrbitConvert/CalGEOYMLambertDv` nominal
- [ ] `/OrbitConvert/GetKozaiIzsakMeanElements` nominal
- [ ] `/OrbitConvert/Kepler2LLAAtAscendNode` nominal
- [ ] `/OrbitConvert/Kepler2RV` nominal
- [ ] `/OrbitConvert/RV2Kepler` nominal

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

- [ ] `/Propagator/Ballistic` nominal
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

- [ ] `/celestial/ephemeris` nominal
- [ ] `/celestial/mpc` nominal
- [ ] `/celestial/transfer` nominal
- [ ] `/orbit/lambert` nominal

### Catalog and Database GET/File Endpoints

- [ ] `/WeatherForecast` nominal
- [ ] `/city` nominal
- [ ] `/facility` nominal
- [ ] `/satcat` nominal
- [ ] `/ssc` nominal
- [ ] `/ssc/admin/upload-database-archive` nominal

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
- [ ] `Entities.Position.*` covers all Position Variants
- [ ] `EngineModels.$type=EngineConstAcc`
- [ ] `EngineModels.$type=EngineConstant`
- [ ] `ComputeCzmlPositions=true`

### `/CAT/DebrisBreakup`

- [ ] `ComputeLifeOfTime=true`

### `/CAT/DebrisBreakupSimple`

- [ ] `ComputeLifeOfTime=true`

### `/CAT/GetTLE`

- [ ] `IsMeanElements=true`

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
- [ ] `GridPointSensor.*` covers all Coverage Sensor Variants
- [ ] `GridPointConstraints.*` covers all Coverage Constraint Variants
- [ ] `ContainAssetAccessResults=true`
- [ ] `ContainCoveragePoints=true`

### `/Coverage/GetGridPoints`

- [ ] `Grid.*` covers all Coverage Grid Variants

### `/InterfaceClass`

- [ ] `AgVAAttitudeControlFiniteAttitude.CoordType=EulerAngles`
- [ ] `AgVAAttitudeControlFiniteAttitude.CoordType=Quaternion`
- [ ] `AgVAAttitudeControlFiniteThrustVector.CoordType=Cartesian`
- [ ] `AgVAAttitudeControlFiniteThrustVector.CoordType=Spherical`
- [ ] `AgVAAttitudeControlImpulsiveAttitude.CoordType=EulerAngles`
- [ ] `AgVAAttitudeControlImpulsiveAttitude.CoordType=Quaternion`
- [ ] `AgVAAttitudeControlImpulsiveThrustVector.CoordType=Cartesian`
- [ ] `AgVAAttitudeControlImpulsiveThrustVector.CoordType=Spherical`

### `/Lighting/LightingTimes`

- [ ] `Position.*` covers all Position Variants

### `/Lighting/SolarIntensity`

- [ ] `Position.*` covers all Position Variants

### `/Propagator/Ballistic`

- [ ] `BallisticType=DeltaV`
- [ ] `BallisticType=DeltaV_MinEcc`
- [ ] `BallisticType=ApogeeAlt`
- [ ] `BallisticType=TimeOfFlight`

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

- [ ] `FromObjectPath.Position.*` covers all Position Variants
- [ ] `ToObjectPath.Position.*` covers all Position Variants
- [ ] `ComputeAER=true`
- [ ] `UseLightTimeDelay=true`

### `/access/ChainCompute`

- [ ] `AllObjects.$type=EntityPath`
- [ ] `AllObjects.$type=EntityPathGroup`
- [ ] `UseLightTimeDelay=true`

## No Additional Branch Axes Discovered Yet

These endpoints currently only have a required `nominal` fixture in this status
file. This does not prove that no branch-changing options exist; it only means
the current heuristics did not identify branch axes.

- [ ] `/CAT/CA_ComputeV3`
- [ ] `/CAT/CA_ComputeV4`
- [ ] `/CAT/DebrisBreakupNASA`
- [ ] `/CAT/LifeTimeTLE`
- [ ] `/LandingZone`
- [ ] `/Lighting/SolarAER`
- [ ] `/OrbitConvert/CalGEOYMLambertDv`
- [ ] `/OrbitConvert/GetKozaiIzsakMeanElements`
- [ ] `/OrbitConvert/Kepler2LLAAtAscendNode`
- [ ] `/OrbitConvert/Kepler2RV`
- [ ] `/OrbitConvert/RV2Kepler`
- [ ] `/OrbitSystem/CentralBodyFrame`
- [ ] `/OrbitSystem/EarthMoonLibration`
- [ ] `/OrbitSystem/EarthMoonLibration2`
- [ ] `/OrbitWizard/GEO`
- [ ] `/OrbitWizard/Molniya`
- [ ] `/OrbitWizard/SSO`
- [ ] `/OrbitWizard/Walker`
- [ ] `/Propagator/HPOP`
- [ ] `/Propagator/J2`
- [ ] `/Propagator/MultiJ2`
- [ ] `/Propagator/MultiSgp4`
- [ ] `/Propagator/MultiTwoBody`
- [ ] `/Propagator/SimpleAscent`
- [ ] `/Propagator/TwoBody`
- [ ] `/Propagator/sgp4`
- [ ] `/Terrain/AzElMask`
- [ ] `/Terrain/AzElMaskSimple`
- [ ] `/WeatherForecast`
- [ ] `/city`
- [ ] `/facility`
- [ ] `/satcat`
- [ ] `/ssc`
- [ ] `/ssc/admin/upload-database-archive`
- [ ] `/celestial/ephemeris`
- [ ] `/celestial/mpc`
- [ ] `/celestial/transfer`
- [ ] `/orbit/lambert`
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
