# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.0.0] — 2026-04-19

### Added
- **Virtual Machines panel** — live VM status cards with Quick Start, Passthrough, and Disk shortcuts
- **Autostart banner** — countdown overlay on the VM list that auto-fires the configured default VM
- **Passthrough panel** — per-VM GPU / PCI device checklist, USB auto-scan or manual selection, companion audio toggle, extra PCI address field
- **Disk Manager panel** — attach disks from `/dev/disk/by-id`, detach, move SCSI entries between VMs
- **Autostart panel** — VM selector, 0–60 s countdown slider, live preview text, persistent config
- **Launch dialog** — streaming log of config changes and `qm start` output in a modal window; non-blocking via `QThread`
- **VM config backups** — timestamped `.backup.*` snapshot before every config mutation
- `backend.py` — all Proxmox host operations isolated, no PyQt5 dependency
- `workers.py` — `LaunchWorker` QThread for quick, custom, and no-passthrough launch modes
- Catppuccin Mocha dark theme applied via Qt stylesheet (`styles.py`)

[Unreleased]: https://github.com/mystique4u/prox-loader/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/mystique4u/prox-loader/releases/tag/v1.0.0
