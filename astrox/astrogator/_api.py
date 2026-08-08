"""Public Astrogator RunMCS endpoint."""

from __future__ import annotations

from collections.abc import Sequence

from astrox._http import raw
from astrox.propagator import HpopConfig

from ._models import (
    EngineConstant,
    EntityPath,
    MCSSegment,
    _mission_wire,
)
from ._results import RunMCSResult, run_mcs_result_from_wire


def _entities_to_wire(values: Sequence[EntityPath] | None) -> list[dict[str, object]] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("entities must be a sequence of astrogator EntityPath values")
    items = tuple(values)
    if not all(isinstance(item, EntityPath) for item in items):
        raise TypeError("entities must be a sequence of astrogator EntityPath values")
    return [item.to_wire() for item in items]


def run_mcs(
    main_sequence: Sequence[MCSSegment],
    *,
    central_body: str = "Earth",
    out_czml_frame_name: str = "INERTIAL",
    compute_czml_positions: bool | None = None,
    entities: Sequence[EntityPath] | None = None,
    propagators: Sequence[HpopConfig] | None = None,
    engine_models: Sequence[EngineConstant] | None = None,
    text: str | None = None,
) -> RunMCSResult:
    """Run an ASTROX Astrogator mission-control sequence."""

    payload = _mission_wire(
        central_body=central_body,
        main_sequence=main_sequence,
        compute_czml_positions=compute_czml_positions,
        out_czml_frame_name=out_czml_frame_name,
        text=text,
        propagators=propagators,
        engine_models=engine_models,
    )
    entity_values = _entities_to_wire(entities)
    if entity_values is not None:
        payload["Entities"] = entity_values

    result = raw.post("/Astrogator/RunMCS", json=payload)
    return run_mcs_result_from_wire(result)


__all__ = ["run_mcs"]
