# Validation Scripts

This directory contains runnable validation scripts for supported SDK behavior.

SDK contract scripts live under `sdk_contract/`. Each script constructs public SDK inputs in Python, calls live ASTROX through the public SDK, normalizes the SDK return, and compares that return with a sidecar `.snap.json` file.

Run one contract family directly:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python tests/validation/sdk_contract/propagator/sgp4.py --check
```

Refresh a snapshot only when intentionally accepting the current live ASTROX return as the maintained SDK contract:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python tests/validation/sdk_contract/propagator/sgp4.py --refresh
```

Shared code under `_support/` is limited to mechanics such as ASTROX configuration, canonical JSON, normalization, snapshot IO, and concise mismatch formatting. Case construction and SDK calls belong in the runnable validation scripts.
