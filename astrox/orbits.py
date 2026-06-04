"""Public orbit value objects and constructors."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CartesianState",
    "KeplerianElements",
    "cartesian_state",
    "keplerian",
]


@dataclass(frozen=True, kw_only=True)
class CartesianState:
    """Cartesian position and velocity state."""

    x_m: float
    y_m: float
    z_m: float
    vx_m_s: float
    vy_m_s: float
    vz_m_s: float

    def to_wire(self) -> list[float]:
        """Lower to ASTROX Cartesian OrbitalElements order."""
        return [
            self.x_m,
            self.y_m,
            self.z_m,
            self.vx_m_s,
            self.vy_m_s,
            self.vz_m_s,
        ]


@dataclass(frozen=True, kw_only=True)
class KeplerianElements:
    """Classical Keplerian orbital elements."""

    semi_major_axis_m: float
    eccentricity: float
    inclination_deg: float
    argument_of_periapsis_deg: float
    raan_deg: float
    true_anomaly_deg: float

    def to_wire(self) -> list[float]:
        """Lower to ASTROX Classical OrbitalElements order."""
        return [
            self.semi_major_axis_m,
            self.eccentricity,
            self.inclination_deg,
            self.argument_of_periapsis_deg,
            self.raan_deg,
            self.true_anomaly_deg,
        ]


def keplerian(
    *,
    semi_major_axis_m: float,
    eccentricity: float,
    inclination_deg: float,
    argument_of_periapsis_deg: float,
    raan_deg: float,
    true_anomaly_deg: float,
) -> KeplerianElements:
    """Create Classical Keplerian orbital elements."""
    return KeplerianElements(
        semi_major_axis_m=semi_major_axis_m,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        argument_of_periapsis_deg=argument_of_periapsis_deg,
        raan_deg=raan_deg,
        true_anomaly_deg=true_anomaly_deg,
    )


def cartesian_state(
    *,
    x_m: float,
    y_m: float,
    z_m: float,
    vx_m_s: float,
    vy_m_s: float,
    vz_m_s: float,
) -> CartesianState:
    """Create Cartesian position and velocity state."""
    return CartesianState(
        x_m=x_m,
        y_m=y_m,
        z_m=z_m,
        vx_m_s=vx_m_s,
        vy_m_s=vy_m_s,
        vz_m_s=vz_m_s,
    )
