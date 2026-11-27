import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

NODES = {}
LOCK = threading.Lock()

def get_tailscale_ip():
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], stderr=subprocess.DEVNULL, text=True).strip()
        return out if out else "None"
    except Exception:
        return "None"

def get_soc_temp():
    # Reads real Raspberry Pi 4 / Linux thermal zone temperature in Celsius
    path = "/sys/class/thermal/thermal_zone0/temp"
    if os.path.exists(path):
        try:
            with open(path) as f:
                return round(int(f.read().strip()) / 1000.0, 1)
        except Exception:
            pass
    return None

def get_ram_pct():
    if os.path.exists("/proc/meminfo"):
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])
        tot = mem.get("MemTotal", 0)
        avail = mem.get("MemAvailable", 0)
        if tot > 0:
            return round((tot - avail) / tot * 100.0, 1)
    return 0.0

def collect_local_metrics(role="Node"):
    try:
        load1 = round(os.getloadavg()[0], 2)
    except OSError:
        load1 = 0.0

    return {
        "hostname": socket.gethostname(),
        "arch": platform.machine(),
        "role": role,
        "tailscale_ip": get_tailscale_ip(),
        "cpu_load_1m": load1,
        "cores": os.cpu_count() or 1,
        "ram_pct": get_ram_pct(),
        "soc_temp_c": get_soc_temp(),
        "last_seen": time.time(),
    }

HUB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Unicore Pi Fleet Monitor</title>
<style>
  body { background: #0d1117; color: #c9d1d9; font-family: monospace; margin: 0; padding: 32px; }
  .wrap { max-width: 960px; margin: 0 auto; }
  .top { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; padding-bottom: 16px; margin-bottom: 24px; }
  h1 { font-size: 20px; color: #58a6ff; margin: 0; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px; }
  .card.offline { opacity: 0.55; border-color: #da3633; }
  .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .name { font-size: 16px; font-weight: bold; color: #f0f6fc; }
  .pill { font-size: 11px; padding: 3px 8px; border-radius: 10px; font-weight: bold; }
  .online { background: #23863633; color: #3fb950; }
  .stale { background: #da363333; color: #f85149; }
  .stat { font-size: 13px; margin: 6px 0; color: #8b949e; }
  .stat span { color: #e6edf3; font-weight: bold; }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <h1>UNICORE // DISTRIBUTED NODE FLEET</h1>
    <div id="count">0 Nodes Active</div>
  </div>
  <div id="grid" class="grid"></div>
</div>
<script>
async function refresh() {
  try {
    const res = await fetch('/api/nodes');
    const data = await res.json();
    const grid = document.getElementById('grid');
    const entries = Object.values(data.nodes);
    let active = 0;
    grid.innerHTML = entries.map(n => {
      const alive = n.age_sec <= 8;
      if (alive) active++;
      const temp = n.soc_temp_c !== null ? n.soc_temp_c + ' °C' : 'N/A';
      return `
        <div class="card ${alive ? '' : 'offline'}">
          <div class="row">
            <div class="name">${n.hostname}</div>
            <div class="pill ${alive ? 'online' : 'stale'}">${alive ? 'ONLINE' : 'OFFLINE (' + n.age_sec + 's)'}</div>
          </div>
          <div class="stat">Role: <span>${n.role}</span> (${n.arch})</div>
          <div class="stat">Tailscale IP: <span>${n.tailscale_ip}</span></div>
          <div class="stat">CPU Load (1m): <span>${n.cpu_load_1m} / ${n.cores} cores</span></div>
          <div class="stat">RAM Usage: <span>${n.ram_pct}%</span></div>
          <div class="stat">SoC Temp: <span>${temp}</span></div>
        </div>
      `;
    }).join('');
    document.getElementById('count').textContent = active + ' / ' + entries.length + ' Nodes Online';
  } catch (e) {}
}
setInterval(refresh, 1500);
refresh();
</script>
</body>
</html>"""

class FleetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/nodes":
            now = time.time()
            with LOCK:
                snapshot = {}
                for k, v in NODES.items():
                    item = dict(v)
                    item["age_sec"] = int(now - v["last_seen"])
                    snapshot[k] = item
            payload = json.dumps({"nodes": snapshot}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HUB_HTML.encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/heartbeat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            body["last_seen"] = time.time()
            with LOCK:
                NODES[body["hostname"]] = body
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

    def log_message(self, format, *args):
        pass

def run_hub(port=8060, local_role="Hub-Control"):
    server = HTTPServer(("0.0.0.0", port), FleetHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"\x1b[1;36m[Unicore Fleet Hub]\x1b[0m Listening on 0.0.0.0:{port} | Dashboard: \x1b[32m{url}\x1b[0m")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    def self_heartbeat():
        while True:
            with LOCK:
                NODES[socket.gethostname()] = collect_local_metrics(local_role)
            time.sleep(2)

    threading.Thread(target=self_heartbeat, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Fleet Hub...")
    finally:
        server.server_close()

def run_agent(hub_url, role="Pi4-Worker"):
    endpoint = hub_url.rstrip("/") + "/api/heartbeat"
    print(f"\x1b[1;36m[Unicore Node Agent]\x1b[0m Reporting as '{role}' -> {endpoint} (Ctrl+C to stop)")
    try:
        while True:
            payload = json.dumps(collect_local_metrics(role)).encode("utf-8")
            req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=3)
            except Exception as e:
                print(f"Heartbeat warning: {e}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nAgent stopped.")

if __name__ == "__main__":
    if "--agent" in sys.argv:
        idx = sys.argv.index("--agent")
        target_hub = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "http://127.0.0.1:8060"
        node_role = sys.argv[idx + 2] if len(sys.argv) > idx + 2 else "Pi4-SNN-Node"
        run_agent(target_hub, node_role)
    else:
        run_hub()
