#!/usr/bin/env python3
"""Live ASTROX spacecraft solar-intensity cross-validation against Orekit."""

from __future__ import annotations

import math
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import entities, lighting
from tests.validation._support import LiveConfigError, configure_astrox_from_env


OREKIT_DATA_URL = (
    "https://gitlab.orekit.org/orekit/orekit-data/-/archive/main/orekit-data-main.zip"
)
OREKIT_DATA_PATH = Path(
    os.environ.get("OREKIT_DATA_PATH", "/tmp/astrox-python-orekit-data.zip")
)
INTENSITY_ABS = 5.0e-6
START = "2024-01-01T00:00:00.000Z"


@dataclass(frozen=True, kw_only=True)
class StateSample:
    offset_s: float
    position_m: tuple[float, float, float]
    velocity_m_s: tuple[float, float, float]


@dataclass(frozen=True, kw_only=True)
class CzmlCase:
    id: str
    stop: str
    samples: tuple[StateSample, ...]


class CrossValidationError(Exception):
    """Raised when ASTROX and Orekit disagree."""


class OrekitContext:
    """Small holder for JVM-backed Orekit classes used by this validation."""

    def __init__(self) -> None:
        import jpype
        import orekit_jpype as orekit

        if not jpype.isJVMStarted():
            orekit.initVM(vmargs="--enable-native-access=ALL-UNNAMED")

        from orekit_jpype.pyhelpers import datetime_to_absolutedate, setup_orekit_data
        from org.hipparchus.geometry.euclidean.threed import Vector3D
        from org.orekit.bodies import CelestialBodyFactory
        from org.orekit.forces.radiation import ConicallyShadowedLightFluxModel
        from org.orekit.frames import FramesFactory
        from org.orekit.propagation import SpacecraftState
        from org.orekit.utils import AbsolutePVCoordinates, Constants, PVCoordinates

        setup_orekit_data(str(ensure_orekit_data()), from_pip_library=False)
        self.datetime_to_absolutedate = datetime_to_absolutedate
        self.Vector3D = Vector3D
        self.AbsolutePVCoordinates = AbsolutePVCoordinates
        self.PVCoordinates = PVCoordinates
        self.SpacecraftState = SpacecraftState
        self.frame = FramesFactory.getEME2000()
        self.shadow = ConicallyShadowedLightFluxModel(
            Constants.SUN_RADIUS,
            CelestialBodyFactory.getSun(),
            Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
        )

    def lighting_ratio(self, *, time_string: str, sample: StateSample) -> float:
        date = self.datetime_to_absolutedate(parse_astrox_time(time_string))
        position = self.Vector3D(*sample.position_m)
        velocity = self.Vector3D(*sample.velocity_m_s)
        state = self.SpacecraftState(
            self.AbsolutePVCoordinates(
                self.frame,
                date,
                self.PVCoordinates(position, velocity),
            )
        )
        return float(self.shadow.getLightingRatio(state))


GENERAL_SHADOW_CASE = CzmlCase(
    id="general_shadow",
    stop="2024-01-01T01:00:00.000Z",
    samples=(
        StateSample(
            offset_s=0.0,
            position_m=(6114454.0, 2870352.0, 3308542.0),
            velocity_m_s=(-3548.0, 6463.0, 1830.0),
        ),
        StateSample(
            offset_s=900.0,
            position_m=(1200000.0, 6500000.0, 2500000.0),
            velocity_m_s=(-7200.0, 1500.0, 1200.0),
        ),
        StateSample(
            offset_s=1800.0,
            position_m=(-5751150.0, 3715517.0, 1150000.0),
            velocity_m_s=(-6060.0, -5250.0, 410.0),
        ),
        StateSample(
            offset_s=2700.0,
            position_m=(-5000000.0, -4000000.0, -2000000.0),
            velocity_m_s=(4500.0, -5600.0, -1500.0),
        ),
        StateSample(
            offset_s=3600.0,
            position_m=(1000000.0, -6500000.0, -2500000.0),
            velocity_m_s=(7200.0, 1100.0, -900.0),
        ),
    ),
)
PARTIAL_SHADOW_POSITION_M = (
    -6779041.942702718,
    1634098.7735145814,
    1214221.9435690104,
)
PARTIAL_SHADOW_CASE = CzmlCase(
    id="partial_shadow",
    stop="2024-01-01T00:04:00.000Z",
    samples=tuple(
        StateSample(
            offset_s=float(offset_s),
            position_m=PARTIAL_SHADOW_POSITION_M,
            velocity_m_s=(0.0, 0.0, 0.0),
        )
        for offset_s in (0.0, 60.0, 120.0, 180.0, 240.0)
    ),
)
CASES = (GENERAL_SHADOW_CASE, PARTIAL_SHADOW_CASE)


def ensure_orekit_data() -> Path:
    if OREKIT_DATA_PATH.exists() and OREKIT_DATA_PATH.stat().st_size > 0:
        return OREKIT_DATA_PATH

    OREKIT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = OREKIT_DATA_PATH.with_suffix(OREKIT_DATA_PATH.suffix + ".tmp")
    with urlopen(OREKIT_DATA_URL, timeout=60) as response, temporary_path.open(
        "wb"
    ) as output:
        shutil.copyfileobj(response, output)
    temporary_path.replace(OREKIT_DATA_PATH)
    return OREKIT_DATA_PATH


def czml_position(case: CzmlCase) -> entities.CzmlPosition:
    return entities.czml_position(
        epoch=START,
        reference_frame="INERTIAL",
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=1,
        cartesian_velocity=[
            value
            for sample in case.samples
            for value in (
                sample.offset_s,
                *sample.position_m,
                *sample.velocity_m_s,
            )
        ],
    )


def astrox_solar_intensity(case: CzmlCase) -> list[dict[str, object]]:
    result = lighting.solar_intensity(
        start=START,
        stop=case.stop,
        position=czml_position(case),
        step_s=case.samples[1].offset_s - case.samples[0].offset_s,
    )
    return result["Datas"]


def compare_case(case: CzmlCase, orekit_context: OrekitContext) -> None:
    failures: list[str] = []
    rows = astrox_solar_intensity(case)
    if len(rows) != len(case.samples):
        raise CrossValidationError(
            f"{case.id} expected {len(case.samples)} samples but got {len(rows)}"
        )

    for row, sample in zip(rows, case.samples, strict=True):
        time_string = require_str(row, "Time")
        orekit_intensity = orekit_context.lighting_ratio(
            time_string=time_string,
            sample=sample,
        )
        if not math.isfinite(orekit_intensity):
            failures.append(
                f"{case.id} {time_string} Orekit lighting ratio is {orekit_intensity}"
            )
            continue

        astrox_intensity = require_float(row, "Intensity")
        astrox_shadow = require_float(row, "PercentShadow")
        intensity_error = abs(astrox_intensity - orekit_intensity)
        shadow_error = abs(astrox_shadow - (1.0 - orekit_intensity))
        if intensity_error > INTENSITY_ABS:
            failures.append(
                f"{case.id} {time_string} Intensity error {intensity_error:.12g}, tolerance {INTENSITY_ABS:.12g}; astrox={astrox_intensity:.12g} orekit={orekit_intensity:.12g}"
            )
        if shadow_error > INTENSITY_ABS:
            failures.append(
                f"{case.id} {time_string} PercentShadow error {shadow_error:.12g}, tolerance {INTENSITY_ABS:.12g}; astrox={astrox_shadow:.12g} orekit={1.0 - orekit_intensity:.12g}"
            )

    if failures:
        raise CrossValidationError("\n".join(failures))


def parse_astrox_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def require_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise CrossValidationError(f"{key} must be a string")
    return value


def require_float(payload: dict[str, object], key: str) -> float:
    value = payload[key]
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise CrossValidationError(f"{key} must be numeric")
    return float(value)


def test_spacecraft_solar_intensity_matches_orekit_conical_shadow() -> None:
    configure_astrox_from_env()
    orekit_context = OrekitContext()
    for case in CASES:
        compare_case(case, orekit_context)


def main() -> int:
    try:
        test_spacecraft_solar_intensity_matches_orekit_conical_shadow()
    except (CrossValidationError, LiveConfigError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("CROSS_VALIDATION_CHECKED=1")
    print("CROSS_VALIDATION_FAILED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
