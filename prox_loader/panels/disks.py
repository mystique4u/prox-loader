"""
panels/disks.py — Attach, detach, and move SCSI disks between VMs.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import backend
from ..dialogs import VMPickerDialog


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("lbl_section")
    return lbl


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    return f


class DisksPanel(QWidget):
    """Manage SCSI disk assignments across VMs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_vmid: str = ""
        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(0)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Disk Manager")
        title.setObjectName("lbl_title")
        hdr.addWidget(title)
        hdr.addStretch()
        btn_refresh = QPushButton("↺  Refresh")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.setFocusPolicy(Qt.TabFocus)
        btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(btn_refresh)
        root.addLayout(hdr)
        root.addSpacing(4)

        sub = QLabel("Attach, detach, and move SCSI storage between VMs")
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
        root.addSpacing(16)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFocusPolicy(Qt.NoFocus)

        body = QWidget()
        body.setFocusPolicy(Qt.NoFocus)
        self._body = QVBoxLayout(body)
        self._body.setContentsMargins(0, 0, 4, 0)
        self._body.setSpacing(10)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self._build_attached_section()
        self._body.addSpacing(20)
        self._build_available_section()
        self._body.addStretch()

        self._populate_vm_combo()

    def _build_attached_section(self):
        self._body.addWidget(_section_label("Attached SCSI Disks"))
        self._body.addSpacing(6)

        self._attached_list = QListWidget()
        self._attached_list.setMaximumHeight(160)
        self._attached_list.setFocusPolicy(Qt.StrongFocus)
        self._body.addWidget(self._attached_list)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_move = QPushButton("Move to VM…")
        self._btn_move.setObjectName("btn_small")
        self._btn_move.setFocusPolicy(Qt.TabFocus)
        self._btn_move.setToolTip("Move selected disk to another VM")
        self._btn_move.clicked.connect(self._move_disk)
        btn_row.addWidget(self._btn_move)

        self._btn_detach = QPushButton("Detach Selected")
        self._btn_detach.setObjectName("btn_small_danger")
        self._btn_detach.setFocusPolicy(Qt.TabFocus)
        self._btn_detach.clicked.connect(self._detach_disk)
        btn_row.addWidget(self._btn_detach)

        self._body.addLayout(btn_row)

    def _build_available_section(self):
        self._body.addWidget(_section_label("Available Disks  (/dev/disk/by-id)"))
        self._body.addSpacing(6)

        self._available_list = QListWidget()
        self._available_list.setMaximumHeight(160)
        self._available_list.setFocusPolicy(Qt.StrongFocus)
        self._body.addWidget(self._available_list)

        # Options row
        opts_row = QHBoxLayout()
        lbl = QLabel("Options:")
        lbl.setStyleSheet("color: #6c7086; font-size: 12px; background: transparent;")
        opts_row.addWidget(lbl)

        self._opts_edit = QLineEdit("backup=0,discard=on")
        self._opts_edit.setMaximumWidth(280)
        self._opts_edit.setFocusPolicy(Qt.StrongFocus)
        opts_row.addWidget(self._opts_edit)
        opts_row.addStretch()
        self._body.addLayout(opts_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_custom = QPushButton("Attach Custom Spec…")
        self._btn_custom.setObjectName("btn_small")
        self._btn_custom.setFocusPolicy(Qt.TabFocus)
        self._btn_custom.setToolTip("Attach a disk by specifying the full spec manually")
        self._btn_custom.clicked.connect(self._attach_custom)
        btn_row.addWidget(self._btn_custom)

        self._btn_attach = QPushButton("Attach Selected  +")
        self._btn_attach.setObjectName("btn_small_primary")
        self._btn_attach.setFocusPolicy(Qt.TabFocus)
        self._btn_attach.clicked.connect(self._attach_disk)
        btn_row.addWidget(self._btn_attach)

        self._body.addLayout(btn_row)

    # ── VM combo ──────────────────────────────────────────────────────────────

    def _populate_vm_combo(self):
        self._vm_combo.blockSignals(True)
        prev = self._selected_vmid
        self._vm_combo.clear()
        self._vm_combo.addItem("— select a VM —", "")
        for vm in backend.get_vm_list():
            self._vm_combo.addItem(f"{vm.name}  ({vm.vmid})", vm.vmid)
            if vm.vmid == prev:
                self._vm_combo.setCurrentIndex(self._vm_combo.count() - 1)
        self._vm_combo.blockSignals(False)
        self._on_vm_changed()

    def _on_vm_changed(self):
        self._selected_vmid = self._vm_combo.currentData() or ""
        self._refresh_attached()

    # ── Public API ─────────────────────────────────────────────────────────────

    def focus_first(self):
        self._vm_combo.setFocus()

    def refresh(self):
        self._populate_vm_combo()
        self._refresh_attached()
        self._refresh_available()

    def set_vm(self, vmid: str):
        self._selected_vmid = vmid
        for i in range(self._vm_combo.count()):
            if self._vm_combo.itemData(i) == vmid:
                self._vm_combo.setCurrentIndex(i)
                break

    # ── List refreshers ───────────────────────────────────────────────────────

    def _refresh_attached(self):
        self._attached_list.clear()
        if not self._selected_vmid:
            return
        for disk in backend.get_vm_scsi_disks(self._selected_vmid):
            item = QListWidgetItem(f"  {disk.slot}    {disk.spec}")
            item.setData(Qt.UserRole, disk)
            self._attached_list.addItem(item)
        if self._attached_list.count() == 0:
            placeholder = QListWidgetItem("  No SCSI disks attached")
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsEnabled)
            self._attached_list.addItem(placeholder)

    def _refresh_available(self):
        self._available_list.clear()
        for disk in backend.get_disks_by_id():
            item = QListWidgetItem(f"  {disk.name}")
            item.setData(Qt.UserRole, disk)
            self._available_list.addItem(item)
        if self._available_list.count() == 0:
            placeholder = QListWidgetItem("  No disks found in /dev/disk/by-id")
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsEnabled)
            self._available_list.addItem(placeholder)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _detach_disk(self):
        if not self._selected_vmid:
            return
        item = self._attached_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a disk to detach.")
            return
        disk = item.data(Qt.UserRole)
        if not disk:
            return
        reply = QMessageBox.question(
            self, "Detach Disk",
            f"Detach {disk.slot} from VM {self._selected_vmid}?\n\n{disk.spec}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            backend.backup_vm_config(self._selected_vmid)
            backend.detach_scsi_disk(self._selected_vmid, disk.slot)
            self._refresh_attached()

    def _attach_disk(self):
        if not self._selected_vmid:
            QMessageBox.warning(self, "No VM", "Select a VM first.")
            return
        item = self._available_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a disk from the available list.")
            return
        disk = item.data(Qt.UserRole)
        if not disk:
            return
        options = self._opts_edit.text().strip() or "backup=0,discard=on"
        backend.backup_vm_config(self._selected_vmid)
        slot_key = backend.attach_scsi_disk(self._selected_vmid, disk.path, options)
        QMessageBox.information(
            self, "Attached",
            f"Attached {disk.name} as {slot_key} on VM {self._selected_vmid}."
        )
        self._refresh_attached()

    def _attach_custom(self):
        if not self._selected_vmid:
            QMessageBox.warning(self, "No VM", "Select a VM first.")
            return
        from PyQt5.QtWidgets import QInputDialog
        spec, ok = QInputDialog.getText(
            self, "Custom Disk Spec",
            "Enter disk spec:\n(e.g. local-lvm:vm-100-disk-2  or  /dev/disk/by-id/ata-…)"
        )
        if ok and spec.strip():
            options = self._opts_edit.text().strip() or "backup=0,discard=on"
            backend.backup_vm_config(self._selected_vmid)
            slot_key = backend.attach_scsi_disk(self._selected_vmid, spec.strip(), options)
            QMessageBox.information(
                self, "Attached",
                f"Attached as {slot_key} on VM {self._selected_vmid}."
            )
            self._refresh_attached()

    def _move_disk(self):
        if not self._selected_vmid:
            return
        item = self._attached_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a disk to move.")
            return
        disk = item.data(Qt.UserRole)
        if not disk:
            return

        vms = [v for v in backend.get_vm_list() if v.vmid != self._selected_vmid]
        if not vms:
            QMessageBox.information(self, "No Other VMs", "No other VMs available.")
            return

        picker = VMPickerDialog(vms, "Select Destination VM", parent=self)
        if picker.exec_() == picker.Accepted and picker.selected_vm:
            dst = picker.selected_vm
            new_slot = backend.move_scsi_disk(
                self._selected_vmid, disk.slot, dst.vmid
            )
            QMessageBox.information(
                self, "Moved",
                f"Moved {disk.slot} from VM {self._selected_vmid} "
                f"to VM {dst.vmid} ({dst.name}) as {new_slot}."
            )
            self._refresh_attached()
