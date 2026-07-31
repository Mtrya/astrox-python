# 参与开发

从本仓库检出后，安装开发依赖并运行测试：

```bash
uv sync --group dev
uv build --no-build-isolation
uv run python -m pytest -q tests/sdk
```
