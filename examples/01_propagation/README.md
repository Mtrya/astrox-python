# Orbit Propagation Examples

This directory contains comprehensive examples for all 9 propagation functions in the `astrox.propagator` module.

## Overview

Orbit propagation computes the future (or past) position and velocity of a satellite based on its current state. Different propagators offer varying levels of accuracy and computational speed.

## Examples

### Single Satellite Propagation

#### 1. `two_body.py` - Two-Body Dynamics
**Function:** `propagate_two_body()`

The simplest propagator using Kepler's laws. Ignores all perturbations.

- **Use case:** Quick calculations, short durations (<1 orbit)
- **Accuracy:** Low for most real orbits
- **Speed:** Fastest
- **Example:** ISS orbit for 1 day

```bash
python two_body.py
```

#### 2. `j2_propagation.py` - J2 Perturbation Model
**Function:** `propagate_j2()`

Includes Earth's oblateness (J2 term), the largest perturbation for most satellites.

- **Use case:** Most Earth satellites, medium-term predictions
- **Accuracy:** Good for days to weeks
- **Speed:** Fast
- **Example:** Sun-synchronous orbit for 7 days
- **Key parameters:**
  - `j2_normalized_value`: 0.000484165143790815 (Earth)
  - `ref_distance`: 6378137.0 m (Earth equatorial radius)

```bash
python j2_propagation.py
```

#### 3. `sgp4_propagation.py` - SGP4 from TLE
**Function:** `propagate_sgp4()`

Standard model for NORAD Two-Line Element (TLE) propagation.

- **Use case:** Public satellite tracking, TLE catalog
- **Accuracy:** Degrades after 5-7 days from TLE epoch
- **Speed:** Fast
- **Example:** International Space Station for 3 days
- **Input:** TLE lines (publicly available from Space-Track.org, Celestrak)

```bash
python sgp4_propagation.py
```

#### 4. `hpop_propagation.py` - High-Precision Propagation
**Function:** `propagate_hpop()`

Most accurate propagator including:
- High-order gravity harmonics
- Atmospheric drag
- Solar radiation pressure
- Third-body perturbations (Moon, Sun)

- **Use case:** Precision applications, collision avoidance, station-keeping
- **Accuracy:** Highest
- **Speed:** Slower due to complexity
- **Example:** GEO satellite for 30 days
- **Requires:** Spacecraft physical properties (mass, area, drag/SRP coefficients)

```bash
python hpop_propagation.py
```

### Specialized Trajectories

#### 5. `ballistic.py` - Ballistic Trajectories
**Function:** `propagate_ballistic()`

Suborbital trajectories from launch to impact.

- **Use case:** Sounding rockets, suborbital tourism, first-stage recovery
- **Example:** Cape Canaveral to Atlantic Ocean
- **Trajectory types:**
  - `ApogeeAlt`: Specify maximum altitude
  - `DeltaV`: Specify initial velocity
  - `TimeOfFlight`: Specify flight duration
  - `DeltaV_MinEcc`: Minimum eccentricity trajectory

```bash
python ballistic.py
```

#### 6. `simple_ascent.py` - Launch Ascent
**Function:** `propagate_simple_ascent()`

Simplified launch vehicle ascent from liftoff to orbit insertion.

- **Use case:** Preliminary mission design, quick studies
- **Example:** Jiuquan launch to LEO (8 minutes)
- **Model:** Linear interpolation between launch and burnout states
- **Note:** For detailed launch analysis, use the rocket module

```bash
python simple_ascent.py
```

### Batch Propagation

#### 7. `batch_propagation.py` - Multiple Satellites
**Functions:**
- `propagate_two_body_batch()`
- `propagate_j2_batch()`
- `propagate_sgp4_batch()`

Efficiently propagate multiple satellites to a common epoch.

- **Use case:** Constellation management, conjunction screening
- **Example 1:** 3-satellite constellation (two-body)
- **Example 2:** 5 satellites at different altitudes (J2)
- **Example 3:** 4 satellites from TLE catalog (SGP4)
- **Advantage:** Single API call for multiple satellites

```bash
python batch_propagation.py
```

## Propagator Comparison

| Propagator | Accuracy | Speed | Perturbations | Best For |
|------------|----------|-------|---------------|----------|
| Two-Body | Low | Fastest | None | Quick checks, <1 orbit |
| J2 | Good | Fast | Earth oblateness | LEO/MEO, days-weeks |
| SGP4 | Medium | Fast | Simplified (J2-J4, drag) | TLE tracking |
| HPOP | Highest | Slower | All major effects | Precision missions |
| Ballistic | Medium | Fast | Gravity only | Suborbital flights |
| Simple Ascent | Low | Fast | Simplified | Launch planning |

## Common Parameters

### Time Format
All times use UTCG format: `"YYYY-MM-DDTHH:MM:SS.fffZ"`
- Example: `"2024-01-01T12:30:45.000Z"`

### Orbital Elements (Classical)
Six elements define an orbit:
1. **Semi-major axis** (a): Orbit size [meters]
2. **Eccentricity** (e): Orbit shape [0-1]
3. **Inclination** (i): Orbit tilt [degrees]
4. **Argument of periapsis** (ω): Orbit orientation [degrees]
5. **RAAN**: Orbital plane orientation [degrees]
6. **True anomaly** (ν): Position in orbit [degrees]

### Coordinate Systems
- **Inertial**: Fixed in space (default for most propagators)
- **Fixed**: Rotating with Earth
- **J2000**: Standard inertial frame
- **TEME**: True Equator Mean Equinox (for SGP4)

## Running the Examples

All examples are standalone and use zero-configuration (no explicit session needed):

```bash
# Run individual examples
python two_body.py
python j2_propagation.py
python sgp4_propagation.py
python hpop_propagation.py
python ballistic.py
python simple_ascent.py
python batch_propagation.py

# Or run all examples
for script in *.py; do
    echo "Running $script..."
    python "$script"
    echo ""
done
```

## Expected Output

Each example prints:
- Input parameters (orbit, time span)
- Success status
- Number of generated position points
- Trajectory characteristics (period, altitude, etc.)
- Key insights about the propagator

## Choosing a Propagator

**Quick reference guide:**

1. **Need high accuracy?** → Use `propagate_hpop()`
2. **Have TLE data?** → Use `propagate_sgp4()`
3. **Medium-term LEO/MEO?** → Use `propagate_j2()`
4. **Quick calculation?** → Use `propagate_two_body()`
5. **Suborbital flight?** → Use `propagate_ballistic()`
6. **Launch ascent?** → Use `propagate_simple_ascent()`
7. **Multiple satellites?** → Use batch versions

## Further Reading

- CLAUDE.md: Complete API documentation
- docs/function_signatures.md: Detailed parameter reference
- astrox/propagator.py: Function source code

## Notes

- All examples use realistic orbital parameters
- Step sizes are chosen for clarity (may not be optimal for production)
- Batch propagation is more efficient than individual calls
- For real missions, validate results with established tools (GMAT, Orekit, etc.)
