# Validation Evidence

Per-domain validation evidence: what is verified, against what, with which tolerances, and what remains unresolved. Each page is an evidence register; status values (`verified`, `partial`, `unresolved`, `unverified`) mirror the coverage checklists in the scripts under `tests/validation/`.

- [Propagator](propagator.md)
- [Orbits](orbits.md)
- [Lighting](lighting.md)
- [Access (includes components evidence)](access.md)
- [Coverage](coverage.md)
- [Conjunction](conjunction.md)
- [CAT](cat.md)
- [Rocket](rocket.md)
- [Astrogator](astrogator.md)

Two evidence layers back these pages:

- `tests/validation/live_snapshot/` — function-centered live SDK contract snapshots with sidecar `.snap.json` files. They prove maintained response shape, not semantic correctness.
- `tests/validation/cross_validation/` — independent oracle comparisons (Skyfield, Brahe, Orekit, GMAT, lamberthub, GeographicLib, local derivations, invariants) that calibrate ASTROX semantics.
