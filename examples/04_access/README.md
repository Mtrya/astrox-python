# Access Examples

This directory contains runnable access examples. The curated access examples use this public SDK style:

```python
from astrox import access, entities
```

The user-facing guides are [docs/sdk/entities.md](../../docs/sdk/entities.md) and [docs/sdk/access.md](../../docs/sdk/access.md). They document named entities, entity groups, access functions, arguments, units, return shape, and caveats.

## Curated Access Examples

| Example | Public API shown |
| --- | --- |
| `compute.py` | `entities.entity(...)`, `entities.site_position(...)`, `entities.sgp4_position(...)`, and `access.compute(...)` |
| `chain.py` | `entities.entity_group(...)`, `access.connection(...)`, and `access.chain(...)` |

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/04_access/compute.py
uv run python examples/04_access/chain.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.
