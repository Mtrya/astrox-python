# GMAT Validation Image

This image provides the reproducible GMAT runtime used by scheduled validation. It is built from the official GMAT R2026a Ubuntu tarball hosted on SourceForge and pins the downloaded artifact with SHA-256 `fe124b4a606b2e3b704a6fbb1c37b87598d5df0d18cb661c304b5f60074a7754`.

The image installs GMAT under `/opt/gmat`, sets `GMAT_ROOT=/opt/gmat`, and keeps `/opt/gmat/bin` on `PATH`. The image contract is script execution through `GmatConsole`; validation driver scripts live in this repository and are mounted read-only into the container at runtime.

`self_check.py` writes a minimal GMAT script, runs `GmatConsole`, parses the generated report file, and verifies that a spacecraft propagated for 60 seconds. This proves more than startup: the console, script parser, force model, propagator, and report output path all have to work.

The image is published by `.github/workflows/gmat-validation-image.yml` as `ghcr.io/<owner>/astrox-gmat-validation:gmat-r2026a`. After container changes merge, run that workflow manually once if the tag has not already been published from a main-branch push.
