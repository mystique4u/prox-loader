"""
config.py — Autostart configuration: load and save /etc/pve/vm-autostart.conf
"""

import os

AUTOSTART_CONFIG = "/etc/pve/vm-autostart.conf"


def load() -> dict:
    """Return {'vm_id': str, 'timeout': int}. Empty vm_id means no autostart."""
    cfg = {"vm_id": "", "timeout": 10}
    if not os.path.isfile(AUTOSTART_CONFIG):
        return cfg
    try:
        with open(AUTOSTART_CONFIG) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEFAULT_VM_ID="):
                    cfg["vm_id"] = line.split("=", 1)[1].strip("\"'")
                elif line.startswith("AUTOSTART_TIMEOUT="):
                    try:
                        cfg["timeout"] = int(line.split("=", 1)[1].strip())
                    except ValueError:
                        pass
    except OSError:
        pass
    return cfg


def save(vm_id: str, timeout: int):
    os.makedirs(os.path.dirname(AUTOSTART_CONFIG), exist_ok=True)
    with open(AUTOSTART_CONFIG, "w") as f:
        f.write("# VM Autostart Configuration\n")
        f.write(f'DEFAULT_VM_ID="{vm_id}"\n')
        f.write(f"AUTOSTART_TIMEOUT={timeout}\n")


def clear():
    save("", 10)
