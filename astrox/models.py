"""
Public API models for the Astrox Python SDK.

This module provides clean, pythonic aliases for commonly-used models from the
internal _models module. Users should import from this module rather than
from _models directly.

Organization:
- Orbit Elements & State
- Attitude Control (Finite & Impulsive)
- Maneuvers & Segments
- Stopping Conditions
- Engines
- Coordinate Systems & Axes
- Scalar Calculations
- Position & Orientation
- Results & Outputs
- Rocket Guidance
- Solar & Environmental
- Core Domain Models
"""

from __future__ import annotations

# Import all internal models that need aliasing
from astrox._models import (
    # Attitude Control - Finite
    AgVAAttitudeControlFiniteAntiVelocityVector,
    AgVAAttitudeControlFiniteAttitude,
    AgVAAttitudeControlFiniteThrustVector,
    AgVAAttitudeControlFiniteVelocityVector,
    # Attitude Control - Impulsive
    AgVAAttitudeControlImpulsiveAntiVelocityVector,
    AgVAAttitudeControlImpulsiveAttitude,
    AgVAAttitudeControlImpulsiveThrustVector,
    AgVAAttitudeControlImpulsiveVelocityVector,
    # Elements (note: some are identical to non-prefixed versions)
    AgVAElementCartesian,
    AgVAElementKeplerian,
    AgVAElementSpherical,
    # Stopping Conditions
    AgVAApoapsisStoppingCondition,
    AgVADurationStoppingCondition,
    AgVAEpochStoppingCondition,
    AgVAPeriapsisStoppingCondition,
    AgVAScalarStoppingCondition,
    # Engines
    AgVAEngineConstAcc,
    AgVAEngineConstant,
    # MCS Components
    AgVAMCSInitialState,
    AgVAMCSManeuverFinite,
    AgVAMCSManeuverImpulsive,
    AgVAMCSPropagate,
    AgVAState,
    # MCS Segments (double nesting)
    AgVAMCSSegmentAgVAMCSInitialState,
    AgVAMCSSegmentAgVAMCSManeuverFinite,
    AgVAMCSSegmentAgVAMCSManeuverImpulsive,
    AgVAMCSSegmentAgVAMCSPropagate,
    AgVAMCSSegmentAgVAMCSSequence,
    AgVAMCSSegmentAgVAMCSStop,
    AgVAMCSSegmentAgVAMCSTargetSequence,
    # CalcScalar redundancy
    CalcScalarCalcScalarBPlane,
    CalcScalarCalcScalarCartographic,
    CalcScalarCalcScalarDeltaSphericalElement,
    CalcScalarCalcScalarDuration,
    CalcScalarCalcScalarEpoch,
    CalcScalarCalcScalarKeplerianElement,
    CalcScalarCalcScalarModifiedKeplerianElement,
    CalcScalarCalcScalarPointElement,
    CalcScalarCalcScalarRelative,
    CalcScalarCalcScalarSphericalElement,
    # Coordinate systems
    CrdnAxesCrdnAxesAlignedAndConstrained,
    CrdnAxesCrdnAxesComposite,
    CrdnAxesCrdnAxesFixed,
    CrdnAxesCrdnAxesFixedAtEpoch,
    CrdnAxesCrdnAxesLVLH,
    CrdnAxesCrdnAxesVNC,
    CrdnAxesCrdnAxesVVLH,
    CrdnAxesCzmlOrientation,
    # MCS Results
    MCSSegmentResultsBase,
    MCSSegmentResultsMCSManeuverFiniteResults,
    MCSSegmentResultsMCSManeuverImpulsiveResults,
    MCSSegmentResultsMCSPropagateResults,
    MCSSegmentResultsMCSSequenceResults,
    MCSSegmentResultsMCSTargetSequenceResults,
    # Rocket Guidance
    RocketGuidRocketGuidCZ2CD,
    RocketGuidRocketGuidCZ3BC,
    RocketGuidRocketGuidCZ4BC,
    RocketGuidRocketGuidCZ7A,
    RocketGuidRocketGuidKZ1A,
    # Solar Intensity
    SolarIntensityDataSolarIntensityScData,
    SolarIntensityDataSolarIntensitySiteData,
    # Entity Positions (with discriminators for IEntityPosition union)
    IEntityPositionEntityPositionCentralBody,
    IEntityPositionEntityPositionCzml,
    IEntityPositionEntityPositionCzmlPositions,
    IEntityPositionEntityPositionJ2,
    IEntityPositionEntityPositionSGP4,
    IEntityPositionEntityPositionSite,
    IEntityPositionEntityPositionTwoBody,
    # Orientations
    OrientationLVLH,
    OrientationVNC,
    OrientationVVLH,
    # Sensors (with discriminators for ISensor union)
    ISensorConicSensor,
    ISensorRectangularSensor,
    # Core domain models (already have good names)
    AccessAER,
    AccessData,
    Cartesian,
    EntityPath,
    Keplerian,
    KeplerElements,
    KeplerElementsWithEpoch,
    MeanKeplerElements,
    RectangularSensor,
    RocketSegmentInfo,
    Spherical,
    TleInfo,
)

# ============================================================================
# ORBIT ELEMENTS & STATE
# ============================================================================

# Note: Cartesian/Keplerian/Spherical already have good names from _models
# AgVAElement* versions are identical - we create semantic aliases

# Cartesian is already imported, no alias needed
# Keplerian is already imported, no alias needed
# Spherical is already imported, no alias needed

# Semantic aliases for AgVA versions (identical to base versions)
CartesianElements = AgVAElementCartesian
KeplerianElements_AgVA = AgVAElementKeplerian  # DISTINCT from KeplerElements!
SphericalElements = AgVAElementSpherical

# IMPORTANT: KeplerElements uses different field names than Keplerian
# - KeplerElements: SemimajorAxis, ArgumentOfPeriapsis, RightAscensionOfAscendingNode
# - Keplerian: SemiMajorAxis, ArgOfPeriapsis, RAAN, plus ElementType/MeanAnomaly/Period
# These are NOT interchangeable!

# KeplerElements is already imported, no alias needed
# KeplerElementsWithEpoch is already imported, no alias needed
# MeanKeplerElements is already imported, no alias needed

# MCS State
MCSState = AgVAState
MCSInitialState = AgVAMCSInitialState

# ============================================================================
# ATTITUDE CONTROL
# ============================================================================

# Finite burn attitude control
FiniteAntiVelocityAttitude = AgVAAttitudeControlFiniteAntiVelocityVector
FiniteAttitude = AgVAAttitudeControlFiniteAttitude
FiniteThrustAttitude = AgVAAttitudeControlFiniteThrustVector
FiniteVelocityAttitude = AgVAAttitudeControlFiniteVelocityVector

# Impulsive attitude control
ImpulsiveAntiVelocityAttitude = AgVAAttitudeControlImpulsiveAntiVelocityVector
ImpulsiveAttitude = AgVAAttitudeControlImpulsiveAttitude
ImpulsiveThrustAttitude = AgVAAttitudeControlImpulsiveThrustVector
ImpulsiveVelocityAttitude = AgVAAttitudeControlImpulsiveVelocityVector

# ============================================================================
# MANEUVERS & SEGMENTS
# ============================================================================

# Maneuvers
FiniteManeuver = AgVAMCSManeuverFinite
ImpulsiveManeuver = AgVAMCSManeuverImpulsive
MCSPropagate = AgVAMCSPropagate

# Segments (double-nested names simplified)
PropagateSegment = AgVAMCSSegmentAgVAMCSPropagate
SequenceSegment = AgVAMCSSegmentAgVAMCSSequence
TargetSequenceSegment = AgVAMCSSegmentAgVAMCSTargetSequence
InitialStateSegment = AgVAMCSSegmentAgVAMCSInitialState
FiniteManeuverSegment = AgVAMCSSegmentAgVAMCSManeuverFinite
ImpulsiveManeuverSegment = AgVAMCSSegmentAgVAMCSManeuverImpulsive
StopSegment = AgVAMCSSegmentAgVAMCSStop

# ============================================================================
# STOPPING CONDITIONS
# ============================================================================

ApoapsisStop = AgVAApoapsisStoppingCondition
DurationStop = AgVADurationStoppingCondition
EpochStop = AgVAEpochStoppingCondition
PeriapsisStop = AgVAPeriapsisStoppingCondition
ScalarStop = AgVAScalarStoppingCondition

# ============================================================================
# ENGINES
# ============================================================================

ConstantAccelerationEngine = AgVAEngineConstAcc
ConstantThrustEngine = AgVAEngineConstant

# ============================================================================
# COORDINATE SYSTEMS & AXES
# ============================================================================

# CrdnAxes variants (remove CrdnAxesCrdnAxes redundancy)
AlignedConstrainedAxes = CrdnAxesCrdnAxesAlignedAndConstrained
CompositeAxes = CrdnAxesCrdnAxesComposite
FixedAxes = CrdnAxesCrdnAxesFixed
FixedAtEpochAxes = CrdnAxesCrdnAxesFixedAtEpoch
LVLHAxes = CrdnAxesCrdnAxesLVLH
VNCAxes = CrdnAxesCrdnAxesVNC
VVLHAxes = CrdnAxesCrdnAxesVVLH
CzmlOrientationAxes = CrdnAxesCzmlOrientation

# Orientation variants
LVLHOrientation = OrientationLVLH
VNCOrientation = OrientationVNC
VVLHOrientation = OrientationVVLH

# ============================================================================
# SCALAR CALCULATIONS
# ============================================================================

# Remove CalcScalarCalcScalar redundancy
BPlaneScalar = CalcScalarCalcScalarBPlane
CartographicScalar = CalcScalarCalcScalarCartographic
DeltaSphericalScalar = CalcScalarCalcScalarDeltaSphericalElement
DurationScalar = CalcScalarCalcScalarDuration
EpochScalar = CalcScalarCalcScalarEpoch
KeplerianElementScalar = CalcScalarCalcScalarKeplerianElement
ModifiedKeplerianScalar = CalcScalarCalcScalarModifiedKeplerianElement
PointElementScalar = CalcScalarCalcScalarPointElement
RelativeScalar = CalcScalarCalcScalarRelative
SphericalElementScalar = CalcScalarCalcScalarSphericalElement

# ============================================================================
# POSITION & ORIENTATION
# ============================================================================

# Position types (using IEntityPosition discriminated union variants)
CentralBodyPosition = IEntityPositionEntityPositionCentralBody
CzmlPosition = IEntityPositionEntityPositionCzml
CzmlPositionsData = IEntityPositionEntityPositionCzmlPositions
J2Position = IEntityPositionEntityPositionJ2
SGP4Position = IEntityPositionEntityPositionSGP4
SitePosition = IEntityPositionEntityPositionSite
TwoBodyPosition = IEntityPositionEntityPositionTwoBody
EntityPositionCentralBody = IEntityPositionEntityPositionCentralBody
EntityPositionCzml = IEntityPositionEntityPositionCzml
EntityPositionCzmlPositions = IEntityPositionEntityPositionCzmlPositions
EntityPositionJ2 = IEntityPositionEntityPositionJ2
EntityPositionSGP4 = IEntityPositionEntityPositionSGP4
EntityPositionSite = IEntityPositionEntityPositionSite
EntityPositionTwoBody = IEntityPositionEntityPositionTwoBody

# Sensor aliases for convenience
ConicSensor = ISensorConicSensor
RectangularSensor = ISensorRectangularSensor

# ============================================================================
# RESULTS & OUTPUTS
# ============================================================================

# MCS Segment Results
SegmentResultsBase = MCSSegmentResultsBase
FiniteManeuverResults = MCSSegmentResultsMCSManeuverFiniteResults
ImpulsiveManeuverResults = MCSSegmentResultsMCSManeuverImpulsiveResults
PropagateResults = MCSSegmentResultsMCSPropagateResults
SequenceResults = MCSSegmentResultsMCSSequenceResults
TargetSequenceResults = MCSSegmentResultsMCSTargetSequenceResults

# ============================================================================
# ROCKET GUIDANCE
# ============================================================================

RocketGuidCZ2CD = RocketGuidRocketGuidCZ2CD
RocketGuidCZ3BC = RocketGuidRocketGuidCZ3BC
RocketGuidCZ4BC = RocketGuidRocketGuidCZ4BC
RocketGuidCZ7A = RocketGuidRocketGuidCZ7A
RocketGuidKZ1A = RocketGuidRocketGuidKZ1A

# ============================================================================
# SOLAR & ENVIRONMENTAL
# ============================================================================

SpacecraftSolarIntensity = SolarIntensityDataSolarIntensityScData
SiteSolarIntensity = SolarIntensityDataSolarIntensitySiteData

# ============================================================================
# CORE DOMAIN MODELS
# ============================================================================

# These already have good names - just re-export for convenience
# AccessAER - already imported
# AccessData - already imported
# ConicSensor - already imported
# EntityPath - already imported
# RectangularSensor - already imported
# TleInfo - already imported

# ============================================================================
# PUBLIC API EXPORTS
# ============================================================================

__all__ = [
    # Orbit Elements & State
    "Cartesian",
    "CartesianElements",
    "Keplerian",
    "KeplerianElements_AgVA",
    "Spherical",
    "SphericalElements",
    "KeplerElements",
    "KeplerElementsWithEpoch",
    "MeanKeplerElements",
    "MCSState",
    "MCSInitialState",
    # Attitude Control - Finite
    "FiniteAntiVelocityAttitude",
    "FiniteAttitude",
    "FiniteThrustAttitude",
    "FiniteVelocityAttitude",
    # Attitude Control - Impulsive
    "ImpulsiveAntiVelocityAttitude",
    "ImpulsiveAttitude",
    "ImpulsiveThrustAttitude",
    "ImpulsiveVelocityAttitude",
    # Maneuvers & Segments
    "FiniteManeuver",
    "ImpulsiveManeuver",
    "MCSPropagate",
    "PropagateSegment",
    "SequenceSegment",
    "TargetSequenceSegment",
    "InitialStateSegment",
    "FiniteManeuverSegment",
    "ImpulsiveManeuverSegment",
    "StopSegment",
    # Stopping Conditions
    "ApoapsisStop",
    "DurationStop",
    "EpochStop",
    "PeriapsisStop",
    "ScalarStop",
    # Engines
    "ConstantAccelerationEngine",
    "ConstantThrustEngine",
    # Coordinate Systems & Axes
    "AlignedConstrainedAxes",
    "CompositeAxes",
    "FixedAxes",
    "FixedAtEpochAxes",
    "LVLHAxes",
    "VNCAxes",
    "VVLHAxes",
    "CzmlOrientationAxes",
    "LVLHOrientation",
    "VNCOrientation",
    "VVLHOrientation",
    # Scalar Calculations
    "BPlaneScalar",
    "CartographicScalar",
    "DeltaSphericalScalar",
    "DurationScalar",
    "EpochScalar",
    "KeplerianElementScalar",
    "ModifiedKeplerianScalar",
    "PointElementScalar",
    "RelativeScalar",
    "SphericalElementScalar",
    # Position Types
    "CentralBodyPosition",
    "CzmlPosition",
    "CzmlPositionsData",
    "J2Position",
    "SGP4Position",
    "SitePosition",
    "TwoBodyPosition",
    # Position aliases (EntityPosition* naming)
    "EntityPositionCentralBody",
    "EntityPositionCzml",
    "EntityPositionCzmlPositions",
    "EntityPositionJ2",
    "EntityPositionSGP4",
    "EntityPositionSite",
    "EntityPositionTwoBody",
    # Results
    "SegmentResultsBase",
    "FiniteManeuverResults",
    "ImpulsiveManeuverResults",
    "PropagateResults",
    "SequenceResults",
    "TargetSequenceResults",
    # Rocket Guidance
    "RocketGuidCZ2CD",
    "RocketGuidCZ3BC",
    "RocketGuidCZ4BC",
    "RocketGuidCZ7A",
    "RocketGuidKZ1A",
    # Solar & Environmental
    "SpacecraftSolarIntensity",
    "SiteSolarIntensity",
    # Core Domain Models (already well-named)
    "AccessAER",
    "AccessData",
    "ConicSensor",
    "EntityPath",
    "RocketSegmentInfo",
    "RectangularSensor",
    "TleInfo",
]
