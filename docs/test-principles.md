# ASTROX Test Principles

Tests are the durable evidence surface for the ASTROX Python SDK. Runtime code in `astrox/` delivers behavior that tests prove; the tests themselves are the contract. Among all tests, cross-validation is the heart because it is the only layer that turns assumptions about ASTROX behavior into evidence-backed truths.

## Definitions

`wire shape` means the JSON-compatible request or response structure ASTROX accepts or returns.

`lowering` means converting public Python inputs into the ASTROX wire shape.

`branch` means a server option, route mode, discriminator value, or public function variant that changes required inputs, units, output shape, role meaning, model behavior, or result interpretation.

`semantic claim` means a statement about what ASTROX behavior means beyond successful request construction and response shape. Examples include physics correctness, coordinate-frame interpretation, lighting geometry, access interval meaning, or agreement with an external astrodynamics model.

`comparison path` means an independent derivation, established library, physical invariant, or local reimplementation used to calibrate ASTROX behavior.

`calibration` means the active process of tuning the transparent comparison path—adjusting frames, time scales, constants, conventions, model choices, axes, or sampling—until the residual between ASTROX and the comparison path is explained.

## Test Layers

The test tree has three layers with non-overlapping jobs. No layer may be used as a substitute for another.

| Layer | Location | Question it answers | What it does NOT prove |
|-------|----------|---------------------|------------------------|
| Behavior | `tests/sdk/` | Does the SDK lower, wire, parse, and error-propagate exactly as designed? | Nothing about the live server. Tests are deterministic and offline. |
| Contract | `tests/validation/sdk_contract/` | Does the live server still return shape-compatible results for maintained public inputs? | Nothing about semantic or physical correctness. It surfaces upstream drift. |
| Cross-validation | `tests/validation/cross_validation/` | What does ASTROX behavior actually mean physically? | Nothing about whether the SDK lowers correctly. That is behavior tests. |

## Behavior Tests

Behavior tests are the foundation. They monkeypatch `astrox.raw` and prove SDK-owned transformations exactly.

A behavior test for a public function must prove five things:

1. **Exact lowering.** The emitted payload matches the canonical expected payload. Comparison is canonical JSON byte-for-byte, not loose shape.
2. **Parser discipline.** If the function has a curated response parser, the test proves it constructs the object correctly from a representative payload and fails loudly (`KeyError`, `TypeError`) when required fields are missing or mistyped.
3. **Type rejection.** Raw fragments are rejected at the public boundary. Passing a list instead of a `KeplerianElements` instance must raise `TypeError`.
4. **Optional-key omission.** Omitted optional arguments are truly omitted from the lowered payload, not sent as `null` or default values.
5. **Error propagation.** `AstroxAPIError` bubbles through the curated surface unchanged. The SDK does not swallow, rewrap, or lose server errors.

Behavior tests must not assert server semantics. They must not claim a mock return value is "correct physics." They must only assert that the SDK transforms and transports values correctly.

## Contract Tests

Contract tests are live drift detectors. Each script constructs public SDK inputs, calls live ASTROX through the public SDK, normalizes the return, and compares it with a committed sidecar snapshot.

Contract tests prove that the live server still returns shape-compatible results for inputs the SDK maintains. They do not prove physical correctness. A passing contract test is not a semantic guarantee.

Snapshots are sidecar `.snap.json` files checked into the repo. They can be `--check`ed or `--refresh`ed. Large arrays are normalized to avoid snapshot bloat. Case IDs must be stable.

## Cross-Validation Tests

Cross-validation is the heart of the test infrastructure. It is mandatory for a branch when that branch has externally meaningful semantics and a credible comparison is feasible.

### Coverage Standard

The standard is comprehensive: for every branch, every response field that carries externally verifiable meaning, and every input parameter that affects the result, there must be a cross-validation case. The goal is to cover at least 90% of semantic detail in every branch.

The remaining 10% is only justified when a credible comparison is genuinely impossible. It is not a convenience bucket for untested cases.

Prefer at least two distinct values for every parameter that affects the result, and at least three cases spanning the expected operational envelope of the branch. Do not claim a branch family is calibrated from one benign happy path.

### Calibration

Calibration is the active process of turning assumptions into evidence-backed truths. The agent should seek mismatch proactively, not wait for it to appear by accident.

Start with the most obvious external convention and expect it to fail. Deliberately vary the most important parameter across at least two values and the branch axis across at least two branches. When mismatch appears, tune the transparent comparison path one adjustment at a time. Document each adjustment in a code comment.

The bounded investigation limit is three external adjustments plus two branch-variant probes per branch. If no explainable residual is found after that budget, mark the case `unresolved` and stop. Do not random-walk parameters.

Tolerances are precision bounds for an explained comparison. They are set at the start based on the comparison's claimed precision. They are never widened to absorb an unexplained residual, a unit mistake, a frame confusion, or a branch misunderstanding.

If the residual is stable and can be characterized as "ASTROX does X instead of Y," that is valid calibration. Document the observed ASTROX convention. Do not judge ASTROX against a textbook; the goal is to understand what ASTROX actually does.

### Evidence States

Cross-validation coverage is tracked in a coverage checklist inside each script. Every branch, field, and parameter is marked with one of four states:

- `verified` — The residual is explained, the comparison is documented, and the test passes.
- `partial` — Some fields or branches are verified; others are explicitly marked as still pending.
- `unresolved` — The residual is unexplained after a bounded investigation. The case is kept visible, typically via `pytest.mark.calibration` and `xfail(strict=True)`, with investigation notes preserved in code comments. An unresolved case may ship if in-depth investigation has been performed and comments carry the investigation notes and insights.
- `unverifiable` — No credible comparison path exists. This state requires maintainer sign-off; an agent may not mark a case unverifiable on its own.

### Local Derivations

Local second implementations are encouraged and often preferable to external libraries, especially for ASTROX-unique features. A local derivation that perfectly matches ASTROX is valuable evidence: it means we have gained full understanding of ASTROX's behavior.

A local derivation must satisfy three rules:

1. **Independence.** It may use the same inputs as ASTROX, but its model path—equations, sampling, transformations—must be independent. It must not read ASTROX response fields to set its own parameters.
2. **Reviewability.** It should fit in the same script or a nearby helper module and be small enough to audit in one sitting. Complex derivations should be broken into independently testable functions.
3. **Explicit assumptions.** Every assumption (spherical Earth, neglecting nutation, first-order approximation, etc.) must be stated in a comment. This makes it obvious when an unexplained residual is due to a violated assumption.

A derivation must expose its knobs—constants, frame choices, conventions—so they can be tuned during calibration. A derivation with hardcoded untunable choices is a bad derivation.

External libraries are also acceptable when they are established, auditable, and their conventions are discoverable. New dev dependencies are added with `uv add --group dev` and documented in the script's module docstring.

### Coverage Checklist Format

Each cross-validation script includes a structured coverage checklist in a docstring or comment block after the module docstring:

```
Coverage:
  Branches:
    - single_j2: verified
    - multi_j2: verified
    - j2 with Cartesian state: unresolved
  Fields (single_j2):
    - Period: verified (compared against analytical secular model)
    - Position.cartesian_velocity: verified (position/velocity samples)
    - Position.epoch: unverifiable (server echo, no physics meaning)
  Parameters:
    - j2_normalized_value: verified (calibrated effective value documented)
    - ref_distance_m: verified
    - coord_system: partial (Inertial verified, Fixed unresolved)
  Comparison:
    - External: analytical J2 secular model with corrected mean motion
    - Constants: EARTH_MU, EARTH_RADIUS_M, ASTROX_EFFECTIVE_J2_NORMALIZED_VALUE
    - Tolerances: POSITION_ABS_M=0.05, VELOCITY_ABS_M_S=5.0e-5
```

## Naming and Organization

Cross-validation test functions:
```
test_<branch>_matches_<comparison>
```

Cross-validation test files:
```
test_<branch>_<comparison_tool>.py
```
If a branch uses different comparison tools, separate them into multiple files.

Behavior test functions:
```
test_<function>_<property>
```

Contract test functions:
```
test_<function>_sdk_contract
```

Never name a cross-validation test `test_<function>_works` or `test_<function>_returns_correct_result`. "Works" and "correct" hide the comparison path and the calibration effort.

## Structured Output Conventions

Cross-validation and contract scripts are runnable as standalone CLIs. They should emit parseable output:

- Cross-validation on success: `CROSS_VALIDATION_CHECKED=<int>` and `CROSS_VALIDATION_FAILED=0`
- Cross-validation on failure: `CROSS_VALIDATION_FAILED=<exception_name>: <message>` to stderr
- Contract on success: `SDK_CONTRACT_CHECKED=<int>`
- Contract on refresh: `SDK_CONTRACT_REFRESHED=<int>`
- Contract on failure: `SDK_CONTRACT_FAILED=<exception_name>: <message>` to stderr

Contract scripts should accept `--check` and `--refresh` as standard CLI flags.

## Anti-patterns

- Setting tolerance by observing the first residual and rounding up. Tolerances are precision bounds for an explained comparison, not a retrospective fit.
- Deleting a failing cross-validation case because it has been failing for a while. Unresolved evidence is valid work product when it preserves the mismatch.
- Writing behavior tests that assert a mock return value is "correct physics." Behavior tests prove SDK transformations, not server semantics.

## Appendix: Cross-Validation Implementation Checklist

When adding cross-validation for a new branch, follow this sequence:

1. Identify the branch family. List every branch axis that changes interpretation.
2. List response fields. For each branch, list every field that carries externally verifiable meaning.
3. Choose comparison paths. For each field and branch, decide: established library, local derivation, physical invariant, or cross-endpoint check. Document why.
4. Write the naive comparison. Start with the most obvious external convention. Expect it to fail.
5. Seek mismatch. Vary the most important parameter across at least two values. Vary the branch axis across at least two branches.
6. Calibrate. When mismatch appears, adjust the external side one change at a time. Document each adjustment in a code comment.
7. Set tolerances. Tolerances are precision bounds for the explained comparison. Never widen to absorb an unexplained residual.
8. Fill the coverage checklist. Mark each field and branch as `verified`, `partial`, `unresolved`, or `unverifiable` (maintainer sign-off required for `unverifiable`).
9. Add `main()` and structured output. Ensure the script is runnable standalone with the standard output conventions.
10. Write behavior tests. Only after the cross-validation comparison is stable, add deterministic SDK behavior tests for lowering, parsing, and type rejection.
