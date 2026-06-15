# Coverage Examples

This directory contains runnable coverage examples. The curated coverage examples use this public SDK style:

```python
from astrox import coverage, entities
```

The user-facing guide is [docs/sdk/coverage.md](../../docs/sdk/coverage.md).

## Curated Coverage Examples

| Example | Public API shown |
| --- | --- |
| `grid_points.py` | `coverage.lat_lon_grid(...)` and `coverage.grid_points(...)` |
| `compute.py` | `coverage.compute(...)`, entity assets, grid-point sensors, shared constraints, and output flags |
| `reports.py` | `coverage.percent_coverage(...)` and `coverage.coverage_by_asset(...)` |

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/06_coverage/grid_points.py
uv run python examples/06_coverage/compute.py
uv run python examples/06_coverage/reports.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.
