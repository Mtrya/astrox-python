# ASTROX Documentation Principles

User-facing documentation is the primary interface for the ASTROX Python SDK. It must be user-facing without internal jargons. It must be honest about what is verified, clear about what is convention, and never claim what tests do not prove.

## Documentation Layers

The documentation tree has four layers with non-overlapping jobs.

| Layer | Location | Audience | Content | Language |
|-------|----------|----------|---------|----------|
| Getting Started | `docs/getting_started.md` | First-time user | One runnable end-to-end example. Install, configure, propagate an orbit, print a position. | Chinese |
| How-To | `docs/how_to/*.md` | Task-oriented user | Cross-domain task guides. Each solves one specific problem completely. | Chinese |
| Manual | `docs/manual/<domain>/*.md` | User who wants the full story | Per-function comprehensive walkthrough grouped by domains. Concepts → API reference → algorithms (only if verified). | Chinese |
| Validation | `docs/validation/*.md` | Maintainer, advanced user | What is verified, against what, known residuals, coverage status. | English |

No layer may substitute for another. A user should be able to follow Getting Started without reading Manual, and a maintainer should be able to read Validation without reading How-To.

## Content Boundaries

### Getting Started

- One complete runnable script.
- No optional arguments, no branches, no caveats.
- Goal: a new user runs this in five minutes and sees output.

### How-To

- States the goal in the title.
- Shows minimal working code.
- Explains the one or two decisions the user must make.
- Links to Manual for background and Validation for evidence.
- Does not discuss calibration residuals, frame conventions, or investigation narratives.

### Manual

- Concepts: what this domain is, when to use it, how it relates to other domains.
- API reference: function signatures, argument tables, return types, minimal examples.
- Algorithms: underlying math or physics only when cross-validation has verified the behavior. Unverified algorithms are marked `unverified` or omitted.
- Convention notes: one-sentence neutral statements about ASTROX conventions (frame interpretations, advance rules, coordinate definitions).
- Does not contain investigation narratives, residual discussions, or calibration history.

### Validation

- Cross-validation results per branch.
- Known residuals with explanations.
- Frame and convention discoveries from calibration.
- Coverage status and comparison paths.
- Links to relevant cross-validation scripts in `tests/validation/cross_validation/`.
- Does not contain usage examples or API signatures.

## Convention vs. Investigation

Content in current `docs/sdk/*.md` must be split according to this rule:

- **Convention statements** stay in Manual as neutral one-sentence asides. Example: "For SGP4 results, `position.reference_frame == 'INERTIAL'` corresponds to GCRF/GCRS-style inertial coordinates."
- **Investigation narratives** move to Validation. Example: "Cross-validation against Skyfield confirms the sign and units for representative cases. An arcsecond-scale residual remains visible after frame and light-time diagnostics."

If a sentence describes what ASTROX does, it is a convention. If a sentence describes how we discovered it or what remains unexplained, it is an investigation narrative.

## Evidence Honesty

Documentation must not claim what tests do not prove.

- If a branch is `verified` in the coverage checklist, the Manual may describe its behavior as documented.
- If a branch is `partial`, `unresolved`, or `unverifiable`, the Manual must mark it as such or omit the claim.
- The Manual must not say "correct" or "accurate" unless cross-validation has established a comparison path. Say "ASTROX returns" or "the result is" instead.
- How-To guides may use verified branches as recommended paths. Unverified branches should not appear in How-To unless clearly marked.

## Voice and Tone

- **Getting Started:** Encouraging, imperative, minimal. Assume the user knows Python but not astrodynamics.
- **How-To:** Direct, task-oriented. "Do X to achieve Y."
- **Manual:** Precise, informative. Explain concepts before showing code. Use explicit unit suffixes (`_m`, `_deg`, `_s`) matching the public API.
- **Validation:** Evidence-backed, cautious. State tolerances, comparison paths, and model assumptions explicitly. Never say "proven"; say "cross-validated against X within tolerance Y."

## Relationship to Examples

Examples under `examples/` are runnable artifacts. Docs explain and link to them. Getting Started may inline one short example. How-To and Manual link to relevant examples. Examples must not contain validation narratives or calibration notes.

## Chinese-First Policy

All user-facing documentation (Getting Started, How-To, Manual) is written in Chinese. English translation is optional and lives in `docs/i18n/en/`.

English is preserved for:
- Validation documentation
- Architecture and principle documents (`docs-principles.md`, `sdk-principles.md`, `test-principles.md`, `automated-workflows.md`, `AGENTS.md`)
- Code comments, tests, and validation scripts
- `README.md` is Chinese-first with a link to the English version

## i18n

When an English original is preserved in `docs/i18n/en/`, it should be a faithful snapshot of the Chinese source at the time of writing. Do not expand or reduce claims during translation.

## Anti-Patterns

- Do not mix validation notes into API reference.
- Do not write "see above" or "as discussed earlier" in Manual pages. Each section should be readable independently.
- Do not use defensive language like "may return" or "might be" when the behavior is verified. Say what ASTROX does.
- Do not use absolute language like "correct" or "accurate" when the behavior is unverified.
- Do not hard-wrap Markdown prose. Preserve unwrapped paragraphs.
- Do not introduce internal jargons when it's a user-facing material.
- Do not write Chinese that looks like a machine translation.
