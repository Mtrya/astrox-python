# Coverage Analysis Examples

This directory contains comprehensive examples demonstrating the ASTROX coverage analysis capabilities. Coverage analysis determines which ground locations can be observed by satellites over time, essential for mission planning, constellation design, and performance evaluation.

## Overview

The coverage module provides 8 functions organized into 3 categories:

### 1. Grid & Basic Coverage (2 functions)
- `get_grid_points()` - Generate coverage grid point coordinates
- `compute_coverage()` - Compute coverage intervals for all grid points

### 2. Figure of Merit (FOM) Calculations (5 functions)
- `fom_simple_coverage()` - Binary coverage indicator (0 or 1)
- `fom_coverage_time()` - Total coverage duration (seconds)
- `fom_number_of_assets()` - Number of satellites covering each point
- `fom_response_time()` - Time to first coverage (seconds)
- `fom_revisit_time()` - Gap between consecutive passes (seconds)

### 3. Statistical Reporting (2 functions)
- `report_coverage_by_asset()` - Per-satellite coverage statistics
- `report_percent_coverage()` - Overall coverage percentage over time

## Example Scripts

### 1. `basic_coverage.py` - Grid Generation and Coverage Computation

**Functions demonstrated:**
- `get_grid_points()`
- `compute_coverage()`

**What you'll learn:**
- Create different grid types (global, latitude bounds, lat/lon bounds)
- Define satellite constellations with J2 and SGP4 propagation
- Configure sensors (conic and rectangular)
- Compute coverage intervals and statistics

**Key scenarios:**
- Global coverage grid (6° resolution)
- Latitude bounds grid (30°S to 60°N)
- Regional grid (China: 18°N-54°N, 73°E-135°E)
- 3-satellite SSO constellation coverage
- ISS coverage over North America with constraints

**Run it:**
```bash
python examples/02_coverage/basic_coverage.py
```

### 2. `fom_calculations.py` - Figure of Merit Analysis

**Functions demonstrated:**
- `fom_simple_coverage()`
- `fom_coverage_time()`
- `fom_number_of_assets()`
- `fom_response_time()`
- `fom_revisit_time()`

**What you'll learn:**
- Calculate all 5 types of coverage FOMs
- Use different output modes (grid_point, grid_stats, grid_stats_over_time)
- Analyze 6-satellite Walker constellation performance
- Compare multiple FOMs for same scenario

**Key metrics explained:**
- **Simple Coverage**: Binary indicator (1 = covered, 0 = not covered)
- **Coverage Time**: Total seconds each point is covered during analysis
- **Number of Assets**: How many satellites simultaneously cover each point
- **Response Time**: Seconds from analysis start until first coverage
- **Revisit Time**: Average gap between consecutive satellite passes

**Output modes:**
- `grid_point` - Values for each grid point over time
- `grid_point_at_time` - Values at specific time instant
- `grid_stats` - Statistical summary (min/max/mean/stddev)
- `grid_stats_over_time` - Statistics evolution over time

**Run it:**
```bash
python examples/02_coverage/fom_calculations.py
```

### 3. `coverage_statistics.py` - Statistical Reporting

**Functions demonstrated:**
- `report_coverage_by_asset()`
- `report_percent_coverage()`

**What you'll learn:**
- Generate per-satellite performance reports
- Track overall coverage percentage evolution
- Compare different constellation architectures
- Analyze sensor field-of-view impact on coverage

**Key scenarios:**
- 9-satellite LEO constellation (3 planes × 3 sats)
- 4-satellite regional constellation (inclined GEO)
- Constellation comparison (LEO vs Regional)
- Sensor FOV impact analysis (narrow/medium/wide)

**Report types:**
- **Per-Asset**: Min/Max/Average/Cumulative coverage % for each satellite
- **Percent Coverage**: Instantaneous and cumulative coverage % over time

**Run it:**
```bash
python examples/02_coverage/fom_calculations.py
```

## Common Patterns

### Creating Coverage Grids

```python
from astrox._models import (
    CoverageGridGlobal,
    CoverageGridLatitudeBounds,
    CoverageGridLatLonBounds,
)

# Global grid (full Earth)
global_grid = CoverageGridGlobal(
    CentralBodyName="Earth",
    Resolution=6.0,  # 6° resolution
    Height=0.0,  # Sea level
)

# Latitude bounds (e.g., ±60°)
lat_grid = CoverageGridLatitudeBounds(
    MinLatitude=-60.0,
    MaxLatitude=60.0,
    Resolution=5.0,
)

# Regional grid (e.g., Asia-Pacific)
region_grid = CoverageGridLatLonBounds(
    MinLatitude=0.0,
    MaxLatitude=60.0,
    MinLongitude=60.0,
    MaxLongitude=180.0,
    Resolution=2.0,
)
```

### Defining Satellites with Sensors

```python
from astrox.models import EntityPath, ConicSensor, J2Position
from astrox._models import KeplerElements

satellite = EntityPath(
    Name="SSO-Sat1",
    Description="Sun-synchronous orbit satellite",
    Position=J2Position(
        CentralBody="Earth",
        J2NormalizedValue=0.000484165143790815,
        RefDistance=6378137.0,
        OrbitEpoch="2024-01-01T00:00:00.000Z",
        CoordType="Classical",
        OrbitalElements=KeplerElements(
            SemimajorAxis=6378137.0 + 800000.0,  # 800 km altitude
            Eccentricity=0.001,
            Inclination=98.5,
            ArgumentOfPeriapsis=0.0,
            RightAscensionOfAscendingNode=0.0,
            TrueAnomaly=0.0,
        ),
    ),
)

# Define sensor (optional)
sensor = ConicSensor(
    outerHalfAngle=50.0,  # 50° half-angle (100° total FOV)
)
```

### Computing Coverage

```python
from astrox.coverage import compute_coverage

result = compute_coverage(
    start="2024-01-01T00:00:00.000Z",
    stop="2024-01-01T12:00:00.000Z",
    grid=grid,
    assets=[satellite1, satellite2, satellite3],
    description="Constellation coverage analysis",
    step=60.0,  # 60-second time step
    contain_coverage_points=True,
)

intervals = result["SatisfactionIntervalsWithNumberOfAssets"]
# Process coverage intervals...
```

### Calculating FOMs

```python
from astrox.coverage import fom_coverage_time, fom_revisit_time

# Coverage time FOM
result = fom_coverage_time(
    start=start_time,
    stop=stop_time,
    grid=grid,
    assets=satellites,
    output="grid_stats",  # Get statistical summary
    step=120.0,
)

mean_time = result["Mean"]
print(f"Mean coverage time: {mean_time / 3600:.2f} hours")

# Revisit time FOM
result = fom_revisit_time(
    start=start_time,
    stop=stop_time,
    grid=grid,
    assets=satellites,
    output="grid_stats",
    step=120.0,
)

mean_revisit = result["Mean"]
print(f"Mean revisit time: {mean_revisit / 60:.1f} minutes")
```

### Generating Reports

```python
from astrox.coverage import report_coverage_by_asset, report_percent_coverage

# Per-asset coverage report
result = report_coverage_by_asset(
    start=start_time,
    stop=stop_time,
    grid=grid,
    assets=satellites,
    step=180.0,
)

for data in result["CoverageByAssetDatas"]:
    name = data["AssetName"]
    avg_pct = data["AveragePercentCovered"]
    cum_pct = data["CumulativePercentCovered"]
    print(f"{name}: Avg={avg_pct:.2f}%, Cumul={cum_pct:.2f}%")

# Overall coverage percentage over time
result = report_percent_coverage(
    start=start_time,
    stop=stop_time,
    grid=grid,
    assets=satellites,
    step=600.0,
)

instant_data = result["InstantaneousPercentCoverages"]
cumul_data = result["CumulativePercentCoverages"]
# Process time series data...
```

## Grid Resolution Guidelines

Choosing appropriate grid resolution affects computation time and accuracy:

| Resolution | Grid Points (Global) | Use Case |
|------------|---------------------|----------|
| 20° | ~100 points | Quick feasibility studies |
| 10° | ~400 points | Preliminary design |
| 6° | ~1,100 points | Standard analysis |
| 2° | ~10,000 points | Detailed mission planning |
| 1° | ~40,000 points | High-fidelity validation |

**Tip**: Start with coarse grids (10-20°) during development, then refine for production.

## Time Step Selection

Time step affects coverage interval accuracy:

| Orbit Type | Recommended Step | Rationale |
|------------|------------------|-----------|
| LEO (< 1000 km) | 30-60 seconds | Fast orbital motion |
| MEO (1000-20000 km) | 60-120 seconds | Moderate orbital period |
| GEO/HEO | 120-300 seconds | Slower apparent motion |

**Tip**: Smaller steps improve accuracy but increase computation time. Balance based on mission requirements.

## Constellation Design Tips

Based on examples in this directory:

1. **Walker Constellations** - Symmetric coverage, good for global applications
   - Example: 3 planes × 2 sats = 6 satellites
   - Provides regular revisit times

2. **Sun-Synchronous Orbits** - Consistent lighting conditions
   - Inclination: ~98° for Earth
   - Altitude: 600-800 km typical
   - Phase shifts improve coverage

3. **Regional Constellations** - Optimized for specific areas
   - Inclined GEO: Better mid-latitude coverage
   - Lower inclination LEO: Equatorial focus

4. **Sensor Selection** - Balance FOV vs resolution
   - Wide FOV (>90°): Better coverage, lower resolution
   - Narrow FOV (<45°): Better resolution, requires more satellites

## Performance Considerations

Coverage calculations can be computationally intensive. Tips for optimization:

1. **Use latitude/regional grids** instead of global when possible
2. **Increase time step** for preliminary analysis (60-120 seconds)
3. **Coarsen grid resolution** during development (10-20°)
4. **Reduce analysis duration** for testing (6-12 hours vs full day)
5. **Use grid_stats output** instead of grid_point when only summary needed

## Further Reading

- **Coverage Theory**: See `docs/coverage_fundamentals.md` (if available)
- **Constellation Design**: See `examples/04_orbit_design/walker_constellation.py`
- **Sensor Modeling**: See `docs/sensor_models.md` (if available)
- **API Reference**: See function docstrings in `astrox/coverage.py`

## Related Examples

- **Access Computation**: `examples/03_access/` - Point-to-point access analysis
- **Orbit Design**: `examples/04_orbit_design/` - Create optimal constellations
- **Propagation**: `examples/01_propagation/` - Understand orbit dynamics

## Troubleshooting

**Q: Coverage computation is slow**
A: Try coarser grid (10-20°), larger time step (120s), or shorter duration (6 hours)

**Q: No coverage intervals returned**
A: Check satellite altitude, sensor FOV, and grid point constraints. LEO satellites need wide FOV sensors (>45°) for global coverage.

**Q: Unexpected coverage gaps**
A: Increase time step accuracy (smaller step size) or check for occulting bodies

**Q: Memory issues with large grids**
A: Use latitude bounds instead of global grid, or increase resolution to reduce points

## Contact & Support

For questions or issues:
- GitHub Issues: https://github.com/your-org/astrox-client/issues
- Documentation: See main README and function docstrings
- API Server: http://astrox.cn:8765/
