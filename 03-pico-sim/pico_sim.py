import json
import math
import os
import random
import sys
import time

NODE_ID = "unicore-rp2350-sim01"

def generate_reading(tick):
    # Smooth sine-wave drift + subtle sensor noise to mimic a real BME280 sensor
    base_temp_c = 22.5 + 1.8 * math.sin(tick / 15.0) + random.uniform(-0.15, 0.15)
    temp_f = (base_temp_c * 9.0 / 5.0) + 32.0
    humidity = max(20.0, min(90.0, 48.0 + 4.0 * math.cos(tick / 20.0) + random.uniform(-0.4, 0.4)))
    pressure_hpa = 1013.25 + 2.5 * math.sin(tick / 30.0) + random.uniform(-0.1, 0.1)
    vsys_volts = 3.30 + random.uniform(-0.02, 0.02)

    return {
        "node_id": NODE_ID,
        "board": "RP2350-Sim",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_sec": tick,
        "sensors": {
            "temp_c": round(base_temp_c, 2),
            "temp_f": round(temp_f, 2),
            "humidity_pct": round(humidity, 1),
            "pressure_hpa": round(pressure_hpa, 2),
            "vsys_v": round(vsys_volts, 3),
        },
        "status": "WARN_THERMAL" if base_temp_c > 24.1 else "OK",
    }

def run_json_stream():
    tick = 0
    try:
        while True:
            payload = generate_reading(tick)
            print(json.dumps(payload), flush=True)
            tick += 1
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def run_live_monitor():
    os.system("")
    tick = 0
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            data = generate_reading(tick)
            s = data["sensors"]
            status_color = "\x1b[31m" if data["status"] != "OK" else "\x1b[32m"
            lines = [
                "\x1b[1;36m==================================================\x1b[0m",
                f"\x1b[1;37m  UNICORE PICO TELEMETRY SIM  |  {data['node_id']}\x1b[0m",
                "\x1b[1;36m==================================================\x1b[0m",
                f"  \x1b[33mBoard / Bus:\x1b[0m   {data['board']} (Virtual I2C 0x76)",
                f"  \x1b[33mTimestamp:\x1b[0m     {data['timestamp']} (+{tick}s)",
                f"  \x1b[33mStatus:\x1b[0m        {status_color}{data['status']}\x1b[0m",
                "\x1b[1;36m--------------------------------------------------\x1b[0m",
                f"  \x1b[33mTemperature:\x1b[0m   {s['temp_c']:.2f} °C  ({s['temp_f']:.2f} °F)",
                f"  \x1b[33mHumidity:\x1b[0m      {s['humidity_pct']:.1f} %",
                f"  \x1b[33mPressure:\x1b[0m      {s['pressure_hpa']:.2f} hPa",
                f"  \x1b[33mVSYS Rail:\x1b[0m     {s['vsys_v']:.3f} V",
                "\x1b[1;36m==================================================\x1b[0m",
                "  Tip: Run with --json for raw telemetry packets | Ctrl+C to exit",
            ]
            sys.stdout.write("\x1b[H" + "\n".join(lines) + "\n")
            sys.stdout.flush()
            tick += 1
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[0m\n")

if __name__ == "__main__":
    if "--json" in sys.argv:
        run_json_stream()
    else:
        run_live_monitor()
