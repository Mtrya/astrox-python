# TLE 与碎片分析示例

本目录展示 `astrox.cat` 的 TLE 生成、寿命估算、简单解体、显式脉冲解体和 NASA 解体分支。

| 示例 | 展示的公开 API |
| --- | --- |
| `cat_workflows.py` | `cat.generate_tle(...)`、`cat.estimate_tle_lifetime(...)`、`cat.simulate_debris_breakup_simple(...)`、`cat.simulate_debris_breakup(...)`、`cat.simulate_debris_breakup_nasa(...)` 与 `cat.DebrisImpulse` |

从仓库根目录运行：

```bash
uv run python examples/09_cat/cat_workflows.py
```

示例使用兼容的 ASTROX 服务地址和可复现的输入。返回的寿命值可能是服务端回退值；碎片数量和解体模型语义也不应从示例输出推断为科学正确性。

完整参数说明见[两行根数与碎片分析手册](../../docs/manual/cat/README.md)，独立证据见 [CAT 验证文档](../../docs/validation/cat.md)。
