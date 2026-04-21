"""
main_window.py — Single window with sidebar navigation.
"""

import subprocess
import sys

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .panels.autostart import AutostartPanel
from .panels.disks import DisksPanel
from .panels.passthrough import PassthroughPanel
from .panels.vm_list import VMListPanel


def _quit_to_tty():
    """Exit cleanly: ask openbox to quit gracefully so xinit exits 0,
    service stops without restarting, ExecStopPost restores getty."""
    try:
        subprocess.Popen(["openbox", "--exit"])
    except Exception:
        pass
    sys.exit(0)


# ── Sidebar nav button ─────────────────────────────────────────────────────────

class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.setObjectName("nav_btn")
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(False)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_active(self, active: bool):
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ── Sidebar ────────────────────────────────────────────────────────────────────

class Sidebar(QWidget):
    navigate = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(188)

        self._buttons: list[NavButton] = []
        self._active_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 16)
        layout.setSpacing(4)

        # Logo
        logo = QLabel("PROX\nLOADER")
        logo.setObjectName("sidebar_logo")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)
        layout.addSpacing(8)

        # Navigation items
        nav_items = [
            ("🖥", "Virtual Machines"),
            ("🔌", "Passthrough"),
            ("💾", "Disk Manager"),
            ("⚡", "Autostart"),
        ]
        for i, (icon, label) in enumerate(nav_items):
            btn = NavButton(icon, label)
            btn.setFocusPolicy(Qt.TabFocus)
            btn.clicked.connect(lambda _, idx=i: self._on_click(idx))
            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

        btn_quit = QPushButton("✕  Quit")
        btn_quit.setObjectName("btn_danger")
        btn_quit.setFocusPolicy(Qt.TabFocus)
        btn_quit.clicked.connect(_quit_to_tty)
        layout.addWidget(btn_quit)

        version = QLabel("v1.0.0")
        version.setObjectName("sidebar_version")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        self.set_active(0)

    def _on_click(self, index: int):
        self.set_active(index)
        self.navigate.emit(index)

    def set_active(self, index: int):
        if 0 <= self._active_index < len(self._buttons):
            self._buttons[self._active_index].set_active(False)
        self._active_index = index
        if 0 <= index < len(self._buttons):
            self._buttons[index].set_active(True)


# ── Main window ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prox Loader — VM Boot Manager")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setMinimumSize(920, 620)
        self.resize(1100, 700)

        central = QWidget()
        central.setObjectName("content_area")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(self)
        self._sidebar.navigate.connect(self._navigate)
        root.addWidget(self._sidebar)

        # Stacked content
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_area")
        root.addWidget(self._stack, 1)

        # Panels (must match sidebar order)
        self._vm_list      = VMListPanel()
        self._passthrough  = PassthroughPanel()
        self._disks        = DisksPanel()
        self._autostart    = AutostartPanel()

        for panel in (self._vm_list, self._passthrough, self._disks, self._autostart):
            self._stack.addWidget(panel)

        # Cross-panel navigation
        self._vm_list.vm_selected_for_passthrough.connect(self._on_vm_to_passthrough)
        self._vm_list.vm_selected_for_disks.connect(self._on_vm_to_disks)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(_quit_to_tty)
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)

        # Initial load
        self._vm_list.refresh()

        # Set keyboard focus after the window is shown
        QTimer.singleShot(200, lambda: self._sidebar._buttons[0].setFocus())

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _navigate(self, index: int):
        panel = self._stack.widget(index)
        # Refresh on switch for data panels
        if hasattr(panel, "refresh") and index != 0:
            panel.refresh()
        self._stack.setCurrentIndex(index)
        self._sidebar.set_active(index)
        # Move keyboard focus into the new panel
        if hasattr(panel, "focus_first"):
            QTimer.singleShot(50, panel.focus_first)

    def _on_vm_to_passthrough(self, vmid: str, name: str):
        self._passthrough.set_vm(vmid)
        self._passthrough.refresh()
        self._navigate(1)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        # Q returns to TTY when focus is NOT in a text-input widget
        if event.key() == Qt.Key_Q:
            focused = QApplication.focusWidget()
            if not isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)):
                _quit_to_tty()
                return
        super().keyPressEvent(event)

    def _on_vm_to_disks(self, vmid: str, name: str):
        self._disks.set_vm(vmid)
        self._disks.refresh()
        self._navigate(2)
