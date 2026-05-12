# OpenAPI Fixtures

This directory stores observed ASTROX wire-contract fixtures.

Fixtures refine `openapi/astrox.openapi.yaml` by recording the request branch
payloads and response shapes that the live server is expected to accept and
return. They are not semantic or numerical oracles. Normal `pytest` tests should
cover exact values, physics checks, and SDK behavior.

Use `STATUS.md` to track which endpoint nominal fixtures and branch-axis
fixtures have been handled.

No endpoint fixture records are checked in yet. Add records incrementally, one
endpoint file at a time, using this layout:

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
openapi_operation_id: OrbitConvert_Kepler2RV
branches:
  nominal:
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
      response:
        kind: json_array
        length: 6
        items:
          kind: number
```

The scheduled fixture CI should verify only wire-level behavior:

- route and method still exist
- branch payload is accepted or rejected as expected
- status code matches
- response content type is JSON when JSON is expected
- response shape matches the fixture

It should not assert exact numerical response values.
