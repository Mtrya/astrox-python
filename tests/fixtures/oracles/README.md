# SDK Oracle Fixtures

This directory holds optional independent evidence for promoted SDK behavior. Oracle fixtures are claim-driven: add them when a lightweight external source can check a specific semantic or numerical claim, and keep the scope narrow enough that the comparison remains reviewable.

These fixtures are not a promotion gate for every SDK function. ASTROX SDK contract snapshots under `tests/fixtures/astrox_sdk_contract/` protect live ASTROX-backed function IO; oracle fixtures add independent checks only where the source, assumptions, and tolerance are explicit.

Run the current oracle checks with:

```bash
uv run python scripts/sdk_oracles/check.py
```
