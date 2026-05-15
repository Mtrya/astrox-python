---
name: openapi-drift-fixture-requests
description: Add ASTROX OpenAPI drift fixture coverage by authoring candidate request payloads and letting repo tools write verified or blocked branch evidence. Use when working in astrox-python on uncovered STATUS.md entries, fixture request blocks, branch-axis coverage, or scripts/openapi_drift probe/reconcile/status workflows.
---

# OpenAPI Drift Fixture Requests

Use this skill in `astrox-python` when adding coverage for `[ ]` entries in `openapi/fixtures/STATUS.md`.

The current division of labor is:

- human or agent authors the candidate `request` payload
- `scripts/openapi_drift/probe_request.py` probes live behavior and writes either `expect` or `blocked`
- `scripts/openapi_drift/generate_status.py` writes `STATUS.md`

Do not edit `STATUS.md` by hand.

## Quick Workflow

1. Pick one target from `openapi/fixtures/STATUS.md`. Prefer a missing nominal endpoint or one uncovered axis/value for an endpoint with an existing nominal fixture.

2. Inspect current discovery and nearby fixture patterns:

   ```bash
   uv run python scripts/openapi_drift/discovery_report.py \
     --json-output /tmp/astrox-discovery.json \
     --markdown-output /tmp/astrox-discovery.md
   ```

   Also inspect the relevant schema in `openapi/astrox.openapi.yaml` and sibling fixture files under `openapi/fixtures/`.

3. Write the smallest plausible branch request as YAML or JSON. Keep the branch focused on the target axis/value. Do not invent endpoints, enum values, discriminator tags, or response fields.

4. Dry-run the candidate:

   ```bash
   uv run python scripts/openapi_drift/probe_request.py \
     --fixture openapi/fixtures/<group>/<endpoint>.yaml \
     --branch <branch_name> \
     --request-file /tmp/request.yaml \
     --dry-run
   ```

5. Apply only when the dry-run classification is expected:

   ```bash
   uv run python scripts/openapi_drift/probe_request.py \
     --fixture openapi/fixtures/<group>/<endpoint>.yaml \
     --branch <branch_name> \
     --request-file /tmp/request.yaml \
     --apply
   ```

   For a new fixture file, include `--endpoint /Path` and `--method POST` or the correct method.

6. Verify deterministic outputs:

   ```bash
   uv run python scripts/openapi_drift/normalize.py --fixture-dir openapi/fixtures --check
   uv run python scripts/openapi_drift/generate_status.py \
     --openapi openapi/astrox.openapi.yaml \
     --fixture-dir openapi/fixtures \
     --output openapi/fixtures/STATUS.md \
     --check
   uv run python scripts/openapi_drift/verify.py
   uv run python -m pytest -q tests/test_openapi_fixtures.py
   ```

## Branch Outcomes

`probe_request.py --apply` may write:

- `state: verified` with an automatically generated `expect` block when the response has a supported JSON or text wire shape
- `state: blocked` for narrow non-fixturable failures such as an empty HTTP 500

Ambiguous results are reported, not written. Previously blocked branches may be promoted only through an explicit `probe_request.py --apply --replace` run.

## Request Rules

- For `GET`, `request` is query parameters and must be an object or null.
- For non-GET methods, `request` is sent as JSON.
- Use direct schema and fixture evidence; do not infer semantic success from HTTP 200, `{}`, or `[]`.
- Fixtures assert wire shape only, not exact physics or floating-point values.
