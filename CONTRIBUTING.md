# Contributing to Prox Loader

Thank you for considering a contribution! This is a small focused tool, so please keep changes minimal and purposeful.

---

## Getting started

1. **Fork** the repository and clone your fork.
2. Create a branch with a descriptive name:
   ```bash
   git checkout -b feat/your-feature
   # or
   git checkout -b fix/your-bugfix
   ```
3. Make your changes, then run the import/compile checks before committing:
   ```bash
   python3 -m py_compile prox_loader/**/*.py prox_loader/*.py
   python3 -c "from prox_loader.main_window import MainWindow; print('OK')"
   ```
4. Open a Pull Request against `main`.

---

## Code style

- **Python 3.9+** — no walrus operator abuse, keep it readable.
- Follow existing naming conventions (`snake_case` for functions/variables, `PascalCase` for classes).
- Keep UI logic in `panels/`, Proxmox host operations in `backend.py`, threading in `workers.py`.
- Do not import PyQt5 in `backend.py` — it must stay framework-agnostic so it can be unit-tested without a display.

---

## Reporting bugs

Open a GitHub Issue with:
- Proxmox VE version (`pveversion`)
- Python and PyQt5 versions (`python3 --version`, `python3 -c "import PyQt5; print(PyQt5.QtCore.PYQT_VERSION_STR)"`)
- Full traceback or log output from the launch dialog

---

## Pull request checklist

- [ ] All modules compile without errors (`py_compile`)
- [ ] New backend operations are in `backend.py` and do not shell-inject user input
- [ ] UI changes match the existing Catppuccin Mocha style (`styles.py`)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] No new required dependencies added without updating `README.md`
