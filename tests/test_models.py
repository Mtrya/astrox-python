"""
Tests for the public API models in astrox.models.

This test suite verifies:
1. All aliases are importable
2. Aliases point to the correct underlying models
3. Critical distinctions (e.g., KeplerElements ≠ Keplerian)
4. Models can be instantiated
5. __all__ exports are complete
"""

import pytest
from astrox import models
from astrox import _models


class TestAliasEquivalence:
    """Test that aliases point to the correct underlying models."""

    def test_cartesian_equivalence(self):
        """Test Cartesian and CartesianElements aliases."""
        # Cartesian is the canonical name
        assert models.Cartesian is _models.Cartesian
        # CartesianElements is an alias for AgVAElementCartesian
        assert models.CartesianElements is _models.AgVAElementCartesian

    def test_keplerian_equivalence(self):
        """Test Keplerian and KeplerianElements_AgVA aliases."""
        # Keplerian is the canonical name
        assert models.Keplerian is _models.Keplerian
        # KeplerianElements_AgVA is an alias for AgVAElementKeplerian
        assert models.KeplerianElements_AgVA is _models.AgVAElementKeplerian

    def test_spherical_equivalence(self):
        """Test Spherical and SphericalElements aliases."""
        # Spherical is the canonical name
        assert models.Spherical is _models.Spherical
        # SphericalElements is an alias for AgVAElementSpherical
        assert models.SphericalElements is _models.AgVAElementSpherical

    def test_attitude_control_finite(self):
        """Test finite attitude control aliases."""
        assert models.FiniteAntiVelocityAttitude is _models.AgVAAttitudeControlFiniteAntiVelocityVector
        assert models.FiniteAttitude is _models.AgVAAttitudeControlFiniteAttitude
        assert models.FiniteThrustAttitude is _models.AgVAAttitudeControlFiniteThrustVector
        assert models.FiniteVelocityAttitude is _models.AgVAAttitudeControlFiniteVelocityVector

    def test_attitude_control_impulsive(self):
        """Test impulsive attitude control aliases."""
        assert models.ImpulsiveAntiVelocityAttitude is _models.AgVAAttitudeControlImpulsiveAntiVelocityVector
        assert models.ImpulsiveAttitude is _models.AgVAAttitudeControlImpulsiveAttitude
        assert models.ImpulsiveThrustAttitude is _models.AgVAAttitudeControlImpulsiveThrustVector
        assert models.ImpulsiveVelocityAttitude is _models.AgVAAttitudeControlImpulsiveVelocityVector

    def test_maneuver_aliases(self):
        """Test maneuver aliases."""
        assert models.FiniteManeuver is _models.AgVAMCSManeuverFinite
        assert models.ImpulsiveManeuver is _models.AgVAMCSManeuverImpulsive
        assert models.MCSPropagate is _models.AgVAMCSPropagate

    def test_segment_aliases(self):
        """Test MCS segment aliases."""
        assert models.PropagateSegment is _models.AgVAMCSSegmentAgVAMCSPropagate
        assert models.SequenceSegment is _models.AgVAMCSSegmentAgVAMCSSequence
        assert models.TargetSequenceSegment is _models.AgVAMCSSegmentAgVAMCSTargetSequence
        assert models.InitialStateSegment is _models.AgVAMCSSegmentAgVAMCSInitialState
        assert models.FiniteManeuverSegment is _models.AgVAMCSSegmentAgVAMCSManeuverFinite
        assert models.ImpulsiveManeuverSegment is _models.AgVAMCSSegmentAgVAMCSManeuverImpulsive
        assert models.StopSegment is _models.AgVAMCSSegmentAgVAMCSStop

    def test_stopping_condition_aliases(self):
        """Test stopping condition aliases."""
        assert models.ApoapsisStop is _models.AgVAApoapsisStoppingCondition
        assert models.DurationStop is _models.AgVADurationStoppingCondition
        assert models.EpochStop is _models.AgVAEpochStoppingCondition
        assert models.PeriapsisStop is _models.AgVAPeriapsisStoppingCondition
        assert models.ScalarStop is _models.AgVAScalarStoppingCondition

    def test_engine_aliases(self):
        """Test engine aliases."""
        assert models.ConstantAccelerationEngine is _models.AgVAEngineConstAcc
        assert models.ConstantThrustEngine is _models.AgVAEngineConstant

    def test_axes_aliases(self):
        """Test coordinate axes aliases."""
        assert models.AlignedConstrainedAxes is _models.CrdnAxesCrdnAxesAlignedAndConstrained
        assert models.CompositeAxes is _models.CrdnAxesCrdnAxesComposite
        assert models.FixedAxes is _models.CrdnAxesCrdnAxesFixed
        assert models.FixedAtEpochAxes is _models.CrdnAxesCrdnAxesFixedAtEpoch
        assert models.LVLHAxes is _models.CrdnAxesCrdnAxesLVLH
        assert models.VNCAxes is _models.CrdnAxesCrdnAxesVNC
        assert models.VVLHAxes is _models.CrdnAxesCrdnAxesVVLH
        assert models.CzmlOrientationAxes is _models.CrdnAxesCzmlOrientation

    def test_scalar_aliases(self):
        """Test scalar calculation aliases."""
        assert models.BPlaneScalar is _models.CalcScalarCalcScalarBPlane
        assert models.CartographicScalar is _models.CalcScalarCalcScalarCartographic
        assert models.DeltaSphericalScalar is _models.CalcScalarCalcScalarDeltaSphericalElement
        assert models.DurationScalar is _models.CalcScalarCalcScalarDuration
        assert models.EpochScalar is _models.CalcScalarCalcScalarEpoch
        assert models.KeplerianElementScalar is _models.CalcScalarCalcScalarKeplerianElement
        assert models.ModifiedKeplerianScalar is _models.CalcScalarCalcScalarModifiedKeplerianElement
        assert models.PointElementScalar is _models.CalcScalarCalcScalarPointElement
        assert models.RelativeScalar is _models.CalcScalarCalcScalarRelative
        assert models.SphericalElementScalar is _models.CalcScalarCalcScalarSphericalElement

    def test_position_aliases(self):
        """Test entity position aliases."""
        assert models.CentralBodyPosition is _models.EntityPositionCentralBody
        assert models.CzmlPosition is _models.EntityPositionCzml
        assert models.CzmlPositionsData is _models.EntityPositionCzmlPositions
        assert models.J2Position is _models.EntityPositionJ2
        assert models.SGP4Position is _models.EntityPositionSGP4
        assert models.SitePosition is _models.EntityPositionSite
        assert models.TwoBodyPosition is _models.EntityPositionTwoBody

    def test_results_aliases(self):
        """Test MCS result aliases."""
        assert models.SegmentResultsBase is _models.MCSSegmentResultsBase
        assert models.FiniteManeuverResults is _models.MCSSegmentResultsMCSManeuverFiniteResults
        assert models.ImpulsiveManeuverResults is _models.MCSSegmentResultsMCSManeuverImpulsiveResults
        assert models.PropagateResults is _models.MCSSegmentResultsMCSPropagateResults
        assert models.SequenceResults is _models.MCSSegmentResultsMCSSequenceResults
        assert models.TargetSequenceResults is _models.MCSSegmentResultsMCSTargetSequenceResults

    def test_rocket_guidance_aliases(self):
        """Test rocket guidance aliases."""
        assert models.RocketGuidCZ2CD is _models.RocketGuidRocketGuidCZ2CD
        assert models.RocketGuidCZ3BC is _models.RocketGuidRocketGuidCZ3BC
        assert models.RocketGuidCZ4BC is _models.RocketGuidRocketGuidCZ4BC
        assert models.RocketGuidCZ7A is _models.RocketGuidRocketGuidCZ7A
        assert models.RocketGuidKZ1A is _models.RocketGuidRocketGuidKZ1A

    def test_solar_intensity_aliases(self):
        """Test solar intensity aliases."""
        assert models.SpacecraftSolarIntensity is _models.SolarIntensityDataSolarIntensityScData
        assert models.SiteSolarIntensity is _models.SolarIntensityDataSolarIntensitySiteData


class TestCriticalDistinctions:
    """Test that semantically different models remain distinct."""

    def test_kepler_elements_vs_keplerian(self):
        """
        CRITICAL: KeplerElements and Keplerian have different field names.
        They must NOT be treated as the same model.

        KeplerElements uses: SemimajorAxis, ArgumentOfPeriapsis, RightAscensionOfAscendingNode
        Keplerian uses: SemiMajorAxis, ArgOfPeriapsis, RAAN, plus ElementType/MeanAnomaly/Period
        """
        assert models.KeplerElements is not models.Keplerian
        assert models.KeplerElements is _models.KeplerElements
        assert models.Keplerian is _models.Keplerian

        # Verify they have different field names
        kepler_fields = set(models.KeplerElements.model_fields.keys())
        keplerian_fields = set(models.Keplerian.model_fields.keys())

        # These should have significant differences
        assert kepler_fields != keplerian_fields

    def test_agva_keplerian_equals_keplerian(self):
        """
        KeplerianElements_AgVA should equal Keplerian (they're identical).
        But it should be distinct from KeplerElements.
        """
        assert models.KeplerianElements_AgVA is _models.AgVAElementKeplerian
        assert models.KeplerianElements_AgVA is not models.KeplerElements


class TestModelInstantiation:
    """Test that key models can be instantiated."""

    def test_cartesian_instantiation(self):
        """Test creating a Cartesian position."""
        pos = models.Cartesian(X=7000000.0, Y=0.0, Z=0.0)
        assert pos.X == 7000000.0

    def test_keplerian_instantiation(self):
        """Test creating a Keplerian orbit."""
        # Using basic required fields
        orbit = models.Keplerian(
            ElementType="ModKeplerian",
            Epoch="1 Jan 2025 00:00:00.000",
            SemiMajorAxis=7000000.0,
            Eccentricity=0.001,
            Inclination=45.0,
            ArgOfPeriapsis=0.0,
            RAAN=0.0,
            MeanAnomaly=0.0,
        )
        assert orbit.SemiMajorAxis == 7000000.0

    def test_kepler_elements_instantiation(self):
        """Test creating KeplerElements (different from Keplerian!)."""
        elements = models.KeplerElements(
            SemimajorAxis=7000000.0,
            Eccentricity=0.001,
            Inclination=45.0,
            ArgumentOfPeriapsis=0.0,
            RightAscensionOfAscendingNode=0.0,
            TrueAnomaly=0.0,
        )
        assert elements.SemimajorAxis == 7000000.0

    def test_stopping_condition_instantiation(self):
        """Test creating a stopping condition."""
        duration_stop = models.DurationStop(
            Name="Duration1",
            Trip=3600.0,  # 1 hour
        )
        assert duration_stop.Trip == 3600.0


class TestExports:
    """Test that __all__ exports are complete and correct."""

    def test_all_exports_exist(self):
        """Verify all items in __all__ exist in the module."""
        for name in models.__all__:
            assert hasattr(models, name), f"'{name}' in __all__ but not found in module"

    def test_all_exports_count(self):
        """Verify we have the expected number of exports (~70-90)."""
        assert len(models.__all__) >= 70, f"Expected at least 70 exports, got {len(models.__all__)}"
        assert len(models.__all__) <= 100, f"Expected at most 100 exports, got {len(models.__all__)}"

    def test_key_models_exported(self):
        """Verify key models are in __all__."""
        key_models = [
            "Cartesian",
            "Keplerian",
            "KeplerElements",
            "FiniteAttitude",
            "ImpulsiveAttitude",
            "PropagateSegment",
            "ApoapsisStop",
            "ConstantThrustEngine",
            "BPlaneScalar",
            "SGP4Position",
        ]
        for name in key_models:
            assert name in models.__all__, f"Key model '{name}' missing from __all__"


class TestImports:
    """Test that all aliases can be imported."""

    def test_import_orbit_elements(self):
        """Test importing orbit element models."""
        from astrox.models import (
            Cartesian,
            CartesianElements,
            Keplerian,
            KeplerianElements_AgVA,
            Spherical,
            SphericalElements,
            KeplerElements,
        )
        assert Cartesian is not None
        assert CartesianElements is not None
        assert Keplerian is not None
        assert KeplerianElements_AgVA is not None
        assert Spherical is not None
        assert SphericalElements is not None
        assert KeplerElements is not None

    def test_import_attitude_control(self):
        """Test importing attitude control models."""
        from astrox.models import (
            FiniteAntiVelocityAttitude,
            FiniteAttitude,
            FiniteThrustAttitude,
            FiniteVelocityAttitude,
            ImpulsiveAntiVelocityAttitude,
            ImpulsiveAttitude,
            ImpulsiveThrustAttitude,
            ImpulsiveVelocityAttitude,
        )
        assert FiniteAntiVelocityAttitude is not None
        assert ImpulsiveAttitude is not None

    def test_import_segments(self):
        """Test importing MCS segment models."""
        from astrox.models import (
            PropagateSegment,
            SequenceSegment,
            TargetSequenceSegment,
            InitialStateSegment,
            FiniteManeuverSegment,
            ImpulsiveManeuverSegment,
            StopSegment,
        )
        assert PropagateSegment is not None
        assert SequenceSegment is not None

    def test_import_stopping_conditions(self):
        """Test importing stopping condition models."""
        from astrox.models import (
            ApoapsisStop,
            DurationStop,
            EpochStop,
            PeriapsisStop,
            ScalarStop,
        )
        assert ApoapsisStop is not None
        assert DurationStop is not None

    def test_import_core_models(self):
        """Test importing core domain models."""
        from astrox.models import (
            AccessAER,
            AccessData,
            ConicSensor,
            EntityPath,
            RectangularSensor,
            TleInfo,
        )
        assert AccessAER is not None
        assert ConicSensor is not None
        assert TleInfo is not None
