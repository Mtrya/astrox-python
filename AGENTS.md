# AGENTS.md

This guide defines how contributors and automated agents should work in the ASTROX Python SDK repository. The goal is a Pythonic public API whose behavior is supported by checked-in OpenAPI state, focused tests, live server evidence, and semantic validation.

## Repository Map

- `openapi/astrox.openapi.yaml` is the checked-in OpenAPI baseline used by tests and model generation.
- `openapi/archive/` stores versioned OpenAPI snapshots when the upstream document changes.
- `scripts/openapi_drift/` fetches the live OpenAPI document and prepares deterministic drift reports.
- `scripts/live_smoke.py` performs a lightweight live OpenAPI and endpoint smoke check.
- `tests/sdk/` contains deterministic tests for public SDK behavior, request lowering, response parsing, and errors.
- `tests/validation/live_snapshot/` records live SDK return values so upstream drift is visible.
- `tests/validation/cross_validation/` checks semantic behavior against independent derivations, invariants, or external implementations.
- `docs/sdk-principles.md`, `docs/test-principles.md`, and `docs/docs-principles.md` define the durable SDK, validation, and documentation policies.
- `docs/getting_started.md`, `docs/how_to/`, and `docs/manual/` are the Chinese-first user documentation.
- `docs/i18n/en/` mirrors the Chinese user documentation in English.
- `docs/validation/` is the English evidence register for validation status, tolerances, residuals, and limitations.
- `docs/automated-workflows.md` defines the boundaries of repository automation.
- `.github/workflows/` contains CI, OpenAPI drift, scheduled SDK health, and release publishing workflows.

## Sources Of Truth

When sources disagree, prefer them in this order:

1. Reproducible live server behavior.
2. Focused SDK tests, live snapshots, cross-validation, and live smoke checks for the behavior they cover.
3. The current live OpenAPI response from `/openapi/v1.json`.
4. The checked-in OpenAPI baseline in `openapi/astrox.openapi.yaml`.
5. The tracked principles and workflow documentation.
6. SDK code, examples, and user documentation.

OpenAPI describes the intended wire contract; it is not proof that an endpoint works or that its output has the assumed meaning. Likewise, an existing wrapper, example, or HTTP 200 response is not proof without focused evidence. Never reinterpret `[]`, `{}`, or an ambiguous result as semantic success.

## Public Content And Repository Hygiene

1. Do not publish personal information, credentials, private URLs, local absolute paths, ignored planning material, private planning labels, temporary handoff language, or assistant/tool branding.
2. Use stable public concepts in source, tests, documentation, examples, branch names, commit messages, and pull requests. Do not expose private phase names or planning identifiers.
3. Never force-add a gitignored file. If a file is ignored, keep it out of commits unless the repository policy is deliberately changed first.
4. Do not hard-wrap Markdown prose. Preserve intentionally structured lists, tables, code blocks, and other syntax.
5. Do not freeze prose in tests unless exact wording is part of the public contract. Test the underlying decision, structure, status, or machine-readable value.

## SDK Design

Follow `docs/sdk-principles.md` when changing `astrox/`.

1. The primary public API is a set of module-level domain functions. `Client` is an advanced configuration surface, not the beginner-facing entry point.
2. Generated Pydantic models are implementation details, not the public vocabulary. Public constructors return JSON-like fragments made from ordinary Python values.
3. Endpoint functions accept curated fragments and normal Python arguments. Raw dictionaries remain an explicit escape hatch for callers who know the wire contract.
4. Public keyword arguments use `snake_case`; SDK internals translate them to ASTROX wire casing. Use explicit unit suffixes such as `_m`, `_deg`, and `_s` when units are part of the contract.
5. Endpoint functions return raw JSON-like responses by default. Add a curated response type only when it is explicit and tests prove that real server responses construct it correctly.
6. Curated constructors are strict about wire shape and light about physical feasibility. Do not turn the SDK into an astrodynamics validation library without evidence that the validation belongs in the client contract.
7. Do not hide meaningful branch axes, discriminator choices, response ambiguity, or known upstream drift merely to make a wrapper look simpler.
8. Prefer failures that expose real schema or behavior mismatches over broad fallbacks, silent coercion, defensive `.get()` chains, or speculative compatibility code.
9. Treat released public APIs as compatibility commitments within their major version. Do not add aliases, shims, dual APIs, or deprecation paths automatically; if correcting the architecture warrants a breaking change, make the tradeoff explicit and obtain a maintainer decision for the version boundary.
10. Target the smallest coherent architectural change, not merely the fewest changed lines. If the affected design is tangled, propose or perform a focused refactor instead of adding another workaround.
11. If existing conventions, documentation, and evidence do not determine the expected API shape, pause for a structured design interview with the maintainer rather than guessing.

## Evidence And Semantic Validation

Use three complementary evidence layers:

1. SDK behavior tests prove public signatures, exact request lowering, response parsing, configuration, and error behavior without requiring the live service.
2. Live snapshots preserve normalized SDK return values, including meaningful numeric values, so server drift remains visible. Do not replace values with shape-only summaries.
3. Cross-validation investigates the meaning of results through independent implementations, derivations, invariants, and targeted branch comparisons.

Cross-validation is central to semantic claims. Pursue a full understanding of the relevant units, constants, frames, origins, time conventions, model assumptions, branch semantics, axes, and tolerances instead of stopping when two arrays look close.

External libraries and independent implementations are secondary comparators, not oracles. Qualify the comparator for the specific role and branch being used, and retain checks that can reveal defects in either implementation. If the comparator appears wrong, record a minimal reproducible discrepancy and supporting evidence in the repository; do not open an upstream issue or contribute a fix automatically without maintainer direction.

Use invariants, analytic limits, plots, symmetry checks, conserved quantities, and comparisons across meaningful options when they clarify semantics. Keep local derivations small and auditable; do not duplicate the production implementation in a test and call that independent validation.

Set tolerances from explained numerical precision, algorithmic differences, and observed residuals. Never loosen a tolerance merely to make a failing comparison pass. Investigate the residual and document the reason for any tolerance change.

Large-scale fuzzing against the shared live server is prohibited. Broad exploratory probing is allowed only against a local ASTROX runtime (see `tests/validation/README.md`); findings from such exploration must be reduced to small, hypothesis-driven cases and re-confirmed against the live server before entering the committed suite. Committed tests use a small, hypothesis-driven case set that covers the important public functions and branches. Follow the bounded calibration rules in `docs/test-principles.md`; do not random-walk through payload variants in committed tests.

Classify evidence honestly as verified, partial, unresolved, or unverifiable. Structural validity without understood semantics remains partial or unresolved. Keep uncertainty and failures visible rather than silently promoting them to supported behavior.

## Testing

1. Test the actual public implementation. Avoid fake tests, meta-tests, and tests that reproduce application logic.
2. Avoid mocks where practical. A behavior test may replace only the HTTP boundary when that is necessary to prove exact request lowering or error translation; it must not simulate the domain behavior under test.
3. Exercise real parsers with representative server-shaped values and exercise cross-validation against genuinely independent evidence.
4. Prefer targeted tests while iterating. Run the full suite when release, integration, or repository-wide confidence requires it.
5. Keep network-dependent validation clearly separated from deterministic SDK tests.

## Documentation

Follow `docs/docs-principles.md`.

1. The Getting Started, How-To, and Manual layers are Chinese-first. Validation and engineering evidence are written in English.
2. English pages under `docs/i18n/en/` must faithfully mirror the corresponding Chinese source rather than introducing a separate contract.
3. User documentation explains public behavior, units, caveats, and verified scope. Investigation history and temporary maintainer notes do not belong in user-facing pages.
4. When an agent creates or materially changes Chinese documentation, use an independent second-pass reviewer prompted in Chinese before finalizing it.
5. Keep claims synchronized with examples, tests, and the validation evidence register.

## Dependencies And Automation

`pyproject.toml` is the source of truth for dependencies. Keep runtime dependencies minimal. Add validation, plotting, or comparison libraries as development dependencies with `uv add --group dev ...`, prefer established scientific packages, and document why each dependency is needed in the relevant validation evidence or pull request.

Follow `docs/automated-workflows.md` and the checked-in workflow files for automation boundaries. OpenAPI drift refreshes the recorded contract but does not establish endpoint correctness. Scheduled SDK health runs validation evidence and tracks failures. Do not silently broaden a workflow's responsibility; update its tests and documentation with the workflow.

## Investigation And Escalation

A normal bounded investigation is:

1. Send the smallest plausible payload.
2. Make one or two evidence-driven schema corrections.
3. Compare the most important enum, discriminator, or option branches.
4. Perform semantic validation once the endpoint returns usable data.
5. Record the conclusion, uncertainty, and reproducible evidence.

Stop and ask the maintainer when:

1. Strong evidence points to an upstream defect and further probing is unlikely to help.
2. The next step is a product or public API design choice rather than an evidence question.
3. Multiple plausible API shapes have meaningful tradeoffs.
4. A broad refactor is required outside the requested scope.
5. Upstream clarification would save substantial investigation.
6. Credentials, network access, permissions, or policy block the work.
7. Unrelated worktree changes make an otherwise appropriate edit or commit unsafe.

## Git And Handoffs

1. Preserve unrelated user changes and keep commits scoped to coherent milestones such as one validation slice, one OpenAPI refresh, one focused fix, or one documentation update.
2. Create a local commit after a coherent milestone only when the worktree makes that safe. Do not push unless explicitly asked.
3. For substantial SDK work, start from `origin/main` on a fresh branch named `sdk/<short-topic>` unless instructed otherwise.
4. Open pull requests only after the intended scope is complete, pushed, and locally validated. Pull requests are ready for review by default, not drafts.
5. Do not add automated-author or assistant branding to branch names, commits, pull request titles, or pull request bodies.
6. A handoff states what changed, what was verified, and what remains unresolved without referring readers to private planning material.

## Starting And Finishing Work

Read these sources before SDK work:

1. `AGENTS.md`
2. `docs/sdk-principles.md`
3. `docs/test-principles.md`
4. `docs/docs-principles.md` when documentation is in scope
5. The relevant paths and schemas in `openapi/astrox.openapi.yaml`
6. The relevant SDK code, tests, validation scripts, examples, and documentation

Before finishing, update the tests, validation snapshots, examples, documentation, and evidence register affected by the change. Report validation gaps explicitly.
