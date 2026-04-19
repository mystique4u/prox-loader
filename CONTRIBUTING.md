# Contributing to Prox Loader

Thank you for considering a contribution. This is a small focused tool — please keep changes minimal and purposeful.

---

## Getting started

1. **Fork** the repository and clone your fork.
2. Create a branch with a descriptive name:
   ```bash
   git checkout -b feat/your-feature
   # or
   git checkout -b fix/your-bugfix
   ```
3. Compile-check before committing:
   ```bash
   python3 -m py_compile prox_loader/**/*.py prox_loader/*.py
   python3 -c "from prox_loader.main_window import MainWindow; print('OK')"
   ```
4. Deploy to the Proxmox host for testing:
   ```bash
   rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
     /path/to/prox-loader/ root@<proxmox-ip>:/opt/prox-loader/
   # Then restart (stop+start, NOT restart):
   ssh root@<proxmox-ip> "systemctl stop prox-loader; sleep 1; systemctl start prox-loader"
   # Check app log:
   ssh root@<proxmox-ip> "cat /tmp/prox-loader.log"
   ```
5. Open a Pull Request against `main`.

---

## Code style

- **Python 3.9+** — no walrus operator abuse, keep it readable.
- Follow existing naming: `snake_case` for functions/variables, `PascalCase` for classes.
- Keep UI logic in `panels/`, Proxmox host operations in `backend.py`, threading in `workers.py`.
- **Do not import PyQt5 in `backend.py`** — it must stay framework-agnostic for unit testing without a display.

---

## Architecture notes

### Keyboard navigation

All interactive widgets must have explicit focus policies — PyQt5 does not assign them automatically:

| Widget type | Required policy |
|---|---|
| `QPushButton`, `QCheckBox` | `Qt.TabFocus` |
| `QComboBox`, `QListWidget`, `QSlider`, `QSpinBox`, `QLineEdit` | `Qt.StrongFocus` |
| `QScrollArea`, container `QWidget`/`QFrame` | `Qt.NoFocus` |

Every panel must implement a `focus_first()` method that calls `.setFocus()` on its first interactive widget. `MainWindow._navigate()` calls this 50 ms after switching panels so Tab works immediately.

Initial focus on app start is set in `__main__.py` via `QTimer.singleShot(200, ...)` after `showFullScreen()` — without this delay, focus is lost.

### Compositor requirement

PyQt5 on a bare X server (no desktop environment) will not repaint windows without a compositor. **picom is required.** Use `--backend xrender`; the `glx` backend fails on many headless/virtual GPU setups. picom must be started before the app in `~/.config/openbox/autostart`.

### Frameless fullscreen

The window uses `Qt.FramelessWindowHint | Qt.Window` and `showFullScreen()`. There is no OS-level title bar or close button. Quit is via Ctrl+Q or the sidebar **✕ Quit** button.

### Signals vs parent() traversal

The `Sidebar` widget emits a `navigate = pyqtSignal(int)` signal connected to `MainWindow._navigate()`. Never call `self.parent()._navigate()` — the immediate parent of Sidebar is the central `QWidget`, not `MainWindow`.

### XAUTHORITY

No `XAUTHORITY` is hardcoded anywhere. The service runs `xinit` without an `-auth` flag, and xinit passes the auth environment to Openbox and its children automatically. Do not add `export XAUTHORITY=...` to `autostart` or the Python app.

### Quit mechanism

The **Q** / **Ctrl+Q** / sidebar Quit button calls `pkill -x openbox` then `sys.exit(0)`. Killing Openbox causes xinit to exit, which stops the systemd service, which runs `ExecStopPost` to restore `getty@tty1`. Do not use `subprocess.call(["systemctl", ...])` from inside the app — calling systemd synchronously from a service it manages will deadlock.

### Security: login-first startup

The app is designed to start only after the operator manually runs `systemctl start prox-loader` from the console or SSH. The service is **not** enabled at boot — Proxmox always prompts for credentials first.

### Autostart config

`/etc/pve/vm-autostart.conf` is shared with any legacy bash-based boot scripts. If upgrading from such a script, verify that `DEFAULT_VM_ID` is empty (`DEFAULT_VM_ID=""`) to prevent the autostart countdown from firing unexpectedly on first launch.

---

## Reporting bugs

Open a GitHub Issue with:

- Proxmox VE version (`pveversion`)
- Python and PyQt5 versions:
  ```bash
  python3 --version
  python3 -c "import PyQt5; print(PyQt5.QtCore.PYQT_VERSION_STR)"
  ```
- Full traceback from `/tmp/prox-loader.log` or `journalctl -u prox-loader`

---

## Pull request checklist

- [ ] All modules compile without errors (`py_compile`)
- [ ] New interactive widgets have correct `setFocusPolicy()` calls
- [ ] New panels implement `focus_first()`
- [ ] New backend operations are in `backend.py` and do not shell-inject user input
- [ ] UI changes match the existing Catppuccin Mocha style (`styles.py`)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] `README.md` updated if new dependencies or startup steps are introduced
