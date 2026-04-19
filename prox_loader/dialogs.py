"""
dialogs.py — Modal dialogs used across the application.
"""

from typing import List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import backend
from .workers import LaunchWorker


# ── Launch dialog ─────────────────────────────────────────────────────────────

class LaunchDialog(QDialog):
    """
    Shows a log stream while LaunchWorker applies passthrough and starts the VM.
    """

    def __init__(
        self,
        vmid: str,
        name: str,
        mode: str,
        gpus: Optional[List[backend.PCIDevice]] = None,
        include_audio: bool = True,
        usb_auto: bool = True,
        usbs: Optional[List[backend.USBDevice]] = None,
        start_after: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Launching — {name}")
        self.setMinimumSize(620, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel(f"VM {vmid}  —  {name}")
        title.setObjectName("lbl_title")
        layout.addWidget(title)

        sub = QLabel("Applying configuration and starting…")
        sub.setObjectName("lbl_subtitle")
        layout.addWidget(sub)

        # Log output
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(220)
        layout.addWidget(self._log, 1)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)   # indeterminate while running
        layout.addWidget(self._progress)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_close = QPushButton("Close")
        self._btn_close.setObjectName("btn_primary")
        self._btn_close.setFocusPolicy(Qt.TabFocus)
        self._btn_close.setEnabled(False)
        self._btn_close.clicked.connect(self.accept)
        btn_row.addWidget(self._btn_close)
        layout.addLayout(btn_row)

        # Start worker
        self._worker = LaunchWorker(
            vmid, name, mode,
            gpus=gpus,
            include_audio=include_audio,
            usb_auto=usb_auto,
            usbs=usbs,
            start_after=start_after,
            parent=self,
        )
        self._worker.log_line.connect(self._append)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _append(self, html: str):
        self._log.append(html)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_finished(self, ok: bool, _msg: str):
        self._progress.setRange(0, 1)
        self._progress.setValue(1)
        if ok:
            self._progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #a6e3a1; border-radius: 5px; }"
            )
        else:
            self._progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #f38ba8; border-radius: 5px; }"
            )
        self._btn_close.setEnabled(True)

    def closeEvent(self, event):
        # Don't close while the worker is still running
        if self._worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)


# ── VM picker dialog ──────────────────────────────────────────────────────────

class VMPickerDialog(QDialog):
    """Simple dialog to pick one VM from the list (for disk moves etc.)."""

    def __init__(self, vms: List[backend.VMInfo], title: str = "Select VM", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(340)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.selected_vm: Optional[backend.VMInfo] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        lbl = QLabel(title)
        lbl.setObjectName("lbl_title")
        layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setFocusPolicy(Qt.StrongFocus)
        for vm in vms:
            item = QListWidgetItem(f"  {vm.vmid}    {vm.name}    {vm.status}")
            item.setData(Qt.UserRole, vm)
            self._list.addItem(item)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setFocusPolicy(Qt.TabFocus)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Select")
        btn_ok.setObjectName("btn_primary")
        btn_ok.setFocusPolicy(Qt.TabFocus)
        btn_ok.clicked.connect(self._accept)

        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

        self._list.itemDoubleClicked.connect(self._accept)

    def _accept(self):
        item = self._list.currentItem()
        if item:
            self.selected_vm = item.data(Qt.UserRole)
            self.accept()
