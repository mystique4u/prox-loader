"""
workers.py — Background QThread workers so the UI stays responsive.
"""

from typing import List, Optional

from PyQt5.QtCore import QThread, pyqtSignal

from . import backend


class VMMonitorWorker(QThread):
    """
    Poll VM status every few seconds. Emits vm_stopped when the VM is no
    longer running so the caller can clean up passthrough and restart X.
    """

    vm_stopped = pyqtSignal()

    def __init__(self, vmid: str, interval_ms: int = 3000, parent=None):
        super().__init__(parent)
        self.vmid = vmid
        self._interval = interval_ms
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        while not self._stop_flag:
            if backend.get_vm_status(self.vmid) != "running":
                self.vm_stopped.emit()
                return
            self.msleep(self._interval)


class LaunchWorker(QThread):
    """
    Apply passthrough configuration to a VM config file, then optionally start it.

    Modes
    -----
    quick  — predefined GPU (0000:01:00) + all connected USB devices
    custom — caller supplies lists of PCIDevice / USBDevice to add
    none   — just start the VM without touching passthrough
    """

    log_line = pyqtSignal(str)          # text, may contain simple HTML
    finished = pyqtSignal(bool, str)    # success, message

    def __init__(
        self,
        vmid: str,
        name: str,
        mode: str,                                      # 'quick' | 'custom' | 'none'
        gpus: Optional[List[backend.PCIDevice]] = None,
        include_audio: bool = True,
        usb_auto: bool = True,
        usbs: Optional[List[backend.USBDevice]] = None,
        start_after: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.vmid = vmid
        self.name = name
        self.mode = mode
        self.gpus = gpus or []
        self.include_audio = include_audio
        self.usb_auto = usb_auto
        self.usbs = usbs or []
        self.start_after = start_after

    # ── helpers ──────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        self.log_line.emit(msg)

    def _add_pci(self, address: str, flags: str):
        slot = backend.get_next_slot(self.vmid, "hostpci")
        key = f"hostpci{slot}"
        value = f"{address},{flags}"
        backend.append_config_line(self.vmid, key, value)
        self._log(f"  + {key}: {value}")

    def _add_usb(self, vendor_product: str):
        slot = backend.get_next_slot(self.vmid, "usb")
        key = f"usb{slot}"
        value = f"host={vendor_product},usb3=1"
        backend.append_config_line(self.vmid, key, value)
        self._log(f"  + {key}: {value}")

    # ── main thread entry ─────────────────────────────────────────────────────

    def run(self):
        try:
            self._log(f"<b>Preparing VM {self.vmid} ({self.name})</b>")

            if self.mode != "none":
                self._configure_passthrough()

            if self.start_after:
                self._start()
            else:
                self.finished.emit(True, "Configuration applied.")

        except Exception as exc:
            self._log(f'<span style="color:#f38ba8">✗ Unexpected error: {exc}</span>')
            self.finished.emit(False, str(exc))

    # ── passthrough logic ─────────────────────────────────────────────────────

    def _configure_passthrough(self):
        if not backend.config_exists(self.vmid):
            raise FileNotFoundError(
                f"Config not found: /etc/pve/qemu-server/{self.vmid}.conf"
            )

        self._log("  Backing up config…")
        backup = backend.backup_vm_config(self.vmid)
        if backup:
            self._log(f'  <span style="color:#6c7086">→ {backup}</span>')

        self._log("  Removing existing passthrough entries…")
        backend.remove_passthrough_entries(self.vmid)

        if self.mode == "quick":
            self._add_quick_passthrough()
        elif self.mode == "custom":
            self._add_custom_passthrough()

    def _add_quick_passthrough(self):
        self._log("<b>GPU passthrough (predefined)</b>")
        self._add_pci("0000:01:00.0", "pcie=1,x-vga=1")
        self._add_pci("0000:01:00.1", "pcie=1")

        self._log("<b>USB passthrough (auto-scan)</b>")
        usb_devices = backend.get_usb_devices()
        if not usb_devices:
            self._log('  <span style="color:#f9e2af">⚠ No USB devices found</span>')
        for dev in usb_devices:
            self._add_usb(dev.vendor_product)

    def _add_custom_passthrough(self):
        all_pci = backend.get_pci_devices()
        primary = True

        if self.gpus:
            self._log("<b>PCI / GPU passthrough</b>")
            for gpu in self.gpus:
                flags = "pcie=1,x-vga=1" if primary else "pcie=1"
                self._add_pci(gpu.address, flags)
                primary = False

                if self.include_audio:
                    audio = backend.find_companion_audio(gpu, all_pci)
                    if audio:
                        self._add_pci(audio.address, "pcie=1")

        if self.usb_auto:
            self._log("<b>USB passthrough (auto-scan)</b>")
            for dev in backend.get_usb_devices():
                self._add_usb(dev.vendor_product)
        elif self.usbs:
            self._log("<b>USB passthrough (manual)</b>")
            for dev in self.usbs:
                self._add_usb(dev.vendor_product)

    def _start(self):
        status = backend.get_vm_status(self.vmid)
        if status == "running":
            self._log('<span style="color:#f9e2af">⚠ VM is already running</span>')
            self.finished.emit(True, "VM is already running.")
            return

        self._log(f"<b>Starting VM {self.vmid}…</b>")
        ok, msg = backend.start_vm(self.vmid)
        if ok:
            self._log(
                f'<span style="color:#a6e3a1">✓ VM {self.vmid} started successfully!</span>'
            )
            self.finished.emit(True, "")
        else:
            self._log(f'<span style="color:#f38ba8">✗ Failed: {msg}</span>')
            self.finished.emit(False, msg)
