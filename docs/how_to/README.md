# How-To 指南

面向任务的操作指南，每篇解决一个具体问题。

- [如何传播一条轨道](propagate_an_orbit.md)：根据手头的轨道描述（开普勒根数、TLE 或力模型配置）选择传播器并读取采样结果。
- [在不同轨道表示之间转换](convert_between_orbit_representations.md)：开普勒根数、笛卡尔状态与 Kozai-Izsak 平均根数之间的相互转换。
- [搭建 HPOP 力模型配置](build_an_hpop_configuration.md)：用 `hpop_config` 系列构造器组装积分器、重力场、大气、太阳辐射压与第三方天体摄动。
- [计算光照条件](compute_lighting_conditions.md)：光照/半影/本影区间、太阳辐射强度与太阳 AER 采样。
- [计算地面站与卫星之间的访问区间](compute_access_intervals.md)：直接访问计算、AER 输出与仰角约束。

每篇指南的完整参数说明见对应的[手册](../manual/README.md)条目，验证证据见[验证文档](../validation/README.md)。
