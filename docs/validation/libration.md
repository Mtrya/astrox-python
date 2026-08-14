# Libration validation

This page registers the live-contract and semantic evidence for `astrox.libration`. The primary comparison path is an independently written circular restricted three-body problem (CRTBP) model: bracketed equilibrium roots, closed-form unit scales, DOP853 integration, Jacobi conservation, symmetry-plane crossings, and full-period closure. Orekit 13.1 and e2m2e 5.6.8 provide separately qualified secondary comparisons; neither package is treated as an oracle. The exact e2m2e release is a development dependency because it is used only by maintained validation, not by the runtime SDK.

| Surface | Status | Primary evidence | Secondary evidence |
| --- | --- | --- | --- |
| Equilibrium points | verified | Independent scalar roots for L1-L3 and analytical L4/L5 coordinates | Orekit L4/L5 only; its L1-L3 results are constrained diagnostics |
| Nondimensional units | verified | Closed-form mass-ratio, length, time, and velocity scales | Cross-endpoint reuse of the returned mass ratio |
| CRTBP trajectory | verified | Independent equations and DOP853 integration | e2m2e equations, propagation, and STM; Orekit force model and STM |
| Earth-Moon L1 Halo family | verified | Local propagation, closure, Jacobi drift, symmetry, and sample-by-sample comparison | e2m2e generation/correction and Orekit Halo correction |
| Earth-Moon L2 Halo family | verified | Local propagation, closure, Jacobi drift, symmetry, and sample-by-sample comparison | e2m2e generation/correction; Orekit output is accepted only as a seed |
| Earth-Moon DRO family | verified | Local propagation, closure, Jacobi drift, planarity, retrograde direction, and samples | e2m2e generation and two-dimensional correction |
| Fixed-x correction | verified | Independently propagated L1, L2, and DRO corrections | e2m2e two-/three-dimensional correction and Orekit Halo seeds |

The live snapshot at [`tests/validation/live_snapshot/libration/libration.snap.json`](../../tests/validation/live_snapshot/libration/libration.snap.json) maintains 15 cases across all seven routes, both Halo hemispheres, both trajectory origins, forward/reverse and adaptive/fixed sampling, and L1/L2/DRO fixed-x correction. It preserves normalized SDK return values, including array lengths and representative samples from long trajectories, so numerical and structural upstream drift remains visible. The independent semantic claims below still come from cross-validation rather than snapshot agreement.

## Equilibrium points and unit scales

[`test_positions_and_units.py`](../../tests/validation/cross_validation/libration/test_positions_and_units.py) covers Earth-Moon, Sun-Earth, and synthetic mass ratios. All five named coordinates and three collinear distances are cross-validated within an absolute tolerance of `5e-13`. The ten-number wire ordering is decoded as three distances, five x coordinates, then the positive and negative triangular-point y coordinates.

The same script covers two explicit dimensional systems plus the omitted server defaults. The comparison uses:

- `mass_ratio = gm2 / (gm1 + gm2)`
- `length_unit_m = mean_separation_m`
- `time_unit_s = sqrt(length_unit_m**3 / (gm1 + gm2))`
- `velocity_unit_m_s = length_unit_m / time_unit_s`

These fields agree within a relative tolerance of `5e-15`. The time unit is therefore one radian of the normalized mean motion, equivalently the dimensional two-body period divided by `2π`.

The live `/libration/unit` defaults currently produce `mass_ratio = 0.012155650403206972`, while the Earth-Moon periodic-family routes and the OpenAPI trajectory default use `0.01215058560962404`. [`test_cross_endpoint_consistency.py`](../../tests/validation/cross_validation/libration/test_cross_endpoint_consistency.py) preserves this distinction. A caller who combines a family seed with `crtbp_trajectory` or fixed-x correction must pass the family mass ratio explicitly; the SDK consequently requires `mass_ratio` on both generic functions instead of inheriting a server default.

## CRTBP trajectory

[`test_crtbp_trajectory.py`](../../tests/validation/cross_validation/libration/test_crtbp_trajectory.py) compares every returned time and all six state components with an independent DOP853 integration. The matrix includes primary-centered and barycentric origins, forward and reverse intervals, adaptive nodes (`output_step=0`), fixed steps of `0.05` and `0.1`, planar and out-of-plane states, Earth-Moon and synthetic mass ratios, and three propagation durations.

The per-component state tolerance is `2e-10`; the observed maximum residual in the maintained matrix is below `6e-13`. Locally computed Jacobi drift is bounded by `5e-10`. The verified origin relation is `x_barycentric = x_primary_centered - mass_ratio`; the other five components are unchanged.

[`test_e2m2e_qualification.py`](../../tests/validation/cross_validation/libration/test_e2m2e_qualification.py) independently qualifies e2m2e equations and propagation against the local model within `5e-12` and its state transition matrix against finite differences within `1e-8`. [`test_orekit_qualification.py`](../../tests/validation/cross_validation/libration/test_orekit_qualification.py) performs the corresponding Orekit force-model comparison within `2e-11` and STM comparison within `1e-8`.

## Periodic families

[`test_periodic_families.py`](../../tests/validation/cross_validation/libration/test_periodic_families.py) exercises low, middle, and high members of L1 Halo, L2 Halo, and DRO families. Both northern and southern branches are covered for every Halo amplitude. Every returned sample is compared with independent propagation at the same nondimensional time; the full-period closure and XZ-plane half-period symmetry tolerances are `2e-8`, and the Jacobi drift recomputed from ASTROX's returned samples is bounded by `5e-10`. The independent integrator's drift is measured separately at the same bound.

The observed family conventions are:

- Family states are primary-centered and return `is_barycentric == False`.
- L1 `z_amplitude` is the signed magnitude of corrected-state z; the southern branch negates z and vz relative to the northern branch.
- L2 and DRO `x_amplitude` equal `corrected_state.x - 1` in the primary-centered convention.
- DRO states are planar and cross the positive x axis with negative y velocity.
- `initial_state` is the family interpolation seed before differential correction; `corrected_state` is the corrected XZ-plane-crossing state used to generate the returned samples.

The rounded lower limits advertised in prose are not accepted literally by the current server. L2 rejects `0.026` and reports its first available value as `0.026000000000018453`; DRO rejects `0.078` and reports `0.0780437044745057`. The validator keeps both rejection branches explicit instead of rounding the bounds or weakening numerical tolerances.

e2m2e L1/L2 Halo and DRO generation survive local closure, symmetry, and Jacobi checks at the same `2e-8`/`5e-10` bounds. Qualification also checks the requested L1/L2 family location, northern/southern sign and reflection, DRO planarity, and retrograde direction relative to the Moon. Its DRO amplitude denotes the mean of minimum and maximum Moon distance, not ASTROX's x-axis amplitude, so the two amplitude parameters are not compared directly. Orekit's L1 Halo correction is accepted secondary evidence. Its maintained L2 result has approximately `3e-7` independent full-period closure and is therefore used only as a seed that ASTROX refines; it is not accepted as a periodic-orbit reference. Orekit's collinear-point calculation is likewise diagnostic because its normalized roots differ from the independently bracketed values by up to approximately `1.8e-7`.

## Fixed-x differential correction

[`test_fixed_x_correction.py`](../../tests/validation/cross_validation/libration/test_fixed_x_correction.py) covers exact and boundedly perturbed L1 Halo, L2 Halo, and DRO seeds, plus primary-centered and barycentric L1 inputs. It verifies that `initial_state` echoes the supplied seed, corrected x remains exactly fixed, the corrected state returns to the associated family member within `2e-8`, and independent full-period propagation meets closure, Jacobi, and symmetry tolerances.

The live route interprets `period_guess` as a full-period guess. Supplying half the family period does not converge, despite the OpenAPI implementation description mentioning internal half-period correction. A separate coarse seed with z increased and y velocity decreased by `0.05` is tested with the valid full-period guess and also remains an explicit API-error case. The SDK does not reinterpret either response as success.

e2m2e's two-dimensional DRO and three-dimensional Halo fixed-x corrections converge unconditionally for the maintained cases and agree with the ASTROX family seeds within `2e-8`. Conversely, ASTROX accepts independently generated e2m2e L1, L2, and DRO seeds and preserves their corrected states and periods within that bound. e2m2e's `jacobi_error` summary is intentionally excluded because it measures maximum adjacent-sample change rather than total drift from the initial Jacobi constant; all invariant residuals used here are recomputed from states.

## Cross-endpoint consistency

[`test_cross_endpoint_consistency.py`](../../tests/validation/cross_validation/libration/test_cross_endpoint_consistency.py) provides supporting, non-independent checks. L1, L2, and DRO family samples agree with `crtbp_trajectory` at shared times within `2e-10`, and an explicitly supplied unit-system mass ratio is reproduced by the positions and trajectory routes. These checks protect route reconciliation but do not replace the independent equation and invariant comparisons.
