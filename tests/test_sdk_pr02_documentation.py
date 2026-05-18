"""Focused documentation and example checks for the PR 02 SDK slice."""

from __future__ import annotations

import py_compile
import re
from pathlib import Path


DOC_PATH = Path("docs/sdk/propagator.md")
README_PATH = Path("examples/01_propagation/README.md")
PR02_EXAMPLE_PATHS = [
    Path("examples/01_propagation/pr02_reference_slice.py"),
    Path("examples/01_propagation/j2_classical.py"),
    Path("examples/01_propagation/two_body_classical.py"),
    Path("examples/01_propagation/ballistic_delta_v.py"),
    Path("examples/01_propagation/ballistic_min_ecc.py"),
    Path("examples/01_propagation/ballistic_apogee_alt.py"),
    Path("examples/01_propagation/ballistic_time_of_flight.py"),
]
FORBIDDEN_PUBLIC_STYLE = [
    "astrox.models",
    "from astrox import models",
    "propagate_j2(",
    "propagate_two_body(",
    "propagate_ballistic(",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pr02_user_facing_doc_covers_documented_surface() -> None:
    content = read(DOC_PATH)

    for required in [
        "from astrox import orbits, propagator",
        "orbits.keplerian",
        "KeplerianElements",
        "to_wire",
        "propagator.j2",
        "propagator.two_body",
        "propagator.PropagatorPosition",
        "propagator.ballistic",
        "propagator.ballistic_delta_v",
        "propagator.ballistic_delta_v_min_ecc",
        "propagator.ballistic_apogee_altitude",
        "propagator.ballistic_time_of_flight",
        "fixture-backed for wire shape",
        "not semantic or physics validation",
        "astrox.raw",
    ]:
        assert required in content


def test_pr02_docs_reference_existing_examples() -> None:
    content = read(DOC_PATH)

    referenced_examples = {
        Path(match)
        for match in re.findall(r"examples/01_propagation/[a-z0-9_]+\.py", content)
    }

    assert Path("examples/01_propagation/pr02_reference_slice.py") in referenced_examples
    assert referenced_examples <= set(PR02_EXAMPLE_PATHS)
    for path in referenced_examples:
        assert path.exists()


def test_pr02_docs_and_examples_do_not_use_removed_public_style() -> None:
    paths = [DOC_PATH, README_PATH, *PR02_EXAMPLE_PATHS]

    for path in paths:
        content = read(path)
        for forbidden in FORBIDDEN_PUBLIC_STYLE:
            assert forbidden not in content, f"{path} contains {forbidden}"


def test_pr02_examples_compile() -> None:
    for path in PR02_EXAMPLE_PATHS:
        py_compile.compile(str(path), doraise=True)
