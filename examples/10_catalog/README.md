# 目录查询示例

本目录展示 `astrox.catalog` 的城市、设施和卫星目录查询函数。

| 示例 | 展示的公开 API |
| --- | --- |
| `catalog_queries.py` | `catalog.query_cities(...)`、`catalog.query_facilities(...)` 与 `catalog.query_satellites(...)` |

从仓库根目录运行：

```bash
uv run python examples/10_catalog/catalog_queries.py
```

目录数据由服务端数据库维护，记录数量、TLE 内容和更新时间可能变化。示例只展示查询和读取原始 JSON-like 响应，不应据此推断目录完整性或记录长期稳定。

完整参数说明见[目录查询手册](../../docs/manual/catalog/README.md)，请求与响应形状证据见[目录验证文档](../../docs/validation/catalog.md)。
