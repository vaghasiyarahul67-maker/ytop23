# USA VPN Dynamic Controller & IP Rotator

High-performance native Linux VPN management application with automatic IP rotation, live connection status tracking, and GNOME/NetworkManager desktop integration.

## Features

- **Dynamic IP Rotation**: Automatically cycles through verified live VPN servers on connect/disconnect toggles.
- **Background Daemon**: Monitors NetworkManager VPN status (`auto_rotator_daemon.py`) and seamlessly updates configurations.
- **Intuitive GUI**: Built with Python Tkinter (`usa_vpn_app.py`) for quick connect/disconnect and live IP/country status.
- **Failover & Testing**: Built-in verification (`test_50_ips.py`) and server configuration store (`live_servers.json`).
- **OpenVPN Native Support**: Integrated directly with Ubuntu / GNOME NetworkManager via native `nmcli`.

## Project Structure

- `usa_vpn_app.py`: Main desktop GUI application.
- `auto_rotator_daemon.py`: Background daemon for automatic server switching and IP rotation.
- `live_servers.json`: Active list of validated VPN endpoints and configurations.
- `rotator_state.json`: State file tracking the active server rotation index.
- `test_50_ips.py`: Diagnostic and latency validation tool for server pool.
- `USA_California.ovpn` & `USA_live.ovpn`: Active OpenVPN client configuration files.
- `icon.png`: Application launcher asset.

## Usage

### Run GUI
```bash
python3 usa_vpn_app.py
```

### Run Auto-Rotator Daemon
```bash
python3 auto_rotator_daemon.py
```
