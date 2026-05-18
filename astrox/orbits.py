"""Public orbit value objects and constructors."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "KeplerianElements",
    "keplerian",
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
