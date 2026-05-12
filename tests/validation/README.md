# Validation Tests

These tests verify ASTROX API results against reference values computed with
external, trusted aerospace libraries.

## Reference Value Sources

### brahe (Rust/Python)
- Version: 0.9.0
- Source: https://github.com/duncaneddy/brahe
- Used for: Orbit propagation, coordinate conversions, Keplerian elements

### STK (Systems Tool Kit)
- Version: STK 12
- Source: Analytical Graphics, Inc.
- Used for: High-precision access calculations, coverage analysis

### tudatpy
- Version: 0.8.0
- Source: https://docs.tudat.space/
- Used for: Frame conversions, orbital mechanics

## Generating Reference Values

To generate new reference values:

1. **Install brahe**:
   ```bash
   pip install brahe
   ```

2. **Create a reference script**:
   ```python
   import brahe

   # Compute reference value
   orbit = brahe.Orbit.from_keplerian(...)
   period = orbit.period
   print(f"Reference period: {period:.6f}")
   ```

3. **Hardcode the value** in the test file with a comment indicating the source

## Tolerance Guidelines

| Calculation Type | Typical Tolerance | Notes |
|-----------------|-------------------|-------|
| Orbital period | ±1.0 seconds | J2 effects can vary |
| Position (ECI) | ±100 meters | Depends on propagation model |
| Velocity | ±0.1 m/s | Depends on propagation model |
| Access times | ±1.0 seconds | Ground station dependent |
| Lighting times | ±10 seconds | Seasonal variations |

## Adding New Validation Tests

1. Compute reference value with external tool
2. Hardcode the reference in the test file
3. Use `pytest.approx()` with appropriate tolerance
4. Document the source and version in comments

Example:
```python
# Reference computed with brahe v0.9.0
ISS_PERIOD_REF = 5555.0  # seconds

def test_orbital_period(session):
    result = propagate_two_body(..., session=session)
    period = extract_period(result)
    assert period == pytest.approx(ISS_PERIOD_REF, abs=1.0)
```
