# /// script
# requires-python = ">=3.10"
# dependencies = ["astrox", "matplotlib", "numpy"]
# ///
"""Example: Ballistic Trajectory Propagation (Apogee Altitude)

Computes a suborbital ballistic trajectory shaped by apogee altitude
(Cape Canaveral → ~1000 km downrange in the Atlantic) and plots the
altitude profile alongside a 3D lat/lon/alt view.

API: POST /Propagator/Ballistic (ApogeeAlt type)
"""

import matplotlib.pyplot as plt
import numpy as np

from astrox.propagator import propagate_ballistic


def main():
    result = propagate_ballistic(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude=30.0,       # Atlantic Ocean
        impact_longitude=-70.0,
        launch_latitude=28.5721,    # Cape Canaveral
        launch_longitude=-80.6480,
        launch_altitude=10.0,       # meters
        impact_altitude=0.0,
        ballistic_type="ApogeeAlt",
        ballistic_type_value=200000.0,  # 200 km apogee
        step=5.0,
    )

    print(f"Success: {result['IsSuccess']}")
    print(f"Message: {result['Message']}")

    # CZML cartesianVelocity: [t, x, y, z, vx, vy, vz, ...] in ECEF (FIXED)
    flat = result["Position"]["cartesianVelocity"]
    pts = np.array(flat).reshape(-1, 7)
    t_sec = pts[:, 0]
    x, y, z = pts[:, 1], pts[:, 2], pts[:, 3]

    # ECEF → geodetic (spherical approximation)
    R_EARTH = 6378137.0
    r = np.sqrt(x**2 + y**2 + z**2)
    alt_km = (r - R_EARTH) / 1e3
    lat = np.degrees(np.arcsin(z / r))
    lon = np.degrees(np.arctan2(y, x))

    apogee_idx = np.argmax(alt_km)
    print(f"Points: {len(t_sec)}")
    print(f"Apogee: {alt_km[apogee_idx]:.1f} km at t={t_sec[apogee_idx]:.0f} s")
    print(f"Time of flight: {t_sec[-1]:.0f} s ({t_sec[-1]/60:.1f} min)")

    # --- Plot ---
    fig = plt.figure(figsize=(14, 6))

    # Left: altitude vs time
    ax1 = fig.add_subplot(121)
    ax1.plot(t_sec / 60, alt_km, "orangered", lw=2)
    ax1.axhline(0, color="steelblue", lw=1, ls="--", alpha=0.5, label="Sea level")
    ax1.set_xlabel("Time (min)")
    ax1.set_ylabel("Altitude (km)")
    ax1.set_title("Altitude Profile")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Right: 3D trajectory in lat/lon/alt
    ax2 = fig.add_subplot(122, projection="3d")
    ax2.plot(lon, lat, alt_km, "orangered", lw=2)
    ax2.scatter(lon[0], lat[0], alt_km[0],
                color="green", s=60, zorder=5, label="Launch")
    ax2.scatter(lon[-1], lat[-1], alt_km[-1],
                color="red", s=60, zorder=5, label="Impact")
    ax2.scatter(lon[apogee_idx], lat[apogee_idx], alt_km[apogee_idx],
                color="gold", s=100, marker="*", zorder=5,
                label=f"Apogee ({alt_km[apogee_idx]:.1f} km)")
    # Ground track shadow
    ax2.plot(lon, lat, np.zeros_like(alt_km),
             color="gray", lw=1, ls="--", alpha=0.5)

    ax2.set_xlabel("Longitude (°)")
    ax2.set_ylabel("Latitude (°)")
    ax2.set_zlabel("Altitude (km)")
    ax2.set_title("Ballistic Trajectory — 200 km Apogee")
    ax2.legend(fontsize=8, loc="upper left")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
