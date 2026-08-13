# How-To Guides

Task-oriented how-to guides; each one solves a specific problem.

- [How to propagate an orbit](propagate_an_orbit.md): choose a propagator based on the orbit description you have (Keplerian elements, TLE, or force model config) and read the sampled output.
- [Convert between orbit representations](convert_between_orbit_representations.md): convert between Keplerian elements, Cartesian state, and Kozai-Izsak mean elements.
- [Generate and inspect a CRTBP periodic orbit](generate_a_crtbp_periodic_orbit.md): generate an Earth-Moon Halo orbit, apply fixed-x correction, and integrate one full period.
- [Build an HPOP force model config](build_an_hpop_configuration.md): assemble integrator, gravity field, atmosphere, solar radiation pressure, and third-body perturbations using the `hpop_config` family of constructors.
- [Compute lighting conditions](compute_lighting_conditions.md): sunlight/penumbra/umbra intervals, solar intensity, and solar AER samples.
- [Compute access intervals between a ground station and a satellite](compute_access_intervals.md): direct access computation, AER output, and elevation constraints.
- [Run an Astrogator mission sequence](run_an_astrogator_mcs.md): run a RunMCS mission from an initial state with a registered custom two-body propagator and a duration stop condition, then read the segment results.
- [Screen close approaches between a satellite and space objects](screen_close_approaches.md): use the primary satellite TLE and a list of target TLEs to find close approaches within the analysis window, and understand the filter counts and result fields.
- [Compute a Lambert transfer window between bodies](compute_lambert_transfer.md): scan Lambert transfers between bodies over departure/arrival time windows, and read the transfer results and velocity increments.

For full parameter descriptions for each guide, see the corresponding [manual](../manual/README.md) entries; validation evidence is in the [validation documents](../../../validation/README.md).
