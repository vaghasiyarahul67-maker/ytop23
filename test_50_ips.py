import socket
import time
import subprocess
import json
import sys

TOR_CONTROL_PORT = 9053
TOR_SOCKS_PORT = 9052

def send_newnym():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(("127.0.0.1", TOR_CONTROL_PORT))
            s.sendall(b'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT\r\n')
            s.recv(1024)
    except Exception as e:
        pass

def fetch_ip(session_id):
    username = f"test_{session_id}"
    cmd = [
        "curl", "-s",
        "--socks5-hostname", f"{username}:pwd@127.0.0.1:{TOR_SOCKS_PORT}",
        "--max-time", "8",
        "http://ip-api.com/json"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=9)
        if res.returncode == 0 and res.stdout:
            d = json.loads(res.stdout)
            if d.get("status") == "success":
                return d
    except Exception as e:
        pass
    return None

def main():
    target_count = 50
    results = []
    seen_ips = set()
    attempts = 0
    max_attempts = 120

    print(f"Starting test to collect {target_count} unique USA IPs...\n")
    print(f"{'#':<3} | {'IP ADDRESS':<16} | {'CITY':<16} | {'REGION/STATE':<14} | {'COMPANY / ISP':<30} | {'COUNTRY'}")
    print("-" * 100)

    while len(results) < target_count and attempts < max_attempts:
        attempts += 1
        send_newnym()
        session_id = f"{int(time.time() * 1000)}_{attempts}"
        data = fetch_ip(session_id)

        if not data:
            time.sleep(0.5)
            continue

        ip = data.get("query")
        country = data.get("country")

        if not ip or ip in seen_ips:
            time.sleep(0.3)
            continue

        seen_ips.add(ip)
        city = data.get("city", "Unknown")[:15]
        region = data.get("regionName", "Unknown")[:13]
        isp = data.get("isp", "Unknown")[:28]

        results.append(data)
        idx = len(results)
        print(f"{idx:<3} | {ip:<16} | {city:<16} | {region:<14} | {isp:<30} | {country} 🇺🇸")
        sys.stdout.flush()

        time.sleep(0.4)

    print("-" * 100)
    print(f"\nTotal unique USA IPs collected: {len(results)}")
    non_us = [r for r in results if r.get("countryCode") != "US"]
    print(f"Non-USA IPs: {len(non_us)} (Expected 0)")
    
    unique_cities = len(set(r.get("city") for r in results))
    unique_isps = len(set(r.get("isp") for r in results))
    print(f"Unique Cities found: {unique_cities}")
    print(f"Unique Companies / ISPs found: {unique_isps}")

if __name__ == "__main__":
    main()
