# ASTROX SDK Principles

This document records stable design principles for the public Python SDK surface. It is not an implementation roadmap.

## Public Shape

The SDK should feel like a Python package. The primary public API is module-level domain functions organized around user tasks:

```python
from astrox import propagator, orbits

result = propagator.j2(
    start="2026-01-01T00:00:00Z",
    stop="2026-01-01T01:00:00Z",
    orbit=orbits.keplerian(...),
)
```

`Client` is an advanced configuration surface, not the main beginner-facing concept. Users should be able to use the package without explicitly managing a client for ordinary calls.

## Models And Payloads

Generated Pydantic models are internal implementation details. They are not the public SDK vocabulary, and user-facing docs should not require users to understand both generated model classes and JSON-like Python values.

Curated public constructors should return JSON-like request fragments made of ordinary Python values. Endpoint functions should accept those fragments and normal Python arguments. Raw dictionaries may be accepted as an escape hatch for advanced users who know the wire contract, but they are not the documented primary style.

Public keyword arguments use `snake_case`. The SDK translates to ASTROX wire casing internally. Curated constructors should use explicit unit suffixes such as `_m`, `_deg`, and `_s` when units are part of the public contract.

## Scope Of Interpretation

The SDK should perform near-zero semantic preprocessing or postprocessing. It may normalize Python interface details, assemble request payloads, add required wire discriminators, and handle network concerns. It should not hide meaningful API options or silently reinterpret ambiguous server results.

Curated constructors are strict about wire shape and light about physics semantics. They should catch missing required fields, invalid option names, wrong container shapes, and mutually exclusive choices. They should not become an astrodynamics validation library unless server behavior and documented contract evidence justify that validation.

Endpoint functions return raw JSON-like API responses by default. Curated response parsing must be explicit and backed by tests proving that server responses can construct the curated response object.

## Coverage And Honesty

Public SDK surfaces must be backed by verified evidence for the behavior they advertise. A function does not need coverage for every OpenAPI branch cross-product, but every documented parameter value, branch mode, constructor, and response parser must be supported by fixture or validation evidence.

Endpoint names should use Python and domain language rather than mechanically mirror OpenAPI operation names, but every public endpoint function must have a clear backing route or operation.

Curated wrappers are not added merely because an OpenAPI endpoint exists. Raw and fixture-verified access can exist before a polished SDK abstraction is ready.

## Non-Goals

- Do not make generated Pydantic models the public SDK vocabulary.
- Do not require users to hand-craft JSON for ordinary documented workflows.
- Do not make `Client` the main beginner-facing concept.
- Do not teach raw JSON in examples unless the example is explicitly raw or advanced.
- Do not add curated wrappers just because an OpenAPI endpoint exists.
- Do not claim semantic or physics correctness from wire-shape verification alone.
