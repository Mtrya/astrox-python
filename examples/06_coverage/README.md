# Coverage Examples

This directory contains runnable coverage examples. The curated coverage examples use this public SDK style:

```python
from astrox import coverage, components
```

The user-facing guide is [docs/sdk/coverage.md](../../docs/sdk/coverage.md).

## Curated Coverage Examples

| Example | Public API shown |
| --- | --- |
| `grid_points.py` | `coverage.lat_lon_grid(...)` and `coverage.grid_points(...)` |
| `compute.py` | `coverage.compute(...)`, SGP4 entity assets, resource-count options, and output flags |
| `reports.py` | `coverage.percent_coverage(...)` and `coverage.coverage_by_asset(...)` |
| `fom.py` | `coverage.simple_coverage`, `coverage.number_of_assets`, `coverage.coverage_time`, `coverage.response_time`, and `coverage.revisit_time` metric namespaces |

The examples use SGP4 satellite entities as coverage assets because that is the calibrated path for this SDK surface. Use `minimum_assets` for the demonstrated resource-count rule; `exactly_assets` is available, but current ASTROX behavior in the validated duplicate-asset case matches the same threshold style rather than strict equality.

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/06_coverage/grid_points.py
uv run python examples/06_coverage/compute.py
uv run python examples/06_coverage/reports.py
uv run python examples/06_coverage/fom.py
```

These examples call the ASTROX API through the package's default client configuration. Running them end to end requires access to a compatible ASTROX server.
