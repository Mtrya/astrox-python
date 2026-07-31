# astrox-python

astrox-python is the Python SDK for the ASTROX Web API.

## Installation

Requires Python 3.10 or later.

```bash
pip install astrox-python
```

## One-minute example

Propagate with J2 using a set of Keplerian elements:

```python
import astrox
from astrox import orbits, propagator

astrox.configure(base_url="http://astrox.cn:8765")

orbit = orbits.keplerian(
    semi_major_axis_m=6778137.0,
    eccentricity=0.001,
    inclination_deg=51.6,
    argument_of_periapsis_deg=0.0,
    raan_deg=120.0,
    true_anomaly_deg=45.0,
)

period_s, position = propagator.j2(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T00:10:00.000Z",
    orbit_epoch="2024-01-01T00:00:00.000Z",
    orbit=orbit,
)

print(f"轨道周期: {period_s:.3f} s")
print(f"位置/速度采样数: {len(position.cartesian_velocity)}")
```

For the full first-run walkthrough, see [Getting Started](getting_started.md).

## Documentation

- Full documentation navigation: [docs/README.md](../../README.md)
- Runnable examples: [examples/](../../../examples/)
- This page is the English snapshot of the Chinese-first [README](../../../README.md). English snapshots of the user-facing docs live alongside it under `docs/i18n/en/`.

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for development setup and build steps.

## License

MIT — see [LICENSE](../../../LICENSE).

This project is currently in Alpha.
