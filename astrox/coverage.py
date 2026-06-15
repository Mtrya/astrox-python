"""Coverage analysis functions and coverage-owned grid fragments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any, TypeAlias

from astrox import entities
from astrox._http import raw

__all__ = [
    "CbLatLonGrid",
    "CoverageGrid",
    "GlobalGrid",
    "LatitudeGrid",
    "LatLonGrid",
    "cb_lat_lon_grid",
    "compute",
    "coverage_by_asset",
    "global_grid",
    "grid_points",
    "lat_lon_grid",
    "latitude_grid",
    "percent_coverage",
]


def _include_if_supplied(payload: dict[str, Any], wire_key: str, value: Any) -> None:
    if value is not None:
        payload[wire_key] = value


def _real_number(value: float, *, parameter: str) -> float:
    if not isinstance(value, Real) or isinstance(value, bool):
        raise TypeError(f"{parameter} must be a number")
    return value


def _optional_real(value: float | None, *, parameter: str) -> float | None:
    if value is None:
        return None
    return _real_number(value, parameter=parameter)


def _optional_bool(value: bool | None, *, parameter: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError(f"{parameter} must be a bool")
    return value


def _optional_string(value: str | None, *, parameter: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{parameter} must be a string")
    return value


def _optional_asset_count(value: int | None, *, parameter: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, Integral) or isinstance(value, bool):
        raise TypeError(f"{parameter} must be an integer")
    return int(value)


def _include_grid_options(
    payload: dict[str, Any],
    *,
    central_body: str | None,
    resolution_deg: float | None,
    height_m: float | None,
    use_cell_surface_area_for_weight: bool | None,
) -> None:
    _include_if_supplied(payload, "CentralBodyName", central_body)
    _include_if_supplied(payload, "Resolution", resolution_deg)
    _include_if_supplied(payload, "Height", height_m)
    _include_if_supplied(
        payload,
        "UseCellSurfaceAreaForWeight",
        use_cell_surface_area_for_weight,
    )


@dataclass(frozen=True, kw_only=True)
class GlobalGrid:
    """Global central-body coverage grid definition."""

    central_body: str | None = None
    resolution_deg: float | None = None
    height_m: float | None = None
    use_cell_surface_area_for_weight: bool | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX Global coverage grid fragment."""
        payload: dict[str, Any] = {"$type": "Global"}
        _include_grid_options(
            payload,
            central_body=self.central_body,
            resolution_deg=self.resolution_deg,
            height_m=self.height_m,
            use_cell_surface_area_for_weight=self.use_cell_surface_area_for_weight,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class LatitudeGrid:
    """Latitude-bounded central-body coverage grid definition."""

    min_latitude_deg: float
    max_latitude_deg: float
    central_body: str | None = None
    resolution_deg: float | None = None
    height_m: float | None = None
    use_cell_surface_area_for_weight: bool | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX LatitudeBounds coverage grid fragment."""
        payload: dict[str, Any] = {
            "$type": "LatitudeBounds",
            "MinLatitude": self.min_latitude_deg,
            "MaxLatitude": self.max_latitude_deg,
        }
        _include_grid_options(
            payload,
            central_body=self.central_body,
            resolution_deg=self.resolution_deg,
            height_m=self.height_m,
            use_cell_surface_area_for_weight=self.use_cell_surface_area_for_weight,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class LatLonGrid:
    """Latitude/longitude-bounded central-body coverage grid definition."""

    min_latitude_deg: float
    max_latitude_deg: float
    min_longitude_deg: float
    max_longitude_deg: float
    central_body: str | None = None
    resolution_deg: float | None = None
    height_m: float | None = None
    use_cell_surface_area_for_weight: bool | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX LatLonBounds coverage grid fragment."""
        payload: dict[str, Any] = {
            "$type": "LatLonBounds",
            "MinLatitude": self.min_latitude_deg,
            "MaxLatitude": self.max_latitude_deg,
            "MinLongitude": self.min_longitude_deg,
            "MaxLongitude": self.max_longitude_deg,
        }
        _include_grid_options(
            payload,
            central_body=self.central_body,
            resolution_deg=self.resolution_deg,
            height_m=self.height_m,
            use_cell_surface_area_for_weight=self.use_cell_surface_area_for_weight,
        )
        return payload


@dataclass(frozen=True, kw_only=True)
class CbLatLonGrid:
    """Server-traceable CbLatLonBounds coverage grid definition."""

    min_latitude_deg: float
    max_latitude_deg: float
    min_longitude_deg: float
    max_longitude_deg: float
    central_body: str | None = None
    resolution_deg: float | None = None
    height_m: float | None = None
    use_cell_surface_area_for_weight: bool | None = None

    def to_wire(self) -> dict[str, Any]:
        """Lower to an ASTROX CbLatLonBounds coverage grid fragment."""
        payload: dict[str, Any] = {
            "$type": "CbLatLonBounds",
            "MinLatitude": self.min_latitude_deg,
            "MaxLatitude": self.max_latitude_deg,
            "MinLongitude": self.min_longitude_deg,
            "MaxLongitude": self.max_longitude_deg,
        }
        _include_grid_options(
            payload,
            central_body=self.central_body,
            resolution_deg=self.resolution_deg,
            height_m=self.height_m,
            use_cell_surface_area_for_weight=self.use_cell_surface_area_for_weight,
        )
        return payload


CoverageGrid: TypeAlias = GlobalGrid | LatitudeGrid | LatLonGrid | CbLatLonGrid
_GRID_TYPES = (GlobalGrid, LatitudeGrid, LatLonGrid, CbLatLonGrid)
_SENSOR_TYPES = (entities.ConicSensor, entities.RectangularSensor)
_CONSTRAINT_TYPES = (
    entities.ElevationConstraint,
    entities.RangeConstraint,
    entities.AzElMaskConstraint,
)


def global_grid(
    *,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> GlobalGrid:
    """Create a global coverage grid definition."""
    return GlobalGrid(
        central_body=_optional_string(central_body, parameter="central_body"),
        resolution_deg=_optional_real(resolution_deg, parameter="resolution_deg"),
        height_m=_optional_real(height_m, parameter="height_m"),
        use_cell_surface_area_for_weight=_optional_bool(
            use_cell_surface_area_for_weight,
            parameter="use_cell_surface_area_for_weight",
        ),
    )


def latitude_grid(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> LatitudeGrid:
    """Create a latitude-bounded coverage grid definition."""
    return LatitudeGrid(
        min_latitude_deg=_real_number(
            min_latitude_deg,
            parameter="min_latitude_deg",
        ),
        max_latitude_deg=_real_number(
            max_latitude_deg,
            parameter="max_latitude_deg",
        ),
        central_body=_optional_string(central_body, parameter="central_body"),
        resolution_deg=_optional_real(resolution_deg, parameter="resolution_deg"),
        height_m=_optional_real(height_m, parameter="height_m"),
        use_cell_surface_area_for_weight=_optional_bool(
            use_cell_surface_area_for_weight,
            parameter="use_cell_surface_area_for_weight",
        ),
    )


def lat_lon_grid(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    min_longitude_deg: float,
    max_longitude_deg: float,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> LatLonGrid:
    """Create a latitude/longitude-bounded coverage grid definition."""
    return LatLonGrid(
        min_latitude_deg=_real_number(
            min_latitude_deg,
            parameter="min_latitude_deg",
        ),
        max_latitude_deg=_real_number(
            max_latitude_deg,
            parameter="max_latitude_deg",
        ),
        min_longitude_deg=_real_number(
            min_longitude_deg,
            parameter="min_longitude_deg",
        ),
        max_longitude_deg=_real_number(
            max_longitude_deg,
            parameter="max_longitude_deg",
        ),
        central_body=_optional_string(central_body, parameter="central_body"),
        resolution_deg=_optional_real(resolution_deg, parameter="resolution_deg"),
        height_m=_optional_real(height_m, parameter="height_m"),
        use_cell_surface_area_for_weight=_optional_bool(
            use_cell_surface_area_for_weight,
            parameter="use_cell_surface_area_for_weight",
        ),
    )


def cb_lat_lon_grid(
    *,
    min_latitude_deg: float,
    max_latitude_deg: float,
    min_longitude_deg: float,
    max_longitude_deg: float,
    central_body: str | None = None,
    resolution_deg: float | None = None,
    height_m: float | None = None,
    use_cell_surface_area_for_weight: bool | None = None,
) -> CbLatLonGrid:
    """Create a server-traceable CbLatLonBounds coverage grid definition."""
    return CbLatLonGrid(
        min_latitude_deg=_real_number(
            min_latitude_deg,
            parameter="min_latitude_deg",
        ),
        max_latitude_deg=_real_number(
            max_latitude_deg,
            parameter="max_latitude_deg",
        ),
        min_longitude_deg=_real_number(
            min_longitude_deg,
            parameter="min_longitude_deg",
        ),
        max_longitude_deg=_real_number(
            max_longitude_deg,
            parameter="max_longitude_deg",
        ),
        central_body=_optional_string(central_body, parameter="central_body"),
        resolution_deg=_optional_real(resolution_deg, parameter="resolution_deg"),
        height_m=_optional_real(height_m, parameter="height_m"),
        use_cell_surface_area_for_weight=_optional_bool(
            use_cell_surface_area_for_weight,
            parameter="use_cell_surface_area_for_weight",
        ),
    )


def grid_points(
    *,
    grid: CoverageGrid,
    text: str | None = None,
) -> dict[str, Any]:
    """Generate coverage grid points from a grid definition."""
    payload: dict[str, Any] = {"Grid": _grid_to_wire(grid)}
    _include_if_supplied(payload, "Text", _optional_string(text, parameter="text"))
    return raw.post("/Coverage/GetGridPoints", json=payload)


def compute(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[entities.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: Sequence[entities.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute coverage over a grid for one or more entity assets."""
    payload = _coverage_input_payload(
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )
    return raw.post("/Coverage/ComputeCoverage", json=payload)


def percent_coverage(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[entities.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: Sequence[entities.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute the ASTROX percent-coverage report."""
    payload = _coverage_input_payload(
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )
    return raw.post("/Coverage/Report/PercentCoverage", json=payload)


def coverage_by_asset(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[entities.Entity],
    minimum_assets: int | None = None,
    exactly_assets: int | None = None,
    grid_point_sensor: entities.EntitySensor | None = None,
    grid_point_constraints: Sequence[entities.Constraint] | None = None,
    include_asset_access_results: bool | None = None,
    include_coverage_points: bool | None = None,
    step_s: float | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Compute the ASTROX coverage-by-asset report."""
    payload = _coverage_input_payload(
        start=start,
        stop=stop,
        grid=grid,
        assets=assets,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
        grid_point_sensor=grid_point_sensor,
        grid_point_constraints=grid_point_constraints,
        include_asset_access_results=include_asset_access_results,
        include_coverage_points=include_coverage_points,
        step_s=step_s,
        description=description,
    )
    return raw.post("/Coverage/Report/CoverageByAsset", json=payload)


def _coverage_input_payload(
    *,
    start: str,
    stop: str,
    grid: CoverageGrid,
    assets: Sequence[entities.Entity],
    minimum_assets: int | None,
    exactly_assets: int | None,
    grid_point_sensor: entities.EntitySensor | None,
    grid_point_constraints: Sequence[entities.Constraint] | None,
    include_asset_access_results: bool | None,
    include_coverage_points: bool | None,
    step_s: float | None,
    description: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "Start": start,
        "Stop": stop,
        "Grid": _grid_to_wire(grid),
        "Assets": _assets_to_wire(assets),
    }
    _include_if_supplied(
        payload,
        "Description",
        _optional_string(description, parameter="description"),
    )
    _include_resource_count_rule(
        payload,
        minimum_assets=minimum_assets,
        exactly_assets=exactly_assets,
    )
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = _sensor_to_wire(grid_point_sensor)
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = _constraints_to_wire(grid_point_constraints)
    _include_if_supplied(
        payload,
        "ContainAssetAccessResults",
        _optional_bool(
            include_asset_access_results,
            parameter="include_asset_access_results",
        ),
    )
    _include_if_supplied(
        payload,
        "ContainCoveragePoints",
        _optional_bool(include_coverage_points, parameter="include_coverage_points"),
    )
    _include_if_supplied(payload, "Step", _optional_real(step_s, parameter="step_s"))
    return payload


def _include_resource_count_rule(
    payload: dict[str, Any],
    *,
    minimum_assets: int | None,
    exactly_assets: int | None,
) -> None:
    minimum = _optional_asset_count(minimum_assets, parameter="minimum_assets")
    exactly = _optional_asset_count(exactly_assets, parameter="exactly_assets")
    if minimum is not None and exactly is not None:
        raise ValueError("minimum_assets and exactly_assets cannot both be supplied")
    if minimum is not None:
        payload["FilterType"] = "AtLeastN"
        payload["NumberOfAssets"] = minimum
    if exactly is not None:
        payload["FilterType"] = "ExactlyN"
        payload["NumberOfAssets"] = exactly


def _grid_to_wire(grid: CoverageGrid) -> dict[str, Any]:
    if not isinstance(grid, _GRID_TYPES):
        raise TypeError("grid must be an astrox.coverage grid value")
    return grid.to_wire()


def _assets_to_wire(values: Sequence[entities.Entity]) -> list[dict[str, Any]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("assets must be a sequence of astrox.entities.Entity values")
    items = tuple(values)
    if not all(isinstance(item, entities.Entity) for item in items):
        raise TypeError("assets must be a sequence of astrox.entities.Entity values")
    return [item.to_wire() for item in items]


def _sensor_to_wire(sensor: entities.EntitySensor) -> dict[str, Any]:
    if not isinstance(sensor, _SENSOR_TYPES):
        raise TypeError("grid_point_sensor must be an astrox.entities sensor value")
    return sensor.to_wire()


def _constraints_to_wire(
    values: Sequence[entities.Constraint],
) -> list[dict[str, Any]]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(
            "grid_point_constraints must be a sequence of astrox.entities constraint values"
        )
    items = tuple(values)
    if not all(isinstance(item, _CONSTRAINT_TYPES) for item in items):
        raise TypeError(
            "grid_point_constraints must be a sequence of astrox.entities constraint values"
        )
    return [item.to_wire() for item in items]
