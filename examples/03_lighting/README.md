# Lighting Examples

This directory contains runnable lighting examples. The curated lighting examples use this public SDK style:

```python
from astrox import entities, lighting
```

The user-facing guides are [docs/sdk/entities.md](../../docs/sdk/entities.md) and [docs/sdk/lighting.md](../../docs/sdk/lighting.md). They document position sources, named entities, sensors, lighting functions, arguments, units, and return shape.

The example prints sunlight interval counts, the visible and shadowed fractions from a site solar-intensity sample, and solar azimuth/elevation/range for the same site.

## Curated Lighting Examples

| Example | Public API shown |
| --- | --- |
| `lighting.py` | `entities.site_position(...)`, `entities.sgp4_position(...)`, `lighting.lighting_times(...)`, `lighting.solar_intensity(...)`, and `lighting.solar_aer(...)` |

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/03_lighting/lighting.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.
