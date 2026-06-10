# ASTROX SDK Principles

This document defines stable design principles for the ASTROX Python SDK.

## Core Rule

Design the SDK, not the service:

1. Let requests and responses pass through.
2. Expose whatever the server exposes.

## Definitions

`wire shape` means the JSON-compatible request or response structure ASTROX accepts or returns.

`lowering` means converting public Python inputs into the ASTROX wire shape.

`curated surface` means the Pythonic public API the SDK recommends for ordinary users.

`raw surface` means route-level JSON access `astrox.raw`, where callers intentionally work with ASTROX payloads directly.

`branch` means a server option, route mode, discriminator value, or public function variant that can change required inputs, units, output shape, role meaning, model behavior, or result interpretation.

`semantic claim` means a statement about what ASTROX behavior means beyond successful request construction and response shape. Examples include physics correctness, coordinate-frame interpretation, lighting geometry, access interval meaning, or agreement with an external astrodynamics model.

## Public Shape

The primary public API is module-level domain functions organized around user tasks:

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

Public names should use domain language and idiomatic Python. Public keyword arguments use `snake_case`. Use explicit unit suffixes such as `_m`, `_deg`, and `_s` whenever the value has a unit.

Public request values are ordinary Python values plus small SDK-owned Python objects when an object makes a repeated domain concept easier to compose, inspect, or reuse. A good SDK-owned object has a clear domain name, discoverable fields, predictable equality, and an explicit `to_wire()` method when callers may need to inspect the ASTROX request fragment. Do not create an object merely to mirror an OpenAPI request envelope.

Raw dictionaries belong to raw or explicitly advanced surfaces. Curated endpoint functions should accept the Python values and SDK-owned objects they document.

## Runtime Boundary

Validate only what would prevent the SDK from lowering and sending the request correctly. Everything else is server-owned.

SDK-owned validation includes object type checks, mutually exclusive SDK arguments, sequence and mapping shape needed for deterministic lowering, SDK-owned branch or discriminator spelling, and fields consumed by an explicit response parser. SDK-owned validation does not include physical feasibility, server support policy, empty-container meaning, model correctness, orbit validity, time validity, or whether a server-exposed option is recommended.

If the SDK can lower a value without interpreting it, send it to ASTROX and let ASTROX respond. For example, an empty array, an unusual string option, or a physically questionable orbit should not be rejected by runtime code merely because the SDK has not proven its semantic meaning.

Optional server fields should be omitted unless the caller supplies them. Omission keeps server defaults owned by the server and makes SDK behavior easier to test.

Do not hide a server-exposed branch merely because it is untested, not yet recommended, or not yet semantically understood. If the SDK can represent the branch clearly and lower it honestly, preserve the branch in the curated surface or an explicit advanced surface. Use tests, validation, and docs to say what is proven; do not use runtime omission as a substitute for evidence.

The narrow reasons to keep a branch out of the curated surface are implementation-specific: the SDK cannot lower it unambiguously, the public shape would mislead users about meaning, or the branch is intentionally left to the raw surface until its Python interface can be designed clearly.

## Thin Implementation

Endpoint implementations should be thin, explicit, and local. Prefer writing route paths, payload keys, discriminator values, and consumed response fields in the function that owns the route.

The SDK owns ergonomic request construction, role wiring, casing translation, discriminator insertion, optional-key omission, and explicit response parsing when a response object is intentionally designed. It does not own broad normalization, scientific correction layers, server support classification, or generic policy engines.

Do not introduce generic request builders, casing frameworks, endpoint registries, or broad helper layers before repeated endpoint implementations prove that the abstraction removes real complexity.

Do not flatten away meaningful API options. If a server branch changes required inputs, units, result meaning, role meaning, or interpretation, the public API should preserve that distinction with explicit names or objects instead of hiding it behind vague mode/value pairs.

## Responses

Raw route calls return raw JSON-like API responses.

Curated endpoint functions may also return raw JSON-like dictionaries when response parsing would imply more understanding than the SDK has evidence for. When they do, tests and docs must treat the raw return policy as intentional and avoid promising fields beyond what has been validated.

Add curated response parsing only when the success-path value is intentionally designed and backed by representative server-shaped response tests. A parser must fail loudly when required consumed fields are missing or incompatible.

Do not treat `[]`, `{}`, HTTP 200, or `IsSuccess: true` as semantic proof. They can prove that a route responded; they cannot prove that the returned behavior means what users think it means.

## Evidence Layers

Evidence is layered. Each layer answers a different question and should not be used as a substitute for another layer.

`examples/` can be used early as public API shape sketches. Early examples are discussion artifacts for finding the most usable Python interface with the maintainer; they are not evidence that the behavior is implemented, validated, or recommended. Final examples are different: they should demonstrate the implemented SDK style users are expected to copy.

`astrox/` is runtime SDK code. It implements the settled public shape, lowers Python inputs to ASTROX wire payloads, calls routes, and constructs intentionally designed response values. It is not the evidence source for server semantics.

`tests/sdk/` contains deterministic SDK behavior tests. These tests protect SDK self-consistency: public imports, call style, exact request lowering, optional-key omission, branch and discriminator wiring, parser behavior, raw response policy, and error propagation. When the SDK owns a transformation, compare the complete emitted payload or return snapshot, not only loose shape.

`tests/validation/sdk_contract/` contains live SDK contract validation. Each script constructs public SDK inputs in Python, calls live ASTROX through the public SDK, normalizes the SDK return, and compares that return with a committed sidecar snapshot. This layer surfaces upstream server behavior drift for maintained public SDK cases. It does not prove physical or semantic correctness.

`tests/validation/cross_validation/` contains semantic cross-validation. Each script compares live ASTROX behavior with an external library, trusted tool, physical invariant, or independent local derivation. This layer calibrates what ASTROX behavior appears to mean.

`docs/sdk/` is user-facing documentation. It should make the recommended path obvious and may also document other callable branches when that helps users understand choices, scope, and caveats. It must distinguish validated behavior from behavior that is merely callable or still unexplained.

The sequence is allowed to loop, but claims must not outrun evidence. If later validation changes the understanding of a branch, update runtime code only when SDK lowering or parsing was wrong, then update behavior tests, contract validation, cross-validation, docs, and examples as appropriate.

## Cross-Validation

Cross-validation is mandatory for a branch when that branch has externally meaningful semantics and a credible comparison is feasible. A credible comparison may use an established external library, a trusted external tool, a physical invariant, or a local reimplementation that is small enough to review.

Cross-validation compares live ASTROX behavior with the independent comparison path. It is not a snapshot check. It should state the units, constants, frame, origin, axis convention, time scale, model assumptions, and tolerance that make the comparison meaningful.

Coverage must be broad enough for the branch being promoted. Do not claim a branch family is calibrated from one benign happy path when meaningful axes remain unchecked. Prefer multiple branches and multiple cases per branch when the endpoint exposes branch axes that can change behavior.

When ASTROX and the comparison path differ, investigate the difference. Tune the comparison path when the external side is the transparent side: adjust frames, time scales, constants, model choices, axes, event definitions, or sampling until the residual is explained. Calibration starts at the mismatch.

Tolerances are precision bounds for an explained comparison. Do not widen tolerances to absorb unknown frame choices, unit mistakes, model differences, time-scale differences, branch confusion, or SDK parsing errors. Do not hand-select only benign cases to make a comparison pass.

If the residual cannot be explained after a bounded investigation, keep the case marked as unresolved and visible. Do not delete the case merely because it fails. Unresolved cross-validation evidence is valid work product when it clearly preserves the mismatch and prevents accidental claims of understanding.

## Docs And Examples

Public docs should describe the Python interface, units, return policy, recommended path, and caveats. They may be comprehensive, but they must not turn runtime callability into a semantic guarantee.

Final examples should be copyable demonstrations of the style users should imitate. If a branch is callable but not yet understood well enough to recommend, prefer documenting its caveat in `docs/sdk/` instead of making it a main example.

Docs and examples should use user-facing language. Do not expose internal planning labels, validation bookkeeping terms, or temporary implementation notes as if they were product concepts.

Do not freeze prose in tests unless exact wording is the contract. Prefer testing runnable examples, public imports, payload construction, return shape, and machine-readable outputs.

## Implementation Sequence

Use this sequence when developing a new curated SDK surface:

1. Sketch the desired public API shape in `examples/` when discussion with the maintainer would clarify the most usable interface.
2. Implement the settled runtime surface in `astrox/` with thin lowering, minimal SDK-owned validation, explicit route calls, and intentional response policy.
3. Add `tests/sdk/` behavior tests for SDK-owned lowering, wiring, parsing, raw return policy, and error propagation.
4. Add `tests/validation/sdk_contract/` cases and sidecar snapshots for maintained public SDK calls so live upstream drift surfaces.
5. Add `tests/validation/cross_validation/` cases for semantics-sensitive branches whenever credible comparison is feasible.
6. Revisit `astrox/` only if behavior tests or validation reveal an SDK lowering, wiring, public-shape, or parser problem.
7. Write or update `docs/sdk/` with the implemented interface, units, return policy, recommended path, and caveats that match the evidence.
8. Tighten final `examples/` so they demonstrate the actual implemented SDK code and the style users should copy.

The workflow details for carrying out these steps belong in an agent skill or task-specific plan. This document records the stable principles and ownership boundaries.

## Non-Goals

- Do not make `Client` the main beginner-facing concept.
- Do not require ordinary users to handcraft ASTROX JSON for curated workflows.
- Do not use runtime SDK code to decide server support, readiness, or semantic validity.
- Do not hide server-exposed options solely because validation is incomplete.
- Do not claim semantic correctness from snapshots, HTTP 200, empty arrays, or payload-shape tests alone.
- Do not add generic helper frameworks before repeated implementations prove they are worth it.
- Do not preserve a misleading public shape for backward compatibility during the pre-milestone SDK architecture phase.
