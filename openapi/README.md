# ASTROX OpenAPI Baseline

This directory stores the repo-owned OpenAPI baseline used by CI.

- `astrox.openapi.yaml` is the checked-in latest spec snapshot.
- `archive/` stores versioned snapshots when the upstream OpenAPI version changes.

The live ASTROX server remains the source of truth. This baseline exists so CI
can detect when the live OpenAPI surface or generated models drift from what the
repository currently understands.
