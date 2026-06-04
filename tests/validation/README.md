# Validation Scripts

This directory contains runnable validation scripts for supported SDK behavior.

## SDK Contract

SDK contract scripts live under `sdk_contract/`. Each script constructs public SDK inputs in Python, calls live ASTROX through the public SDK, normalizes the SDK return, and compares that return with a sidecar `.snap.json` file. The point of SDK contract is to identify potential upstream server behaviour drifts.

Run all live validation tests:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation
```

Run one SDK contract family through pytest:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/sdk_contract/propagator/test_sgp4.py
```

Refresh a snapshot only when intentionally accepting the current live ASTROX return as the maintained SDK contract:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python tests/validation/sdk_contract/propagator/test_sgp4.py --refresh
```

## Cross Validation

Cross validation scripts live under `cross_validation/`. Each script calls live ASTROX and compares the SDK return with external libraries. The meaning of cross validation is to calibrate ASTROX and our understanding of ASTROX against external sources.

Run the live SGP4 cross-validation test:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/cross_validation/propagator/test_sgp4_skyfield.py
```

Run the live propagator cross-validation tests:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/cross_validation/propagator
```

Refresh a snapshot only when intentionally accepting the current live ASTROX return as the maintained SDK contract:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python tests/validation/sdk_contract/propagator/test_sgp4.py --refresh
```

Shared code under `_support/` is limited to mechanics such as ASTROX configuration, canonical JSON, normalization, snapshot IO, and concise mismatch formatting. Case construction and SDK calls belong in the runnable validation scripts.
