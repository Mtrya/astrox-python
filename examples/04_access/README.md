# Access Examples

This directory contains runnable access examples. The curated access examples use this public SDK style:

```python
from astrox import access, components
```

The user-facing guides are [docs/sdk/components.md](../../docs/sdk/components.md) and [docs/sdk/access.md](../../docs/sdk/access.md). They document named entities, entity groups, access functions, arguments, units, return shape, and caveats.

## Curated Access Examples

| Example | Public API shown |
| --- | --- |
| `compute.py` | `components.entity(...)`, `components.site_position(...)`, `components.sgp4_position(...)`, and `access.compute(...)` |
| `chain.py` | `components.entity_group(...)`, `access.connection(...)`, and `access.chain(...)` |
| `sensor_pointing.py` | `components.vvlh_axes(...)`, `components.conic_sensor(...)`, `components.fixed_sensor_pointing(...)`, quaternion sensor pointing, and `access.compute(...)` |
| `custom_axes.py` | `components.fixed_axes(...)`, `components.euler_rotation(...)`, calibrated VVLH-relative sensor frames, and `access.compute(...)` |

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/04_access/compute.py
uv run python examples/04_access/chain.py
uv run python examples/04_access/sensor_pointing.py
uv run python examples/04_access/custom_axes.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.
