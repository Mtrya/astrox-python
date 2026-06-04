# Automated Workflows

This document defines the durable boundary for repository automation. The workflows are intentionally split by responsibility: OpenAPI drift automation refreshes deterministic upstream contract artifacts, PR CI protects mergeability, and scheduled SDK health catches live regressions when no refresh PR is involved.

## Workflow Map

| Workflow | File | Purpose |
| --- | --- | --- |
| CI | `.github/workflows/ci.yml` | Runs package build/import checks, pytest, and live smoke on PRs, pushes to `main`, and manual dispatch. |
| OpenAPI drift | `.github/workflows/openapi-drift.yml` | Fetches the live OpenAPI document, updates deterministic drift artifacts, opens or updates a refresh PR, and enables native GitHub auto-merge. |
| Scheduled SDK health | `.github/workflows/sdk-health.yml` | Runs CI-like SDK health checks on a schedule/manual dispatch and creates or updates one issue on failure. |
| GMAT validation image | `.github/workflows/gmat-validation-image.yml` | Publishes the pinned GMAT runtime image used by scheduled validation. |

## OpenAPI Drift

The OpenAPI drift workflow owns deterministic refresh work only:

- fetch the live OpenAPI document
- validate that the fetched document is usable
- update `openapi/astrox.openapi.yaml` when the stable live document changed
- write a versioned snapshot under `openapi/archive/`
- build report artifacts for the workflow run
- create or update the automated refresh PR when tracked drift artifacts changed
- enable native GitHub auto-merge for deterministic refresh PRs

The OpenAPI drift workflow does not run endpoint replay, endpoint discovery backlog reporting, pytest, package build checks, live smoke checks, or SDK semantic validation. Normal PR CI is the merge gate for refresh PRs.

If the live OpenAPI document cannot be fetched or validated, the workflow fails without opening a PR or creating an issue by default.

If the stable live OpenAPI document matches `openapi/astrox.openapi.yaml`, the workflow exits successfully without opening a PR, running tests, or creating an issue.

If OpenAPI changed but deterministic refresh fails, the workflow fails without creating a PR. Partial refresh PRs are not useful review artifacts.

If OpenAPI changed and deterministic refresh succeeds, the workflow opens or updates a ready-to-review PR and enables native GitHub auto-merge. Repository rules and required PR checks decide whether the PR actually merges.

## CI

CI is the merge gate for human and automated PRs. It owns:

- package build
- built-package import verification
- pytest
- live smoke
- syntax checks for validation scripts and support files

Do not duplicate those checks inside the OpenAPI drift workflow. If an automated drift PR breaks supported SDK behavior, required CI checks should fail and keep the PR open.

## Scheduled SDK Health

Scheduled SDK health exists for live regressions that are not accompanied by an OpenAPI refresh PR. It should mirror CI closely enough to catch supported SDK breakage and direct endpoint smoke failures.

Scheduled SDK health also runs live validation tests under `tests/validation/`. SDK contract validation protects promoted public SDK calls against ASTROX return drift, and cross-validation scripts compare selected behavior with independent tools when that comparison is lightweight and credible enough for scheduled execution.

When scheduled validation depends on a prepared external tool, SDK health prepares that tool before running validation. GMAT-backed validation uses the pinned `ghcr.io/<owner>/astrox-gmat-validation:gmat-r2026a` image, runs the image self-check, and only then exposes `GMAT_VALIDATION_IMAGE` to validation scripts. A preparation failure is reported separately from validation pytest failure.

On failure, the workflow creates or updates one open issue. On success, it does not automatically close that issue. Human review decides whether a previous health issue was transient, resolved, duplicate, or no longer relevant.

## GMAT Validation Image

The GMAT validation image workflow publishes the reproducible external-tool runtime used by scheduled SDK health. It builds from tracked container files, downloads the official pinned GMAT R2026a Linux artifact, verifies the checksum, runs a minimal GMAT propagation self-check, and publishes the stable `gmat-r2026a` tag to GHCR.

The image workflow runs on manual dispatch and on `main` changes to the container files or workflow. It does not publish images from pull requests.

## Validation Policy

Supported SDK behavior is protected by tests, not by endpoint-centered replay. Deterministic behavior tests live under `tests/sdk/`; live SDK contract and cross-validation checks live under `tests/validation/` and run in scheduled SDK health.

## Automation Principles

- Keep workflow responsibilities separate.
- Prefer one live check path for supported SDK behavior instead of duplicate endpoint replay plus tests.
- Let required PR checks control automated merges.
- Fail without creating PRs when deterministic refresh cannot produce a coherent artifact set.
- Keep generated artifacts deterministic and checked in only while they carry useful review value.
- Do not make automated PR bodies carry transient implementation plans or internal roadmap language.
