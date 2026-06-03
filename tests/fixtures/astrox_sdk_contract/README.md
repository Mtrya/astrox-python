# ASTROX SDK Contract Snapshots

This directory stores live black-box snapshots for promoted public SDK functions. A snapshot records public SDK inputs and the JSON-compatible return value produced by calling the public function against live ASTROX. It is not an OpenAPI endpoint fixture and does not record raw routes, raw request payloads, or server response envelopes.

Each YAML file may contain multiple cases for the same SDK function and scenario. Authored fields describe the function, comparison mode, and public inputs. Generated `expected` fields are written by the refresh script.

Run a focused refresh when a maintained input should become the new live ASTROX contract:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python scripts/sdk_contract/refresh.py --glob 'propagator/j2/*.yaml'
```

Run a focused check when comparing live ASTROX behavior with checked-in snapshots:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python scripts/sdk_contract/check.py --glob 'propagator/j2/*.yaml'
```

`refresh.py` writes deterministic YAML and creates or updates `expected.refreshed_at` and `expected.return`. `check.py` never writes files. Fast PR tests should only lint fixture structure and local harness mechanics; live snapshot checks belong in scheduled SDK health once the workflow is wired to this harness.

Function inputs use ordinary public SDK values. A case may use a one-level constructor value for an input when the public value is easier to read that way:

```yaml
orbit:
  constructor: astrox.orbits.keplerian
  kwargs:
    semi_major_axis_m: 6778137.0
    eccentricity: 0.001
    inclination_deg: 28.5
    argument_of_periapsis_deg: 0.0
    raan_deg: 0.0
    true_anomaly_deg: 0.0
```

Only explicit whitelisted SDK constructors are allowed. Nested constructor graphs are intentionally unsupported.

Returned values are normalized before storage. Tuples become lists, dataclasses become mappings, and arrays are sampled recursively: arrays with length `<= 20` are stored fully, while arrays with length `> 20` are stored as `length`, `first`, and `last`, with ten samples on each side. Comparison can be exact JSON or approximate JSON with explicit numeric tolerances.

Independent cross-validation is separate from this directory. Add runnable cross-validation scripts when a credible lightweight external source exists or when public docs make semantic claims that need independent support.
