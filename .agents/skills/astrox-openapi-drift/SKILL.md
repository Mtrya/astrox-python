---
name: astrox-openapi-drift
description: Handle small ASTROX upstream OpenAPI changes in astrox-python. Use when upstream/openapi-drift moved, a new schema field/enum/constraint/endpoint appears, or Codex must inspect latest ASTROX OpenAPI drift, update SDK code/tests/docs, design mandatory cross-validation, and distill the workflow without hiding live-server issues.
---

# ASTROX OpenAPI Drift

Use this workflow when upstream changed the ASTROX OpenAPI surface and the SDK must move with it. Treat "small change" as a disciplined evidence workflow, not as a mechanical schema copy.

## Source Order

Read the repo context before editing:

1. `AGENTS.md`
2. `docs/sdk-principles.md`
3. `docs/test-principles.md`
4. Relevant OpenAPI paths/schemas in `openapi/astrox.openapi.yaml`
5. Relevant SDK code, behavior tests, validation scripts, examples, and docs

Prefer live server behavior over OpenAPI when they disagree. Do not invent endpoints, fields, enum values, defaults, or semantics. Do not hide a server-exposed branch merely because validation is incomplete.

## Workflow

1. Inspect the upstream drift. Fetch the relevant branch or compare the checked-in OpenAPI diff. Identify the exact new/changed discriminator, property, enum, route, or schema.
2. Map the changed wire shape to existing SDK ownership. Find public constructors, endpoint functions, internal lowering helpers, accepted type unions, exports, and existing tests that already cover the same concept family.
3. Design cross-validation before implementing. Name the comparison path for each affected semantic surface: established external library, physical invariant, local derivation, or endpoint-to-endpoint invariant. For ASTROX constraints and modifiers, include every role where the SDK forwards the option.
4. Implement the smallest honest SDK change. Preserve server branch axes; use explicit Python names and unit suffixes; omit optional server fields unless supplied; keep generated models out of the public vocabulary.
5. Add behavior tests for SDK-owned behavior. Cover public exports, exact lowering, optional-key omission, type rejection where relevant, and endpoint payload embedding at every affected call site.
6. Add or update live cross-validation. The validator must include a coverage checklist, structured CLI output, and cases for each promoted semantic branch. If live behavior reveals an upstream/server issue, keep the evidence visible and adjust fixtures only when the issue is fixture-specific.
7. Update user-facing docs and examples only to the level justified by evidence. Say `callable`, `verified`, `partial`, `unresolved`, or `unknown` explicitly when that boundary matters.
8. Run focused offline tests, live cross-validation scripts, and hygiene checks. Record exact commands and outcomes in the final handoff.

## Cross-Validation Standard

Cross-validation is mandatory when the change has externally meaningful behavior and a credible comparison path exists. Do not replace it with offline payload tests or HTTP 200 checks.

For each affected surface, require:

- Behavior tests for SDK lowering and public API shape.
- Live validation or cross-validation for server behavior the SDK documentation will mention.
- Both endpoint-route and role variants when the same object can appear in multiple roles, such as `from_entity`, `to_entity`, coverage `grid_point_constraints`, and FOM shared options.
- At least one distinguishing case for every branch where the semantic claim depends on filtering, transformation, or calculation. If a branch is only callable in a non-distinguishing fixture, document that narrower state instead of promoting full semantics.

Do not use fallback exit criteria. If a planned validator is required, it must pass before the work is called complete. If it cannot pass because live upstream behavior is broken, preserve the failure evidence and report the blocker unless the user explicitly narrows the claim.

## Live Issue Handling

When a live probe fails:

- First distinguish fixture bugs from upstream behavior. Try a bounded set of better fixtures that are physically sane, epoch-aligned, and branch-relevant.
- Do not delete failing evidence just because it is inconvenient.
- Do not turn an error into a silent xfail unless the validation principle for that branch explicitly allows unresolved evidence and the user has accepted that state.
- If the user decides the error is self-documenting and not worth blocking on, keep the public claim narrow: for example, "callable in a no-access fixture" rather than "fully interval-calibrated."

## Done Means

Finish only when all applicable items are true:

- OpenAPI diff understood and mapped to SDK code paths.
- SDK runtime surface updated with idiomatic public names and honest lowering.
- Behavior tests pass for exports, constructors, optional omission, and endpoint embedding.
- Required live cross-validation passes with `CROSS_VALIDATION_FAILED=0`.
- Docs describe the new surface and validation scope without overstating semantics.
- Worktree hygiene is checked with `git status --short --branch` and `git diff --check`.
