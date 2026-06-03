# OpenAPI Drift Workflow Refactor Plan

This document records the simplified direction for OpenAPI drift automation.

The old workflow tried to combine OpenAPI refresh, fixture replay, fixture inventory reporting, pull request creation, and test hosting. The refactor splits those concerns:

- OpenAPI drift workflow: deterministic OpenAPI refresh PRs.
- Normal PR CI: merge gate for drift PRs.
- Scheduled SDK health workflow: scheduled CI-like live health check when no OpenAPI drift PR is involved.
- Fixtures: reference-only discovery evidence during the transition to stronger tests.

## Final Decision Tree

```text
OpenAPI drift workflow
  Fetch live OpenAPI
    fetch or validation fails
      fail workflow
      no pull request
      no issue by default

    fetch succeeds
      stable live OpenAPI equals checked-in baseline
        exit successfully
        no pull request
        no issue
        no fixture replay
        no tests

      stable live OpenAPI differs from checked-in baseline
        regenerate deterministic drift artifacts
          refresh fails
            fail workflow
            no pull request

          refresh succeeds
            create or update drift pull request
            enable native GitHub auto-merge
            rely on required PR CI checks to merge or block
```

```text
Scheduled SDK health workflow
  Run CI-like SDK health checks on schedule or manual dispatch
    checks pass
      exit successfully
      do not close existing issue automatically

    checks fail
      create or update one tracking issue
      fail workflow
```

## OpenAPI Drift Workflow

The drift workflow owns:

- fetching the live OpenAPI document
- validating that the fetched document is usable
- detecting whether the stable fetched document differs from `openapi/astrox.openapi.yaml`
- updating `openapi/astrox.openapi.yaml` when the schema changed
- writing an archive snapshot in `openapi/archive/`
- regenerating `openapi/fixtures/STATUS.md` while that transitional fixture inventory exists
- producing a short report artifact and pull request body
- creating or updating the drift pull request
- enabling native GitHub auto-merge on deterministic refresh PRs

The drift workflow does not own:

- fixture replay
- full pytest runs
- package build/import checks
- live smoke checks
- SDK semantic validation
- classifying refresh PRs as needing intervention
- creating issues for live SDK health failures

If OpenAPI changed but deterministic refresh fails, the workflow should fail without creating a pull request. A partial refresh PR is more dangerous than a failed workflow.

If OpenAPI changed and deterministic refresh succeeds, the workflow should create or update a ready-to-review pull request and run `gh pr merge --auto` for that pull request. Repository rules and required PR checks decide whether the PR actually merges.

## Drift PR Body

The drift PR body should stay short:

- OpenAPI version before and after
- changed tracked files
- generated `STATUS.md` summary while the file exists
- statement that normal PR CI is the merge gate
- link or note for the workflow artifact

The body should not include a verdict line. Auto-merge state and CI status are visible in GitHub.

## Scheduled SDK Health Workflow

The scheduled SDK health workflow is separate from OpenAPI drift.

It should mirror current CI closely enough to catch live regressions:

- build package
- verify built package import
- run `pytest tests`
- run `scripts/live_smoke.py`

On scheduled failure, it should create or update one tracking issue. On success, it should not automatically close that issue.

This workflow is the replacement for the earlier idea of running tests from the OpenAPI drift workflow when the OpenAPI document has not changed.

## Fixture Policy

Fixture replay is removed from the OpenAPI drift workflow.

Existing fixture YAML remains useful as reference-only discovery evidence and as seed material for future tests. It is no longer a scheduled drift gate.

The long-term direction is tracked in https://github.com/Mtrya/astrox-python/issues/37:

- promote useful fixture coverage into tests
- make tests protect supported SDK behavior with shape and behavioral assertions
- retire fixture branches that no longer provide useful evidence
- retire `openapi/fixtures/STATUS.md` and its generated inventory mechanism once tests are mature enough to replace fixture coverage tracking

During the transition, OpenAPI drift PRs should still regenerate `openapi/fixtures/STATUS.md` so checked-in generated files remain self-consistent. This is temporary maintenance of the existing fixture mechanism, not a long-term drift gate.

## Implementation Plan

1. Simplify `.github/workflows/openapi-drift.yml`.
   - Keep dependency setup, OpenAPI fetch, deterministic status regeneration, report artifact upload, PR creation/update, and auto-merge enablement.
   - Remove fixture reconciliation, fixture replay, focused drift checks, and pytest.
   - Fail before PR creation if fetch or deterministic generation fails.

2. Simplify or replace `scripts/openapi_drift/drift_pipeline_report.py`.
   - Report no-op versus refresh-required.
   - Summarize changed files and OpenAPI version transition.
   - Generate a short PR body.
   - Stop accepting test outcomes and fixture reconciliation as merge classification inputs.

3. Add a scheduled SDK health workflow.
   - Mirror CI checks.
   - On failure, create or update one issue.
   - Do not close the issue automatically on success.

4. Update tests for the simplified report behavior.
   - Prefer testing machine-readable decisions and structure instead of exact prose.

5. Validate locally.
   - Parse workflow YAML.
   - Run focused report tests.
   - Run the full test suite if shared report code changed broadly.
