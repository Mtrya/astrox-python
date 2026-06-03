from __future__ import annotations

import pytest

from tests.validation.cross_validation.propagator import sgp4_skyfield


def test_samples_from_astrox_parses_flat_state_samples() -> None:
    samples = sgp4_skyfield.samples_from_astrox(
        (
            0.0,
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
            6.0,
            300.0,
            7.0,
            8.0,
            9.0,
            10.0,
            11.0,
            12.0,
        )
    )

    assert samples[0.0].position_m == (1.0, 2.0, 3.0)
    assert samples[0.0].velocity_m_s == (4.0, 5.0, 6.0)
    assert samples[300.0].position_m == (7.0, 8.0, 9.0)
    assert samples[300.0].velocity_m_s == (10.0, 11.0, 12.0)


def test_compare_reports_position_mismatch() -> None:
    astrox_samples = {
        0.0: sgp4_skyfield.StateSample(
            offset_s=0.0,
            position_m=(0.0, 0.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0),
        ),
        300.0: sgp4_skyfield.StateSample(
            offset_s=300.0,
            position_m=(0.0, 0.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0),
        ),
    }
    skyfield_samples = {
        0.0: sgp4_skyfield.StateSample(
            offset_s=0.0,
            position_m=(0.1, 0.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0),
        ),
        300.0: sgp4_skyfield.StateSample(
            offset_s=300.0,
            position_m=(0.0, 0.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0),
        ),
    }

    with pytest.raises(sgp4_skyfield.CrossValidationError, match="position error"):
        sgp4_skyfield.compare(1.0, astrox_samples, 1.0, skyfield_samples)
