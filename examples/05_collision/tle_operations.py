"""
TLE Generation from Orbital Elements

Demonstrates conversion from Keplerian orbital elements to Two-Line Element (TLE)
format for satellite catalog operations and SGP4 propagation.
"""

from astrox.conjunction_analysis import get_tle

# Example 1: Generate TLE for LEO satellite
print("=" * 70)
print("Example 1: LEO Satellite TLE Generation")
print("=" * 70)

# ISS-like orbit parameters
iss_tle = get_tle(
    name="ISS-LIKE",
    ssc="99001",  # NORAD catalog number (5 digits)
    epoch="2021-04-30T12:00:00.000Z",
    b_star=0.000037381,  # Atmospheric drag coefficient (1/Earth radii)
    sma=6778.0,  # Semi-major axis (km) - ~400 km altitude
    ecc=0.0002714,  # Eccentricity
    inc=51.6441,  # Inclination (deg, TEME frame)
    w=302.6679,  # Argument of perigee (deg, TEME)
    raan=217.3237,  # Right ascension of ascending node (deg, TEME)
    ta=206.5255,  # True anomaly (deg, TEME)
    is_mean_elements=False,  # Using osculating elements
)

print("\nGenerated TLE for LEO satellite:")
print(f"Name: {iss_tle['SAT_Name']}")  # ISS-LIKE
print(f"SSC: {iss_tle['SAT_Number']}")  # 99001
print(f"\nTLE Line 1: {iss_tle['TLE_Line1']}")  # e.g., 1 99001U 99999A   21120.50000000  .00000000  00000-0  00000-0 0  9995
print(f"TLE Line 2: {iss_tle['TLE_Line2']}")  # e.g., 2 99001  51.6346 217.3462 0016077 284.8260 224.4008 15.56945662    01

# Example 2: GEO satellite TLE
print("\n" + "=" * 70)
print("Example 2: Geostationary Satellite TLE")
print("=" * 70)

geo_tle = get_tle(
    name="GEO-COMSAT",
    ssc="99002",
    epoch="2021-04-30T00:00:00.000Z",
    b_star=0.0,  # Negligible drag at GEO altitude
    sma=42164.0,  # GEO semi-major axis (km)
    ecc=0.0001,  # Near-circular
    inc=0.05,  # Near-equatorial (deg)
    w=0.0,  # Argument of perigee
    raan=75.0,  # RAAN for specific longitude
    ta=0.0,  # True anomaly
    is_mean_elements=True,  # Mean elements more common for GEO
)

print("\nGenerated TLE for GEO satellite:")
print(f"Name: {geo_tle['SAT_Name']}")  # GEO-COMSAT
print(f"TLE Line 1: {geo_tle['TLE_Line1']}")  # e.g., 1 99002U 99999A   21120.00000000  .00000000  00000-0  00000-0 0  9991
print(f"TLE Line 2: {geo_tle['TLE_Line2']}")  # e.g., 2 99002   0.0727  79.1489 0000989 356.0137 359.8399  1.00278301    05

altitude_geo = 42164.0 - 6378.137  # km above Earth surface
print(f"\nOrbital parameters:")
print(f"  Altitude: {altitude_geo:.1f} km")  # 35785.9 km
print(f"  Inclination: {0.05} deg (near-equatorial)")
print(f"  Eccentricity: {0.0001} (near-circular)")

# Example 3: Sun-Synchronous Orbit (SSO) TLE
print("\n" + "=" * 70)
print("Example 3: Sun-Synchronous Orbit TLE")
print("=" * 70)

sso_tle = get_tle(
    name="SSO-EARTH-OBS",
    ssc="99003",
    epoch="2021-04-30T06:00:00.000Z",
    b_star=0.00005,  # Moderate drag
    sma=7078.0,  # ~700 km altitude
    ecc=0.001,  # Nearly circular
    inc=98.2,  # Sun-synchronous inclination (deg)
    w=90.0,  # Argument of perigee
    raan=120.0,  # RAAN
    ta=0.0,  # True anomaly at epoch
    is_mean_elements=False,
)

print("\nGenerated TLE for SSO satellite:")
print(f"Name: {sso_tle['SAT_Name']}")  # SSO-EARTH-OBS
print(f"TLE Line 1: {sso_tle['TLE_Line1']}")  # e.g., 1 99003U 99999A   21120.25000000  .00000000  00000-0  00000-0 0  9999
print(f"TLE Line 2: {sso_tle['TLE_Line2']}")  # e.g., 2 99003  98.1947 120.0000 0016452  90.0000   0.0000 14.54214189    00

altitude_sso = 7078.0 - 6378.137
print(f"\nOrbital parameters:")
print(f"  Altitude: {altitude_sso:.1f} km")  # 699.9 km
print(f"  Inclination: {98.2} deg (sun-synchronous)")
print(f"  Period: ~99 minutes")

# Example 4: Molniya orbit TLE
print("\n" + "=" * 70)
print("Example 4: Molniya Orbit TLE")
print("=" * 70)

molniya_tle = get_tle(
    name="MOLNIYA-COM",
    ssc="99004",
    epoch="2021-04-30T00:00:00.000Z",
    b_star=0.00001,  # Low drag (high apogee)
    sma=26554.0,  # Semi-major axis for 12-hour period (km)
    ecc=0.74,  # Highly eccentric
    inc=63.4,  # Critical inclination (minimizes argument of perigee drift)
    w=270.0,  # Argument of perigee (deg)
    raan=180.0,  # RAAN
    ta=0.0,  # At perigee
    is_mean_elements=True,
)

print("\nGenerated TLE for Molniya satellite:")
print(f"Name: {molniya_tle['SAT_Name']}")
print(f"TLE Line 1: {molniya_tle['TLE_Line1']}")
print(f"TLE Line 2: {molniya_tle['TLE_Line2']}")

perigee_alt = 26554.0 * (1 - 0.74) - 6378.137
apogee_alt = 26554.0 * (1 + 0.74) - 6378.137
print(f"\nOrbital parameters:")
print(f"  Perigee altitude: {perigee_alt:.1f} km")
print(f"  Apogee altitude: {apogee_alt:.1f} km")
print(f"  Inclination: {63.4} deg (critical)")
print(f"  Period: ~12 hours")

# Example 5: Debris object with high drag
print("\n" + "=" * 70)
print("Example 5: Space Debris with High Drag")
print("=" * 70)

debris_tle = get_tle(
    name="DEBRIS-FRAG",
    ssc="99005",
    epoch="2021-04-30T12:00:00.000Z",
    b_star=0.001,  # Very high drag coefficient
    sma=6678.0,  # Low altitude (~300 km)
    ecc=0.01,  # Slightly eccentric
    inc=45.0,  # Moderate inclination
    w=180.0,
    raan=90.0,
    ta=45.0,
    is_mean_elements=False,
)

print("\nGenerated TLE for high-drag debris:")
print(f"Name: {debris_tle['SAT_Name']}")
print(f"TLE Line 1: {debris_tle['TLE_Line1']}")
print(f"TLE Line 2: {debris_tle['TLE_Line2']}")

altitude_debris = 6678.0 - 6378.137
print(f"\nOrbital parameters:")
print(f"  Altitude: {altitude_debris:.1f} km (low)")
print(f"  B*: {0.001} (high drag - rapid decay expected)")

# Example 6: Batch generation for constellation
print("\n" + "=" * 70)
print("Example 6: Constellation TLE Generation")
print("=" * 70)

print("\nGenerating TLEs for 4-satellite constellation:")

constellation_tles = []
for i in range(4):
    tle = get_tle(
        name=f"CONST-SAT-{i + 1}",
        ssc=f"9901{i}",
        epoch="2021-04-30T00:00:00.000Z",
        b_star=0.00005,
        sma=7178.0,  # 800 km altitude
        ecc=0.001,
        inc=55.0,
        w=0.0,
        raan=i * 90.0,  # Evenly spaced RAANs (0, 90, 180, 270 deg)
        ta=0.0,
        is_mean_elements=True,
    )
    constellation_tles.append(tle)

for i, tle in enumerate(constellation_tles, 1):
    print(f"\nSatellite {i}:")
    print(f"  {tle['TLE_Line1']}")
    print(f"  {tle['TLE_Line2']}")

print("\n" + "=" * 70)
print("TLE Generation Complete")
print("=" * 70)
print("\nKey Parameters:")
print("  - ssc: NORAD catalog number (5-digit string)")
print("  - epoch: Element epoch in UTC (YYYY-MM-DDTHH:MM:SS.fffZ)")
print("  - b_star: Drag coefficient (1/Earth radii)")
print("    * LEO: 0.00001-0.0001 (typical)")
print("    * High drag debris: 0.001+")
print("    * GEO: ~0 (negligible)")
print("  - sma: Semi-major axis in km")
print("  - All angles in degrees, TEME reference frame")
print("  - is_mean_elements:")
print("    * True: Mean elements (removes short-period variations)")
print("    * False: Osculating elements (instantaneous state)")
print("\nUse Cases:")
print("  - Generate TLEs from propagated states")
print("  - Create synthetic satellite catalogs")
print("  - Convert between orbital element formats")
print("  - Feed TLEs to SGP4 propagator")
