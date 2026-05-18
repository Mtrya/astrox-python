# Test Layout

The test tree is organized around the kind of confidence each test provides.

- `tests/sdk/<domain>/`: SDK-facing tests for curated public functions and their expected response/schema behavior.
- `tests/openapi/`: OpenAPI fixture tooling, generated-model maintenance, fixture discovery, and drift-report checks.
- `tests/validation/`: numerical or physics cross-validation against independent references. Add this directory when the first validation test lands.

There is no separate `tests/live/` bucket. Endpoint-facing SDK tests should be live-backed when they are meant to prove behavior; non-live tests should stay limited to SDK mechanics, generated-model tooling, and local fixture-tool behavior.
