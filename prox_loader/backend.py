"""
backend.py — subprocess wrappers around qm, lspci, lsusb, config files.
All interaction with the Proxmox host lives here.
"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class VMInfo:
    vmid: str
    name: str
    status: str  # 'running' | 'stopped' | 'paused' | 'unknown'

    @property
    def is_running(self) -> bool:
        return self.status == "running"

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.vmid})"


@dataclass
class PCIDevice:
    address: str    # e.g. "0000:01:00.0"
    description: str

    @property
    def short_addr(self) -> str:
        return self.address.replace("0000:", "")


@dataclass
class USBDevice:
    vendor_product: str   # e.g. "1532:005c"
    description: str


@dataclass
class DiskEntry:
    name: str    # symlink name in /dev/disk/by-id/
    path: str    # full /dev/disk/by-id/<name>


@dataclass
class VMDisk:
    slot: str    # e.g. "scsi0"
    spec: str    # full value after the colon


# ── Low-level subprocess helper ───────────────────────────────────────────────

def _run(cmd: List[str]) -> Tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# ── VM operations ─────────────────────────────────────────────────────────────

def get_vm_list() -> List[VMInfo]:
    rc, out, _ = _run(["qm", "list"])
    if rc != 0:
        return []
    vms = []
    for line in out.splitlines()[1:]:   # skip header
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit():
            vms.append(VMInfo(vmid=parts[0], name=parts[1], status=parts[2]))
    return vms


def get_vm_status(vmid: str) -> str:
    rc, out, _ = _run(["qm", "status", vmid])
    if rc == 0:
        m = re.search(r"status:\s*(\w+)", out)
        if m:
            return m.group(1)
    return "unknown"


def start_vm(vmid: str) -> Tuple[bool, str]:
    rc, out, err = _run(["qm", "start", vmid])
    return rc == 0, (err or out).strip()


def stop_vm(vmid: str) -> Tuple[bool, str]:
    rc, out, err = _run(["qm", "stop", vmid])
    return rc == 0, (err or out).strip()


# ── VM config file ────────────────────────────────────────────────────────────

def _config_path(vmid: str) -> str:
    return f"/etc/pve/qemu-server/{vmid}.conf"


def config_exists(vmid: str) -> bool:
    return os.path.isfile(_config_path(vmid))


def read_vm_config(vmid: str) -> Dict[str, str]:
    cfg: Dict[str, str] = {}
    try:
        with open(_config_path(vmid)) as f:
            for line in f:
                line = line.rstrip("\n")
                if ":" in line and not line.startswith("#"):
                    key, _, val = line.partition(":")
                    cfg[key.strip()] = val.strip()
    except OSError:
        pass
    return cfg


def backup_vm_config(vmid: str) -> str:
    src = _config_path(vmid)
    if os.path.isfile(src):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = f"{src}.backup.{ts}"
        shutil.copy2(src, dst)
        return dst
    return ""


def remove_passthrough_entries(vmid: str):
    """Remove all hostpciN and usbN lines from a VM's config."""
    path = _config_path(vmid)
    if not os.path.isfile(path):
        return
    with open(path) as f:
        lines = f.readlines()
    with open(path, "w") as f:
        for line in lines:
            if not re.match(r"^(hostpci|usb)\d+:", line):
                f.write(line)


def append_config_line(vmid: str, key: str, value: str):
    with open(_config_path(vmid), "a") as f:
        f.write(f"{key}: {value}\n")


def get_next_slot(vmid: str, prefix: str) -> int:
    cfg = read_vm_config(vmid)
    for i in range(16):
        if f"{prefix}{i}" not in cfg:
            return i
    return 0


# ── SCSI disk management ──────────────────────────────────────────────────────

def get_vm_scsi_disks(vmid: str) -> List[VMDisk]:
    cfg = read_vm_config(vmid)
    return [
        VMDisk(slot=k, spec=v)
        for k, v in sorted(cfg.items())
        if re.match(r"^scsi\d+$", k)
    ]


def detach_scsi_disk(vmid: str, slot: str):
    path = _config_path(vmid)
    with open(path) as f:
        lines = f.readlines()
    with open(path, "w") as f:
        for line in lines:
            if not line.startswith(f"{slot}:"):
                f.write(line)


def attach_scsi_disk(vmid: str, disk_spec: str, options: str = "backup=0,discard=on") -> str:
    slot = get_next_slot(vmid, "scsi")
    key = f"scsi{slot}"
    append_config_line(vmid, key, f"{disk_spec},{options}")
    return key


def move_scsi_disk(src_vmid: str, src_slot: str, dst_vmid: str) -> str:
    """Move a SCSI disk entry from one VM to another. Returns new slot key."""
    src_cfg = read_vm_config(src_vmid)
    spec = src_cfg.get(src_slot, "")
    if not spec:
        raise ValueError(f"Slot {src_slot} not found in VM {src_vmid}")
    backup_vm_config(src_vmid)
    backup_vm_config(dst_vmid)
    detach_scsi_disk(src_vmid, src_slot)
    new_slot = get_next_slot(dst_vmid, "scsi")
    key = f"scsi{new_slot}"
    append_config_line(dst_vmid, key, spec)
    return key


# ── PCI / USB / disk enumeration ──────────────────────────────────────────────

def get_pci_devices() -> List[PCIDevice]:
    rc, out, _ = _run(["lspci", "-nn"])
    if rc != 0:
        return []
    devices = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        addr, _, desc = line.partition(" ")
        devices.append(PCIDevice(address=f"0000:{addr}", description=desc))
    return devices


_GPU_KEYWORDS = ("VGA", "DISPLAY", "3D CONTROLLER", "NVIDIA", "RADEON", "INTEL GRAPHICS")


def get_gpu_devices() -> List[PCIDevice]:
    return [d for d in get_pci_devices() if any(k in d.description.upper() for k in _GPU_KEYWORDS)]


def find_companion_audio(gpu: PCIDevice, all_pci: List[PCIDevice]) -> Optional[PCIDevice]:
    """Find an audio device on the same PCI bus/slot as the GPU (function .1)."""
    base = gpu.address.rsplit(".", 1)[0]
    companion_addr = f"{base}.1"
    for dev in all_pci:
        if dev.address == companion_addr and "audio" in dev.description.lower():
            return dev
    return None


def get_usb_devices() -> List[USBDevice]:
    rc, out, _ = _run(["lsusb"])
    if rc != 0:
        return []
    devices = []
    for line in out.splitlines():
        if "root hub" in line.lower():
            continue
        m = re.search(r"([0-9a-f]{4}:[0-9a-f]{4})\s+(.*)", line)
        if m:
            devices.append(USBDevice(vendor_product=m.group(1), description=m.group(2).strip()))
    return devices


def get_disks_by_id() -> List[DiskEntry]:
    by_id = "/dev/disk/by-id"
    if not os.path.isdir(by_id):
        return []
    entries = []
    for name in sorted(os.listdir(by_id)):
        if re.search(r"-part\d+$", name):
            continue
        entries.append(DiskEntry(name=name, path=os.path.join(by_id, name)))
    return entries
