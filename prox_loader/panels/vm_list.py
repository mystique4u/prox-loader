"""
panels/vm_list.py — VM selection panel with autostart countdown.
"""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import backend
from .. import config as cfg
from ..dialogs import LaunchDialog


# ── Autostart countdown banner ────────────────────────────────────────────────

class AutostartBanner(QFrame):
    cancelled = pyqtSignal()
    triggered = pyqtSignal(str)   # vmid

    def __init__(self, vm: backend.VMInfo, timeout: int, parent=None):
        super().__init__(parent)
        self.setObjectName("banner_autostart")
        self._vm = vm
        self._remaining = timeout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        icon = QLabel("⚡")
        icon.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(icon)

        self._msg = QLabel()
        self._msg.setStyleSheet("color: #89b4fa; font-size: 13px; background: transparent;")
        self._msg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self._msg, 1)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("btn_small")
        btn_cancel.clicked.connect(self._cancel)
        layout.addWidget(btn_cancel)

        btn_now = QPushButton("Launch Now")
        btn_now.setObjectName("btn_small_primary")
        btn_now.clicked.connect(lambda: self.triggered.emit(self._vm.vmid))
        layout.addWidget(btn_now)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._update_label()
        self._timer.start(1000)

    def _update_label(self):
        self._msg.setText(
            f"Autostart: <b>{self._vm.name}</b> (VM {self._vm.vmid}) "
            f"launches in <b>{self._remaining}s</b>"
        )

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            self.triggered.emit(self._vm.vmid)
        else:
            self._update_label()

    def _cancel(self):
        self._timer.stop()
        self.cancelled.emit()

    def stop(self):
        self._timer.stop()


# ── Single VM card ────────────────────────────────────────────────────────────

class VMCard(QFrame):
    action_passthrough = pyqtSignal(str, str)   # vmid, name
    action_disks       = pyqtSignal(str, str)
    action_quick_start = pyqtSignal(str, str)
    action_start       = pyqtSignal(str, str)
    action_stop        = pyqtSignal(str, str)

    def __init__(self, vm: backend.VMInfo, is_autostart: bool = False, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setObjectName("vm_card")
        self._build(is_autostart)

    def _build(self, is_autostart: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        # VMID badge
        vmid_lbl = QLabel(self.vm.vmid)
        vmid_lbl.setObjectName("lbl_vmid")
        vmid_lbl.setFixedWidth(46)
        vmid_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(vmid_lbl)

        # Info column
        info = QVBoxLayout()
        info.setSpacing(3)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_lbl = QLabel(self.vm.name)
        name_lbl.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #cdd6f4; background: transparent;"
        )
        name_row.addWidget(name_lbl)

        if is_autostart:
            badge = QLabel("AUTO")
            badge.setStyleSheet(
                "background-color: #f9e2af; color: #1e1e2e; border-radius: 4px;"
                " padding: 1px 7px; font-size: 10px; font-weight: bold;"
            )
            name_row.addWidget(badge)
        name_row.addStretch()
        info.addLayout(name_row)

        status_lbl = QLabel()
        status_lbl.setStyleSheet("background: transparent;")
        if self.vm.status == "running":
            status_lbl.setText("● Running")
            status_lbl.setObjectName("lbl_status_running")
        elif self.vm.status == "stopped":
            status_lbl.setText("○ Stopped")
            status_lbl.setObjectName("lbl_status_stopped")
        else:
            status_lbl.setText(f"◐ {self.vm.status.title()}")
            status_lbl.setObjectName("lbl_status_paused")
        info.addWidget(status_lbl)
        layout.addLayout(info, 1)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        if not self.vm.is_running:
            btn_quick = QPushButton("⚡ Quick Start")
            btn_quick.setObjectName("btn_small_primary")
            btn_quick.setToolTip("Apply GPU + all USB passthrough and start VM")
            btn_quick.clicked.connect(
                lambda: self.action_quick_start.emit(self.vm.vmid, self.vm.name)
            )
            btn_row.addWidget(btn_quick)

        btn_pt = QPushButton("🔌 Passthrough")
        btn_pt.setObjectName("btn_small")
        btn_pt.setToolTip("Configure device passthrough for this VM")
        btn_pt.clicked.connect(
            lambda: self.action_passthrough.emit(self.vm.vmid, self.vm.name)
        )
        btn_row.addWidget(btn_pt)

        btn_dk = QPushButton("💾 Disks")
        btn_dk.setObjectName("btn_small")
        btn_dk.setToolTip("Attach / detach storage disks")
        btn_dk.clicked.connect(
            lambda: self.action_disks.emit(self.vm.vmid, self.vm.name)
        )
        btn_row.addWidget(btn_dk)

        if not self.vm.is_running:
            btn_start = QPushButton("▶ Start")
            btn_start.setObjectName("btn_small")
            btn_start.setToolTip("Start VM without changing passthrough config")
            btn_start.clicked.connect(
                lambda: self.action_start.emit(self.vm.vmid, self.vm.name)
            )
            btn_row.addWidget(btn_start)
        else:
            btn_stop = QPushButton("■ Stop")
            btn_stop.setObjectName("btn_small_danger")
            btn_stop.clicked.connect(
                lambda: self.action_stop.emit(self.vm.vmid, self.vm.name)
            )
            btn_row.addWidget(btn_stop)

        layout.addLayout(btn_row)


# ── VM list panel ─────────────────────────────────────────────────────────────

class VMListPanel(QWidget):
    """Main panel — lists all Proxmox VMs as interactive cards."""

    vm_selected_for_passthrough = pyqtSignal(str, str)
    vm_selected_for_disks       = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vms: list = []
        self._autostart_cfg: dict = {}
        self._banner: AutostartBanner = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("Virtual Machines")
        title.setObjectName("lbl_title")
        hdr.addWidget(title)
        hdr.addStretch()

        btn_refresh = QPushButton("↺  Refresh")
        btn_refresh.setObjectName("btn_secondary")
        btn_refresh.clicked.connect(self.refresh)
        hdr.addWidget(btn_refresh)
        root.addLayout(hdr)
        root.addSpacing(4)

        sub = QLabel("Select a VM to configure and launch")
        sub.setObjectName("lbl_subtitle")
        root.addWidget(sub)
        root.addSpacing(18)

        # ── Autostart banner slot ──────────────────────────────
        self._banner_slot = QVBoxLayout()
        self._banner_slot.setContentsMargins(0, 0, 0, 0)
        self._banner_slot.setSpacing(0)
        root.addLayout(self._banner_slot)

        # ── Scrollable VM card list ────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 4, 0)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        root.addWidget(scroll, 1)

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self):
        self._vms = backend.get_vm_list()
        self._autostart_cfg = cfg.load()
        self._rebuild_cards()
        self._rebuild_banner()

    # ── Card list ─────────────────────────────────────────────────────────────

    def _rebuild_cards(self):
        # Remove everything except the final stretch
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        autostart_id = self._autostart_cfg.get("vm_id", "")

        if not self._vms:
            no_vms = QLabel(
                "No VMs found.\n\n"
                "Make sure 'qm' is accessible and this app is running as root."
            )
            no_vms.setAlignment(Qt.AlignCenter)
            no_vms.setStyleSheet("color: #6c7086; font-size: 13px; padding: 60px;")
            self._cards_layout.insertWidget(0, no_vms)
            return

        for i, vm in enumerate(self._vms):
            card = VMCard(vm, is_autostart=(vm.vmid == autostart_id))
            card.action_passthrough.connect(self.vm_selected_for_passthrough)
            card.action_disks.connect(self.vm_selected_for_disks)
            card.action_quick_start.connect(self._on_quick_start)
            card.action_start.connect(self._on_plain_start)
            card.action_stop.connect(self._on_stop)
            self._cards_layout.insertWidget(i, card)

    # ── Autostart banner ──────────────────────────────────────────────────────

    def _rebuild_banner(self):
        if self._banner:
            self._banner.stop()
            self._banner.deleteLater()
            self._banner = None

        vm_id = self._autostart_cfg.get("vm_id", "")
        timeout = self._autostart_cfg.get("timeout", 10)
        if not vm_id:
            return

        vm = next((v for v in self._vms if v.vmid == vm_id), None)
        if vm is None or vm.is_running:
            return

        self._banner = AutostartBanner(vm, timeout, self)
        self._banner.cancelled.connect(self._on_banner_cancel)
        self._banner.triggered.connect(self._on_autostart_trigger)

        self._banner_slot.addWidget(self._banner)
        self._banner_slot.addSpacing(14)

    def _on_banner_cancel(self):
        if self._banner:
            self._banner.stop()
            self._banner.hide()
            self._banner.deleteLater()
            self._banner = None
            # Remove spacing widget
            while self._banner_slot.count():
                item = self._banner_slot.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def _on_autostart_trigger(self, vmid: str):
        vm = next((v for v in self._vms if v.vmid == vmid), None)
        if vm:
            self._on_quick_start(vmid, vm.name)

    # ── Launch actions ────────────────────────────────────────────────────────

    def _on_quick_start(self, vmid: str, name: str):
        dlg = LaunchDialog(vmid, name, mode="quick", start_after=True, parent=self)
        dlg.exec_()
        self.refresh()

    def _on_plain_start(self, vmid: str, name: str):
        dlg = LaunchDialog(vmid, name, mode="none", start_after=True, parent=self)
        dlg.exec_()
        self.refresh()

    def _on_stop(self, vmid: str, name: str):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Stop VM",
            f"Stop VM {vmid} ({name})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            ok, msg = backend.stop_vm(vmid)
            if not ok:
                QMessageBox.warning(self, "Error", f"Could not stop VM:\n{msg}")
            self.refresh()
