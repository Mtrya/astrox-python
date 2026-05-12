"""Coverage analysis functions."""

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel

from astrox._http import HTTPClient, get_session
from astrox._models import (
    CovGridLatLonBounds,
    CoverageGridGlobal,
    CoverageGridLatitudeBounds,
    CoverageGridLatLonBounds,
    EntityPath,
    IContraint,
    ISensor,
)

__all__ = [
    "get_grid_points",
    "compute_coverage",
    "fom_simple_coverage",
    "fom_coverage_time",
    "fom_number_of_assets",
    "fom_response_time",
    "fom_revisit_time",
    "report_coverage_by_asset",
    "report_percent_coverage",
]


def _add_grid_discriminator(grid: BaseModel) -> dict:
    """Add $type discriminator to grid payload for API compatibility.

    The ASTROX API requires a $type field to distinguish between different
    grid types (Global, LatitudeBounds, LatLonBounds, CbLatLonBounds).
    """
    grid_dict = grid.model_dump(by_alias=True, exclude_none=True)

    # Map Python class names to API discriminator values
    grid_type_map = {
        "CoverageGridGlobal": "Global",
        "CoverageGridLatitudeBounds": "LatitudeBounds",
        "CoverageGridLatLonBounds": "LatLonBounds",
        "CovGridLatLonBounds": "CbLatLonBounds",
    }

    class_name = grid.__class__.__name__
    if class_name in grid_type_map:
        grid_dict["$type"] = grid_type_map[class_name]

    return grid_dict


def get_grid_points(
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    *,
    text: Optional[str] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Get all grid points and cell information from grid definition.

    Endpoint: POST /Coverage/GetGridPoints

    Args:
        grid: Grid definition (one of several grid types)
        text: Description/comment
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Grid points with cell information
    """
    sess = session or get_session()

    payload: dict = {
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
    }

    if text is not None:
        payload["Text"] = text

    return sess.post(endpoint="/Coverage/GetGridPoints", data=payload)


def compute_coverage(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Compute coverage for all grid points.

    Endpoint: POST /Coverage/ComputeCoverage

    Returns coverage time intervals and asset counts for all grid points.

    Args:
        start: Analysis start time (UTCG) format: "yyyy-MM-ddTHH:mm:ss.fffZ"
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets/resources
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points (Range, AzElMask, ElevationAngle)
        filter_type: Asset count constraint type ("AtLeastN", "ExactlyN")
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Coverage computation results with satisfaction intervals
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint="/Coverage/ComputeCoverage", data=payload)


def fom_simple_coverage(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    output: str = "grid_point",
    time: Optional[str] = None,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate simple binary coverage (0 or 1).

    Endpoints (merged by output parameter):
    - POST /Coverage/FOM/ValueByGridPoint/SimpleCoverage (output="grid_point")
    - POST /Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage (output="grid_point_at_time")
    - POST /Coverage/FOM/GridStats/SimpleCoverage (output="grid_stats")
    - POST /Coverage/FOM/GridStatsOverTime/SimpleCoverage (output="grid_stats_over_time")

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        output: Output format type
        time: Specific time for "grid_point_at_time" output
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        FOM results (1 if covered, 0 otherwise)
    """
    sess = session or get_session()

    # Map output parameter to endpoint
    endpoints = {
        "grid_point": "/Coverage/FOM/ValueByGridPoint/SimpleCoverage",
        "grid_point_at_time": "/Coverage/FOM/ValueByGridPointAtTime/SimpleCoverage",
        "grid_stats": "/Coverage/FOM/GridStats/SimpleCoverage",
        "grid_stats_over_time": "/Coverage/FOM/GridStatsOverTime/SimpleCoverage",
    }
    endpoint = endpoints.get(output, "/Coverage/FOM/ValueByGridPoint/SimpleCoverage")

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if time is not None:
        payload["Time"] = time
    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint=endpoint, data=payload)


def fom_coverage_time(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    output: str = "grid_point",
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate total coverage time for each grid point.

    Endpoints (merged):
    - POST /Coverage/FOM/ValueByGridPoint/CoverageTime (output="grid_point")
    - POST /Coverage/FOM/GridStats/CoverageTime (output="grid_stats")

    Note: No "grid_stats_over_time" variant exists for CoverageTime.

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        output: Output format type
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Coverage time FOM results
    """
    sess = session or get_session()

    # Map output parameter to endpoint
    endpoints = {
        "grid_point": "/Coverage/FOM/ValueByGridPoint/CoverageTime",
        "grid_stats": "/Coverage/FOM/GridStats/CoverageTime",
    }
    endpoint = endpoints.get(output, "/Coverage/FOM/ValueByGridPoint/CoverageTime")

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint=endpoint, data=payload)


def fom_number_of_assets(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    output: str = "grid_point",
    time: Optional[str] = None,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate number of assets covering each grid point.

    Endpoints (merged):
    - POST /Coverage/FOM/ValueByGridPoint/NumberOfAssets (output="grid_point")
    - POST /Coverage/FOM/ValueByGridPointAtTime/NumberOfAssets (output="grid_point_at_time")
    - POST /Coverage/FOM/GridStats/NumberOfAssets (output="grid_stats")
    - POST /Coverage/FOM/GridStatsOverTime/NumberOfAssets (output="grid_stats_over_time")

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        output: Output format type
        time: Specific time for "grid_point_at_time" output
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Number of assets FOM results
    """
    sess = session or get_session()

    # Map output parameter to endpoint
    endpoints = {
        "grid_point": "/Coverage/FOM/ValueByGridPoint/NumberOfAssets",
        "grid_point_at_time": "/Coverage/FOM/ValueByGridPointAtTime/NumberOfAssets",
        "grid_stats": "/Coverage/FOM/GridStats/NumberOfAssets",
        "grid_stats_over_time": "/Coverage/FOM/GridStatsOverTime/NumberOfAssets",
    }
    endpoint = endpoints.get(output, "/Coverage/FOM/ValueByGridPoint/NumberOfAssets")

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if time is not None:
        payload["Time"] = time
    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint=endpoint, data=payload)


def fom_response_time(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    output: str = "grid_point",
    time: Optional[str] = None,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate response time (time to reach target).

    Endpoints (merged):
    - POST /Coverage/FOM/ValueByGridPoint/ResponseTime
    - POST /Coverage/FOM/ValueByGridPointAtTime/ResponseTime
    - POST /Coverage/FOM/GridStats/ResponseTime
    - POST /Coverage/FOM/GridStatsOverTime/ResponseTime

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        output: Output format type
        time: Specific time for "grid_point_at_time" output
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Response time FOM results
    """
    sess = session or get_session()

    # Map output parameter to endpoint
    endpoints = {
        "grid_point": "/Coverage/FOM/ValueByGridPoint/ResponseTime",
        "grid_point_at_time": "/Coverage/FOM/ValueByGridPointAtTime/ResponseTime",
        "grid_stats": "/Coverage/FOM/GridStats/ResponseTime",
        "grid_stats_over_time": "/Coverage/FOM/GridStatsOverTime/ResponseTime",
    }
    endpoint = endpoints.get(output, "/Coverage/FOM/ValueByGridPoint/ResponseTime")

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if time is not None:
        payload["Time"] = time
    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint=endpoint, data=payload)


def fom_revisit_time(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    output: str = "grid_point",
    time: Optional[str] = None,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Calculate revisit time (time between successive passes).

    Endpoints (merged):
    - POST /Coverage/FOM/ValueByGridPoint/RevisitTime
    - POST /Coverage/FOM/ValueByGridPointAtTime/RevisitTime
    - POST /Coverage/FOM/GridStats/RevisitTime
    - POST /Coverage/FOM/GridStatsOverTime/RevisitTime

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        output: Output format type
        time: Specific time for "grid_point_at_time" output
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Revisit time FOM results
    """
    sess = session or get_session()

    # Map output parameter to endpoint
    endpoints = {
        "grid_point": "/Coverage/FOM/ValueByGridPoint/RevisitTime",
        "grid_point_at_time": "/Coverage/FOM/ValueByGridPointAtTime/RevisitTime",
        "grid_stats": "/Coverage/FOM/GridStats/RevisitTime",
        "grid_stats_over_time": "/Coverage/FOM/GridStatsOverTime/RevisitTime",
    }
    endpoint = endpoints.get(output, "/Coverage/FOM/ValueByGridPoint/RevisitTime")

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if time is not None:
        payload["Time"] = time
    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint=endpoint, data=payload)


def report_coverage_by_asset(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Get coverage percentage report for each asset.

    Endpoint: POST /Coverage/Report/CoverageByAsset

    Returns min, max, average, and cumulative coverage percentages per asset.

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Coverage percentage report for each asset
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint="/Coverage/Report/CoverageByAsset", data=payload)


def report_percent_coverage(
    start: str,
    stop: str,
    grid: Union[
        CoverageGridGlobal,
        CoverageGridLatitudeBounds,
        CoverageGridLatLonBounds,
        CovGridLatLonBounds,
    ],
    assets: list[EntityPath],
    *,
    description: Optional[str] = None,
    grid_point_sensor: Optional[ISensor] = None,
    grid_point_constraints: Optional[list[IContraint]] = None,
    filter_type: Optional[str] = None,
    number_of_assets: Optional[int] = None,
    contain_asset_access_results: Optional[bool] = None,
    contain_coverage_points: Optional[bool] = None,
    step: Optional[float] = None,
    session: Optional[HTTPClient] = None,
) -> dict:
    """Get instantaneous and cumulative coverage percentage over time.

    Endpoint: POST /Coverage/Report/PercentCoverage

    Args:
        start: Analysis start time (UTCG)
        stop: Analysis end time (UTCG)
        grid: Grid definition
        assets: Coverage assets
        description: Description/comment
        grid_point_sensor: Sensor at grid points
        grid_point_constraints: Constraints for grid points
        filter_type: Asset count constraint type
        number_of_assets: Minimum coverage resources required
        contain_asset_access_results: Include individual asset coverage results
        contain_coverage_points: Include all point coordinates
        step: Calculation step size (seconds)
        session: Optional HTTP session (uses default if not provided)

    Returns:
        Instantaneous and cumulative coverage percentage over time
    """
    sess = session or get_session()

    payload: dict = {
        "Start": start,
        "Stop": stop,
        "Grid": _add_grid_discriminator(grid)
        if isinstance(grid, BaseModel)
        else grid,
        "Assets": [
            asset.model_dump(by_alias=True, exclude_none=True)
            if isinstance(asset, BaseModel)
            else asset
            for asset in assets
        ],
    }

    if description is not None:
        payload["Description"] = description
    if grid_point_sensor is not None:
        payload["GridPointSensor"] = grid_point_sensor.model_dump(
            by_alias=True, exclude_none=True
        )
    if grid_point_constraints is not None:
        payload["GridPointConstraints"] = [
            c.model_dump(by_alias=True, exclude_none=True)
            if isinstance(c, BaseModel)
            else c
            for c in grid_point_constraints
        ]
    if filter_type is not None:
        payload["FilterType"] = filter_type
    if number_of_assets is not None:
        payload["NumberOfAssets"] = number_of_assets
    if contain_asset_access_results is not None:
        payload["ContainAssetAccessResults"] = contain_asset_access_results
    if contain_coverage_points is not None:
        payload["ContainCoveragePoints"] = contain_coverage_points
    if step is not None:
        payload["Step"] = step

    return sess.post(endpoint="/Coverage/Report/PercentCoverage", data=payload)
