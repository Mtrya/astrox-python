"""Independent numerical support for libration cross-validation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from astrox import libration


EARTH_MOON_MASS_RATIO = 0.01215058560962404
EARTH_GM_M3_S2 = 398600441800000.0
MOON_GM_M3_S2 = 4904869500000.0
EARTH_MOON_MEAN_SEPARATION_M = 384400000.0

ROOT_ABS_TOL = 5.0e-13
UNIT_REL_TOL = 5.0e-15
TRAJECTORY_TIME_ABS_TOL = 5.0e-14
TRAJECTORY_STATE_ABS_TOL = 2.0e-10
PERIODIC_SAMPLE_ABS_TOL = 2.0e-8
PERIODIC_CLOSURE_ABS_TOL = 2.0e-8
JACOBI_DRIFT_ABS_TOL = 5.0e-10
SYMMETRY_ABS_TOL = 2.0e-8


class CrossValidationError(Exception):
    """Raised when ASTROX disagrees with an independent CRTBP calculation."""


@dataclass(frozen=True, kw_only=True)
class EquilibriumSolution:
    """Independent five-point equilibrium solution in barycentric coordinates."""

    points: tuple[tuple[float, float], ...]
    distances: tuple[float, float, float]


@dataclass(frozen=True, kw_only=True)
class PeriodicMetrics:
    """Independent residuals for one ASTROX periodic orbit."""

    max_sample_residual: float
    closure_residual: float
    jacobi_drift: float
    half_period_y_abs: float
    half_period_vx_abs: float
    half_period_vz_abs: float


def as_array(state: libration.CrtbpState) -> np.ndarray:
    """Convert an SDK state to a six-value NumPy array."""
    return np.asarray(state.to_wire(), dtype=float)


def to_barycentric_state(
    state: Sequence[float] | np.ndarray,
    *,
    mass_ratio: float,
    is_barycentric: bool,
) -> np.ndarray:
    """Normalize an ASTROX state to the standard barycentric rotating origin."""
    values = np.asarray(state, dtype=float).copy()
    if values.shape != (6,):
        raise ValueError("CRTBP states must contain six values")
    if not is_barycentric:
        values[0] -= mass_ratio
    return values


def from_barycentric_states(
    states: np.ndarray,
    *,
    mass_ratio: float,
    is_barycentric: bool,
) -> np.ndarray:
    """Convert standard barycentric states to an ASTROX response origin."""
    values = np.asarray(states, dtype=float).copy()
    if values.ndim != 2 or values.shape[1] != 6:
        raise ValueError("CRTBP state arrays must have shape (n, 6)")
    if not is_barycentric:
        values[:, 0] += mass_ratio
    return values


def crtbp_derivative(
    _time: float,
    state: np.ndarray,
    mass_ratio: float,
) -> np.ndarray:
    """Standard nondimensional CRTBP equations in the barycentric rotating frame."""
    x, y, z, vx, vy, vz = state
    primary_distance = math.sqrt((x + mass_ratio) ** 2 + y**2 + z**2)
    secondary_distance = math.sqrt((x - 1.0 + mass_ratio) ** 2 + y**2 + z**2)
    primary_factor = (1.0 - mass_ratio) / primary_distance**3
    secondary_factor = mass_ratio / secondary_distance**3
    ax = 2.0 * vy + x - primary_factor * (x + mass_ratio) - secondary_factor * (
        x - 1.0 + mass_ratio
    )
    ay = -2.0 * vx + y - primary_factor * y - secondary_factor * y
    az = -primary_factor * z - secondary_factor * z
    return np.asarray((vx, vy, vz, ax, ay, az), dtype=float)


def propagate_local(
    *,
    mass_ratio: float,
    initial_state: Sequence[float] | np.ndarray,
    times: Sequence[float] | np.ndarray,
    is_barycentric: bool,
) -> np.ndarray:
    """Integrate the local CRTBP equations at the supplied ASTROX sample times."""
    sample_times = np.asarray(times, dtype=float)
    if sample_times.ndim != 1 or sample_times.size == 0:
        raise ValueError("times must be a non-empty one-dimensional sequence")
    if sample_times.size > 1:
        differences = np.diff(sample_times)
        direction = math.copysign(1.0, float(sample_times[-1] - sample_times[0]))
        if np.any(direction * differences <= 0.0):
            raise ValueError("times must be strictly monotonic")
    normalized_initial = to_barycentric_state(
        initial_state,
        mass_ratio=mass_ratio,
        is_barycentric=is_barycentric,
    )
    if sample_times.size == 1:
        return from_barycentric_states(
            normalized_initial.reshape(1, 6),
            mass_ratio=mass_ratio,
            is_barycentric=is_barycentric,
        )
    result = solve_ivp(
        lambda time, state: crtbp_derivative(time, state, mass_ratio),
        (float(sample_times[0]), float(sample_times[-1])),
        normalized_initial,
        method="DOP853",
        t_eval=sample_times,
        rtol=2.0e-13,
        atol=2.0e-15,
        max_step=0.01,
    )
    if not result.success or result.y.shape != (6, sample_times.size):
        raise CrossValidationError(
            f"local CRTBP integration failed: {result.message}; shape={result.y.shape}"
        )
    return from_barycentric_states(
        result.y.T,
        mass_ratio=mass_ratio,
        is_barycentric=is_barycentric,
    )


def jacobi_constant(
    state: Sequence[float] | np.ndarray,
    *,
    mass_ratio: float,
    is_barycentric: bool,
) -> float:
    """Return the Parker-convention Jacobi constant for one ASTROX state."""
    x, y, z, vx, vy, vz = to_barycentric_state(
        state,
        mass_ratio=mass_ratio,
        is_barycentric=is_barycentric,
    )
    primary_distance = math.sqrt((x + mass_ratio) ** 2 + y**2 + z**2)
    secondary_distance = math.sqrt((x - 1.0 + mass_ratio) ** 2 + y**2 + z**2)
    potential = (
        0.5 * (x**2 + y**2)
        + (1.0 - mass_ratio) / primary_distance
        + mass_ratio / secondary_distance
    )
    return 2.0 * potential - (vx**2 + vy**2 + vz**2)


def jacobi_drift(
    states: Sequence[Sequence[float]] | np.ndarray,
    *,
    mass_ratio: float,
    is_barycentric: bool,
) -> float:
    """Compute ``max(abs(C(t) - C(0)))`` without external summary metrics."""
    constants = np.asarray(
        [
            jacobi_constant(
                state,
                mass_ratio=mass_ratio,
                is_barycentric=is_barycentric,
            )
            for state in states
        ],
        dtype=float,
    )
    return float(np.max(np.abs(constants - constants[0])))


def equilibrium_solution(mass_ratio: float) -> EquilibriumSolution:
    """Solve all five equilibrium points independently with bracketed roots."""
    mu = float(mass_ratio)
    primary_x = -mu
    secondary_x = 1.0 - mu
    epsilon = 1.0e-10

    def equilibrium_x(x: float) -> float:
        primary_delta = x + mu
        secondary_delta = x - 1.0 + mu
        return (
            x
            - (1.0 - mu) * primary_delta / abs(primary_delta) ** 3
            - mu * secondary_delta / abs(secondary_delta) ** 3
        )

    l1_x = brentq(
        equilibrium_x,
        primary_x + epsilon,
        secondary_x - epsilon,
        xtol=5.0e-15,
        rtol=1.0e-15,
    )
    l2_x = brentq(
        equilibrium_x,
        secondary_x + epsilon,
        secondary_x + 5.0,
        xtol=5.0e-15,
        rtol=1.0e-15,
    )
    l3_x = brentq(
        equilibrium_x,
        primary_x - 5.0,
        primary_x - epsilon,
        xtol=5.0e-15,
        rtol=1.0e-15,
    )
    triangular_x = 0.5 - mu
    triangular_y = math.sqrt(3.0) / 2.0
    return EquilibriumSolution(
        points=(
            (l1_x, 0.0),
            (l2_x, 0.0),
            (l3_x, 0.0),
            (triangular_x, triangular_y),
            (triangular_x, -triangular_y),
        ),
        distances=(
            secondary_x - l1_x,
            l2_x - secondary_x,
            primary_x - l3_x,
        ),
    )


def unit_scales(
    *,
    primary_gravitational_parameter_m3_s2: float,
    secondary_gravitational_parameter_m3_s2: float,
    mean_separation_m: float,
) -> tuple[float, float, float, float]:
    """Derive mass ratio and CRTBP length/time/velocity units in closed form."""
    total_gm = (
        primary_gravitational_parameter_m3_s2
        + secondary_gravitational_parameter_m3_s2
    )
    mass_ratio = secondary_gravitational_parameter_m3_s2 / total_gm
    time_unit_s = math.sqrt(mean_separation_m**3 / total_gm)
    velocity_unit_m_s = mean_separation_m / time_unit_s
    return mass_ratio, mean_separation_m, time_unit_s, velocity_unit_m_s


def trajectory_arrays(
    result: libration.CrtbpTrajectory,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract time and six-state arrays from an SDK trajectory result."""
    return (
        np.asarray([sample.time for sample in result.samples], dtype=float),
        np.asarray([sample.state.to_wire() for sample in result.samples], dtype=float),
    )


def periodic_arrays(
    result: libration.PeriodicOrbit,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract time and six-state arrays from an SDK periodic result."""
    return (
        np.asarray([sample.time for sample in result.samples], dtype=float),
        np.asarray([sample.state.to_wire() for sample in result.samples], dtype=float),
    )


def maximum_absolute_residual(actual: np.ndarray, expected: np.ndarray) -> float:
    """Return the largest componentwise absolute residual."""
    actual_values = np.asarray(actual, dtype=float)
    expected_values = np.asarray(expected, dtype=float)
    if actual_values.shape != expected_values.shape:
        raise CrossValidationError(
            f"comparison shape mismatch: actual={actual_values.shape}, expected={expected_values.shape}"
        )
    return float(np.max(np.abs(actual_values - expected_values)))


def validate_periodic_orbit(
    result: libration.PeriodicOrbit,
    *,
    mass_ratio: float = EARTH_MOON_MASS_RATIO,
) -> PeriodicMetrics:
    """Independently propagate and measure a complete ASTROX periodic result."""
    times, states = periodic_arrays(result)
    if times.size < 3:
        raise CrossValidationError("periodic result must contain at least three samples")
    if not math.isclose(times[0], 0.0, abs_tol=TRAJECTORY_TIME_ABS_TOL):
        raise CrossValidationError(f"periodic samples start at {times[0]:.12g}, expected 0")
    if not math.isclose(
        times[-1],
        result.period,
        abs_tol=TRAJECTORY_TIME_ABS_TOL,
    ):
        raise CrossValidationError(
            f"periodic samples end at {times[-1]:.12g}, period={result.period:.12g}"
        )
    independent_states = propagate_local(
        mass_ratio=mass_ratio,
        initial_state=result.corrected_state.to_wire(),
        times=times,
        is_barycentric=result.is_barycentric,
    )
    max_sample_residual = maximum_absolute_residual(states, independent_states)
    closure_residual = maximum_absolute_residual(
        independent_states[-1],
        independent_states[0],
    )
    drift = jacobi_drift(
        independent_states,
        mass_ratio=mass_ratio,
        is_barycentric=result.is_barycentric,
    )
    half_times = np.asarray((0.0, result.period / 2.0), dtype=float)
    half_state = propagate_local(
        mass_ratio=mass_ratio,
        initial_state=result.corrected_state.to_wire(),
        times=half_times,
        is_barycentric=result.is_barycentric,
    )[-1]
    return PeriodicMetrics(
        max_sample_residual=max_sample_residual,
        closure_residual=closure_residual,
        jacobi_drift=drift,
        half_period_y_abs=abs(float(half_state[1])),
        half_period_vx_abs=abs(float(half_state[3])),
        half_period_vz_abs=abs(float(half_state[5])),
    )


def assert_periodic_metrics(metrics: PeriodicMetrics, *, case_id: str) -> None:
    """Apply pre-declared precision bounds to independent periodic metrics."""
    bounds = {
        "sample residual": (metrics.max_sample_residual, PERIODIC_SAMPLE_ABS_TOL),
        "closure residual": (metrics.closure_residual, PERIODIC_CLOSURE_ABS_TOL),
        "Jacobi drift": (metrics.jacobi_drift, JACOBI_DRIFT_ABS_TOL),
        "half-period y": (metrics.half_period_y_abs, SYMMETRY_ABS_TOL),
        "half-period vx": (metrics.half_period_vx_abs, SYMMETRY_ABS_TOL),
        "half-period vz": (metrics.half_period_vz_abs, SYMMETRY_ABS_TOL),
    }
    failures = [
        f"{name}={value:.12g} > {bound:.12g}"
        for name, (value, bound) in bounds.items()
        if value > bound
    ]
    if failures:
        raise CrossValidationError(f"{case_id}: " + "; ".join(failures))
