#!/usr/bin/env python3
"""
USA NATIVE VPN - Dynamic Controller & IP Rotator
1. Native NetworkManager VPN with official [VPN] top bar icon next to WiFi!
2. Every time you turn OFF and ON or click CHANGE IP, a BRAND NEW IP connects!
3. All laptop traffic (inside and outside, all browsers, websites) routes through the VPN!
4. Strictly manual control.
"""

import os
import sys
import time
import json
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox

SERVERS_FILE = "/home/ubantu/Documents/vpnss/live_servers.json"
STATE_FILE = "/home/ubantu/Documents/vpnss/rotator_state.json"
VPN_NAME = "USA-VPN"

def get_servers():
    if os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE) as f:
                servers = json.load(f)
                if servers:
                    return servers
        except Exception:
            pass
    return [
        {"ip": "168.150.121.131", "port": 995, "country": "US", "city": "Davis, California"},
        {"ip": "50.39.199.184", "port": 1442, "country": "US", "city": "Hillsboro, Oregon"},
        {"ip": "130.215.124.186", "port": 995, "country": "US", "city": "North Smithfield, RI"},
        {"ip": "219.100.37.4", "port": 443, "country": "JP", "city": "Tokyo, Japan"},
        {"ip": "219.100.37.214", "port": 443, "country": "JP", "city": "Osaka, Japan"},
        {"ip": "217.138.212.62", "port": 443, "country": "RO", "city": "Bucharest, Romania"},
        {"ip": "211.197.16.167", "port": 995, "country": "KR", "city": "Seoul, Korea"}
    ]

def set_next_server():
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

    remote = f"{server['ip']}:{server['port']}"
    cmd = ["nmcli", "connection", "modify", VPN_NAME, "+vpn.data", f"remote={remote}"]
    subprocess.run(cmd, capture_output=True, text=True)
    return server

def is_vpn_connected():
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
            text=True
        )
        return f"{VPN_NAME}:vpn" in out or f"{VPN_NAME}:tun" in out
    except Exception:
        return False

class USAVPNApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USA NATIVE VPN - Dynamic Controller")
        self.root.geometry("520x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        self.is_connected = False
        self.is_changing = False
        self.current_ip = None

        # Ensure proxy is none
        subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "none"], check=False)

        # Build UI
        self.setup_ui()

        # Check initial state
        self.check_initial_state()

        # Start background monitor for GNOME top-bar toggles
        self.start_system_monitor()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#1e293b", pady=15)
        header_frame.pack(fill="x")

        title_label = tk.Label(
            header_frame,
            text="🇺🇸 USA NATIVE VPN",
            font=("Helvetica", 18, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="ઓરિજિનલ [VPN] આઇકન સાથે આખા લેપટોપમાં Dynamic IPs",
            font=("Helvetica", 11),
            fg="#94a3b8",
            bg="#1e293b"
        )
        subtitle_label.pack(pady=(2, 0))

        # Main Card
        card = tk.Frame(self.root, bg="#1e293b", padx=20, pady=20, highlightthickness=1, highlightbackground="#334155")
        card.pack(fill="both", expand=True, padx=25, pady=20)

        # Status Badge
        self.status_frame = tk.Frame(card, bg="#1e293b")
        self.status_frame.pack(fill="x", pady=(0, 15))

        self.status_dot = tk.Label(self.status_frame, text="●", font=("Helvetica", 18), fg="#ef4444", bg="#1e293b")
        self.status_dot.pack(side="left", padx=(0, 8))

        self.status_text = tk.Label(
            self.status_frame,
            text="🔴 VPN બંધ છે (સામાન્ય નેટ ચાલુ છે)",
            font=("Helvetica", 13, "bold"),
            fg="#cbd5e1",
            bg="#1e293b"
        )
        self.status_text.pack(side="left")

        # Separator
        sep1 = tk.Frame(card, bg="#334155", height=1)
        sep1.pack(fill="x", pady=10)

        # IP Display Box
        ip_box = tk.Frame(card, bg="#0f172a", padx=15, pady=12, highlightthickness=1, highlightbackground="#334155")
        ip_box.pack(fill="x", pady=5)

        tk.Label(ip_box, text="CURRENT PUBLIC IP:", font=("Helvetica", 10, "bold"), fg="#64748b", bg="#0f172a").pack(anchor="w")

        ip_inner = tk.Frame(ip_box, bg="#0f172a")
        ip_inner.pack(fill="x", pady=(2, 0))

        self.ip_label = tk.Label(
            ip_inner,
            text="VPN બંધ છે - Connect દબાવો",
            font=("Monospace", 16, "bold"),
            fg="#94a3b8",
            bg="#0f172a"
        )
        self.ip_label.pack(side="left")

        self.copy_btn = tk.Button(
            ip_inner,
            text="📋 Copy",
            font=("Helvetica", 9),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            state="disabled",
            command=self.copy_ip
        )
        self.copy_btn.pack(side="right")

        # Location details
        loc_box = tk.Frame(card, bg="#1e293b", pady=8)
        loc_box.pack(fill="x")

        # City Row
        row1 = tk.Frame(loc_box, bg="#1e293b")
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="City / State:", font=("Helvetica", 11), fg="#94a3b8", bg="#1e293b", width=14, anchor="w").pack(side="left")
        self.city_label = tk.Label(row1, text="-", font=("Helvetica", 11, "bold"), fg="#f8fafc", bg="#1e293b")
        self.city_label.pack(side="left")

        # Company / ISP Row
        row2 = tk.Frame(loc_box, bg="#1e293b")
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Company / ISP:", font=("Helvetica", 11), fg="#94a3b8", bg="#1e293b", width=14, anchor="w").pack(side="left")
        self.isp_label = tk.Label(row2, text="-", font=("Helvetica", 11, "bold"), fg="#38bdf8", bg="#1e293b")
        self.isp_label.pack(side="left")

        # Country Row
        row3 = tk.Frame(loc_box, bg="#1e293b")
        row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Country:", font=("Helvetica", 11), fg="#94a3b8", bg="#1e293b", width=14, anchor="w").pack(side="left")
        self.country_label = tk.Label(row3, text="-", font=("Helvetica", 11, "bold"), fg="#22c55e", bg="#1e293b")
        self.country_label.pack(side="left")

        # Top Bar Indicator
        row4 = tk.Frame(loc_box, bg="#1e293b")
        row4.pack(fill="x", pady=2)
        tk.Label(row4, text="Top Bar [VPN]:", font=("Helvetica", 11), fg="#94a3b8", bg="#1e293b", width=14, anchor="w").pack(side="left")
        self.badge_label = tk.Label(row4, text="OFF", font=("Helvetica", 11, "bold"), fg="#ef4444", bg="#1e293b")
        self.badge_label.pack(side="left")

        # Separator
        sep2 = tk.Frame(card, bg="#334155", height=1)
        sep2.pack(fill="x", pady=12)

        # MAIN TOGGLE BUTTON (Connect / Disconnect)
        self.toggle_btn = tk.Button(
            card,
            text="🟢  CONNECT VPN  (આખા લેપટોપમાં ચાલુ કરો)",
            font=("Helvetica", 12, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief="flat",
            pady=12,
            cursor="hand2",
            command=self.toggle_connection
        )
        self.toggle_btn.pack(fill="x", pady=6)

        # CHANGE IP BUTTON
        self.rotate_btn = tk.Button(
            card,
            text="🔄  CHANGE IP  (નવો IP & Server બદલો)",
            font=("Helvetica", 12, "bold"),
            bg="#334155",
            fg="#94a3b8",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            pady=10,
            cursor="hand2",
            state="disabled",
            command=self.on_click_change_ip
        )
        self.rotate_btn.pack(fill="x", pady=6)

        # Bottom Hint
        hint_label = tk.Label(
            self.root,
            text="💡 VPN On/Off કરતાં કે 'CHANGE' દબાવતાં જ દર વખતે નવો IP અને સિટી બદલાશે.",
            font=("Helvetica", 9),
            fg="#64748b",
            bg="#0f172a"
        )
        hint_label.pack(side="bottom", pady=12)

    def copy_ip(self):
        ip = self.ip_label.cget("text")
        if ip and "VPN" not in ip and "પકડી" not in ip:
            self.root.clipboard_clear()
            self.root.clipboard_append(ip)
            messagebox.showinfo("Copied", f"IP {ip} copied to clipboard!")

    def check_initial_state(self):
        connected = is_vpn_connected()
        self.update_status_ui(connected)
        if connected:
            self.fetch_ip_thread()

    def update_status_ui(self, connected):
        self.is_connected = connected
        if connected:
            self.status_dot.config(fg="#22c55e")
            self.status_text.config(text="🟢 VPN ચાલુ છે (નવો IP સક્રિય)", fg="#22c55e")
            self.badge_label.config(text="ON [VPN]", fg="#22c55e")
            self.toggle_btn.config(
                text="🔴  DISCONNECT VPN  (VPN બંધ કરો)",
                bg="#dc2626",
                activebackground="#b91c1c",
                state="normal"
            )
            self.rotate_btn.config(
                text="🔄  CHANGE IP  (નવો IP & Server બદલો)",
                bg="#2563eb",
                fg="#ffffff",
                state="normal"
            )
            self.copy_btn.config(state="normal")
        else:
            self.status_dot.config(fg="#ef4444")
            self.status_text.config(text="🔴 VPN બંધ છે (સામાન્ય નેટ ચાલુ છે)", fg="#cbd5e1")
            self.badge_label.config(text="OFF", fg="#ef4444")
            self.toggle_btn.config(
                text="🟢  CONNECT VPN  (આખા લેપટોપમાં ચાલુ કરો)",
                bg="#16a34a",
                activebackground="#15803d",
                state="normal"
            )
            self.rotate_btn.config(
                text="🔄  CHANGE IP  (નવો IP & Server બદલો)",
                bg="#334155",
                fg="#94a3b8",
                state="disabled"
            )
            self.ip_label.config(text="VPN બંધ છે - Connect દબાવો", fg="#94a3b8")
            self.city_label.config(text="-")
            self.isp_label.config(text="-")
            self.country_label.config(text="-")
            self.copy_btn.config(state="disabled")

    def toggle_connection(self):
        if self.is_connected:
            self.toggle_btn.config(text="⏳  ડિસ્કનેક્ટ થઈ રહ્યું છે...", state="disabled")
            def worker():
                subprocess.run(["nmcli", "connection", "down", VPN_NAME], capture_output=True, text=True)
                set_next_server()
                def done():
                    self.update_status_ui(False)
                    messagebox.showinfo("Disconnected", "VPN બંધ થઈ ગયું છે.\nસામાન્ય નેટ ચાલુ છે.")
                self.root.after(0, done)
            threading.Thread(target=worker, daemon=True).start()
        else:
            self.toggle_btn.config(text="⏳  કનેક્ટ થઈ રહ્યું છે...", state="disabled")
            self.ip_label.config(text="VPN સર્વર સાથે જોડાઈ રહ્યું છે...", fg="#fbbf24")

            def worker():
                subprocess.run(["nmcli", "connection", "up", VPN_NAME], capture_output=True, text=True)
                time.sleep(2)
                info = self.fetch_fresh_ip_data()
                def done():
                    connected = is_vpn_connected()
                    self.update_status_ui(connected)
                    if info:
                        self.display_info(info)
                    messagebox.showinfo("Connected", "આખા લેપટોપમાં VPN ચાલુ થઈ ગયું છે!\nઉપર [VPN] આવી ગયું છે અને નવો IP સેટ થયો છે.")
                self.root.after(0, done)
            threading.Thread(target=worker, daemon=True).start()

    def fetch_fresh_ip_data(self):
        cmd = ["curl", "-s", "--max-time", "6", "http://ip-api.com/json"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=7)
            if res.returncode == 0 and res.stdout:
                d = json.loads(res.stdout)
                if d.get("status") == "success":
                    self.current_ip = d.get("query")
                    return d
        except Exception:
            pass
        return None

    def display_info(self, info):
        ip = info.get("query", "-")
        city = info.get("city", "-")
        region = info.get("regionName", "")
        isp = info.get("isp", "-")
        country = info.get("country", "-")
        self.ip_label.config(text=ip, fg="#38bdf8")
        self.city_label.config(text=f"{city}, {region}" if region else city)
        self.isp_label.config(text=isp[:35])
        self.country_label.config(text=f"{country} 🌐")

    def fetch_ip_thread(self):
        def worker():
            info = self.fetch_fresh_ip_data()
            if info:
                self.root.after(0, lambda: self.display_info(info))
        threading.Thread(target=worker, daemon=True).start()

    def on_click_change_ip(self):
        if self.is_changing:
            return
        self.is_changing = True
        self.rotate_btn.config(text="⏳  નવો IP પકડી રહ્યું છે...", state="disabled", bg="#475569")
        self.ip_label.config(text="બદલાઈ રહ્યો છે...", fg="#fbbf24")

        def worker():
            subprocess.run(["nmcli", "connection", "down", VPN_NAME], capture_output=True, text=True)
            new_s = set_next_server()
            time.sleep(1)
            subprocess.run(["nmcli", "connection", "up", VPN_NAME], capture_output=True, text=True)
            time.sleep(2)
            info = self.fetch_fresh_ip_data()

            def done():
                self.is_changing = False
                connected = is_vpn_connected()
                self.update_status_ui(connected)
                if info:
                    self.display_info(info)
                    messagebox.showinfo("IP Changed", f"નવો IP સેટ થઈ ગયો છે!\n\nIP: {info.get('query')}\nશહેર: {info.get('city')}, {info.get('regionName')}\nદેશ: {info.get('country')}\nકંપની: {info.get('isp')}")
                self.rotate_btn.config(text="🔄  CHANGE IP  (નવો IP & Server બદલો)", state="normal", bg="#2563eb")

            self.root.after(0, done)
        threading.Thread(target=worker, daemon=True).start()

    def start_system_monitor(self):
        def loop():
            was_active = is_vpn_connected()
            while True:
                time.sleep(1.5)
                active = is_vpn_connected()
                if active != was_active:
                    was_active = active
                    # Auto update UI when toggled from GNOME top-bar
                    self.root.after(0, lambda a=active: self.update_status_ui(a))
                    if active:
                        self.fetch_ip_thread()
                    else:
                        # Prepare next server for next activation
                        set_next_server()
        threading.Thread(target=loop, daemon=True).start()

    def on_closing(self):
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = USAVPNApp(root)
    root.mainloop()
