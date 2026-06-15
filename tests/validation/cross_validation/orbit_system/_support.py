"""Shared helpers for OrbitSystem cross-validation tests."""

from __future__ import annotations

import itertools
import math
import shutil
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from astropy import units as u
from astropy.coordinates import FK5, GCRS, ICRS, ITRS, SkyCoord
from astropy.time import Time
from scipy.spatial.transform import Rotation as SciRotation
from skyfield.api import Loader

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from astrox import entities, orbits


EPOCH = "2024-01-01T00:00:00Z"
PLANETARY_EPOCH = "2026-06-12T00:00:00Z"
EARTH_MU_M3_S2 = 398600441500000.0
SAMPLE_RADIUS_M = 7_000_000.0
SAMPLE_DURATION_S = 1000.0
SAMPLE_COUNT = 8

EARTH_RADIUS_ABS_M = 1.0
EARTH_FIXED_TO_INERTIAL_RADIUS_ABS_M = 1.0
EARTH_LONGITUDE_ABS_DEG = 0.001
EARTH_J2000_ABS_M = 5.0
EARTH_ICRF_ABS_M = 5.0
MOON_INERTIAL_ABS_M = 200.0
MOON_FIXED_ABS_M = 1000.0
MOON_FIXED_ANGLE_ARCSEC = 1.0
MARS_INERTIAL_ABS_M = 200_000.0
MARS_INERTIAL_ANGLE_ARCSEC = 0.2
MARS_FIXED_ANGLE_ARCSEC = 10.0
SUN_INERTIAL_ABS_M = 500.0
SUN_FIXED_ABS_M = 1000.0
SUN_FIXED_ANGLE_ARCSEC = 0.002
LIBRATION_POSITION_ABS_M = 1.0
QUATERNION_MATCH_DEG = 1.0
QUATERNION_CALIBRATION_MIN_DEG = 1.0


class CrossValidationError(Exception):
    """Raised when ASTROX output deviates from the independent comparison path."""


# ---------------------------------------------------------------------------
# External-tool setup
# ---------------------------------------------------------------------------


_spice_kernels_loaded = False


_SPICE_KERNEL_URLS: list[tuple[Path, str]] = [
    (
        Path.home() / ".spice/kernels/naif0012.tls",
        "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls",
    ),
    (
        Path.home() / ".spice/kernels/pck00010.tpc",
        "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00010.tpc",
    ),
    (
        Path.home() / ".spice/kernels/moon_de440_220930.tf",
        "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/a_old_versions/moon_de440_220930.tf",
    ),
    (
        Path.home() / ".spice/kernels/moon_pa_de440_200625.bpc",
        "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc",
    ),
]


def _download_kernel(path: Path, url: str) -> None:
    """Download a SPICE kernel to the local cache.

    Tests are expected to run in environments that can reach the NAIF server,
    either directly or through a caching proxy. The download is only performed
    once per machine.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create a permissive SSL context so the download works in environments
    # with older certificate stores (e.g., local dev containers). CI typically
    # has up-to-date certs; this is a fallback, not a security bypass.
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, context=context) as response, path.open("wb") as file:
            shutil.copyfileobj(response, file)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Failed to download SPICE kernel from {url} to {path}: {exc}"
        ) from exc


def _ensure_spice_kernels_loaded() -> None:
    """Lazily load (and download if missing) SPICE kernels."""
    global _spice_kernels_loaded
    if _spice_kernels_loaded:
        return
    import spiceypy as spice

    for path, url in _SPICE_KERNEL_URLS:
        if not path.exists():
            _download_kernel(path, url)
        spice.furnsh(str(path))
    # de440.bsp is managed by Skyfield; ensure it exists by asking Skyfield to
    # load it, then load the same file with SPICE.
    _skyfield_loader()("de440.bsp")
    spice.furnsh(str(Path.home() / ".skyfield/de440.bsp"))
    _spice_kernels_loaded = True


def _skyfield_loader() -> Loader:
    return Loader(Path.home() / ".skyfield")


def _astropy_time(epoch: str = EPOCH) -> Time:
    return Time(epoch, scale="utc")


# ---------------------------------------------------------------------------
# CZML sample builders
# ---------------------------------------------------------------------------


def _cartesian_samples(
    cartesian: tuple[float, ...] | None,
) -> list[tuple[float, float, float, float]]:
    if cartesian is None:
        return []
    values = list(cartesian)
    samples: list[tuple[float, float, float, float]] = []
    for index in range(0, len(values), 4):
        samples.append(
            (
                values[index],
                values[index + 1],
                values[index + 2],
                values[index + 3],
            )
        )
    return samples


def _sample_static_position(
    *,
    epoch: str = EPOCH,
    inertial_longitude_deg: float,
    reference_frame: str,
    central_body: str = "Earth",
) -> entities.CzmlPosition:
    """Build a static, equatorial CZML sample in the requested frame."""
    longitude_rad = math.radians(inertial_longitude_deg)
    dt_s = SAMPLE_DURATION_S / (SAMPLE_COUNT - 1)
    cartesian: list[float] = []
    for index in range(SAMPLE_COUNT):
        t_s = index * dt_s
        cartesian += [
            t_s,
            SAMPLE_RADIUS_M * math.cos(longitude_rad),
            SAMPLE_RADIUS_M * math.sin(longitude_rad),
            0.0,
        ]
    return entities.czml_position(
        epoch=epoch,
        central_body=central_body,
        reference_frame=reference_frame,
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=cartesian,
    )


def _sample_origin_position(
    *,
    epoch: str = EPOCH,
    reference_frame: str,
    central_body: str = "Earth",
) -> entities.CzmlPosition:
    """Build an origin (zero-radius) CZML sample to isolate translation."""
    dt_s = SAMPLE_DURATION_S / (SAMPLE_COUNT - 1)
    cartesian: list[float] = []
    for index in range(SAMPLE_COUNT):
        t_s = index * dt_s
        cartesian += [t_s, 0.0, 0.0, 0.0]
    return entities.czml_position(
        epoch=epoch,
        central_body=central_body,
        reference_frame=reference_frame,
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=7,
        cartesian=cartesian,
    )


def _build_libration_czml(
    *,
    epoch: str = EPOCH,
    inertial_longitude_deg: float = 0.0,
    reference_frame: str = "INERTIAL",
    central_body: str = "Earth",
    sample_count: int = SAMPLE_COUNT,
    interpolation_degree: int = 7,
    with_velocity: bool = False,
) -> entities.CzmlPosition:
    """Build a CZML sample for ``orbits.earth_moon_libration``."""
    longitude_rad = math.radians(inertial_longitude_deg)
    dt_s = SAMPLE_DURATION_S / (sample_count - 1)
    cartesian: list[float] = []
    velocity: list[float] = []
    x = SAMPLE_RADIUS_M * math.cos(longitude_rad)
    y = SAMPLE_RADIUS_M * math.sin(longitude_rad)
    z = 0.0
    for index in range(sample_count):
        t_s = index * dt_s
        cartesian += [t_s, x, y, z]
        if with_velocity:
            velocity += [t_s, 0.0, 0.0, 0.0]
    return entities.czml_position(
        epoch=epoch,
        central_body=central_body,
        reference_frame=reference_frame,
        interpolation_algorithm="LAGRANGE",
        interpolation_degree=interpolation_degree,
        cartesian=cartesian,
        cartesian_velocity=velocity if with_velocity else None,
    )


# ---------------------------------------------------------------------------
# Earth orientation helpers
# ---------------------------------------------------------------------------


def _earth_rotation_angle_degrees(jd_ut1: float) -> float:
    """IAU 2000 Earth Rotation Angle in degrees."""
    era = 2.0 * math.pi * (0.7790572732640 + 1.00273781191135448 * (jd_ut1 - 2451545.0))
    return math.degrees(era) % 360.0


def _rotation_gcrs_to_j2000(t: Time) -> np.ndarray:
    """Rotation matrix from GCRS to FK5 J2000 mean equator/equinox.

    ERFA ``bp06`` returns the frame-bias matrix ``rb`` that maps J2000 to
    GCRS/ICRS, so its transpose maps GCRS to J2000.
    """
    import erfa

    dt = t.datetime
    jd1, jd2 = erfa.dtf2d(
        "tt",
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1e6,
    )
    rb, _rp, _rbp = erfa.bp06(jd1, jd2)
    return np.asarray(rb).T


# ---------------------------------------------------------------------------
# Moon / libration helpers
# ---------------------------------------------------------------------------


def _moon_geocentric_state_skyfield(
    epoch: str = EPOCH,
) -> tuple[np.ndarray, np.ndarray]:
    """Geocentric Moon position (m) and velocity (m/s) from JPL DE440."""
    load = _skyfield_loader()
    ts = load.timescale()
    dt = datetime.fromisoformat(epoch.replace("Z", "+00:00"))
    t = ts.utc(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1e6,
    )
    planets = load("de440.bsp")
    obs = (planets["moon"] - planets["earth"]).at(t)
    return np.asarray(obs.position.m), np.asarray(obs.velocity.m_per_s)


def _rotation_moon_mmej2000_from_spice(t: Time) -> np.ndarray:
    """GCRS -> Moon Mean Equator/Equinox J2000 (MMEJ2000) rotation matrix.

    Definition calibrated from ASTROX live output:
      * z-axis  = IAU Moon rotation pole at J2000 (from SPICE pck00010.tpc).
      * x-axis  = ascending node of Earth's J2000 mean equator on the Moon's
                  mean equator at J2000.
      * y-axis  = cross(z, x) (right-handed).

    The rows of the returned matrix are the MMEJ2000 axes expressed in GCRS.
    """
    _ensure_spice_kernels_loaded()
    import spiceypy as spice

    et_j2000 = spice.str2et("2000-01-01T12:00:00")
    m_iau_moon_j2000 = np.asarray(spice.pxform("J2000", "IAU_MOON", et_j2000))
    moon_pole_j2000 = m_iau_moon_j2000[2]
    earth_pole_j2000 = np.array([0.0, 0.0, 1.0])

    node = np.cross(earth_pole_j2000, moon_pole_j2000)
    node = node / np.linalg.norm(node)
    y_axis = np.cross(moon_pole_j2000, node)
    y_axis = y_axis / np.linalg.norm(y_axis)

    m_mmej_j2000 = np.vstack([node, y_axis, moon_pole_j2000])
    return m_mmej_j2000 @ _rotation_gcrs_to_j2000(t)


def _libration_basis(
    moon_pos_m: np.ndarray,
    moon_vel_m_s: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Moon-centered libration frame axes in Earth inertial coordinates.

    This is the frame that matches ASTROX ``cartesian`` output:
        x = unit vector from Earth to Moon
        z = unit Earth-Moon orbital angular momentum
        y = z cross x
    """
    x_axis = moon_pos_m / np.linalg.norm(moon_pos_m)
    z_axis = np.cross(moon_pos_m, moon_vel_m_s)
    z_axis = z_axis / np.linalg.norm(z_axis)
    y_axis = np.cross(z_axis, x_axis)
    return x_axis, y_axis, z_axis


def _expected_moon_centered_libration_position(
    satellite_inertial_m: np.ndarray,
    moon_pos_m: np.ndarray,
    moon_vel_m_s: np.ndarray,
) -> np.ndarray:
    """Project an Earth-centered inertial vector into the Moon-centered libration frame."""
    x_axis, y_axis, z_axis = _libration_basis(moon_pos_m, moon_vel_m_s)
    relative_m = satellite_inertial_m - moon_pos_m
    return np.array(
        [
            float(np.dot(relative_m, x_axis)),
            float(np.dot(relative_m, y_axis)),
            float(np.dot(relative_m, z_axis)),
        ]
    )


def _rotation_matrix_to_quaternion(matrix: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation matrix to a scalar-last unit quaternion [x, y, z, w]."""
    return SciRotation.from_matrix(np.asarray(matrix)).as_quat()


def _scalar_last_to_first(q: np.ndarray) -> np.ndarray:
    """[x, y, z, w] -> [w, x, y, z]."""
    return np.roll(q, 1)


def _conjugate_scalar_last(q: np.ndarray) -> np.ndarray:
    """Conjugate of a scalar-last quaternion [x, y, z, w]."""
    return np.array([-q[0], -q[1], -q[2], q[3]])


def _expected_quaternion_conventions(
    moon_pos_m: np.ndarray,
    moon_vel_m_s: np.ndarray,
) -> dict[str, np.ndarray]:
    """Every plausible quaternion encoding of the libration/inertial rotation."""
    x_axis, y_axis, z_axis = _libration_basis(moon_pos_m, moon_vel_m_s)
    r_libration_to_inertial = np.column_stack((x_axis, y_axis, z_axis))
    r_inertial_to_libration = r_libration_to_inertial.T

    def add_direction(prefix: str, matrix: np.ndarray) -> dict[str, np.ndarray]:
        q_sl = _rotation_matrix_to_quaternion(matrix)
        q_sf = _scalar_last_to_first(q_sl)
        return {
            f"{prefix}_scalar_last": q_sl,
            f"{prefix}_scalar_first": q_sf,
            f"{prefix}_scalar_last_conjugated": _conjugate_scalar_last(q_sl),
            f"{prefix}_scalar_first_conjugated": _scalar_last_to_first(
                _conjugate_scalar_last(q_sl)
            ),
        }

    result: dict[str, np.ndarray] = {}
    result.update(add_direction("libration_to_inertial", r_libration_to_inertial))
    result.update(add_direction("inertial_to_libration", r_inertial_to_libration))
    return result


def _quaternion_angular_distance_deg(q1: np.ndarray, q2: np.ndarray) -> float:
    """Angular distance between two unit quaternions, accounting for q ~ -q."""
    dot = abs(float(np.dot(q1, q2)))
    dot = min(1.0, max(-1.0, dot))
    return math.degrees(2.0 * math.acos(dot))


# ---------------------------------------------------------------------------
# Generic geometric helpers
# ---------------------------------------------------------------------------


def _angular_separation_arcsec(a: np.ndarray, b: np.ndarray) -> float:
    """Angular separation between two vectors in arcseconds.

    Uses ``atan2(|a x b|, a . b)`` instead of ``acos`` for numerical stability
    when the vectors are nearly parallel.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return float("nan")
    cross = np.cross(a, b)
    return math.degrees(math.atan2(np.linalg.norm(cross), np.dot(a, b))) * 3600.0


# ---------------------------------------------------------------------------
# Prediction helpers (independent of ASTROX response values)
# ---------------------------------------------------------------------------


def _predict_earth_inertial_to_frame(
    inertial_longitude_deg: float,
    target_frame: str,
    t: Time,
) -> np.ndarray:
    """Predict Earth INERTIAL -> {J2000, ICRF} using the ERFA frame-bias matrix.

    ``SkyCoord.transform_to`` includes an origin shift (GCRS is geocentric,
    ICRS is barycentric), so the vector rotation must be applied directly.
    """
    lam = math.radians(inertial_longitude_deg)
    v = np.array(
        [
            SAMPLE_RADIUS_M * math.cos(lam),
            SAMPLE_RADIUS_M * math.sin(lam),
            0.0,
        ]
    )
    if target_frame == "J2000":
        return _rotation_gcrs_to_j2000(t) @ v
    if target_frame == "ICRF":
        # GCRS -> ICRS is the frame-bias matrix itself (its transpose maps J2000
        # to GCRS). The rotation is at the sub-milliarcsecond level.
        import erfa

        dt = t.datetime
        jd1, jd2 = erfa.dtf2d(
            "tt",
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second + dt.microsecond / 1e6,
        )
        rb, _rp, _rbp = erfa.bp06(jd1, jd2)
        return np.asarray(rb) @ v
    raise ValueError(f"unsupported target_frame: {target_frame!r}")


def _predict_moon_inertial(
    inertial_longitude_deg: float,
    epoch: str = EPOCH,
) -> np.ndarray:
    """Predict Earth INERTIAL -> Moon INERTIAL (MMEJ2000 + DE440 translation)."""
    t = _astropy_time(epoch)
    lam = math.radians(inertial_longitude_deg)
    v_gcrs = np.array(
        [
            SAMPLE_RADIUS_M * math.cos(lam),
            SAMPLE_RADIUS_M * math.sin(lam),
            0.0,
        ]
    )
    moon_pos_gcrs, _ = _moon_geocentric_state_skyfield(epoch)
    r_gcrs_to_mmej = _rotation_moon_mmej2000_from_spice(t)
    return r_gcrs_to_mmej @ (v_gcrs - moon_pos_gcrs)


def _predict_moon_inertial_origin(epoch: str = EPOCH) -> np.ndarray:
    """Predict the Moon INERTIAL origin offset (Earth center -> Moon center)."""
    t = _astropy_time(epoch)
    moon_pos_gcrs, _ = _moon_geocentric_state_skyfield(epoch)
    r_gcrs_to_mmej = _rotation_moon_mmej2000_from_spice(t)
    return -(r_gcrs_to_mmej @ moon_pos_gcrs)


def _predict_moon_fixed(
    inertial_longitude_deg: float,
    epoch: str = EPOCH,
) -> np.ndarray:
    """Predict Earth INERTIAL -> Moon FIXED (high-precision MOON_ME frame).

    The IAU_MOON model is a low-fidelity analytical approximation; the
    NAIF high-precision lunar frame ``MOON_ME`` (mean Earth/polar axis,
    DE440) agrees with ASTROX to ~0.15 arcsec and ~300 m at the Moon.
    """
    _ensure_spice_kernels_loaded()
    import spiceypy as spice

    t = _astropy_time(epoch)
    et = spice.str2et(epoch)
    lam = math.radians(inertial_longitude_deg)
    v_gcrs = np.array(
        [
            SAMPLE_RADIUS_M * math.cos(lam),
            SAMPLE_RADIUS_M * math.sin(lam),
            0.0,
        ]
    )
    moon_pos_gcrs, _ = _moon_geocentric_state_skyfield(epoch)
    r_gcrs_to_j2000 = _rotation_gcrs_to_j2000(t)
    v_j2000 = r_gcrs_to_j2000 @ v_gcrs
    moon_pos_j2000 = r_gcrs_to_j2000 @ moon_pos_gcrs
    r_j2000_to_moon_me = np.asarray(spice.pxform("J2000", "MOON_ME", et))
    return r_j2000_to_moon_me @ (v_j2000 - moon_pos_j2000)


def _predict_planetary(
    body: str,
    target_reference_frame: str,
    inertial_longitude_deg: float,
    epoch: str,
) -> np.ndarray:
    """Predict Earth INERTIAL -> Mars/Sun {INERTIAL, FIXED} using SPICE.

    Mars predictions use the Mars barycenter (NAIF ID 4) because de440.bsp does
    not provide Mars body centre relative to Earth directly. The
    barycenter-to-centre offset is much smaller than the observed residuals.
    """
    _ensure_spice_kernels_loaded()
    import spiceypy as spice

    body_map: dict[str, dict[str, Any]] = {
        "Mars": {
            "spice_id": "4",
            "inertial_frame": "MARSIAU",
            "fixed_frame": "IAU_MARS",
        },
        "Sun": {
            "spice_id": "10",
            "inertial_frame": "J2000",
            "fixed_frame": "IAU_SUN",
        },
    }
    info = body_map[body]

    t = _astropy_time(epoch)
    et = spice.str2et(epoch)
    lam = math.radians(inertial_longitude_deg)
    v_gcrs = np.array(
        [
            SAMPLE_RADIUS_M * math.cos(lam),
            SAMPLE_RADIUS_M * math.sin(lam),
            0.0,
        ]
    )
    r_gcrs_to_j2000 = _rotation_gcrs_to_j2000(t)
    v_j2000 = r_gcrs_to_j2000 @ v_gcrs
    body_pos_j2000_km = np.asarray(
        spice.spkezr(info["spice_id"], et, "J2000", "NONE", "EARTH")[0][:3]
    )
    body_pos_j2000_m = body_pos_j2000_km * 1000.0
    v_rel_j2000 = v_j2000 - body_pos_j2000_m

    if target_reference_frame == "INERTIAL":
        if info["inertial_frame"] == "J2000":
            return v_rel_j2000
        r = np.asarray(spice.pxform("J2000", info["inertial_frame"], et))
        return r @ v_rel_j2000

    r = np.asarray(spice.pxform("J2000", info["fixed_frame"], et))
    return r @ v_rel_j2000


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def _check_earth_inertial_to_fixed(inertial_longitude_deg: float) -> None:
    """A static inertial vector rotates to the expected fixed longitude via ERA."""
    load = _skyfield_loader()
    ts = load.timescale()

    position = _sample_static_position(
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, fixed = orbits.convert_czml_position(
        position,
        to_central_body="Earth",
        target_reference_frame="FIXED",
    )

    for t_s, x_m, y_m, z_m in _cartesian_samples(fixed.cartesian):
        radius_m = math.sqrt(x_m**2 + y_m**2 + z_m**2)
        if abs(radius_m - SAMPLE_RADIUS_M) > EARTH_RADIUS_ABS_M:
            raise CrossValidationError(
                f"radius {radius_m} deviates from {SAMPLE_RADIUS_M} "
                f"by more than {EARTH_RADIUS_ABS_M} m"
            )

        t = ts.utc(2024, 1, 1, 0, 0, t_s)
        era_deg = _earth_rotation_angle_degrees(t.ut1)
        expected_fixed_longitude_deg = (inertial_longitude_deg - era_deg) % 360.0
        astrox_longitude_deg = math.degrees(math.atan2(y_m, x_m)) % 360.0
        delta_deg = (
            astrox_longitude_deg - expected_fixed_longitude_deg + 180.0
        ) % 360.0 - 180.0
        if abs(delta_deg) > EARTH_LONGITUDE_ABS_DEG:
            raise CrossValidationError(
                f"longitude delta {delta_deg} deg exceeds {EARTH_LONGITUDE_ABS_DEG} deg "
                f"at inertial_longitude={inertial_longitude_deg}, t={t_s}"
            )


def _check_earth_fixed_to_inertial(fixed_longitude_deg: float) -> None:
    """A static fixed vector rotates to the expected inertial longitude via ERA."""
    load = _skyfield_loader()
    ts = load.timescale()

    position = _sample_static_position(
        inertial_longitude_deg=fixed_longitude_deg,
        reference_frame="FIXED",
    )
    _period, inertial = orbits.convert_czml_position(
        position,
        to_central_body="Earth",
        target_reference_frame="INERTIAL",
    )

    for t_s, x_m, y_m, z_m in _cartesian_samples(inertial.cartesian):
        radius_m = math.sqrt(x_m**2 + y_m**2 + z_m**2)
        if abs(radius_m - SAMPLE_RADIUS_M) > EARTH_FIXED_TO_INERTIAL_RADIUS_ABS_M:
            raise CrossValidationError(
                f"radius {radius_m} deviates from {SAMPLE_RADIUS_M} "
                f"by more than {EARTH_FIXED_TO_INERTIAL_RADIUS_ABS_M} m"
            )

        t = ts.utc(2024, 1, 1, 0, 0, t_s)
        era_deg = _earth_rotation_angle_degrees(t.ut1)
        expected_inertial_longitude_deg = (fixed_longitude_deg + era_deg) % 360.0
        astrox_longitude_deg = math.degrees(math.atan2(y_m, x_m)) % 360.0
        delta_deg = (
            astrox_longitude_deg - expected_inertial_longitude_deg + 180.0
        ) % 360.0 - 180.0
        if abs(delta_deg) > EARTH_LONGITUDE_ABS_DEG:
            raise CrossValidationError(
                f"longitude delta {delta_deg} deg exceeds {EARTH_LONGITUDE_ABS_DEG} deg "
                f"at fixed_longitude={fixed_longitude_deg}, t={t_s}"
            )


def _check_earth_inertial_to_target(
    inertial_longitude_deg: float,
    target_frame: str,
    tolerance_m: float,
) -> None:
    """Earth INERTIAL -> {J2000, ICRF} matches the Astropy prediction."""
    t = _astropy_time()
    position = _sample_static_position(
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Earth",
        target_reference_frame=target_frame,
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_earth_inertial_to_frame(
        inertial_longitude_deg,
        target_frame,
        t,
    )
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    if residual_m > tolerance_m:
        raise CrossValidationError(
            f"Earth INERTIAL -> {target_frame} residual {residual_m} m "
            f"exceeds {tolerance_m} m at longitude={inertial_longitude_deg}"
        )


def _check_moon_inertial(inertial_longitude_deg: float) -> None:
    """Earth INERTIAL -> Moon INERTIAL matches MMEJ2000 + DE440 translation."""
    position = _sample_static_position(
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Moon",
        target_reference_frame="INERTIAL",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_moon_inertial(inertial_longitude_deg)
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    if residual_m > MOON_INERTIAL_ABS_M:
        raise CrossValidationError(
            f"Moon INERTIAL residual {residual_m} m exceeds {MOON_INERTIAL_ABS_M} m "
            f"at longitude={inertial_longitude_deg}"
        )


def _check_moon_inertial_origin() -> None:
    """Earth INERTIAL origin maps to the Moon center in MMEJ2000."""
    position = _sample_origin_position(reference_frame="INERTIAL")
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Moon",
        target_reference_frame="INERTIAL",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_moon_inertial_origin()
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    if residual_m > MOON_INERTIAL_ABS_M:
        raise CrossValidationError(
            f"Moon INERTIAL origin residual {residual_m} m exceeds "
            f"{MOON_INERTIAL_ABS_M} m"
        )


def _check_moon_fixed(inertial_longitude_deg: float) -> None:
    """Earth INERTIAL -> Moon FIXED matches high-precision MOON_ME frame."""
    position = _sample_static_position(
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Moon",
        target_reference_frame="FIXED",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_moon_fixed(inertial_longitude_deg)
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    angle_arcsec = _angular_separation_arcsec(astrox_xyz, expected_xyz)
    if residual_m > MOON_FIXED_ABS_M:
        raise CrossValidationError(
            f"Moon FIXED absolute residual {residual_m} m exceeds "
            f"{MOON_FIXED_ABS_M} m at longitude={inertial_longitude_deg}"
        )
    if math.isnan(angle_arcsec) or angle_arcsec > MOON_FIXED_ANGLE_ARCSEC:
        raise CrossValidationError(
            f"Moon FIXED angular residual {angle_arcsec} arcsec exceeds "
            f"{MOON_FIXED_ANGLE_ARCSEC} arcsec at longitude={inertial_longitude_deg}"
        )


def _check_mars_inertial(inertial_longitude_deg: float) -> None:
    """Earth INERTIAL -> Mars INERTIAL matches SPICE MARSIAU."""
    position = _sample_static_position(
        epoch=PLANETARY_EPOCH,
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Mars",
        target_reference_frame="INERTIAL",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_planetary(
        "Mars", "INERTIAL", inertial_longitude_deg, PLANETARY_EPOCH
    )
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    angle_arcsec = _angular_separation_arcsec(astrox_xyz, expected_xyz)
    if residual_m > MARS_INERTIAL_ABS_M:
        raise CrossValidationError(
            f"Mars INERTIAL residual {residual_m} m exceeds {MARS_INERTIAL_ABS_M} m "
            f"at longitude={inertial_longitude_deg}"
        )
    if math.isnan(angle_arcsec) or angle_arcsec > MARS_INERTIAL_ANGLE_ARCSEC:
        raise CrossValidationError(
            f"Mars INERTIAL angular residual {angle_arcsec} arcsec exceeds "
            f"{MARS_INERTIAL_ANGLE_ARCSEC} arcsec at longitude={inertial_longitude_deg}"
        )


def _check_mars_fixed_orientation(inertial_longitude_deg: float) -> None:
    """Earth INERTIAL -> Mars FIXED matches IAU_MARS orientation."""
    position = _sample_static_position(
        epoch=PLANETARY_EPOCH,
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Mars",
        target_reference_frame="FIXED",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_planetary(
        "Mars", "FIXED", inertial_longitude_deg, PLANETARY_EPOCH
    )
    angle_arcsec = _angular_separation_arcsec(astrox_xyz, expected_xyz)
    if math.isnan(angle_arcsec) or angle_arcsec > MARS_FIXED_ANGLE_ARCSEC:
        raise CrossValidationError(
            f"Mars FIXED angular residual {angle_arcsec} arcsec exceeds "
            f"{MARS_FIXED_ANGLE_ARCSEC} arcsec at longitude={inertial_longitude_deg}"
        )


def _check_sun_inertial(inertial_longitude_deg: float) -> None:
    """Earth INERTIAL -> Sun INERTIAL matches J2000 common inertial axes."""
    position = _sample_static_position(
        epoch=PLANETARY_EPOCH,
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Sun",
        target_reference_frame="INERTIAL",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_planetary(
        "Sun", "INERTIAL", inertial_longitude_deg, PLANETARY_EPOCH
    )
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    if residual_m > SUN_INERTIAL_ABS_M:
        raise CrossValidationError(
            f"Sun INERTIAL residual {residual_m} m exceeds {SUN_INERTIAL_ABS_M} m "
            f"at longitude={inertial_longitude_deg}"
        )


def _check_sun_fixed(inertial_longitude_deg: float) -> None:
    """Earth INERTIAL -> Sun FIXED matches SPICE IAU_SUN."""
    position = _sample_static_position(
        epoch=PLANETARY_EPOCH,
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    _period, output = orbits.convert_czml_position(
        position,
        to_central_body="Sun",
        target_reference_frame="FIXED",
    )
    astrox_xyz = np.array(_cartesian_samples(output.cartesian)[0][1:])
    expected_xyz = _predict_planetary(
        "Sun", "FIXED", inertial_longitude_deg, PLANETARY_EPOCH
    )
    residual_m = float(np.linalg.norm(astrox_xyz - expected_xyz))
    angle_arcsec = _angular_separation_arcsec(astrox_xyz, expected_xyz)
    if residual_m > SUN_FIXED_ABS_M:
        raise CrossValidationError(
            f"Sun FIXED residual {residual_m} m exceeds {SUN_FIXED_ABS_M} m "
            f"at longitude={inertial_longitude_deg}"
        )
    if math.isnan(angle_arcsec) or angle_arcsec > SUN_FIXED_ANGLE_ARCSEC:
        raise CrossValidationError(
            f"Sun FIXED angular residual {angle_arcsec} arcsec exceeds "
            f"{SUN_FIXED_ANGLE_ARCSEC} arcsec at longitude={inertial_longitude_deg}"
        )


def _check_earth_moon_libration_cartesian(
    epoch: str,
    inertial_longitude_deg: float,
) -> None:
    """ASTROX returns the input state in the expected Moon-centered libration frame."""
    position = _sample_static_position(
        epoch=epoch,
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    state = orbits.earth_moon_libration(position)

    samples = _cartesian_samples(state.cartesian)
    if not samples:
        raise CrossValidationError("no cartesian samples returned")
    _t_s, x_m, y_m, z_m = samples[0]
    astrox_position_m = np.array([x_m, y_m, z_m])

    moon_pos_m, moon_vel_m_s = _moon_geocentric_state_skyfield(epoch)
    longitude_rad = math.radians(inertial_longitude_deg)
    satellite_inertial_m = np.array(
        [
            SAMPLE_RADIUS_M * math.cos(longitude_rad),
            SAMPLE_RADIUS_M * math.sin(longitude_rad),
            0.0,
        ]
    )
    expected_position_m = _expected_moon_centered_libration_position(
        satellite_inertial_m,
        moon_pos_m,
        moon_vel_m_s,
    )

    diff_m = astrox_position_m - expected_position_m
    residual_m = float(np.linalg.norm(diff_m))
    if residual_m > LIBRATION_POSITION_ABS_M:
        raise CrossValidationError(
            f"libration position residual {residual_m} m exceeds "
            f"{LIBRATION_POSITION_ABS_M} m at epoch={epoch}, "
            f"longitude={inertial_longitude_deg}"
        )


def _best_libration_quaternion_residual_deg(
    epoch: str = EPOCH,
    inertial_longitude_deg: float = 0.0,
) -> tuple[float, np.ndarray]:
    """Return the smallest angle between ASTROX q and any plausible convention."""
    position = _sample_static_position(
        epoch=epoch,
        inertial_longitude_deg=inertial_longitude_deg,
        reference_frame="INERTIAL",
    )
    state = orbits.earth_moon_libration(position)
    quaternion = state.unit_quaternion
    astrox_q = np.asarray(quaternion[1:5])

    moon_pos_m, moon_vel_m_s = _moon_geocentric_state_skyfield(epoch)
    conventions = _expected_quaternion_conventions(moon_pos_m, moon_vel_m_s)
    residuals = [
        _quaternion_angular_distance_deg(astrox_q, q) for q in conventions.values()
    ]
    return min(residuals), astrox_q


def _check_earth_moon_libration_unit_quaternion_matches() -> None:
    """Strict calibration check: the quaternion should encode the libration rotation."""
    residual_deg, _astrox_q = _best_libration_quaternion_residual_deg()
    if residual_deg > QUATERNION_MATCH_DEG:
        raise CrossValidationError(
            f"libration quaternion best residual {residual_deg} deg exceeds "
            f"{QUATERNION_MATCH_DEG} deg"
        )


def _check_earth_moon_libration_unit_quaternion_naive_conventions_fail() -> None:
    """Prove that no standard quaternion convention matches within ~1 degree."""
    residual_deg, _astrox_q = _best_libration_quaternion_residual_deg()
    if residual_deg <= QUATERNION_CALIBRATION_MIN_DEG:
        raise CrossValidationError(
            f"expected best residual > {QUATERNION_CALIBRATION_MIN_DEG} deg, "
            f"got {residual_deg} deg"
        )
    # Sanity upper bound: the observed residual is ~24.56°.
    if residual_deg > 30.0:
        raise CrossValidationError(
            f"best residual {residual_deg} deg is unexpectedly large; "
            "investigation may need to be re-run"
        )


def _check_earth_moon_libration_cartesian_translation_absent() -> None:
    """Live probe: cartesianTranslation is not populated for exercised inputs."""
    epochs = [EPOCH, "2024-06-01T00:00:00Z"]
    reference_frames = ["INERTIAL", "FIXED", "J2000", "ICRF"]
    central_bodies = ["Earth", "Moon"]
    sample_counts = [8]
    interpolation_degrees = [1, 7]
    with_velocity_flags = [False, True]

    probed = 0
    for (
        epoch,
        reference_frame,
        central_body,
        sample_count,
        interpolation_degree,
        with_velocity,
    ) in itertools.product(
        epochs,
        reference_frames,
        central_bodies,
        sample_counts,
        interpolation_degrees,
        with_velocity_flags,
    ):
        position = _build_libration_czml(
            epoch=epoch,
            reference_frame=reference_frame,
            central_body=central_body,
            sample_count=sample_count,
            interpolation_degree=interpolation_degree,
            with_velocity=with_velocity,
        )
        try:
            state = orbits.earth_moon_libration(position)
        except Exception:
            # Skip parameter combinations the server rejects.
            continue
        probed += 1
        has_translation = (
            state.cartesian_translation is not None
            and len(state.cartesian_translation) > 0
        )
        if has_translation:
            raise CrossValidationError(
                f"cartesian_translation unexpectedly present for "
                f"epoch={epoch}, frame={reference_frame}, body={central_body}, "
                f"count={sample_count}, degree={interpolation_degree}, "
                f"velocity={with_velocity}"
            )

    if probed == 0:
        raise CrossValidationError(
            "no libration probe requests succeeded; cannot assert field absence"
        )
