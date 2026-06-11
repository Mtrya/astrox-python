# Test Layout

The test tree is organized around the kind of confidence each test provides.

- `tests/sdk/<domain>/`: SDK-facing tests for curated public functions and their expected response/schema behavior.
- `tests/openapi/`: OpenAPI baseline, generated-model maintenance, and drift-report checks.
- `tests/validation/`: live snapshot validation and scoped cross-validation against independent references.

There is no separate `tests/live/` bucket. Fast PR CI excludes `tests/validation`; scheduled SDK health runs it with live ASTROX configuration.
