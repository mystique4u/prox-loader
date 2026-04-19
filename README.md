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

```bash
sudo python3 -m prox_loader
```

For a desktop shortcut or autostart kiosk session, see [docs/kiosk.md](docs/kiosk.md) *(coming soon)*.

> **Tip:** If you want a graphical session on the Proxmox host itself, install a minimal X environment:  
> `apt install --no-install-recommends xorg openbox lightdm`

---

## Project layout

```
prox_loader/
├── __main__.py          # Entry point
├── backend.py           # All qm / lspci / lsusb / config-file operations
├── config.py            # Autostart config I/O (/etc/pve/vm-autostart.conf)
├── dialogs.py           # Launch log dialog + VM picker modal
├── main_window.py       # Sidebar + stacked panel shell
├── styles.py            # Qt stylesheet (Catppuccin Mocha)
├── workers.py           # QThread worker for non-blocking VM launch
└── panels/
    ├── vm_list.py       # VM cards + autostart countdown banner
    ├── passthrough.py   # PCI / GPU / USB passthrough configuration
    ├── disks.py         # SCSI disk attach / detach / move
    └── autostart.py     # Default VM + delay settings
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
