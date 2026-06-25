# Validation Scripts

This directory contains runnable validation scripts for supported SDK behavior.

## Live Snapshot

Live snapshot scripts live under `live_snapshot/`. Each script constructs public SDK inputs in Python, calls live ASTROX through the public SDK, normalizes the SDK return, and compares that return with a sidecar `.snap.json` file. The point of live snapshot validation is to identify potential upstream server behaviour drifts.

Run all live validation tests:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation -m "not calibration"
```

Run one live snapshot family through pytest:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python -m pytest tests/validation/live_snapshot/propagator/test_sgp4.py
```

Refresh a snapshot only when intentionally accepting the current live ASTROX return as the maintained live snapshot:

```bash
ASTROX_BASE_URL=http://astrox.cn:8765 uv run python tests/validation/live_snapshot/propagator/test_sgp4.py --refresh
```

### Known dual live baselines

The access and ballistic live snapshot families currently have two observed numeric baselines from `http://astrox.cn:8765`. The maintained sidecars are the refreshed primary baseline from June 25, 2026. GitHub Actions runs a few minutes later also observed the older baseline that was in the sidecars before the refresh. The returned structures, case ids, pass counts, sampled array lengths, and route success fields stayed stable; the differences were numeric and millisecond timestamp changes in deterministic-looking live responses. These are treated as backend routing drift, not SDK lowering drift.

The tests keep the refreshed sidecar as the passing baseline and xfail only when the first mismatch signatures exactly match the known older backend baseline. A third baseline, shape drift, case-id drift, missing field, added field, or an unrecognized numeric mismatch still fails CI.

Access baseline examples:

| Case and field | Primary sidecar value, refreshed `2026-06-25T08:30:00Z` | Older backend value, previous sidecar refreshed `2026-06-15T10:03:13Z` | Absolute difference |
| --- | ---: | ---: | ---: |
| `access_compute_site_sgp4` `Passes[0].AccessBeginData.Range` | `2578529.975389784` | `2578529.9866241547` | `0.0112343705 m` |
| `access_compute_site_sgp4` `Passes[0].AccessEndData.Range` | `2581520.690936737` | `2581520.653653178` | `0.0372835593 m` |
| `access_compute_site_sgp4` `Passes[0].MaxElevationData.Range` | `2366670.5565347625` | `2366676.614264067` | `6.0577293045 m` |
| `access_compute_site_sgp4` `Passes[0].MinRangeData.Range` | `2366667.1043814677` | `2366673.1620865404` | `6.0577050727 m` |
| `access_compute_site_sgp4_elevation_range_constraints` `Passes[0].AccessBeginData.Range` | `1477833.5431410752` | `1477833.5484862048` | `0.0053451296 m` |
| `access_compute_site_sgp4_az_el_mask_constraint` `Passes[0].AccessBeginData.Range` | `1477834.3351905418` | `1477834.3404856182` | `0.0052950764 m` |
| `access_compute_site_sgp4_az_el_mask_constraint_with_max_range` `Passes[0].AccessBeginData.Range` | `1477834.3351905418` | `1477834.3404856182` | `0.0052950764 m` |

Ballistic baseline examples:

| Case and field | Primary sidecar value, refreshed `2026-06-25T08:30:02Z` | Older backend value, previous sidecar refreshed `2026-06-12T08:53:18Z` | Absolute difference |
| --- | ---: | ---: | ---: |
| `nominal` `cartesian_velocity.first[2]` | `-5531176.889920627` | `-5531176.8899206305` | `3.72529029846e-09` |
| `nominal` `cartesian_velocity.first[8]` | `970419.4459664853` | `970419.4388905002` | `0.0070759851` |
| `nominal` `cartesian_velocity.first[9]` | `-5696170.982255595` | `-5696170.984774548` | `0.0025189528` |
| `delta_v` `cartesian_velocity.first[9]` | `-5569949.47401831` | `-5569949.468769019` | `0.0052492917` |
| `delta_v_min_ecc` `cartesian_velocity.first[9]` | `-5569949.47401831` | `-5569949.468769019` | `0.0052492917` |
| `apogee_altitude` `cartesian_velocity.first[9]` | `-5555762.890130799` | `-5555762.889552631` | `0.0005781678` |
| `time_of_flight` `cartesian_velocity.first[8]` | `975242.2322593918` | `975242.2315001311` | `0.0007592607` |

Do not replace these targeted xfails with broad numeric tolerances unless the snapshot helper becomes field-aware. A global `abs_tol` large enough for the access range drift would also hide unrelated angle and duration drift.

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
