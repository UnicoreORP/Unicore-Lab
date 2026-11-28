# Orbital Sim — ISS Telemetry Tracker

A lightweight Python terminal script using [Skyfield](https://rhodesmill.org) to track the International Space Station (`ISS (ZARYA)`) in real time relative to a ground station in Fort Worth, TX.

## Features
- **Live Elevation & Azimuth:** Computes real-time look angles (`altaz`) from Fort Worth, TX (`32.7555° N, 97.3308° W`).
- **Power State Detection:** Checks planetary ephemeris (`de421.bsp`) to determine whether the ISS is in direct sunlight (`SOLAR`) or Earth's shadow (`ECLIPSE`).
- **Downlink Availability:** Evaluates line-of-sight communication status using a `10°` minimum elevation mask (`DOWNLINK OPEN` vs. `BLACKOUT`).

## Setup & Usage

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the tracker:**
   ```bash
   python tracker.py
   ```
   *(Press `Ctrl+C` to stop the telemetry stream. On first run, Skyfield automatically downloads `de421.bsp` and the latest CelesTrak TLE data locally.)*
