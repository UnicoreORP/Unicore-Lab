import os
import platform
import shutil
import socket
import subprocess
import sys
import time

def get_tailscale_ip():
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], stderr=subprocess.DEVNULL, text=True).strip()
        return out if out else "Not connected"
    except Exception:
        return "Not installed / offline"

def get_ram_usage():
    # Reads /proc/meminfo directly on Linux/Termux with zero external dependencies
    if os.path.exists("/proc/meminfo"):
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])
        total_gb = mem.get("MemTotal", 0) / (1024 ** 2)
        avail_gb = mem.get("MemAvailable", 0) / (1024 ** 2)
        used_gb = total_gb - avail_gb
        pct = (used_gb / total_gb * 100) if total_gb > 0 else 0
        return f"{used_gb:.2f} / {total_gb:.2f} GB ({pct:.1f}%)"
    return "N/A (Non-Linux)"

def get_cpu_load():
    try:
        load1, load5, load15 = os.getloadavg()
        cores = os.cpu_count() or 1
        return f"{load1:.2f} (1m) | {load5:.2f} (5m) [{cores} cores]"
    except OSError:
        return "N/A"

def get_uptime():
    if os.path.exists("/proc/uptime"):
        with open("/proc/uptime") as f:
            seconds = float(f.readline().split()[0])
        hrs, rem = divmod(int(seconds), 3600)
        mins, secs = divmod(rem, 60)
        return f"{hrs}h {mins}m {secs}s"
    return "N/A"

def render_dashboard():
    host = socket.gethostname()
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    disk = shutil.disk_usage("/")
    disk_used = disk.used / (1024 ** 3)
    disk_total = disk.total / (1024 ** 3)

    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            lines = [
                "\x1b[1;36m==================================================\x1b[0m",
                f"\x1b[1;37m  UNICORE NODE PULSE  |  {ts}\x1b[0m",
                "\x1b[1;36m==================================================\x1b[0m",
                f"  \x1b[33mHostname:\x1b[0m      {host}",
                f"  \x1b[33mOS / Arch:\x1b[0m     {os_info}",
                f"  \x1b[33mUptime:\x1b[0m        {get_uptime()}",
                f"  \x1b[33mCPU Load:\x1b[0m      {get_cpu_load()}",
                f"  \x1b[33mMemory (RAM):\x1b[0m  {get_ram_usage()}",
                f"  \x1b[33mDisk (/):\x1b[0m      {disk_used:.1f} / {disk_total:.1f} GB",
                f"  \x1b[33mTailscale IP:\x1b[0m  \x1b[32m{get_tailscale_ip()}\x1b[0m",
                "\x1b[1;36m==================================================\x1b[0m",
                "  Press Ctrl+C to exit",
            ]
            sys.stdout.write("\x1b[H" + "\n".join(lines) + "\n")
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[0m\n")

if __name__ == "__main__":
    os.system("")
    render_dashboard()
