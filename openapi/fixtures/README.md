# OpenAPI Fixtures

This directory stores observed ASTROX wire-contract fixtures.

Fixtures refine `openapi/astrox.openapi.yaml` by recording the request branch
payloads and response shapes that the live server is expected to accept and
return. They are not semantic or numerical oracles. Normal `pytest` tests should
cover exact values, physics checks, and SDK behavior.

`STATUS.md` is generated from this fixture corpus and the checked-in OpenAPI
document. Do not edit it by hand.

Add records incrementally, one endpoint file at a time, using this layout:

```text
openapi/fixtures/
  orbit_convert/
    kepler2rv.yaml
  propagator/
    ballistic.yaml
  access/
    access_compute_v2.yaml
```

Each endpoint file contains endpoint metadata and branch records:

```yaml
schema_version: 1
endpoint: /OrbitConvert/Kepler2RV
method: POST
openapi_operation_id: null
openapi_request_schema: KeplerElements
openapi_response_schema: array
branches:
  nominal:
    state: verified
    request:
      SemimajorAxis: 6778137.0
      Eccentricity: 0.0
      Inclination: 0.0
      ArgumentOfPeriapsis: 0.0
      RightAscensionOfAscendingNode: 0.0
      TrueAnomaly: 0.0
      GravitationalParameter: 398600441800000.0
    expect:
      status: 200
      content_type: application/json
      response:
        kind: json_array
        length: 6
        items:
          kind: json_number
```

Branches use explicit state:

- `state: verified` records a live-verified wire contract and must include an
  `expect` block.
- `state: blocked` records a request branch that is known not to have usable
  fixture evidence yet and must include a `blocked` block.

Blocked branches are tracked as evidence, but they are not verified coverage:

```yaml
branches:
  nominal:
    state: blocked
    request:
      Example: payload
    blocked:
      reason: empty_http_500
      observed_status: 500
      observed_content_type: ""
      observed_shape: null
      last_seen: "2026-05-15"
      note: "Valid-looking payload reaches endpoint execution but returns an empty HTTP 500."
```

Fixture files are normalized by `scripts/openapi_fixtures/normalize.py` into
plain deterministic YAML. Do not rely on YAML anchors or aliases in checked-in
fixtures.

Existing fixture branches can be reconciled against live behavior with
`scripts/openapi_fixtures/reconcile.py`. Dry-run mode emits JSON and Markdown
reports without editing files. Apply mode may refresh an existing verified
branch `expect` block or mark an existing verified branch as blocked for a
narrow non-fixturable failure such as an empty HTTP 500. It does not create
fixtures for newly discovered endpoints or automatically unblock previously
blocked branches.

Discovery coverage can be reported with
`scripts/openapi_fixtures/discovery_report.py`. It compares OpenAPI-discovered
endpoints and branch axis values against checked-in fixture request payloads.
It reports uncovered contracts and can optionally probe saved blocked branch
requests to flag branches that now look reachable, but it does not generate
new endpoint fixtures.

The scheduled fixture CI should verify only wire-level behavior:

- route and method still exist
- branch payload is accepted or rejected as expected
- status code matches
- response content type is JSON when JSON is expected
- response shape matches the fixture

It should not assert exact numerical response values.

Primitive response shapes may include `const` when a stable wire value is the
branch contract, such as `IsSuccess: false` for an observed failure-only
payload. Do not use `const` for floating point physics values, arrays, or
objects.
