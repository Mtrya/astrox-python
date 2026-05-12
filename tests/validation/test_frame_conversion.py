"""Validation tests for frame and coordinate conversions.

Reference values computed with brahe v0.9.0 and tudatpy v0.8.0.
"""

import pytest

from astrox.orbit_convert import kepler_to_rv, rv_to_kepler
from astrox.models import Keplerian, Cartesian


# Reference: brahe v0.9.0
# Circular equatorial orbit at 400 km
# Position should be [a, 0, 0] in ECI at epoch
# Velocity should be [0, sqrt(mu/a), 0]
# a = 6778137 m, mu = 3.986004418e14 m^3/s^2
# v = sqrt(3.986004418e14 / 6778137) = 7668.6 m/s
LEO_400KM_VELOCITY_REF = 7668.6  # m/s


def test_kepler_to_rv_circular_equatorial(session):
    """Keplerian to RV conversion for circular equatorial orbit.

    Reference: brahe v0.9.0
    At true anomaly = 0, position should be at [a, 0, 0]
    Velocity should be purely in Y direction.
    """
    result = kepler_to_rv(
        central_body="Earth",
        semi_major_axis=6778137.0,
        eccentricity=0.0,
        inclination=0.0,
        arg_of_periapsis=0.0,
        raan=0.0,
        true_anomaly=0.0,
        session=session,
    )

    assert result["IsSuccess"] is True
    assert "Position" in result
    assert "Velocity" in result

    pos = result["Position"]
    vel = result["Velocity"]

    # For circular equatorial at TA=0:
    # Position should be approximately [a, 0, 0]
    assert pos[0] == pytest.approx(6778137.0, abs=1.0)
    assert abs(pos[1]) < 1.0  # Should be near zero
    assert abs(pos[2]) < 1.0  # Should be near zero

    # Velocity should be approximately [0, v_circ, 0]
    assert abs(vel[0]) < 1.0  # Should be near zero
    assert vel[1] == pytest.approx(LEO_400KM_VELOCITY_REF, abs=1.0)
    assert abs(vel[2]) < 1.0  # Should be near zero


def test_rv_to_kepler_roundtrip(session):
    """RV to Keplerian conversion should roundtrip correctly.

    Reference: brahe v0.9.0
    Converting RV -> Keplerian -> RV should give consistent results.
    """
    # Start with known Keplerian elements
    a = 6778137.0
    e = 0.001
    i = 45.0

    # Convert to RV
    rv_result = kepler_to_rv(
        central_body="Earth",
        semi_major_axis=a,
        eccentricity=e,
        inclination=i,
        arg_of_periapsis=0.0,
        raan=0.0,
        true_anomaly=0.0,
        session=session,
    )

    assert rv_result["IsSuccess"] is True

    # Extract position and velocity
    pos = rv_result["Position"]
    vel = rv_result["Velocity"]

    # Convert back to Keplerian
    kepler_result = rv_to_kepler(
        central_body="Earth",
        position=pos,
        velocity=vel,
        session=session,
    )

    assert kepler_result["IsSuccess"] is True

    # Verify elements match (within tolerance)
    assert kepler_result["SemimajorAxis"] == pytest.approx(a, rel=1e-6)
    assert kepler_result["Eccentricity"] == pytest.approx(e, abs=1e-6)
    assert kepler_result["Inclination"] == pytest.approx(i, abs=1e-6)
