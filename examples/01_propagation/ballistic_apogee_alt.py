# /// script
# requires-python = ">=3.10"
# dependencies = ["astrox-python", "matplotlib", "numpy"]
# ///
"""示例：弹道轨迹传播（远地点高度约束）

按远地点高度计算一条次轨道弹道（卡纳维拉尔角 → 大西洋约 1000 km 下程），
并绘制高度曲线与三维经纬高轨迹。

"""

import matplotlib.pyplot as plt
import numpy as np

from astrox import propagator


def main():
    period_s, position = propagator.ballistic_apogee_altitude(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        launch_latitude_deg=28.5721,
        launch_longitude_deg=-80.6480,
        launch_altitude_m=10.0,
        impact_altitude_m=0.0,
        apogee_altitude_m=200000.0,
        step_s=5.0,
    )

    print(f"轨道周期: {period_s:.3f} s")
    print(f"参考系: {position.reference_frame}")

    # CZML cartesianVelocity: [t, x, y, z, vx, vy, vz, ...]，ECEF（FIXED）
    flat = position.cartesian_velocity
    pts = np.array(flat).reshape(-1, 7)
    t_sec = pts[:, 0]
    x, y, z = pts[:, 1], pts[:, 2], pts[:, 3]

    # ECEF → 大地经纬高（球近似）
    R_EARTH = 6378137.0
    r = np.sqrt(x**2 + y**2 + z**2)
    alt_km = (r - R_EARTH) / 1e3
    lat = np.degrees(np.arcsin(z / r))
    lon = np.degrees(np.arctan2(y, x))

    apogee_idx = np.argmax(alt_km)
    print(f"采样点数: {len(t_sec)}")
    print(f"远地点: {alt_km[apogee_idx]:.1f} km，t={t_sec[apogee_idx]:.0f} s")
    print(f"飞行时间: {t_sec[-1]:.0f} s ({t_sec[-1]/60:.1f} min)")

    # --- 绘图 ---
    fig = plt.figure(figsize=(14, 6))

    # 左图：高度随时间变化
    ax1 = fig.add_subplot(121)
    ax1.plot(t_sec / 60, alt_km, "orangered", lw=2)
    ax1.axhline(0, color="steelblue", lw=1, ls="--", alpha=0.5, label="海平面")
    ax1.set_xlabel("时间 (min)")
    ax1.set_ylabel("高度 (km)")
    ax1.set_title("高度曲线")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 右图：三维经纬高轨迹
    ax2 = fig.add_subplot(122, projection="3d")
    ax2.plot(lon, lat, alt_km, "orangered", lw=2)
    ax2.scatter(lon[0], lat[0], alt_km[0],
                color="green", s=60, zorder=5, label="发射点")
    ax2.scatter(lon[-1], lat[-1], alt_km[-1],
                color="red", s=60, zorder=5, label="落点")
    ax2.scatter(lon[apogee_idx], lat[apogee_idx], alt_km[apogee_idx],
                color="gold", s=100, marker="*", zorder=5,
                label=f"远地点 ({alt_km[apogee_idx]:.1f} km)")
    # 地面投影
    ax2.plot(lon, lat, np.zeros_like(alt_km),
             color="gray", lw=1, ls="--", alpha=0.5)

    ax2.set_xlabel("经度 (°)")
    ax2.set_ylabel("纬度 (°)")
    ax2.set_zlabel("高度 (km)")
    ax2.set_title("弹道轨迹 — 200 km 远地点")
    ax2.legend(fontsize=8, loc="upper left")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
