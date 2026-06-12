"""Internal sample helpers for examples and validation tests.

These utilities are not part of the public ``astrox`` API and may change
without notice.
"""

from __future__ import annotations

import math

EARTH_MU_M3_S2 = 398600441500000.0


def circular_leo_samples(
    radius_m: float = 7000000.0,
    n_samples: int = 8,
    gravitational_parameter_m3_s2: float = EARTH_MU_M3_S2,
) -> list[float]:
    """Build an evenly sampled circular LEO cartesian array for CZML interpolation.

    The returned list has the shape ``[t0, x0, y0, z0, t1, x1, y1, z1, ...]``.
    """
    velocity_m_s = math.sqrt(gravitational_parameter_m3_s2 / radius_m)
    period_s = 2 * math.pi * math.sqrt(radius_m**3 / gravitational_parameter_m3_s2)
    dt_s = period_s / (n_samples - 1)
    samples: list[float] = []
    for index in range(n_samples):
        t_s = index * dt_s
        angle = velocity_m_s / radius_m * t_s
        samples += [
            t_s,
            radius_m * math.cos(angle),
            radius_m * math.sin(angle),
            0.0,
        ]
    return samples
