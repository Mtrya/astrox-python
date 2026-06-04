# Validation Scripts

This directory contains runnable validation scripts for supported SDK behavior.

## SDK Contract

SDK contract scripts live under `sdk_contract/`. Each script constructs public SDK inputs in Python, calls live ASTROX through the public SDK, normalizes the SDK return, and compares that return with a sidecar `.snap.json` file. The point of SDK contract is to identify potential upstream server behaviour drifts.

Run all live validation tests:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation -m "not calibration"
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

Run a single cross-validation test (sgp4_skyfield):

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/cross_validation/propagator/test_sgp4_skyfield.py
```

Run the full live propagator cross-validation tests:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/cross_validation/propagator
```

## Calibration

Calibration tests use the `calibration` pytest marker. They are live investigations for unresolved external-tool mismatches that should remain visible but should not block scheduled SDK health. Scheduled SDK health runs blocking validation with `-m "not calibration"` and runs calibration separately with `--runxfail` as a nonblocking diagnostic step.

Run calibration diagnostics:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation -m calibration --runxfail
```
