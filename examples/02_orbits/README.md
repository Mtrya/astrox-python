# Orbit Conversion And Wizard Examples

This directory contains runnable orbit examples. The curated orbit examples use this public SDK style:

```python
from astrox import orbits
```

The user-facing guide is [docs/sdk/orbits.md](../../docs/sdk/orbits.md). It documents arguments, units, return values, and notes for orbit conversions, GEO/Molniya/SSO helpers, Walker constellation helpers, and Lambert delta-v.

## Curated Orbit Examples

| Example | Public API shown |
| --- | --- |
| `conversions.py` | `orbits.keplerian_to_cartesian(...)`, `orbits.cartesian_to_keplerian(...)`, `orbits.lla_at_ascending_node(...)`, and `orbits.kozai_izsak_mean_elements(...)` |
| `wizards.py` | `orbits.geo(...)`, `orbits.molniya(...)`, `orbits.sso(...)`, `orbits.walker_delta(...)`, `orbits.walker_star(...)`, and `orbits.walker_custom(...)` |
| `lambert_delta_v.py` | `orbits.lambert_delta_v(...)` and `orbits.geo_ym_lambert_delta_v(...)` |

Install the development environment once, then run examples from the repository root:

```bash
uv sync --group dev
uv run python examples/02_orbits/conversions.py
uv run python examples/02_orbits/wizards.py
uv run python examples/02_orbits/lambert_delta_v.py
```

These examples call the ASTROX API through the package default client configuration. Running them end to end requires access to a compatible ASTROX server.
