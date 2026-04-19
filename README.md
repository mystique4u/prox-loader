# Prox Loader

A graphical VM boot manager for [Proxmox VE](https://www.proxmox.com/). Select which virtual machine to start, configure GPU / USB / PCI passthrough, manage SCSI disks, and set an autostart countdown — all from a single modern dark-themed window.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![PyQt5](https://img.shields.io/badge/UI-PyQt5-green)
![License](https://img.shields.io/badge/license-MIT-purple)

---

## Features

- **VM list** — live status cards for every VM on the host (`running` / `stopped`)
- **⚡ Quick Start** — one click applies GPU + all-USB passthrough and starts the VM
- **Passthrough panel** — granular GPU / PCI / USB device selection with checkboxes; auto-scan or manual; companion audio toggle
- **Disk Manager** — attach disks from `/dev/disk/by-id`, detach, or move SCSI entries between VMs
- **Autostart** — choose a default VM and countdown delay (0–60 s); live preview; persisted across reboots
- **Non-blocking UI** — all Proxmox operations run in a background thread with a real-time log stream
- **Keyboard-first** — full Tab / arrow-key navigation; no mouse required
- **Frameless fullscreen** — designed for bare kiosk-style console use; Ctrl+Q or the sidebar Quit button to exit
- **Dark theme** — Catppuccin Mocha throughout

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.9+ |
| PyQt5 | 5.x |
| Proxmox VE | 7 or 8 |
| `qm` in `$PATH` | (standard on PVE host) |
| `lspci` / `lsusb` | (standard on Debian/PVE) |

Install Python dependencies on the Proxmox host:

```bash
apt install python3-pyqt5
# or via pip
pip3 install PyQt5
```

---

## Running

Prox Loader must run **as root** on the Proxmox host (it reads and writes `/etc/pve/qemu-server/*.conf`).

### Install dependencies

```bash
apt install --no-install-recommends xorg openbox picom python3-pyqt5
```

> **picom is required.** Without a compositor, PyQt5 windows will not repaint after being moved or overlapped (shows as a black or grey rectangle). Use `--backend xrender` — the `glx` backend may fail on headless/virtual GPUs.

---

### Startup flow (systemd service, recommended)

Prox Loader is designed to start **manually from the Proxmox console** — not automatically at boot. The systemd service manages the full X session lifecycle.

**How it works:**
1. Proxmox boots → getty shows the login prompt on tty1
2. Root logs in and runs `systemctl start prox-loader` (or uses the `/usr/local/bin/prox-loader` command)
3. The service stops getty, starts `xinit openbox-session` on tty1
4. Openbox autostart launches picom + Prox Loader
5. Pressing `Q`, `Ctrl+Q`, or the **✕ Quit** button kills Openbox → xinit exits → service stops → getty is restored

**Install the service (one-time on the Proxmox host):**

```bash
cp prox-loader.service /etc/systemd/system/
systemctl daemon-reload
```

**`~/.config/openbox/autostart`:**

```bash
picom --backend xrender &
sleep 1
cd /opt/prox-loader && python3 -m prox_loader > /tmp/prox-loader.log 2>&1
```

**Start / stop / restart:**

```bash
# Start (from console or SSH)
systemctl start prox-loader

# Stop
systemctl stop prox-loader

# Restart (use stop+start, NOT restart — avoids systemd restart race)
systemctl stop prox-loader; sleep 1; systemctl start prox-loader

# Check status / logs
systemctl status prox-loader
journalctl -u prox-loader -f
cat /tmp/prox-loader.log
```

> The service is **not enabled at boot** — Proxmox always shows the login prompt first, protecting the host from unauthenticated access.

---

### Keyboard shortcuts

| Key | Action |
|---|---|
| `Tab` | Move focus to next element |
| `Shift+Tab` | Move focus to previous element |
| `Arrow keys` | Navigate within lists, adjust sliders and spin boxes |
| `Space` | Toggle checkbox / activate focused button |
| `Enter` | Activate focused button |
| `Q` | Quit (when focus is not in a text field) |
| `Ctrl+Q` | Quit (always) |

> The window is **frameless and fullscreen** — no title bar, resize handle, or OS close button. Use the **✕ Quit** button in the sidebar or press `Ctrl+Q`.

---

### Headless / CI testing with Xvfb

```bash
apt install -y xvfb
Xvfb :99 -screen 0 1280x800x24 &
DISPLAY=:99 python3 -m prox_loader
```

Since `qm` is not present outside a Proxmox host, the VM list will be empty — but all panels, navigation, dialogs, and styling can be fully exercised.

---

### X11 forwarding

```bash
ssh -X root@<proxmox-ip> "cd /opt/prox-loader && python3 -m prox_loader"
```

## Project layout

```
prox_loader/
├── __main__.py          # Entry point — activates window, sets initial keyboard focus
├── backend.py           # All qm / lspci / lsusb / config-file operations (no PyQt5)
├── config.py            # Autostart config I/O (/etc/pve/vm-autostart.conf)
├── dialogs.py           # Launch log dialog + VM picker modal
├── main_window.py       # Sidebar + QStackedWidget panel shell; focus routing on panel switch
├── styles.py            # Qt stylesheet (Catppuccin Mocha)
├── workers.py           # QThread worker for non-blocking VM launch
└── panels/
    ├── vm_list.py       # VM cards + autostart countdown banner
    ├── passthrough.py   # PCI / GPU / USB passthrough configuration
    ├── disks.py         # SCSI disk attach / detach / move
    └── autostart.py     # Default VM + delay settings
```

Deployment files (repo root):

```
prox-loader.service      # systemd unit for SSH-triggered restart
prox-loader-start.sh     # standalone launcher script (installed to /usr/local/bin/prox-loader)
```

---

## Configuration files

| File | Purpose |
|---|---|
| `/etc/pve/qemu-server/<vmid>.conf` | Proxmox VM config (modified for passthrough) |
| `/etc/pve/vm-autostart.conf` | Prox Loader autostart settings |

A timestamped backup (`*.backup.YYYYMMDD_HHMMSS`) is created automatically before any config change.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT — see [LICENSE](LICENSE).
