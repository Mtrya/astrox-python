#!/usr/bin/env python3
"""Prove the GMAT validation image can run a minimal propagation."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    gmat_root = Path(os.environ.get("GMAT_ROOT", "/opt/gmat"))
    gmat_console = gmat_root / "bin" / "GmatConsole"
    if not gmat_console.is_file():
        raise RuntimeError(f"GmatConsole not found: {gmat_console}")

    with tempfile.TemporaryDirectory(prefix="gmat-self-check-") as tmp:
        workspace = Path(tmp)
        report_path = workspace / "state_report.txt"
        script_path = workspace / "self_check.script"
        script_path.write_text(_script(report_path), encoding="utf-8")
        completed = subprocess.run(
            [str(gmat_console), "--exit", "--run", str(script_path)],
            cwd=gmat_console.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120.0,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "GMAT self-check propagation failed: "
                f"returncode={completed.returncode}; stdout={_short(completed.stdout)}; stderr={_short(completed.stderr)}"
            )
        rows = _read_numeric_rows(report_path)
        if len(rows) < 2:
            raise RuntimeError(f"GMAT self-check report did not contain two numeric state rows: {report_path}")
        initial = rows[0]
        final = rows[-1]
        if not math.isclose(final[0], 60.0, abs_tol=1e-6):
            raise RuntimeError(f"GMAT self-check final elapsed seconds mismatch: {final[0]!r}")
        displacement_km = math.dist(initial[1:4], final[1:4])
        if displacement_km <= 1e-6:
            raise RuntimeError("GMAT self-check propagation did not move the spacecraft")

    print(
        json.dumps(
            {
                "GMAT_SELF_CHECK": "ok",
                "elapsed_s": final[0],
                "displacement_km": displacement_km,
            },
            sort_keys=True,
        )
    )
    return 0


def _script(report_path: Path) -> str:
    filename = str(report_path).replace("\\", "/").replace("'", "''")
    return f"""Create Spacecraft Sat;
Sat.DateFormat = UTCGregorian;
Sat.Epoch = '01 Jan 2024 00:00:00.000';
Sat.DisplayStateType = Cartesian;
Sat.CoordinateSystem = EarthMJ2000Eq;
Sat.X = 7000.0;
Sat.Y = 0.0;
Sat.Z = 0.0;
Sat.VX = 0.0;
Sat.VY = 7.5;
Sat.VZ = 1.0;
Sat.DryMass = 1000.0;
Sat.Cd = 2.2;
Sat.Cr = 1.8;
Sat.DragArea = 15.0;
Sat.SRPArea = 15.0;

Create ForceModel SelfCheckForceModel;
SelfCheckForceModel.CentralBody = Earth;
SelfCheckForceModel.PointMasses = {{Earth}};
SelfCheckForceModel.Drag = None;
SelfCheckForceModel.SRP = Off;
SelfCheckForceModel.RelativisticCorrection = Off;
SelfCheckForceModel.ErrorControl = RSSStep;

Create Propagator SelfCheckPropagator;
SelfCheckPropagator.Type = PrinceDormand78;
SelfCheckPropagator.FM = SelfCheckForceModel;
SelfCheckPropagator.InitialStepSize = 10.0;
SelfCheckPropagator.Accuracy = 1e-12;
SelfCheckPropagator.MinStep = 1e-5;
SelfCheckPropagator.MaxStep = 60.0;

Create ReportFile StateReport;
StateReport.Filename = '{filename}';
StateReport.Precision = 16;
StateReport.WriteHeaders = true;
StateReport.Delimiter = ' ';

BeginMissionSequence;
Report StateReport Sat.ElapsedSecs Sat.EarthMJ2000Eq.X Sat.EarthMJ2000Eq.Y Sat.EarthMJ2000Eq.Z Sat.EarthMJ2000Eq.VX Sat.EarthMJ2000Eq.VY Sat.EarthMJ2000Eq.VZ;
Propagate SelfCheckPropagator(Sat) {{Sat.ElapsedSecs = 60.0}};
Report StateReport Sat.ElapsedSecs Sat.EarthMJ2000Eq.X Sat.EarthMJ2000Eq.Y Sat.EarthMJ2000Eq.Z Sat.EarthMJ2000Eq.VX Sat.EarthMJ2000Eq.VY Sat.EarthMJ2000Eq.VZ;
"""


def _read_numeric_rows(path: Path) -> list[list[float]]:
    if not path.is_file():
        raise RuntimeError(f"GMAT self-check report was not written: {path}")
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
        if len(values) >= 7:
            rows.append(values)
    return rows


def _short(text: str, limit: int = 4000) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
