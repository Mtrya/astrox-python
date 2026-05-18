# astrox-python

Python SDK work for the ASTROX Web API.

## Development

Install development dependencies and build the package from a checkout:

```bash
uv sync --group dev
uv build --no-build-isolation
```

The CI build imports the wheel from outside the repository before running tests, so packaging problems are caught separately from source-tree imports.
