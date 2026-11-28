# Orbital Sim — ISS Tracker & Live Telemetry

Python terminal scripts for tracking the International Space Station (`ISS (ZARYA)`) relative to Fort Worth, TX and streaming real-time onboard sensor telemetry from NASA's ISSLive feed.

## Scripts
- `tracker.py` — Uses Skyfield and planetary ephemeris (`de421.bsp`) to calculate real-time look angles (`altaz`) over Fort Worth, TX (`32.7555° N, 97.3308° W`), solar/eclipse power state, and `10°` elevation downlink windows.
- `telemetry.py` — Connects to NASA's `ISSLIVE` Lightstreamer server to stream live onboard channels including Solar Array 2A voltage/current, Starboard Radiator Loop A temperature, US Lab cabin pressure, and the ISS GMT signal heartbeat.

## Setup & Usage

1. Create and activate a virtual environment:
   python3 -m venv venv && source venv/bin/activate

2. Install dependencies:
   pip install -r requirements.txt

3. Run the orbital tracker:
   python tracker.py

4. Run the live NASA telemetry stream:
   python telemetry.py

Press Ctrl+C to stop either stream cleanly.
