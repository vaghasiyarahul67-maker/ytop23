#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import json

TORRC_PATH = "/home/ubantu/.tor_uk/torrc"
DATA_DIR = "/home/ubantu/.tor_uk/data"

def ensure_tor_uk():
    # Check if port 9052 is listening
    try:
        out = subprocess.check_output(["ss", "-tlpn"], text=True)
        if "127.0.0.1:9052" in out:
            return True
    except Exception:
        pass

    os.makedirs(DATA_DIR, exist_ok=True)
    os.chmod(DATA_DIR, 0o700)
    if not os.path.exists(TORRC_PATH):
        with open(TORRC_PATH, "w") as f:
            f.write("""SocksPort 127.0.0.1:9052
ControlPort 127.0.0.1:9053
DataDirectory /home/ubantu/.tor_uk/data
ExitNodes {gb}
StrictNodes 1
CookieAuthentication 0
MaxCircuitDirtiness 30
NewCircuitPeriod 30
""")

    subprocess.Popen(["tor", "-f", TORRC_PATH, "--RunAsDaemon", "1"])
    for _ in range(15):
        time.sleep(1)
        try:
            out = subprocess.check_output(["ss", "-tlpn"], text=True)
            if "127.0.0.1:9052" in out:
                return True
        except Exception:
            pass
    return False

def configure_proxies():
    # GNOME system proxy
    subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"], check=False)
    subprocess.run(["gsettings", "set", "org.gnome.system.proxy.socks", "host", "127.0.0.1"], check=False)
    subprocess.run(["gsettings", "set", "org.gnome.system.proxy.socks", "port", "9052"], check=False)

    # Firefox Snap profiles
    snap_ff = "/home/ubantu/snap/firefox/common/.mozilla/firefox"
    if os.path.exists(snap_ff):
        for entry in os.listdir(snap_ff):
            profile_dir = os.path.join(snap_ff, entry)
            if os.path.isdir(profile_dir):
                user_js = os.path.join(profile_dir, "user.js")
                with open(user_js, "w") as f:
                    f.write("""user_pref("network.proxy.type", 1);
user_pref("network.proxy.socks", "127.0.0.1");
user_pref("network.proxy.socks_port", 9052);
user_pref("network.proxy.socks_version", 5);
user_pref("network.proxy.socks_remote_dns", true);
""")

def get_current_uk_ip():
    cmd = ["curl", "-s", "--socks5-hostname", "127.0.0.1:9052", "--max-time", "10", "http://ip-api.com/json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            if data.get("status") == "success":
                return data
    except Exception:
        pass
    return None

def main():
    print("Connecting UK IP...")
    ensure_tor_uk()
    configure_proxies()
    ip_info = get_current_uk_ip()
    if ip_info:
        ip = ip_info.get("query")
        city = ip_info.get("city")
        country = ip_info.get("country")
        isp = ip_info.get("isp")
        print(f"SUCCESS: Connected to {country} ({city})")
        print(f"IP: {ip} | ISP: {isp}")

        # Send Desktop notification
        try:
            subprocess.run([
                "notify-send",
                "🇬🇧 UK IP Connected!",
                f"IP: {ip}\nLocation: {city}, {country}\nISP: {isp}",
                "-i", "network-vpn"
            ], check=False)
        except Exception:
            pass
    else:
        print("Connected to UK proxy port 9052.")

if __name__ == "__main__":
    main()
