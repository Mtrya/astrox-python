# How-To Guides

Task-oriented how-to guides; each one solves a specific problem.

- [How to propagate an orbit](propagate_an_orbit.md): choose a propagator based on the orbit description you have (Keplerian elements, TLE, or force model config) and read the sampled output.
- [Convert between orbit representations](convert_between_orbit_representations.md): convert between Keplerian elements, Cartesian state, and Kozai-Izsak mean elements.
- [Build an HPOP force model config](build_an_hpop_configuration.md): assemble integrator, gravity field, atmosphere, solar radiation pressure, and third-body perturbations using the `hpop_config` family of constructors.
- [Compute lighting conditions](compute_lighting_conditions.md): sunlight/penumbra/umbra intervals, solar intensity, and solar AER samples.
- [Compute access intervals between a ground station and a satellite](compute_access_intervals.md): direct access computation, AER output, and elevation constraints.

For full parameter descriptions for each guide, see the corresponding [manual](../manual/README.md) entries; validation evidence is in the [validation documents](../../../validation/README.md).
