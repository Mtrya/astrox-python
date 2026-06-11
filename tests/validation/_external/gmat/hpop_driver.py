#!/usr/bin/env python3
"""Run one normalized HPOP comparison case through GMAT."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


MASS_KG = 1000.0
GMAT_BODY_NAMES = {
    "Earth": "Earth",
    "Moon": "Luna",
    "Luna": "Luna",
    "Sun": "Sun",
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = run_case(payload)
    except Exception as exc:
        print(f"GMAT_HPOP_DRIVER_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


def run_case(payload: dict[str, Any]) -> dict[str, Any]:
    gmat_root = Path(os.environ.get("GMAT_ROOT", "/opt/gmat"))
    gmat_console = gmat_root / "bin" / "GmatConsole"
    if not gmat_console.is_file():
        raise RuntimeError(f"GmatConsole not found: {gmat_console}")

    offsets = _sample_offsets(payload["sample_offsets_s"])
    with tempfile.TemporaryDirectory(prefix="gmat-hpop-") as tmp:
        workspace = Path(tmp)
        report_path = workspace / "hpop_state_report.txt"
        script_path = workspace / "hpop.script"
        script_path.write_text(_script(payload, offsets, report_path), encoding="utf-8")
        completed = subprocess.run(
            [str(gmat_console), "--exit", "--run", str(script_path)],
            cwd=gmat_console.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=float(payload.get("timeout_s", 180.0)),
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "GMAT HPOP propagation failed: "
                f"returncode={completed.returncode}; stdout={_short(completed.stdout)}; stderr={_short(completed.stderr)}"
            )
        rows = _read_numeric_rows(report_path)
    return {"samples": _samples(rows, offsets)}


def _script(payload: dict[str, Any], offsets: list[float], report_path: Path) -> str:
    state = payload["initial_state"]
    force_model = payload["force_model"]
    integrator = payload.get("integrator", {})
    spacecraft = payload.get("spacecraft", {})
    coordinate_system = payload.get("coordinate_system", "EarthMJ2000Eq")
    if coordinate_system != "EarthMJ2000Eq":
        raise ValueError(f"unsupported GMAT coordinate system: {coordinate_system!r}")

    lines = [
        "Create Spacecraft Sat;",
        "Sat.DateFormat = UTCGregorian;",
        f"Sat.Epoch = '{_gmat_epoch(payload['epoch_utc'])}';",
        f"Sat.CoordinateSystem = {coordinate_system};",
        *_state_lines(state),
        f"Sat.DryMass = {MASS_KG:.16g};",
        f"Sat.Cd = {float(spacecraft.get('coefficient_of_drag', 2.2)):.16g};",
        f"Sat.Cr = {float(spacecraft.get('coefficient_of_srp', 1.0)):.16g};",
        f"Sat.DragArea = {float(spacecraft.get('area_mass_ratio_drag_m2_kg', 0.0)) * MASS_KG:.16g};",
        f"Sat.SRPArea = {float(spacecraft.get('area_mass_ratio_srp_m2_kg', 0.0)) * MASS_KG:.16g};",
        "",
        "Create ForceModel HpopForceModel;",
        "HpopForceModel.CentralBody = Earth;",
        *_force_model_lines(force_model),
        "HpopForceModel.RelativisticCorrection = Off;",
        "HpopForceModel.ErrorControl = RSSStep;",
        "",
        "Create Propagator HpopPropagator;",
        "HpopPropagator.Type = PrinceDormand78;",
        "HpopPropagator.FM = HpopForceModel;",
        f"HpopPropagator.InitialStepSize = {float(integrator.get('initial_step_s', 30.0)):.16g};",
        f"HpopPropagator.Accuracy = {float(integrator.get('accuracy', 1e-12)):.16g};",
        f"HpopPropagator.MinStep = {float(integrator.get('min_step_s', 1e-6)):.16g};",
        f"HpopPropagator.MaxStep = {float(integrator.get('max_step_s', 60.0)):.16g};",
        "",
        "Create ReportFile StateReport;",
        f"StateReport.Filename = '{_gmat_string(report_path)}';",
        "StateReport.Precision = 16;",
        "StateReport.WriteHeaders = true;",
        "StateReport.Delimiter = ' ';",
        "",
        "BeginMissionSequence;",
    ]
    current_offset = 0.0
    for offset in offsets:
        if not math.isclose(offset, current_offset, abs_tol=1e-12):
            delta_s = offset - current_offset
            lines.append(f"Propagate HpopPropagator(Sat) {{Sat.ElapsedSecs = {delta_s:.16g}}};")
            current_offset = offset
        lines.append(
            "Report StateReport Sat.ElapsedSecs Sat.EarthMJ2000Eq.X Sat.EarthMJ2000Eq.Y Sat.EarthMJ2000Eq.Z Sat.EarthMJ2000Eq.VX Sat.EarthMJ2000Eq.VY Sat.EarthMJ2000Eq.VZ;"
        )
    return "\n".join(lines) + "\n"


def _state_lines(state: dict[str, Any]) -> list[str]:
    state_type = state["type"]
    if state_type == "classical":
        return [
            "Sat.DisplayStateType = Keplerian;",
            f"Sat.SMA = {float(state['semi_major_axis_m']) / 1000.0:.16g};",
            f"Sat.ECC = {float(state['eccentricity']):.16g};",
            f"Sat.INC = {float(state['inclination_deg']):.16g};",
            f"Sat.RAAN = {float(state['raan_deg']):.16g};",
            f"Sat.AOP = {float(state['argument_of_periapsis_deg']):.16g};",
            f"Sat.TA = {float(state['true_anomaly_deg']):.16g};",
        ]
    if state_type == "cartesian":
        return [
            "Sat.DisplayStateType = Cartesian;",
            f"Sat.X = {float(state['x_m']) / 1000.0:.16g};",
            f"Sat.Y = {float(state['y_m']) / 1000.0:.16g};",
            f"Sat.Z = {float(state['z_m']) / 1000.0:.16g};",
            f"Sat.VX = {float(state['vx_m_s']) / 1000.0:.16g};",
            f"Sat.VY = {float(state['vy_m_s']) / 1000.0:.16g};",
            f"Sat.VZ = {float(state['vz_m_s']) / 1000.0:.16g};",
        ]
    raise ValueError(f"unsupported initial_state.type: {state_type!r}")


def _force_model_lines(force_model: dict[str, Any]) -> list[str]:
    gravity = force_model["gravity"]
    atmosphere = force_model.get("atmosphere")
    srp = force_model.get("srp")
    third_bodies = force_model.get("third_bodies", [])

    lines: list[str] = []
    point_masses = [GMAT_BODY_NAMES[name] for name in third_bodies]
    gravity_type = gravity["type"]
    if gravity_type == "point_mass":
        point_masses.insert(0, "Earth")
    elif gravity_type == "earth_gravity_field":
        lines.extend(
            [
                "HpopForceModel.PrimaryBodies = {Earth};",
                f"HpopForceModel.GravityField.Earth.Degree = {int(gravity['degree'])};",
                f"HpopForceModel.GravityField.Earth.Order = {int(gravity['order'])};",
                f"HpopForceModel.GravityField.Earth.PotentialFile = '{_gmat_name(gravity['potential_file'])}';",
                f"HpopForceModel.GravityField.Earth.TideModel = '{_gmat_name(gravity.get('tide_model', 'None'))}';",
            ]
        )
    else:
        raise ValueError(f"unsupported gravity.type: {gravity_type!r}")

    if point_masses:
        lines.append(f"HpopForceModel.PointMasses = {{{', '.join(point_masses)}}};")
    else:
        lines.append("HpopForceModel.PointMasses = {};")

    lines.extend(_drag_model_lines(atmosphere))
    if srp is None:
        lines.append("HpopForceModel.SRP = Off;")
    else:
        if srp.get("model") != "spherical":
            raise ValueError(f"unsupported srp.model: {srp.get('model')!r}")
        lines.extend(
            [
                "HpopForceModel.SRP = On;",
                "HpopForceModel.SRP.SRPModel = Spherical;",
                f"HpopForceModel.SRP.Flux = {float(srp.get('flux_w_m2', 1367.0)):.16g};",
                f"HpopForceModel.SRP.Nominal_Sun = {float(srp.get('nominal_sun_km', 149597870.691)):.16g};",
            ]
        )
        extra_shadow_bodies = [
            GMAT_BODY_NAMES[name] for name in srp.get("extra_shadow_bodies", [])
        ]
        if extra_shadow_bodies:
            lines.append(
                f"HpopForceModel.SRP.ExtraShadowBodies = {{{', '.join(extra_shadow_bodies)}}};"
            )
    return lines


def _drag_model_lines(atmosphere: dict[str, Any] | None) -> list[str]:
    if atmosphere is None:
        return ["HpopForceModel.Drag = None;"]

    atmosphere_model = atmosphere["model"]
    if atmosphere_model != "jacchia_roberts":
        raise ValueError(f"unsupported atmosphere.model: {atmosphere_model!r}")
    if atmosphere.get("data_source") != "constant_values":
        raise ValueError(f"unsupported jacchia_roberts data_source: {atmosphere.get('data_source')!r}")
    return [
        "HpopForceModel.Drag = JacchiaRoberts;",
        "HpopForceModel.Drag.AtmosphereModel = 'JacchiaRoberts';",
        "HpopForceModel.Drag.HistoricWeatherSource = 'ConstantFluxAndGeoMag';",
        f"HpopForceModel.Drag.F107 = {float(atmosphere['f10p7']):.16g};",
        f"HpopForceModel.Drag.F107A = {float(atmosphere['f10p7_avg']):.16g};",
        f"HpopForceModel.Drag.MagneticIndex = {float(atmosphere['kp']):.16g};",
    ]


def _sample_offsets(values: list[Any]) -> list[float]:
    offsets = [float(value) for value in values]
    if not offsets:
        raise ValueError("sample_offsets_s must not be empty")
    if offsets[0] < 0.0:
        raise ValueError("sample_offsets_s must be nonnegative")
    if offsets != sorted(offsets):
        raise ValueError("sample_offsets_s must be sorted")
    if len(set(offsets)) != len(offsets):
        raise ValueError("sample_offsets_s must not contain duplicates")
    return offsets


def _samples(rows: list[list[float]], offsets: list[float]) -> list[dict[str, Any]]:
    if len(rows) != len(offsets):
        raise RuntimeError(f"GMAT report row count mismatch: expected {len(offsets)}, got {len(rows)}")
    samples: list[dict[str, Any]] = []
    for expected_offset, row in zip(offsets, rows, strict=True):
        offset = float(row[0])
        if not math.isclose(offset, expected_offset, abs_tol=1e-6):
            raise RuntimeError(f"GMAT sample offset mismatch: expected {expected_offset}, got {offset}")
        samples.append(
            {
                "offset_s": offset,
                "cartesian_m_m_s": [
                    float(row[1]) * 1000.0,
                    float(row[2]) * 1000.0,
                    float(row[3]) * 1000.0,
                    float(row[4]) * 1000.0,
                    float(row[5]) * 1000.0,
                    float(row[6]) * 1000.0,
                ],
            }
        )
    return samples


def _read_numeric_rows(path: Path) -> list[list[float]]:
    if not path.is_file():
        raise RuntimeError(f"GMAT report was not written: {path}")
    rows: list[list[float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        try:
            values = [float(part) for part in parts]
        except ValueError:
            continue
        if len(values) == 7:
            rows.append(values)
    return rows


def _gmat_epoch(value: str) -> str:
    text = value.removesuffix("Z")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")
    return parsed.strftime("%d %b %Y %H:%M:%S.") + f"{parsed.microsecond // 1000:03d}"


def _gmat_string(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _gmat_name(value: str) -> str:
    if not value or any(char in value for char in "'{}\n\r"):
        raise ValueError(f"unsupported GMAT identifier/string value: {value!r}")
    return value


def _short(text: str, limit: int = 4000) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
