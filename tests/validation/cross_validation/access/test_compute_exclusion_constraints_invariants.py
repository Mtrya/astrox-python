#!/usr/bin/env python3
"""Sun/Moon exclusion constraint cross-validation for access compute."""

# Coverage:
#   Branches:
#     - SunExclusionAngle constraint on from_entity fixed site: verified against Skyfield topocentric body-separation geometry
#     - MoonExclusionAngle constraint on from_entity fixed site: verified against Skyfield topocentric body-separation geometry
#     - SunExclusionAngle constraint on to_entity fixed site: verified against Skyfield topocentric body-separation geometry
#     - MoonExclusionAngle constraint on to_entity fixed site: verified against Skyfield topocentric body-separation geometry
#     - SunExclusionAngle constraint on from_entity SGP4 satellite: verified against Skyfield satellite-observer body-separation geometry with Earth occultation
#     - MoonExclusionAngle constraint on from_entity SGP4 satellite: verified against Skyfield satellite-observer body-separation geometry with Earth occultation
#     - SunExclusionAngle constraint on to_entity SGP4 satellite: verified against Skyfield satellite-observer body-separation geometry with Earth occultation
#     - MoonExclusionAngle constraint on to_entity SGP4 satellite: verified against Skyfield satellite-observer body-separation geometry with Earth occultation
#     - ChainCompute direct fixed-site start/end Sun/Moon exclusion routes: verified against AccessCompute and Skyfield body-separation geometry
#     - ChainCompute direct SGP4 start/end Sun/Moon exclusion routes: verified against AccessCompute and Skyfield satellite-observer body-separation geometry with Earth occultation
#   Fields:
#     - Passes.AccessStart/AccessStop under fixed-site Sun/Moon exclusion constraints: verified against independent WGS84 line-of-sight plus Skyfield body-separation predicate
#     - Passes.AccessStart/AccessStop under SGP4 from_entity/to_entity Sun/Moon exclusion constraints: verified against independent WGS84 line-of-sight plus Skyfield body-separation and body-occultation predicates
#     - CompleteChainAccess.Start/Stop under direct-chain Sun/Moon exclusion constraints: verified against independent oracle intervals and AccessCompute intervals
#   Parameters:
#     - SunExclusionAngle.MinimumValue: verified at 0 deg as permissive and 60 deg as restrictive for fixed-site, SGP4 from_entity, and SGP4 to_entity roles
#     - MoonExclusionAngle.MinimumValue: verified at 0 deg as permissive and 25/60 deg as restrictive for the fixed-site role; verified at 0/60 deg for SGP4 from_entity with a Madrid target fixture; verified at 0/120 deg for SGP4 to_entity with an access-producing no-drag TLE fixture
#   Comparison:
#     - External: Skyfield SGP4, DE421 Sun/Moon ephemerides, apparent topocentric body altitude gate, astrometric topocentric/satellite-observer body-separation angle, satellite body Earth-occultation, and WGS84 segment-obstruction visibility
#     - Constants: TLE_A, TLE_TO_ENTITY_NO_DRAG, Hawaii/Madrid WGS84 site coordinates, de421.bsp
#     - Tolerances: EXCLUSION_INTERVAL_ABS_S=0.35 s for live interval boundaries after 15 s sampling plus bisection and ASTROX/Skyfield ephemeris/vector convention residuals
#   Findings:
#     - A fixed-site Sun/Moon exclusion constraint is satisfied when the apparent body is below the constrained site's local horizon, or when the line-of-sight target is separated from the topocentric astrometric body vector by at least MinimumValue degrees.
#     - A constrained SGP4 from_entity Sun/Moon exclusion constraint is satisfied when Earth occults the body from the satellite, or when the target line of sight is separated from the satellite-observer astrometric body vector by at least MinimumValue degrees.
#     - Larger MinimumValue thresholds can split or narrow access intervals; the validator compares the full derived interval set rather than pass count.
#     - A constrained SGP4 to_entity Sun/Moon exclusion constraint follows the same satellite-observer convention in an access-producing no-drag TLE fixture. Drag-bearing fixtures can still expose live SGP4 propagation errors, so this validator uses the stable no-drag fixture as semantic evidence rather than treating those errors as interval semantics.

from __future__ import annotations

import sys
from functools import lru_cache

from astrox import access, components
from astrox.exceptions import AstroxAPIError
from tests.validation._support import (
    LiveConfigError,
    configure_astrox_from_env,
)
from tests.validation.cross_validation.access._cases import (
    DAY_STOP,
    REMOTE_HEIGHT_M,
    REMOTE_LATITUDE_DEG,
    REMOTE_LONGITUDE_DEG,
    SITE_HEIGHT_M,
    SITE_LATITUDE_DEG,
    SITE_LONGITUDE_DEG,
    START,
    TLE_A,
    CrossValidationError,
    compute_access,
    site,
)
from tests.validation.cross_validation.access._exclusion import (
    EXCLUSION_INTERVAL_ABS_S,
    ExclusionEphemeris,
    expected_satellite_exclusion_intervals,
    expected_site_exclusion_intervals,
    load_exclusion_ephemeris,
)
from tests.validation.cross_validation.access._geometry import (
    compare_intervals,
    intervals_from_access_passes,
    intervals_from_chain,
)

TLE_TO_ENTITY_NO_DRAG = (
    "1 90001U 24001A   24001.00000000  .00000000  00000-0  00000-0 0  9994",
    "2 90001  51.6461 339.8014 0001882  64.8995 295.2305 15.48919393000001",
)


@lru_cache(maxsize=1)
def _shared_exclusion_ephemeris() -> ExclusionEphemeris:
    return load_exclusion_ephemeris()


def constrained_site(constraint: components.Constraint | None) -> components.Entity:
    base = site()
    return components.entity(
        name=base.name,
        position=base.position,
        constraints=[] if constraint is None else [constraint],
    )


def constrained_remote_site(constraint: components.Constraint | None) -> components.Entity:
    return components.entity(
        name="Madrid",
        position=components.site_position(
            longitude_deg=REMOTE_LONGITUDE_DEG,
            latitude_deg=REMOTE_LATITUDE_DEG,
            height_m=REMOTE_HEIGHT_M,
        ),
        constraints=[] if constraint is None else [constraint],
    )


def sgp4_entity(
    *,
    name: str,
    tle_lines: tuple[str, str],
    constraint: components.Constraint | None = None,
) -> components.Entity:
    return components.entity(
        name=name,
        position=components.sgp4_position(tle_lines=tle_lines),
        constraints=[] if constraint is None else [constraint],
    )


def test_fixed_site_exclusion_angle_constraints_match_skyfield_body_separation() -> None:
    configure_astrox_from_env()
    ephemeris = _shared_exclusion_ephemeris()
    cases = [
        (
            "from_site_sun0",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
            "from_site",
        ),
        (
            "from_site_sun60",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
            "from_site",
        ),
        (
            "from_site_moon0",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
            "from_site",
        ),
        (
            "from_site_moon25",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=25.0),
            25.0,
            "from_site",
        ),
        (
            "from_site_moon60",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
            "from_site",
        ),
        (
            "to_site_sun60",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
            "to_site",
        ),
        (
            "to_site_moon60",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
            "to_site",
        ),
    ]
    for label, body_name, constraint, minimum_deg, role in cases:
        if role == "from_site":
            result = compute_access(
                constrained_site(constraint),
                sgp4_entity(name="ISS", tle_lines=TLE_A),
                start=START,
                stop=DAY_STOP,
            )
        elif role == "to_site":
            result = compute_access(
                sgp4_entity(name="ISS", tle_lines=TLE_A),
                constrained_site(constraint),
                start=START,
                stop=DAY_STOP,
            )
        else:
            raise AssertionError(f"unknown role {role!r}")
        actual = intervals_from_access_passes(result["Passes"])
        expected = expected_site_exclusion_intervals(
            body_name=body_name,
            minimum_deg=minimum_deg,
            start=START,
            stop=DAY_STOP,
            tle_lines=TLE_A,
            satellite_name="ISS",
            latitude_deg=SITE_LATITUDE_DEG,
            longitude_deg=SITE_LONGITUDE_DEG,
            height_m=SITE_HEIGHT_M,
            ephemeris=ephemeris,
        )
        try:
            compare_intervals(expected, actual, tolerance_s=EXCLUSION_INTERVAL_ABS_S)
        except CrossValidationError as exc:
            raise CrossValidationError(f"{label}: {exc}") from exc


def test_sgp4_from_entity_exclusion_angle_constraints_match_skyfield_body_separation() -> None:
    configure_astrox_from_env()
    ephemeris = _shared_exclusion_ephemeris()
    cases = [
        (
            "sun0_hawaii",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
            constrained_site(None),
            SITE_LATITUDE_DEG,
            SITE_LONGITUDE_DEG,
            SITE_HEIGHT_M,
        ),
        (
            "sun60_hawaii",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
            constrained_site(None),
            SITE_LATITUDE_DEG,
            SITE_LONGITUDE_DEG,
            SITE_HEIGHT_M,
        ),
        (
            "moon0_madrid",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
            constrained_remote_site(None),
            REMOTE_LATITUDE_DEG,
            REMOTE_LONGITUDE_DEG,
            REMOTE_HEIGHT_M,
        ),
        (
            "moon60_madrid",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
            constrained_remote_site(None),
            REMOTE_LATITUDE_DEG,
            REMOTE_LONGITUDE_DEG,
            REMOTE_HEIGHT_M,
        ),
    ]
    for (
        label,
        body_name,
        constraint,
        minimum_deg,
        target_site,
        target_latitude_deg,
        target_longitude_deg,
        target_height_m,
    ) in cases:
        result = compute_access(
            sgp4_entity(name="ISS", tle_lines=TLE_A, constraint=constraint),
            target_site,
            start=START,
            stop=DAY_STOP,
        )
        actual = intervals_from_access_passes(result["Passes"])
        expected = expected_satellite_exclusion_intervals(
            body_name=body_name,
            minimum_deg=minimum_deg,
            start=START,
            stop=DAY_STOP,
            tle_lines=TLE_A,
            satellite_name="ISS",
            target_latitude_deg=target_latitude_deg,
            target_longitude_deg=target_longitude_deg,
            target_height_m=target_height_m,
            ephemeris=ephemeris,
        )
        try:
            compare_intervals(expected, actual, tolerance_s=EXCLUSION_INTERVAL_ABS_S)
        except CrossValidationError as exc:
            raise CrossValidationError(f"{label}: {exc}") from exc


def test_direct_chain_exclusion_angle_constraints_match_compute_and_skyfield() -> None:
    configure_astrox_from_env()
    ephemeris = _shared_exclusion_ephemeris()
    cases = [
        (
            "chain_site_sun60",
            constrained_site(
                components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            ),
            sgp4_entity(name="ISS", tle_lines=TLE_A),
            expected_site_exclusion_intervals(
                body_name="sun",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_A,
                satellite_name="ISS",
                latitude_deg=SITE_LATITUDE_DEG,
                longitude_deg=SITE_LONGITUDE_DEG,
                height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_site_moon60",
            constrained_site(
                components.moon_exclusion_angle_constraint(minimum_deg=60.0),
            ),
            sgp4_entity(name="ISS", tle_lines=TLE_A),
            expected_site_exclusion_intervals(
                body_name="moon",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_A,
                satellite_name="ISS",
                latitude_deg=SITE_LATITUDE_DEG,
                longitude_deg=SITE_LONGITUDE_DEG,
                height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_to_site_sun60",
            sgp4_entity(name="ISS", tle_lines=TLE_A),
            constrained_site(
                components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            ),
            expected_site_exclusion_intervals(
                body_name="sun",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_A,
                satellite_name="ISS",
                latitude_deg=SITE_LATITUDE_DEG,
                longitude_deg=SITE_LONGITUDE_DEG,
                height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_to_site_moon60",
            sgp4_entity(name="ISS", tle_lines=TLE_A),
            constrained_site(
                components.moon_exclusion_angle_constraint(minimum_deg=60.0),
            ),
            expected_site_exclusion_intervals(
                body_name="moon",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_A,
                satellite_name="ISS",
                latitude_deg=SITE_LATITUDE_DEG,
                longitude_deg=SITE_LONGITUDE_DEG,
                height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_sgp4_from_sun60",
            sgp4_entity(
                name="ISS",
                tle_lines=TLE_A,
                constraint=components.sun_exclusion_angle_constraint(
                    minimum_deg=60.0,
                ),
            ),
            constrained_site(None),
            expected_satellite_exclusion_intervals(
                body_name="sun",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_A,
                satellite_name="ISS",
                target_latitude_deg=SITE_LATITUDE_DEG,
                target_longitude_deg=SITE_LONGITUDE_DEG,
                target_height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_sgp4_from_moon60",
            sgp4_entity(
                name="ISS",
                tle_lines=TLE_A,
                constraint=components.moon_exclusion_angle_constraint(
                    minimum_deg=60.0,
                ),
            ),
            constrained_remote_site(None),
            expected_satellite_exclusion_intervals(
                body_name="moon",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_A,
                satellite_name="ISS",
                target_latitude_deg=REMOTE_LATITUDE_DEG,
                target_longitude_deg=REMOTE_LONGITUDE_DEG,
                target_height_m=REMOTE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_sgp4_to_sun60",
            constrained_site(None),
            sgp4_entity(
                name="ConstrainedISS",
                tle_lines=TLE_TO_ENTITY_NO_DRAG,
                constraint=components.sun_exclusion_angle_constraint(
                    minimum_deg=60.0,
                ),
            ),
            expected_satellite_exclusion_intervals(
                body_name="sun",
                minimum_deg=60.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_TO_ENTITY_NO_DRAG,
                satellite_name="ConstrainedISS",
                target_latitude_deg=SITE_LATITUDE_DEG,
                target_longitude_deg=SITE_LONGITUDE_DEG,
                target_height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
        (
            "chain_sgp4_to_moon120",
            constrained_site(None),
            sgp4_entity(
                name="ConstrainedISS",
                tle_lines=TLE_TO_ENTITY_NO_DRAG,
                constraint=components.moon_exclusion_angle_constraint(
                    minimum_deg=120.0,
                ),
            ),
            expected_satellite_exclusion_intervals(
                body_name="moon",
                minimum_deg=120.0,
                start=START,
                stop=DAY_STOP,
                tle_lines=TLE_TO_ENTITY_NO_DRAG,
                satellite_name="ConstrainedISS",
                target_latitude_deg=SITE_LATITUDE_DEG,
                target_longitude_deg=SITE_LONGITUDE_DEG,
                target_height_m=SITE_HEIGHT_M,
                ephemeris=ephemeris,
            ),
        ),
    ]
    for label, from_entity, to_entity, expected in cases:
        compute_result = compute_access(
            from_entity,
            to_entity,
            start=START,
            stop=DAY_STOP,
        )
        chain_result = access.chain(
            start=START,
            stop=DAY_STOP,
            participants=[from_entity, to_entity],
            start_participant=from_entity,
            end_participant=to_entity,
        )
        compute_intervals = intervals_from_access_passes(compute_result["Passes"])
        chain_intervals = intervals_from_chain(chain_result["CompleteChainAccess"])
        try:
            compare_intervals(
                expected,
                compute_intervals,
                tolerance_s=EXCLUSION_INTERVAL_ABS_S,
            )
            compare_intervals(
                expected,
                chain_intervals,
                tolerance_s=EXCLUSION_INTERVAL_ABS_S,
            )
            compare_intervals(
                compute_intervals,
                chain_intervals,
                tolerance_s=EXCLUSION_INTERVAL_ABS_S,
            )
        except CrossValidationError as exc:
            raise CrossValidationError(f"{label}: {exc}") from exc


def test_sgp4_to_entity_exclusion_angle_constraints_match_skyfield_body_separation() -> None:
    configure_astrox_from_env()
    ephemeris = _shared_exclusion_ephemeris()
    ground = site()
    cases = [
        (
            "sun0",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
        ),
        (
            "sun60",
            "sun",
            components.sun_exclusion_angle_constraint(minimum_deg=60.0),
            60.0,
        ),
        (
            "moon0",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=0.0),
            0.0,
        ),
        (
            "moon120",
            "moon",
            components.moon_exclusion_angle_constraint(minimum_deg=120.0),
            120.0,
        ),
    ]
    for label, body_name, constraint, minimum_deg in cases:
        result = compute_access(
            ground,
            sgp4_entity(
                name="ConstrainedISS",
                tle_lines=TLE_TO_ENTITY_NO_DRAG,
                constraint=constraint,
            ),
            start=START,
            stop=DAY_STOP,
        )
        actual = intervals_from_access_passes(result["Passes"])
        expected = expected_satellite_exclusion_intervals(
            body_name=body_name,
            minimum_deg=minimum_deg,
            start=START,
            stop=DAY_STOP,
            tle_lines=TLE_TO_ENTITY_NO_DRAG,
            satellite_name="ConstrainedISS",
            target_latitude_deg=SITE_LATITUDE_DEG,
            target_longitude_deg=SITE_LONGITUDE_DEG,
            target_height_m=SITE_HEIGHT_M,
            ephemeris=ephemeris,
        )
        try:
            compare_intervals(expected, actual, tolerance_s=EXCLUSION_INTERVAL_ABS_S)
        except CrossValidationError as exc:
            raise CrossValidationError(f"{label}: {exc}") from exc


def run_all_checks() -> int:
    test_fixed_site_exclusion_angle_constraints_match_skyfield_body_separation()
    test_sgp4_from_entity_exclusion_angle_constraints_match_skyfield_body_separation()
    test_direct_chain_exclusion_angle_constraints_match_compute_and_skyfield()
    test_sgp4_to_entity_exclusion_angle_constraints_match_skyfield_body_separation()
    return 4


def main() -> int:
    try:
        configure_astrox_from_env()
        checked = run_all_checks()
        print(f"CROSS_VALIDATION_CHECKED={checked}")
        print("CROSS_VALIDATION_FAILED=0")
        return 0
    except (CrossValidationError, LiveConfigError, AstroxAPIError) as exc:
        print(f"CROSS_VALIDATION_FAILED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
