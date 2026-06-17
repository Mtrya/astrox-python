---
name: astrox-release
description: Maintain astrox-python releases, including version selection, release-prep commits, artifact checks, GitHub Release publishing, trusted PyPI publishing, and post-publish verification. Use when the user asks to publish, release, tag, bump a version, prepare PyPI/TestPyPI, verify release artifacts, or decide whether a newly landed feature should advance the package version.
---

# Astrox Release

## Overview

Release `astrox-python` through the repository's GitHub Release workflow. Treat PyPI files as immutable: once a version appears on PyPI, never reuse, move, or overwrite that version.

## Release Source Of Truth

- Package version lives in `pyproject.toml` under `[project].version`.
- Git tag must be `v{version}`, for example `0.2.0` -> `v0.2.0`.
- Real PyPI publishing is triggered by a published GitHub Release via `.github/workflows/publish.yml`.
- TestPyPI publishing is triggered manually through the same workflow with `workflow_dispatch`.
- Do not publish directly with local `twine upload` unless the user explicitly asks to bypass the workflow.

## Version Policy

Before `1.0.0`, use this convention:

- Patch, `0.x.y+1`: bug fixes, validation infrastructure fixes, packaging fixes, docs/examples clarifications, no meaningful new public SDK surface.
- Minor, `0.x+1.0`: new public SDK domain/function/module, meaningful new supported behavior, or a public API redesign.
- Major, `1.0.0`: only when the maintainer decides the SDK API is stable enough to promise compatibility.

Ask before choosing the version if the change mixes public API additions with compatibility-sensitive behavior. If a roadmap feature lands as a new supported public surface, default to a minor bump.

## Tag Rules

- Tag only after the version bump/release-prep commit is on `main`.
- If a GitHub Release/tag exists but PyPI has not accepted files for that version, it may be deleted/recreated to fix a stale or failed release.
- If PyPI has accepted any file for a version, never move that tag or reuse that version. Fix forward with a new patch or minor version.
- If only release notes are wrong after PyPI publish, edit the GitHub Release notes; do not move the tag.

## Preflight

1. Check state:
   ```bash
   git status --short --branch
   git log --oneline --decorate -5
   ```
2. Verify the target version:
   ```bash
   rg -n '^version = ' pyproject.toml
   git tag --list 'v*' --sort=version:refname
   curl -L -s https://pypi.org/pypi/astrox-python/json
   ```
3. If changing `pyproject.toml`, make one focused release-prep commit and push `main`.
4. Check GitHub environment rules if publishing is blocked:
   ```bash
   gh api repos/Mtrya/astrox-python/environments/pypi
   gh api repos/Mtrya/astrox-python/environments/pypi/deployment-branch-policies
   ```

## Artifact Gate

Run these before publishing:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m pytest -q tests/sdk
UV_CACHE_DIR=/tmp/uv-cache uv build
UV_CACHE_DIR=/tmp/uv-cache uv run --with twine python -m twine check dist/*
```

Inspect package contents:

```bash
python -m zipfile -l dist/astrox_python-<version>-py3-none-any.whl
python -m tarfile -l dist/astrox_python-<version>.tar.gz
```

The wheel should contain only installable package files and metadata. The sdist may include source, docs, examples, and tests, but must not include local/private directories such as `.git`, `.github`, `.agents`, `.codex`, `.qoder`, `.worktrees`, `.venv`, `.pytest_cache`, `roadmap`, `scripts`, `openapi`, `reviews`, `dist`, `build`, `vendor`, or `wheels`. If local/private content leaks, fix `[tool.hatch.build.targets.sdist]` before publishing.

For a final install smoke:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --with dist/astrox_python-<version>-py3-none-any.whl python -c "import astrox, importlib.metadata as m; print(astrox.__version__); print(m.version('astrox-python'))"
```

## Publish

1. Ensure `main` is pushed and the release commit exists on GitHub:
   ```bash
   git push origin main
   git rev-parse HEAD origin/main
   ```
2. If no release/tag exists for this version:
   ```bash
   gh release create v<version> --repo Mtrya/astrox-python --target <commit-sha> --title v<version> --notes "<release notes>"
   ```
3. If a stale GitHub release/tag exists and PyPI has no files for that version, delete and recreate it:
   ```bash
   gh release delete v<version> --repo Mtrya/astrox-python --cleanup-tag --yes
   git tag -d v<version>
   gh release create v<version> --repo Mtrya/astrox-python --target <commit-sha> --title v<version> --notes "<release notes>"
   ```
4. Watch the trusted publish workflow:
   ```bash
   gh run list --repo Mtrya/astrox-python --workflow publish.yml --limit 5
   gh run watch <run-id> --repo Mtrya/astrox-python --exit-status
   ```

## Post-Publish Verification

Verify PyPI and the installed package:

```bash
curl -L -s https://pypi.org/pypi/astrox-python/json
UV_CACHE_DIR=/tmp/uv-cache uv run --with astrox-python==<version> python -c "import astrox, importlib.metadata as m; print(astrox.__version__); print(m.version('astrox-python'))"
git fetch --tags origin
git rev-parse HEAD origin/main v<version>
git ls-remote --tags origin 'v<version>'
gh release view v<version> --repo Mtrya/astrox-python --json tagName,targetCommitish,isDraft,isPrerelease,publishedAt,url
```

Report the PyPI URL, GitHub Release URL, publish workflow run id, artifact checks, install smoke result, and any CI still running. Do not claim success until PyPI JSON shows the version and install smoke imports the published package.
