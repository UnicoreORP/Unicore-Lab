import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor

COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    8000: "HTTP-Alt",
    8080: "HTTP-Proxy",
}

def grab_banner(sock, port):
    try:
        if port in (80, 8000, 8080):
            sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
        data = sock.recv(256)
        first_line = data.decode("utf-8", errors="ignore").splitlines()
        return first_line.strip() if first_line else ""
    except Exception:
        return ""

def scan_port(target_ip, port, timeout=0.6):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        if s.connect_ex((target_ip, port)) == 0:
            service = COMMON_PORTS.get(port, "Unknown")
            banner = grab_banner(s, port)
            return (port, service, banner)
    return None

def run_recon(target="127.0.0.1", ports=None):
    if ports is None:
        ports = sorted(COMMON_PORTS.keys())

    try:
        target_ip = socket.gethostbyname(target)
    except socket.gaierror:
        print(f"Error: Could not resolve host '{target}'")
        sys.exit(1)

    print("\x1b[1;36m==================================================\x1b[0m")
    print(f"\x1b[1;37m  UNICORE PORT RECON  |  Target: {target} ({target_ip})\x1b[0m")
    print("\x1b[1;36m==================================================\x1b[0m")

    start = time.time()
    open_ports = []

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(scan_port, target_ip, p) for p in ports]
        for f in futures:
            res = f.result()
            if res:
                open_ports.append(res)

    open_ports.sort(key=lambda x: x)
    if not open_ports:
        print("  \x1b[33mNo open ports found in scanned range.\x1b[0m")
    else:
        for port, service, banner in open_ports:
            banner_txt = f" -> \x1b[36m{banner}\x1b[0m" if banner else ""
            print(f"  \x1b[32m[OPEN]\x1b[0m Port {port:<5} ({service}){banner_txt}")

    elapsed = time.time() - start
    print("\x1b[1;36m==================================================\x1b[0m")
    print(f"  Scanned {len(ports)} ports in {elapsed:.2f}s | {len(open_ports)} open")

if __name__ == "__main__":
    host = sys.argv if len(sys.argv) > 1 else "127.0.0.1"
    run_recon(host)
