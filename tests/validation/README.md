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

Run the live lighting cross-validation tests:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/cross_validation/lighting
```

Orekit-backed lighting validation uses `orekit-jpype[jdk4py]` to compare ASTROX spacecraft solar intensity against Orekit's conical Earth-shadow lighting ratio, including a partial-shadow sample. The test loads Orekit data from `OREKIT_DATA_PATH`, defaulting to `/tmp/astrox-python-orekit-data.zip`, and downloads that zip if it is not present.

GMAT-backed validation runs through a prepared Docker image. Scheduled SDK health pulls `ghcr.io/<owner>/astrox-gmat-validation:gmat-r2026a`, self-checks it, and sets `ASTROX_EXTERNAL_VALIDATION=strict` before running validation.

Run the HPOP GMAT-backed validation with an already prepared image:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 GMAT_VALIDATION_IMAGE=ghcr.io/<owner>/astrox-gmat-validation:gmat-r2026a ASTROX_EXTERNAL_VALIDATION=strict uv run python -m pytest tests/validation/cross_validation/propagator/test_hpop_gmat.py -m "not calibration"
```

## Calibration

Calibration tests use the `calibration` pytest marker. They are live investigations for unresolved external-tool mismatches that should remain visible while the current mismatch is expected. Calibration xfails are strict and limited to cross-validation mismatch errors, so unexpected passes or unexpected failure types are treated as SDK health failures. Scheduled SDK health runs blocking validation with `-m "not calibration"`, checks calibration expectations without `--runxfail`, and then runs calibration separately with `--runxfail` as a nonblocking diagnostic step.

Run calibration diagnostics:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 GMAT_VALIDATION_IMAGE=ghcr.io/<owner>/astrox-gmat-validation:gmat-r2026a ASTROX_EXTERNAL_VALIDATION=strict uv run python -m pytest tests/validation -m calibration --runxfail
```
