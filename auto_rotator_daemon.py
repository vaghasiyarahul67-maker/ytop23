#!/usr/bin/env python3
import time
import subprocess
import json
import os

SERVERS_FILE = "/home/ubantu/Documents/vpnss/live_servers.json"
STATE_FILE = "/home/ubantu/Documents/vpnss/rotator_state.json"

def get_servers():
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE) as f:
                servers = json.load(f)
                if servers:
                    return servers
        except Exception:
            pass
    # Fallback default verified servers
    return [
        {"ip": "168.150.121.131", "port": 995, "country": "US", "city": "Davis, California"},
        {"ip": "50.39.199.184", "port": 1442, "country": "US", "city": "Hillsboro, Oregon"},
        {"ip": "130.215.124.186", "port": 995, "country": "US", "city": "North Smithfield, RI"},
        {"ip": "219.100.37.4", "port": 443, "country": "JP", "city": "Tokyo, Japan"},
        {"ip": "219.100.37.214", "port": 443, "country": "JP", "city": "Osaka, Japan"},
        {"ip": "217.138.212.62", "port": 443, "country": "RO", "city": "Bucharest, Romania"},
        {"ip": "211.197.16.167", "port": 995, "country": "KR", "city": "Seoul, Korea"}
    ]

def get_next_server():
    servers = get_servers()
    idx = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
                idx = (state.get("last_index", 0) + 1) % len(servers)
        except Exception:
            idx = 0
    
    server = servers[idx]
    with open(STATE_FILE, "w") as f:
        json.dump({"last_index": idx, "current": server}, f)
    return server

def set_next_server():
    s = get_next_server()
    remote = f"{s['ip']}:{s['port']}"
    cmd = ["nmcli", "connection", "modify", "USA-VPN", "+vpn.data", f"remote={remote}"]
    subprocess.run(cmd, capture_output=True, text=True)
    print(f"Set USA-VPN next server to {remote} ({s.get('city', s.get('country_long', 'USA'))})")

def is_vpn_active():
    try:
        out = subprocess.check_output(["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"], text=True)
        return "USA-VPN" in out.splitlines()
    except Exception:
        return False

def main():
    print("Auto-Rotator Daemon Started for USA-VPN.")
    was_active = is_vpn_active()
    while True:
        try:
            active = is_vpn_active()
            if was_active and not active:
                # User just turned VPN OFF! Prepare next IP for when they turn it back ON!
                print("VPN deactivated by user. Preparing next IP...")
                set_next_server()
            was_active = active
            time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    main()
