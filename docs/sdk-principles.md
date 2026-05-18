# ASTROX SDK Principles

This document records stable design principles for the public Python SDK surface. It is not an implementation roadmap.

## Public Shape

The SDK should feel like a Python package. The primary public API is module-level domain functions organized around user tasks:

```python
from astrox import propagator, orbits

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=28.5,
    argument_of_periapsis_deg=0.0,
    raan_deg=0.0,
    true_anomaly_deg=0.0,
)

period_s, position = propagator.j2(
    start="2026-01-01T00:00:00Z",
    stop="2026-01-01T01:00:00Z",
    orbit_epoch="2026-01-01T00:00:00Z",
    orbit=orbit,
)
```

`Client` is an advanced configuration surface, not the main beginner-facing concept. Users should be able to use the package without explicitly managing a client for ordinary calls.

## Models And Payloads

Generated Pydantic models are internal implementation details. They are not the public SDK vocabulary, and user-facing docs should not require users to understand both generated model classes and SDK-owned public objects.

Curated public constructors should return SDK-owned Python value objects, normally frozen stdlib dataclasses, when the concept deserves an object. These objects may expose explicit wire-lowering methods such as `to_wire()` for inspection and endpoint assembly, but they should not behave like generated transport schemas. Raw dictionaries belong in the raw route layer, not as a parallel documented style for curated functions.

Public keyword arguments use `snake_case`. The SDK translates to ASTROX wire casing internally. Curated constructors should use explicit unit suffixes such as `_m`, `_deg`, and `_s` when units are part of the public contract.

Curated endpoint implementations should stay thin and explicit. Prefer writing endpoint payload keys and response field access directly in the function that owns the route. Do not introduce generic request builders, casing mappers, endpoint-helper frameworks, or hand-written request/response envelope dataclasses unless a later repeated pattern proves they remove real complexity.

## Scope Of Interpretation

The SDK should perform near-zero semantic preprocessing or postprocessing. It may normalize Python interface details, assemble request payloads, add required wire discriminators, expose SDK-owned value objects, and handle network concerns. It should not hide meaningful API options, silently reinterpret ambiguous server results, or pre-validate values that the ASTROX server should own.

Curated constructors are strict about wire shape and light about physics semantics. They should catch missing required fields, invalid option names, wrong container shapes, and mutually exclusive choices. They should not become an astrodynamics validation library unless server behavior and documented contract evidence justify that validation.

Raw route calls return raw JSON-like API responses. Curated endpoint functions should return Pythonic success-path values when fixture-backed response construction is stable enough. Curated response parsing must be explicit and backed by tests proving that server responses can construct the SDK-owned value object. Curated functions may temporarily return raw JSON-like responses only when a surface is not mature enough for success-path values, and that maturity caveat should be explicit.

## Coverage And Honesty

Public SDK surfaces must be backed by verified evidence for the behavior they advertise. A function does not need coverage for every OpenAPI branch cross-product, but every documented parameter value, branch mode, constructor, and response parser must be supported by fixture or validation evidence.

Endpoint names should use Python and domain language rather than mechanically mirror OpenAPI operation names, but every public endpoint function must have a clear backing route or operation. Default to one curated public function per endpoint. Split one endpoint into multiple public functions only when a verified endpoint-level branch axis changes the meaning, units, or requiredness of public parameters enough that one function would become unclear.

Curated wrappers are not added merely because an OpenAPI endpoint exists. Raw and fixture-verified access can exist before a polished SDK abstraction is ready.

## Non-Goals

- Do not make generated Pydantic models the public SDK vocabulary.
- Do not require users to hand-craft JSON for ordinary documented workflows.
- Do not expose raw dictionaries as a parallel documented style for curated endpoint functions.
- Do not make `Client` the main beginner-facing concept.
- Do not teach raw JSON in examples unless the example is explicitly raw or advanced.
- Do not add curated wrappers just because an OpenAPI endpoint exists.
- Do not claim semantic or physics correctness from wire-shape verification alone.
- Do not create endpoint request or response envelope dataclasses merely to mirror OpenAPI transport shapes.
- Do not add generic helper frameworks before repeated endpoint implementations prove the abstraction is needed.
