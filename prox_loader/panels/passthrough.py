"""
panels/passthrough.py — Configure GPU, USB, and PCI passthrough for a VM.
"""

from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from .. import backend
from ..dialogs import LaunchDialog


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("lbl_section")
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    return f


class PassthroughPanel(QWidget):
    """Configure PCI / GPU and USB passthrough for a selected VM."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_vmid: str = ""
        self._all_pci: List[backend.PCIDevice] = []
        self._all_usb: List[backend.USBDevice] = []
        self._all_usb_ctrl: List[backend.PCIDevice] = []
        self._scanned = False
        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._scanned:
            self._scanned = True
            self._scan_devices()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(0)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Passthrough")
        title.setObjectName("lbl_title")
        hdr.addWidget(title)
        hdr.addStretch()
        btn_scan = QPushButton("↺  Scan Devices")
        btn_scan.setObjectName("btn_secondary")
        btn_scan.setFocusPolicy(Qt.TabFocus)
        btn_scan.clicked.connect(self.scan_and_refresh)
        hdr.addWidget(btn_scan)
        root.addLayout(hdr)
        root.addSpacing(4)

        sub = QLabel("Select hardware to assign to a VM before launching")
        sub.setObjectName("lbl_subtitle")
        root.addWidget(sub)
        root.addSpacing(20)

        # VM selector
        vm_row = QHBoxLayout()
        vm_row.addWidget(_section_label("Target VM"))
        vm_row.addSpacing(12)
        self._vm_combo = QComboBox()
        self._vm_combo.setMinimumWidth(260)
        self._vm_combo.setFocusPolicy(Qt.StrongFocus)
        self._vm_combo.currentIndexChanged.connect(self._on_vm_changed)
        vm_row.addWidget(self._vm_combo)
        vm_row.addStretch()
        root.addLayout(vm_row)
        root.addSpacing(18)

        root.addWidget(_divider())
        root.addSpacing(14)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFocusPolicy(Qt.NoFocus)

        body = QWidget()
        body.setFocusPolicy(Qt.NoFocus)
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 0, 4, 0)
        self._body_layout.setSpacing(10)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        root.addSpacing(16)
        root.addWidget(_divider())
        root.addSpacing(14)

        # Action buttons
        btn_row = QHBoxLayout()
        self._btn_remove = QPushButton("🗑  Remove All Passthru")
        self._btn_remove.setObjectName("btn_danger")
        self._btn_remove.setFocusPolicy(Qt.TabFocus)
        self._btn_remove.setToolTip("Strip all hostpci/usb entries from this VM's config")
        self._btn_remove.clicked.connect(self._remove_all)
        btn_row.addWidget(self._btn_remove)

        btn_row.addStretch()

        self._btn_apply = QPushButton("Apply Config")
        self._btn_apply.setObjectName("btn_secondary")
        self._btn_apply.setFocusPolicy(Qt.TabFocus)
        self._btn_apply.setToolTip("Write passthrough entries without starting the VM")
        self._btn_apply.clicked.connect(lambda: self._launch(start=False))
        btn_row.addWidget(self._btn_apply)

        self._btn_launch = QPushButton("Apply & Start  ▶")
        self._btn_launch.setObjectName("btn_primary")
        self._btn_launch.setFocusPolicy(Qt.TabFocus)
        self._btn_launch.clicked.connect(lambda: self._launch(start=True))
        btn_row.addWidget(self._btn_launch)

        root.addLayout(btn_row)

        self._populate_vm_combo()

    # ── VM combo ──────────────────────────────────────────────────────────────

    def _populate_vm_combo(self):
        self._vm_combo.blockSignals(True)
        prev = self._selected_vmid
        self._vm_combo.clear()
        vms = backend.get_vm_list()
        self._vm_combo.addItem("— select a VM —", "")
        for vm in vms:
            self._vm_combo.addItem(f"{vm.name}  ({vm.vmid})", vm.vmid)
            if vm.vmid == prev:
                self._vm_combo.setCurrentIndex(self._vm_combo.count() - 1)
        self._vm_combo.blockSignals(False)
        self._on_vm_changed()

    def _on_vm_changed(self):
        self._selected_vmid = self._vm_combo.currentData() or ""
        has_vm = bool(self._selected_vmid)
        self._btn_remove.setEnabled(has_vm)
        self._btn_apply.setEnabled(has_vm)
        self._btn_launch.setEnabled(has_vm)

    # ── Refresh (called by main window on tab switch) ─────────────────────────

    def focus_first(self):
        self._vm_combo.setFocus()

    def refresh(self):
        """Called on tab switch — only refresh VM combo, don't rescan hardware."""
        self._populate_vm_combo()

    def scan_and_refresh(self):
        """Full refresh including hardware scan."""
        self._populate_vm_combo()
        self._scan_devices()

    def set_vm(self, vmid: str):
        """Pre-select a VM (called from VM list panel)."""
        self._selected_vmid = vmid
        for i in range(self._vm_combo.count()):
            if self._vm_combo.itemData(i) == vmid:
                self._vm_combo.setCurrentIndex(i)
                break

    def _scan_devices(self):
        self._all_pci = backend.get_pci_devices()
        self._all_usb = backend.get_usb_devices()
        self._all_usb_ctrl = backend.get_usb_controllers()
        self._rebuild_body()

    # ── Device widgets ────────────────────────────────────────────────────────

    def _rebuild_body(self):
        # Clear
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._build_gpu_section()
        self._body_layout.addSpacing(16)
        self._build_usb_ctrl_section()
        self._body_layout.addSpacing(16)
        self._build_usb_section()
        self._body_layout.addStretch()

    def _build_gpu_section(self):
        self._body_layout.addWidget(_section_label("GPU / PCI Devices"))
        self._body_layout.addSpacing(6)

        info = QLabel("lbl_info")
        info.setObjectName("lbl_info")
        info.setText(
            "First selected GPU will use x-vga=1. "
            "Enable 'Audio companion' to auto-add the matching audio function."
        )
        info.setWordWrap(True)
        self._body_layout.addWidget(info)
        self._body_layout.addSpacing(8)

        # Audio companion toggle (global for all GPUs)
        self._chk_audio = QCheckBox("Include companion audio device (function .1)")
        self._chk_audio.setChecked(True)
        self._chk_audio.setFocusPolicy(Qt.TabFocus)
        self._body_layout.addWidget(self._chk_audio)
        self._body_layout.addSpacing(8)

        # GPU/display device checkboxes
        _GPU_KEYWORDS = (
            "VGA", "DISPLAY", "3D CONTROLLER", "NVIDIA", "RADEON",
            "INTEL GRAPHICS", "USB CONTROLLER",
        )
        gpu_devices = [
            d for d in self._all_pci
            if any(k in d.description.upper() for k in _GPU_KEYWORDS)
        ]

        self._gpu_list = QListWidget()
        self._gpu_list.setMaximumHeight(160)
        self._gpu_list.setFocusPolicy(Qt.StrongFocus)

        if not gpu_devices:
            item = QListWidgetItem("No GPU/display devices found (lspci)")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self._gpu_list.addItem(item)
        else:
            for dev in gpu_devices:
                item = QListWidgetItem(f"  {dev.short_addr}    {dev.description}")
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, dev)
                self._gpu_list.addItem(item)

        self._body_layout.addWidget(self._gpu_list)

        # "Add other PCI device" row
        add_row = QHBoxLayout()
        lbl = QLabel("Add any PCI device by address:")
        lbl.setStyleSheet("color: #6c7086; font-size: 12px; background: transparent;")
        add_row.addWidget(lbl)

        from PyQt5.QtWidgets import QLineEdit
        self._pci_extra = QLineEdit()
        self._pci_extra.setPlaceholderText("e.g. 0000:03:00.0")
        self._pci_extra.setMaximumWidth(220)
        self._pci_extra.setFocusPolicy(Qt.StrongFocus)
        add_row.addWidget(self._pci_extra)
        add_row.addStretch()
        self._body_layout.addLayout(add_row)

    def _build_usb_ctrl_section(self):
        self._body_layout.addWidget(_section_label("USB Controllers (PCI Passthrough)"))
        self._body_layout.addSpacing(6)

        info = QLabel(
            "Pass an entire USB controller to a VM. "
            "All devices plugged into that controller will be available inside the VM."
        )
        info.setObjectName("lbl_info")
        info.setWordWrap(True)
        self._body_layout.addWidget(info)
        self._body_layout.addSpacing(6)

        self._usb_ctrl_list = QListWidget()
        self._usb_ctrl_list.setMaximumHeight(120)
        self._usb_ctrl_list.setFocusPolicy(Qt.StrongFocus)
        self._usb_ctrl_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._usb_ctrl_list.setTextElideMode(Qt.ElideNone)
        self._usb_ctrl_list.setWordWrap(True)
        self._usb_ctrl_list.itemClicked.connect(self._toggle_pci_item)

        if not self._all_usb_ctrl:
            item = QListWidgetItem("No USB controllers found (lspci)")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self._usb_ctrl_list.addItem(item)
        else:
            for dev in self._all_usb_ctrl:
                item = QListWidgetItem(f"{dev.short_addr}  {dev.description}")
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                item.setData(Qt.UserRole, dev)
                self._usb_ctrl_list.addItem(item)

        self._body_layout.addWidget(self._usb_ctrl_list)

    def _toggle_pci_item(self, item: QListWidgetItem):
        if not (item.flags() & Qt.ItemIsUserCheckable):
            return
        item.setCheckState(
            Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        )

    def _build_usb_section(self):
        self._body_layout.addWidget(_section_label("USB Devices"))
        self._body_layout.addSpacing(6)

        self._chk_usb_auto = QCheckBox("Auto-scan — pass all connected USB devices")
        self._chk_usb_auto.setChecked(True)
        self._chk_usb_auto.setFocusPolicy(Qt.TabFocus)
        self._chk_usb_auto.stateChanged.connect(self._on_usb_auto_changed)
        self._body_layout.addWidget(self._chk_usb_auto)
        self._body_layout.addSpacing(8)

        # Manual device list
        manual_lbl = QLabel("Manual selection (active when auto-scan is off):")
        manual_lbl.setStyleSheet("color: #6c7086; font-size: 12px; background: transparent;")
        self._body_layout.addWidget(manual_lbl)

        self._usb_list = QListWidget()
        self._usb_list.setMinimumHeight(120)
        self._usb_list.setMaximumHeight(220)
        self._usb_list.setFocusPolicy(Qt.StrongFocus)
        self._usb_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._usb_list.setTextElideMode(Qt.ElideNone)
        self._usb_list.setWordWrap(True)
        self._usb_list.itemClicked.connect(self._on_usb_item_clicked)

        if not self._all_usb:
            item = QListWidgetItem("No USB devices found")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self._usb_list.addItem(item)
        else:
            for dev in self._all_usb:
                label = f"{dev.vendor_product}  {dev.description}"
                item = QListWidgetItem(label)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                # checkboxes enabled only when auto-scan is off
                item.setData(Qt.UserRole, dev)
                self._usb_list.addItem(item)

        self._usb_list.setEnabled(True)
        self._usb_list.itemClicked.connect(self._toggle_usb_item)
        # list is always enabled so mouse scroll works
        self._body_layout.addWidget(self._usb_list)
        self._on_usb_auto_changed(Qt.Checked)  # apply initial state

    def _toggle_usb_item(self, item: QListWidgetItem):
        """Clicking anywhere on a row toggles its checkbox."""
        if not (item.flags() & Qt.ItemIsUserCheckable):
            return
        item.setCheckState(
            Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        )

    def _on_usb_auto_changed(self, state: int):
        auto = (state == Qt.Checked)
        for i in range(self._usb_list.count()):
            item = self._usb_list.item(i)
            if item.data(Qt.UserRole) is None:
                continue  # placeholder row
            if auto:
                # auto-scan: show for reference only, no checkboxes
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setData(Qt.CheckStateRole, None)
            else:
                # manual: checkable but unchecked by default
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)

    def _on_usb_item_clicked(self, item: QListWidgetItem):
        """Toggle checkbox when the user clicks anywhere on the row."""
        if not (item.flags() & Qt.ItemIsUserCheckable):
            return
        item.setCheckState(
            Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        )

    # ── Gather selections ─────────────────────────────────────────────────────

    def _selected_gpus(self) -> List[backend.PCIDevice]:
        gpus = []
        for i in range(self._gpu_list.count()):
            item = self._gpu_list.item(i)
            if item.checkState() == Qt.Checked:
                dev = item.data(Qt.UserRole)
                if dev:
                    gpus.append(dev)
        return gpus

    def _selected_usb_ctrls(self) -> List[backend.PCIDevice]:
        ctrls = []
        if not hasattr(self, "_usb_ctrl_list"):
            return ctrls
        for i in range(self._usb_ctrl_list.count()):
            item = self._usb_ctrl_list.item(i)
            if item.checkState() == Qt.Checked:
                dev = item.data(Qt.UserRole)
                if dev:
                    ctrls.append(dev)
        return ctrls

    def _selected_usbs(self) -> List[backend.USBDevice]:
        usbs = []
        for i in range(self._usb_list.count()):
            item = self._usb_list.item(i)
            if item.checkState() == Qt.Checked:
                dev = item.data(Qt.UserRole)
                if dev:
                    usbs.append(dev)
        return usbs

    # ── Actions ───────────────────────────────────────────────────────────────

    def _remove_all(self):
        if not self._selected_vmid:
            return
        reply = QMessageBox.question(
            self, "Remove Passthrough",
            f"Remove all passthrough (hostpci/usb) entries from VM {self._selected_vmid}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            backend.backup_vm_config(self._selected_vmid)
            backend.remove_passthrough_entries(self._selected_vmid)
            QMessageBox.information(self, "Done", "Passthrough entries removed.")

    def _launch(self, start: bool):
        if not self._selected_vmid:
            QMessageBox.warning(self, "No VM Selected", "Please select a VM first.")
            return

        gpus = self._selected_gpus()
        gpus += self._selected_usb_ctrls()   # USB controllers are also PCI passthrough
        usb_auto = self._chk_usb_auto.isChecked()
        usbs = [] if usb_auto else self._selected_usbs()
        include_audio = self._chk_audio.isChecked()

        # Add any extra PCI device
        extra_addr = self._pci_extra.text().strip() if hasattr(self, "_pci_extra") else ""
        if extra_addr:
            gpus.append(backend.PCIDevice(address=extra_addr, description="(custom)"))

        mode = "custom" if (gpus or usb_auto or usbs) else "none"

        vm_name = self._vm_combo.currentText().split("(")[0].strip()
        dlg = LaunchDialog(
            self._selected_vmid,
            vm_name,
            mode=mode,
            gpus=gpus,
            include_audio=include_audio,
            usb_auto=usb_auto,
            usbs=usbs,
            start_after=start,
            parent=self,
        )
        dlg.exec_()
