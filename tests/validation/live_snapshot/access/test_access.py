#!/usr/bin/env python3
"""Live snapshots for access functions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import access, components, orbits, propagator
from tests.validation._support import (
    LiveSnapshotCase,
    check_snapshot,
    configure_astrox_from_env,
    main,
)


SNAPSHOT_PATH = Path(__file__).with_name("access.snap.json")
# GitHub Actions and local runs have observed millisecond/sub-millidegree
# numeric differences from the same public ASTROX endpoint, likely due to
# backend routing. Live snapshots guard maintained response shape; semantic
# precision lives in cross-validation.
ACCESS_SNAPSHOT_ABS_TOL = 5.0e-3
START = "2024-01-01T00:00:00.000Z"
STOP = "2024-01-01T02:00:00.000Z"
DAY_STOP = "2024-01-02T00:00:00.000Z"
EARTH_MU = 398600441500000.0
TLE_A = (
    "1 25544U 98067A   24001.00000000  .00002182  00000-0  41420-4 0  9995",
    "2 25544  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393123456",
)
TLE_B = (
    "1 20580U 90037B   24001.00000000  .00000200  00000-0  10270-3 0  9998",
    "2 20580  28.4696 347.5666 0002829  78.7776 281.3137 15.09293543345678",
)
CZML_VELOCITY_SAMPLES = [
    0.0,
    6114454.0,
    2870352.0,
    3308542.0,
    -3548.0,
    6463.0,
    1830.0,
    900.0,
    1200000.0,
    6500000.0,
    2500000.0,
    -7200.0,
    1500.0,
    1200.0,
    1800.0,
    -5751150.0,
    3715517.0,
    1150000.0,
    -6060.0,
    -5250.0,
    410.0,
    2700.0,
    -5000000.0,
    -4000000.0,
    -2000000.0,
    4500.0,
    -5600.0,
    -1500.0,
    3600.0,
    1000000.0,
    -6500000.0,
    -2500000.0,
    7200.0,
    1100.0,
    -900.0,
]


def site() -> components.Entity:
    return components.entity(
        name="Ground",
        position=components.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
    )


def orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6778137.0,
        eccentricity=0.001,
        inclination_deg=28.5,
        argument_of_periapsis_deg=0.0,
        raan_deg=15.0,
        true_anomaly_deg=45.0,
    )


def controlled_sensor_orbit() -> orbits.KeplerianElements:
    return orbits.keplerian(
        semi_major_axis_m=6878137.0,
        eccentricity=0.001,
        inclination_deg=45.0,
        argument_of_periapsis_deg=0.0,
        raan_deg=20.0,
        true_anomaly_deg=10.0,
    )


def sgp4_entity(
    name: str = "ISS",
    tle_lines: tuple[str, str] = TLE_A,
) -> components.Entity:
    return components.entity(
        name=name,
        position=components.sgp4_position(tle_lines=tle_lines),
    )


def controlled_target_site() -> components.Entity:
    return components.entity(
        name="TargetSite",
        position=components.site_position(
            longitude_deg=-105.0,
            latitude_deg=40.0,
            height_m=1800.0,
        ),
    )


def two_body_sensor_entity() -> components.Entity:
    return components.entity(
        name="ObserverSat",
        position=components.two_body_position(
            orbit_epoch=START,
            orbit=controlled_sensor_orbit(),
            start=START,
            stop=STOP,
            step_s=120.0,
        ),
        orientation=components.vvlh_axes(),
        sensor=components.conic_sensor(outer_half_angle_deg=8.0),
        sensor_pointing=components.fixed_sensor_pointing(
            rotation=components.az_el_rotation(
                azimuth_deg=0.0,
                elevation_deg=-20.0,
            ),
        ),
    )


def two_body_custom_axes_sensor_entity() -> components.Entity:
    # Live access accepts fixed axes when they reference the built-in VVLH axes
    # name. Custom VGT-defined axes name resolution is left to cross-validation.
    camera_axes = components.fixed_axes(
        reference_axes="VVLH",
        rotation=components.euler_rotation(
            sequence="321",
            a_deg=0.0,
            b_deg=20.0,
            c_deg=0.0,
        ),
    )
    return components.entity(
        name="ObserverSat",
        position=components.two_body_position(
            orbit_epoch=START,
            orbit=controlled_sensor_orbit(),
            start=START,
            stop=STOP,
            step_s=120.0,
        ),
        orientation=camera_axes,
        sensor=components.conic_sensor(outer_half_angle_deg=8.0),
    )


def two_body_vgt_container_entity() -> components.Entity:
    body_axes = components.vvlh_axes(name="Body VVLH")
    return components.entity(
        name="ObserverSat",
        position=components.two_body_position(
            orbit_epoch=START,
            orbit=controlled_sensor_orbit(),
            start=START,
            stop=STOP,
            step_s=120.0,
        ),
        vgt=components.vgt(axes=[body_axes]),
        orientation=components.vvlh_axes(),
        sensor=components.conic_sensor(outer_half_angle_deg=8.0),
    )


def moon_entity() -> components.Entity:
    return components.entity(
        name="Moon",
        position=components.central_body_position("Moon"),
    )


def hpop_entity() -> components.Entity:
    return components.entity(
        name="HPOP",
        position=components.hpop_position(
            start=START,
            stop=STOP,
            orbit_epoch=START,
            orbit=orbit(),
            gravitational_parameter_m3_s2=EARTH_MU,
            config=propagator.hpop_config(
                integrator=propagator.hpop_rkf78(
                    initial_step_s=30.0,
                    max_step_s=120.0,
                ),
                gravity=propagator.hpop_two_body_gravity(),
            ),
        ),
    )


def czml_positions_entity() -> components.Entity:
    return components.entity(
        name="CzmlSequence",
        position=components.czml_positions(
            [
                components.czml_position(
                    epoch=START,
                    reference_frame="INERTIAL",
                    interpolation_algorithm="LAGRANGE",
                    interpolation_degree=5,
                    cartesian_velocity=CZML_VELOCITY_SAMPLES,
                )
            ],
            central_body="Earth",
        ),
    )


def simple_ascent_entity() -> components.Entity:
    return components.entity(
        name="Ascent",
        position=components.simple_ascent_position(
            start="2024-01-01T03:00:00.000Z",
            stop="2024-01-01T03:02:00.000Z",
            launch_latitude_deg=40.9575,
            launch_longitude_deg=100.2912,
            launch_altitude_m=1000.0,
            burnout_velocity_m_s=7800.0,
            burnout_latitude_deg=41.3,
            burnout_longitude_deg=101.0,
            burnout_altitude_m=200000.0,
        ),
    )


def ballistic_entity() -> components.Entity:
    return components.entity(
        name="Ballistic",
        position=components.ballistic_position(
            start="2024-01-01T12:00:00.000Z",
            ballistic_type="DeltaV",
            ballistic_type_value=3000.0,
            launch_latitude_deg=28.5721,
            launch_longitude_deg=-80.648,
            launch_altitude_m=10.0,
            impact_latitude_deg=30.0,
            impact_longitude_deg=-70.0,
            impact_altitude_m=0.0,
        ),
    )


def access_compute_site_sgp4() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=DAY_STOP,
        from_entity=site(),
        to_entity=sgp4_entity(),
        step_s=600.0,
        compute_aer=True,
    )


def constrained_site(*, constraints: list[Any]) -> components.Entity:
    return components.entity(
        name="ConstrainedGround",
        position=components.site_position(
            longitude_deg=-155.468,
            latitude_deg=19.821,
            height_m=4205.0,
        ),
        constraints=constraints,
    )


def access_compute_site_sgp4_elevation_range_constraints() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=DAY_STOP,
        from_entity=constrained_site(
            constraints=[
                components.elevation_constraint(minimum_deg=10.0),
                components.range_constraint(maximum_km=2500.0, maximum_enabled=True),
            ],
        ),
        to_entity=sgp4_entity(),
        step_s=600.0,
        compute_aer=True,
    )


def access_compute_site_sgp4_az_el_mask_constraint() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=DAY_STOP,
        from_entity=constrained_site(
            constraints=[
                components.az_el_mask_constraint(
                    az_el_mask_rad=[
                        0.0,
                        0.17453292519943295,
                        1.5707963267948966,
                        0.17453292519943295,
                        3.141592653589793,
                        0.17453292519943295,
                        4.71238898038469,
                        0.17453292519943295,
                    ],
                ),
            ],
        ),
        to_entity=sgp4_entity(),
        step_s=600.0,
        compute_aer=True,
    )


def access_compute_site_sgp4_az_el_mask_constraint_with_max_range() -> dict[str, Any]:
    """AzElMask with a tiny MaxRange.

    ASTROX currently forwards MaxRange but does not enforce it, so this request
    returns the same intervals as ``access_compute_site_sgp4_az_el_mask_constraint``.
    If a future upstream version starts enforcing MaxRange, this snapshot will
    mismatch because a 1 km limit would eliminate all ISS passes.
    """
    return access.compute(
        start=START,
        stop=DAY_STOP,
        from_entity=constrained_site(
            constraints=[
                components.az_el_mask_constraint(
                    az_el_mask_rad=[
                        0.0,
                        0.17453292519943295,
                        1.5707963267948966,
                        0.17453292519943295,
                        3.141592653589793,
                        0.17453292519943295,
                        4.71238898038469,
                        0.17453292519943295,
                    ],
                    max_range_km=1.0,
                ),
            ],
        ),
        to_entity=sgp4_entity(),
        step_s=600.0,
        compute_aer=True,
    )


def access_compute_site_central_body() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=STOP,
        from_entity=site(),
        to_entity=moon_entity(),
        step_s=1800.0,
    )


def access_compute_site_hpop() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=STOP,
        from_entity=site(),
        to_entity=hpop_entity(),
        step_s=600.0,
    )


def access_compute_site_czml_positions() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=STOP,
        from_entity=site(),
        to_entity=czml_positions_entity(),
        step_s=600.0,
    )


def access_compute_site_simple_ascent() -> dict[str, Any]:
    return access.compute(
        start="2024-01-01T03:00:00.000Z",
        stop="2024-01-01T03:10:00.000Z",
        from_entity=site(),
        to_entity=simple_ascent_entity(),
        step_s=60.0,
    )


def access_compute_site_ballistic() -> dict[str, Any]:
    return access.compute(
        start="2024-01-01T12:00:00.000Z",
        stop="2024-01-01T12:30:00.000Z",
        from_entity=site(),
        to_entity=ballistic_entity(),
        step_s=60.0,
    )


def access_compute_sensor_pointing() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=STOP,
        from_entity=two_body_sensor_entity(),
        to_entity=controlled_target_site(),
        step_s=120.0,
        compute_aer=True,
    )


def access_compute_custom_axes_sensor() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=STOP,
        from_entity=two_body_custom_axes_sensor_entity(),
        to_entity=controlled_target_site(),
        step_s=120.0,
        compute_aer=True,
    )


def access_compute_vgt_container() -> dict[str, Any]:
    return access.compute(
        start=START,
        stop=STOP,
        from_entity=two_body_vgt_container_entity(),
        to_entity=controlled_target_site(),
        step_s=120.0,
        compute_aer=True,
    )


def access_chain_site_sgp4() -> dict[str, Any]:
    ground = site()
    target = sgp4_entity()
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, target],
        start_participant=ground,
        end_participant=target,
    )


def access_chain_site_group() -> dict[str, Any]:
    ground = site()
    targets = components.entity_group(
        name="Targets",
        members=[
            sgp4_entity(),
            sgp4_entity(name="Hubble", tle_lines=TLE_B),
        ],
        to_restriction="AnyOf",
    )
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, targets],
        start_participant=ground,
        end_participant=targets,
    )


def access_chain_explicit_multi_hop() -> dict[str, Any]:
    ground = site()
    relay = sgp4_entity(name="Relay", tle_lines=TLE_A)
    target = sgp4_entity(name="Hubble", tle_lines=TLE_B)
    return access.chain(
        start=START,
        stop=DAY_STOP,
        participants=[ground, relay, target],
        start_participant=ground,
        end_participant=target,
        connections=[
            access.connection(ground, relay),
            access.connection(relay, target),
        ],
    )


CASES = [
    LiveSnapshotCase(
        id="access_compute_site_sgp4",
        description="Direct access from a fixed site to an SGP4 entity, including AER output.",
        run=access_compute_site_sgp4,
    ),
    LiveSnapshotCase(
        id="access_compute_site_sgp4_elevation_range_constraints",
        description="Direct access from a fixed site with elevation and range constraints to an SGP4 entity.",
        run=access_compute_site_sgp4_elevation_range_constraints,
    ),
    LiveSnapshotCase(
        id="access_compute_site_sgp4_az_el_mask_constraint",
        description="Direct access from a fixed site with an azimuth/elevation mask constraint to an SGP4 entity.",
        run=access_compute_site_sgp4_az_el_mask_constraint,
    ),
    LiveSnapshotCase(
        id="access_compute_site_sgp4_az_el_mask_constraint_with_max_range",
        description="Direct access from a fixed site with an AzElMask constraint that includes a tiny MaxRange. ASTROX currently forwards MaxRange without enforcing it; this snapshot freezes that behavior.",
        run=access_compute_site_sgp4_az_el_mask_constraint_with_max_range,
    ),
    LiveSnapshotCase(
        id="access_compute_site_central_body",
        description="Direct access from a fixed site to a central-body entity.",
        run=access_compute_site_central_body,
    ),
    LiveSnapshotCase(
        id="access_compute_site_hpop",
        description="Direct access from a fixed site to an HPOP entity.",
        run=access_compute_site_hpop,
    ),
    LiveSnapshotCase(
        id="access_compute_site_czml_positions",
        description="Direct access from a fixed site to a composite CZML positions entity.",
        run=access_compute_site_czml_positions,
    ),
    LiveSnapshotCase(
        id="access_compute_site_simple_ascent",
        description="Direct access from a fixed site to a simple ascent entity.",
        run=access_compute_site_simple_ascent,
    ),
    LiveSnapshotCase(
        id="access_compute_site_ballistic",
        description="Direct access from a fixed site to a ballistic entity.",
        run=access_compute_site_ballistic,
    ),
    LiveSnapshotCase(
        id="access_compute_sensor_pointing",
        description="Direct access from a sensor-bearing two-body satellite to a fixed site, including entity axes and fixed sensor pointing metadata.",
        run=access_compute_sensor_pointing,
    ),
    LiveSnapshotCase(
        id="access_compute_custom_axes_sensor",
        description="Direct access from a sensor-bearing two-body satellite using fixed axes relative to built-in VVLH axes.",
        run=access_compute_custom_axes_sensor,
    ),
    LiveSnapshotCase(
        id="access_compute_vgt_container",
        description="Direct access from a sensor-bearing two-body satellite carrying a VGT provider with a named VVLH axes definition.",
        run=access_compute_vgt_container,
    ),
    LiveSnapshotCase(
        id="access_chain_site_sgp4",
        description="Direct chain access between a site participant and an SGP4 participant.",
        run=access_chain_site_sgp4,
    ),
    LiveSnapshotCase(
        id="access_chain_site_group",
        description="Chain access from a site participant to an entity group.",
        run=access_chain_site_group,
    ),
    LiveSnapshotCase(
        id="access_chain_explicit_multi_hop",
        description="Explicit chain topology through a relay participant.",
        run=access_chain_explicit_multi_hop,
    ),
]


def test_access_live_snapshot() -> None:
    configure_astrox_from_env()
    check_snapshot(
        cases=CASES,
        snapshot_path=SNAPSHOT_PATH,
        abs_tol=ACCESS_SNAPSHOT_ABS_TOL,
        datetime_abs_tol_s=ACCESS_SNAPSHOT_ABS_TOL,
    )


if __name__ == "__main__":
    raise SystemExit(main(cases=CASES, snapshot_path=SNAPSHOT_PATH))
