import json
import math
import os
import random
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

NODE_ID = "unicore-rp2350-sim01"
START_TIME = time.time()

def generate_reading(tick=None):
    if tick is None:
        tick = int(time.time() - START_TIME)
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

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Unicore Pico Telemetry</title>
<style>
  body { background: #0d1117; color: #c9d1d9; font-family: monospace; display: flex; justify-content: center; padding: 40px 20px; margin: 0; }
  .panel { width: 100%; max-width: 640px; background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
  .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; padding-bottom: 16px; margin-bottom: 20px; }
  h1 { font-size: 18px; color: #58a6ff; margin: 0; }
  .badge { padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; background: #1f6feb33; color: #58a6ff; }
  .badge.ok { background: #23863633; color: #3fb950; }
  .badge.warn { background: #da363333; color: #f85149; }
  .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
  .card { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 16px; }
  .label { font-size: 12px; color: #8b949e; text-transform: uppercase; margin-bottom: 6px; }
  .val { font-size: 24px; font-weight: bold; color: #f0f6fc; }
  .sub { font-size: 12px; color: #8b949e; margin-top: 4px; }
  .footer { margin-top: 20px; font-size: 12px; color: #8b949e; display: flex; justify-content: space-between; }
</style>
</head>
<body>
<div class="panel">
  <div class="header">
    <h1>UNICORE // RP2350 TELEMETRY</h1>
    <span id="status" class="badge ok">CONNECTING...</span>
  </div>
  <div class="grid">
    <div class="card"><div class="label">Temperature</div><div id="temp" class="val">-- °C</div><div id="tempf" class="sub">-- °F</div></div>
    <div class="card"><div class="label">Humidity</div><div id="hum" class="val">-- %</div><div class="sub">Virtual BME280</div></div>
    <div class="card"><div class="label">Pressure</div><div id="pres" class="val">-- hPa</div><div class="sub">I2C Bus 0x76</div></div>
    <div class="card"><div class="label">VSYS Rail</div><div id="vsys" class="val">-- V</div><div class="sub">3.3V Regulated</div></div>
  </div>
  <div class="footer">
    <span id="node">Node: --</span>
    <span id="uptime">Uptime: 0s</span>
  </div>
</div>
<script>
async function poll() {
  try {
    const res = await fetch('/api/telemetry');
    const d = await res.json();
    document.getElementById('temp').textContent = d.sensors.temp_c.toFixed(2) + ' °C';
    document.getElementById('tempf').textContent = d.sensors.temp_f.toFixed(2) + ' °F';
    document.getElementById('hum').textContent = d.sensors.humidity_pct.toFixed(1) + ' %';
    document.getElementById('pres').textContent = d.sensors.pressure_hpa.toFixed(2) + ' hPa';
    document.getElementById('vsys').textContent = d.sensors.vsys_v.toFixed(3) + ' V';
    document.getElementById('node').textContent = 'Node: ' + d.node_id;
    document.getElementById('uptime').textContent = 'Uptime: ' + d.uptime_sec + 's';
    const st = document.getElementById('status');
    st.textContent = d.status;
    st.className = 'badge ' + (d.status === 'OK' ? 'ok' : 'warn');
  } catch (e) {}
}
setInterval(poll, 1000);
poll();
</script>
</body>
</html>"""

class TelemetryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/telemetry":
            payload = json.dumps(generate_reading()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_UI.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Keep terminal output clean

def run_web_ui(port=8050):
    url = f"http://127.0.0.1:{port}"
    server = HTTPServer(("127.0.0.1", port), TelemetryHandler)
    print(f"\x1b[1;36m[Unicore Web UI]\x1b[0m Serving live telemetry at \x1b[32m{url}\x1b[0m (Ctrl+C to stop)")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web UI...")
    finally:
        server.server_close()

def run_json_stream():
    tick = 0
    try:
        while True:
            print(json.dumps(generate_reading(tick)), flush=True)
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
                "  Modes: default (TUI) | --json | --web | Ctrl+C to exit",
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
    if "--web" in sys.argv:
        run_web_ui()
    elif "--json" in sys.argv:
        run_json_stream()
    else:
        run_live_monitor()
