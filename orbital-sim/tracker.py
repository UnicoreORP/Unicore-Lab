import time
from skyfield.api import load, wgs84

# Load timescale, planetary ephemeris, and TLEs
ts = load.timescale()
eph = load('de421.bsp')

# Use local 'stations.tle' if saved, or fetch from CelesTrak
sats = load.tle_file('https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle')
sat = {s.name: s for s in sats}['ISS (ZARYA)']

# Fort Worth, TX Ground Station (10-degree elevation mask for link)
ground_station = wgs84.latlon(32.7555, -97.3308)

print(f"Tracking {sat.name} over Fort Worth, TX (Ctrl+C to stop)...\n")

try:
    while True:
        t = ts.now()
        alt, az, dist = (sat - ground_station).at(t).altaz()
        sunlit = sat.at(t).is_sunlit(eph)
        link_up = alt.degrees > 10.0

        power_mode = "SOLAR (100%)" if sunlit else "ECLIPSE (BATTERY THROTTLE)"
        net_mode = f"DOWNLINK OPEN ({dist.km:.0f} km)" if link_up else "BLACKOUT (STORE-AND-FORWARD)"

        print(f"[{t.utc_strftime('%H:%M:%S')}] Elev: {alt.degrees:6.2f}° | Az: {az.degrees:6.2f}° | {power_mode} | {net_mode}")
        time.sleep(2)
except KeyboardInterrupt:
    print("\nTelemetry stream stopped.")

