"""
panels/autostart.py — Configure which VM launches automatically at boot.
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from .. import backend
from .. import config as cfg


def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    return f


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("lbl_section")
    return lbl


class AutostartPanel(QWidget):
    """Configure and save the autostart VM + countdown timeout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vms: list = []
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._update_preview)
        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def focus_first(self):
        self._vm_combo.setFocus()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 30, 36, 30)
        root.setSpacing(0)

        # Header
        title = QLabel("Autostart Settings")
        title.setObjectName("lbl_title")
        root.addWidget(title)
        root.addSpacing(4)

        sub = QLabel(
            "Choose a VM to launch automatically at boot, with an optional countdown delay"
        )
        sub.setObjectName("lbl_subtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)
        root.addSpacing(32)

        # ── VM selector ────────────────────────────────────────
        root.addWidget(_section_label("Default VM"))
        root.addSpacing(10)

        vm_row = QHBoxLayout()
        self._vm_combo = QComboBox()
        self._vm_combo.setMinimumWidth(300)
        self._vm_combo.setFocusPolicy(Qt.StrongFocus)
        self._vm_combo.currentIndexChanged.connect(self._on_setting_changed)
        vm_row.addWidget(self._vm_combo)

        btn_none = QPushButton("Clear")
        btn_none.setObjectName("btn_secondary")
        btn_none.setFocusPolicy(Qt.TabFocus)
        btn_none.setToolTip("Disable autostart")
        btn_none.clicked.connect(self._clear_autostart)
        vm_row.addWidget(btn_none)
        vm_row.addStretch()
        root.addLayout(vm_row)
        root.addSpacing(28)

        root.addWidget(_divider())
        root.addSpacing(28)

        # ── Timeout slider ─────────────────────────────────────
        root.addWidget(_section_label("Launch Delay"))
        root.addSpacing(10)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(16)

        lbl_0 = QLabel("0 s")
        lbl_0.setStyleSheet("color: #6c7086; background: transparent;")
        slider_row.addWidget(lbl_0)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(60)
        self._slider.setValue(10)
        self._slider.setTickInterval(10)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.setFocusPolicy(Qt.StrongFocus)
        self._slider.valueChanged.connect(self._sync_slider_to_spin)
        slider_row.addWidget(self._slider, 1)

        lbl_60 = QLabel("60 s")
        lbl_60.setStyleSheet("color: #6c7086; background: transparent;")
        slider_row.addWidget(lbl_60)

        self._spin = QSpinBox()
        self._spin.setMinimum(0)
        self._spin.setMaximum(60)
        self._spin.setValue(10)
        self._spin.setSuffix(" sec")
        self._spin.setFocusPolicy(Qt.StrongFocus)
        self._spin.valueChanged.connect(self._sync_spin_to_slider)
        slider_row.addWidget(self._spin)

        root.addLayout(slider_row)
        root.addSpacing(28)

        root.addWidget(_divider())
        root.addSpacing(28)

        # ── Preview box ────────────────────────────────────────
        root.addWidget(_section_label("Preview"))
        root.addSpacing(10)

        self._preview = QFrame()
        self._preview.setObjectName("banner_autostart")
        prev_layout = QHBoxLayout(self._preview)
        prev_layout.setContentsMargins(18, 14, 18, 14)

        icon = QLabel("⚡")
        icon.setStyleSheet("font-size: 20px; background: transparent;")
        prev_layout.addWidget(icon)

        self._preview_lbl = QLabel("No autostart configured.")
        self._preview_lbl.setStyleSheet(
            "color: #89b4fa; font-size: 13px; background: transparent;"
        )
        self._preview_lbl.setWordWrap(True)
        prev_layout.addWidget(self._preview_lbl, 1)

        root.addWidget(self._preview)
        root.addStretch()

        # ── Save / clear row ───────────────────────────────────
        root.addWidget(_divider())
        root.addSpacing(16)

        btn_row = QHBoxLayout()
        self._btn_disable = QPushButton("Disable Autostart")
        self._btn_disable.setObjectName("btn_danger")
        self._btn_disable.setFocusPolicy(Qt.TabFocus)
        self._btn_disable.clicked.connect(self._disable_autostart)
        btn_row.addWidget(self._btn_disable)

        btn_row.addStretch()

        self._btn_save = QPushButton("Save Settings")
        self._btn_save.setObjectName("btn_primary")
        self._btn_save.setFocusPolicy(Qt.TabFocus)
        self._btn_save.clicked.connect(self._save)
        btn_row.addWidget(self._btn_save)

        root.addLayout(btn_row)

        self._populate_vm_combo()

    # ── VM combo ──────────────────────────────────────────────────────────────

    def _populate_vm_combo(self):
        current_cfg = cfg.load()
        saved_id = current_cfg.get("vm_id", "")
        saved_timeout = current_cfg.get("timeout", 10)

        self._vms = backend.get_vm_list()

        self._vm_combo.blockSignals(True)
        self._vm_combo.clear()
        self._vm_combo.addItem("— none (disabled) —", "")

        for vm in self._vms:
            self._vm_combo.addItem(f"{vm.name}  ({vm.vmid})", vm.vmid)
            if vm.vmid == saved_id:
                self._vm_combo.setCurrentIndex(self._vm_combo.count() - 1)

        self._slider.blockSignals(True)
        self._spin.blockSignals(True)
        self._slider.setValue(saved_timeout)
        self._spin.setValue(saved_timeout)
        self._slider.blockSignals(False)
        self._spin.blockSignals(False)

        self._vm_combo.blockSignals(False)
        self._update_preview()

    # ── Sync slider ↔ spin ────────────────────────────────────────────────────

    def _sync_slider_to_spin(self, value: int):
        self._spin.blockSignals(True)
        self._spin.setValue(value)
        self._spin.blockSignals(False)
        self._on_setting_changed()

    def _sync_spin_to_slider(self, value: int):
        self._slider.blockSignals(True)
        self._slider.setValue(value)
        self._slider.blockSignals(False)
        self._on_setting_changed()

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_setting_changed(self):
        self._preview_timer.start(200)   # debounce rapid slider drags

    def _update_preview(self):
        vmid = self._vm_combo.currentData() or ""
        timeout = self._spin.value()

        if not vmid:
            self._preview_lbl.setText("Autostart is disabled — no VM will launch automatically.")
            return

        vm = next((v for v in self._vms if v.vmid == vmid), None)
        name = vm.name if vm else vmid

        if timeout == 0:
            self._preview_lbl.setText(
                f"On next boot, <b>{name}</b> (VM {vmid}) will launch immediately."
            )
        else:
            self._preview_lbl.setText(
                f"On next boot, <b>{name}</b> (VM {vmid}) will launch automatically "
                f"after a <b>{timeout}-second</b> countdown."
            )

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh(self):
        self._populate_vm_combo()

    # ── Save / clear ──────────────────────────────────────────────────────────

    def _save(self):
        vmid = self._vm_combo.currentData() or ""
        timeout = self._spin.value()
        try:
            cfg.save(vmid, timeout)
        except OSError as e:
            QMessageBox.critical(self, "Save Error", f"Could not save config:\n{e}")
            return
        if vmid:
            vm = next((v for v in self._vms if v.vmid == vmid), None)
            name = vm.name if vm else vmid
            QMessageBox.information(
                self, "Saved",
                f"Autostart set: {name} (VM {vmid}), timeout {timeout}s."
            )
        else:
            QMessageBox.information(self, "Saved", "Autostart disabled.")

    def _clear_autostart(self):
        self._vm_combo.setCurrentIndex(0)
        self._update_preview()

    def _disable_autostart(self):
        reply = QMessageBox.question(
            self, "Disable Autostart",
            "Clear autostart configuration?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            cfg.clear()
            self._vm_combo.setCurrentIndex(0)
            self._update_preview()
            QMessageBox.information(self, "Done", "Autostart disabled.")
