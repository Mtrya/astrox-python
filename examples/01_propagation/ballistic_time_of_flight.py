# /// script
# dependencies = ["astrox-python"]
# requires-python = ">=3.10"
# ///
"""Ballistic propagation using the time-of-flight branch."""

from astrox import propagator


def main():
    period_s, position = propagator.ballistic_time_of_flight(
        start="2024-01-01T12:00:00.000Z",
        impact_latitude_deg=30.0,
        impact_longitude_deg=-70.0,
        launch_latitude_deg=28.5721,
        launch_longitude_deg=-80.6480,
        launch_altitude_m=10.0,
        impact_altitude_m=0.0,
        time_of_flight_s=600.0,
        step_s=5.0,
    )

    print(f"Period: {period_s:.3f} s")
    print(f"Position epoch: {position.epoch}")


if __name__ == "__main__":
    main()
