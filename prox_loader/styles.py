"""
styles.py — Catppuccin Mocha dark theme for the entire application.
"""

STYLESHEET = """
/* ── Base ─────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #1e1e2e;
}
QWidget {
    background-color: transparent;
    color: #cdd6f4;
    font-family: 'Cantarell', 'Segoe UI', 'Noto Sans', Ubuntu, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ───────────────────────────────────────────── */
QWidget#sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}
QLabel#sidebar_logo {
    color: #cba6f7;
    font-size: 17px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 20px 0 12px 0;
}
QPushButton#nav_btn {
    background-color: transparent;
    color: #a6adc8;
    border: none;
    border-radius: 8px;
    padding: 11px 14px;
    text-align: left;
    font-size: 13px;
}
QPushButton#nav_btn:hover {
    background-color: #2a2b3c;
    color: #cdd6f4;
}
QPushButton#nav_btn[active="true"] {
    background-color: #313244;
    color: #cba6f7;
    font-weight: bold;
}
QLabel#sidebar_version {
    color: #45475a;
    font-size: 11px;
    padding: 8px;
}

/* ── Content area ──────────────────────────────────────── */
QWidget#content_area {
    background-color: #1e1e2e;
}

/* ── VM cards ──────────────────────────────────────────── */
QFrame#vm_card {
    background-color: #24273a;
    border: 1px solid #363a4f;
    border-radius: 12px;
}
QFrame#vm_card:hover {
    border-color: #7287fd;
    background-color: #2a2d3e;
}

/* ── Buttons ───────────────────────────────────────────── */
QPushButton#btn_primary {
    background-color: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#btn_primary:hover   { background-color: #d5b8ff; }
QPushButton#btn_primary:pressed { background-color: #b694f0; }
QPushButton#btn_primary:disabled {
    background-color: #45475a;
    color: #6c7086;
}

QPushButton#btn_secondary {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
}
QPushButton#btn_secondary:hover   { background-color: #45475a; border-color: #585b70; }
QPushButton#btn_secondary:pressed { background-color: #3a3d50; }

QPushButton#btn_danger {
    background-color: #f38ba8;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-weight: bold;
}
QPushButton#btn_danger:hover { background-color: #f7aabf; }

QPushButton#btn_small {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px 13px;
    font-size: 12px;
}
QPushButton#btn_small:hover { background-color: #45475a; }

QPushButton#btn_small_primary {
    background-color: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 5px 13px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton#btn_small_primary:hover { background-color: #d5b8ff; }

QPushButton#btn_small_danger {
    background-color: transparent;
    color: #f38ba8;
    border: 1px solid #f38ba8;
    border-radius: 6px;
    padding: 5px 13px;
    font-size: 12px;
}
QPushButton#btn_small_danger:hover { background-color: #3d2030; }

/* ── Labels ────────────────────────────────────────────── */
QLabel#lbl_title {
    font-size: 22px;
    font-weight: bold;
    color: #cba6f7;
}
QLabel#lbl_subtitle {
    font-size: 12px;
    color: #6c7086;
}
QLabel#lbl_section {
    font-size: 10px;
    color: #6c7086;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#lbl_vmid {
    background-color: #1e3a5f;
    color: #89b4fa;
    border-radius: 6px;
    padding: 2px 9px;
    font-size: 12px;
    font-weight: bold;
    font-family: monospace;
}
QLabel#lbl_status_running { color: #a6e3a1; font-size: 12px; font-weight: bold; }
QLabel#lbl_status_stopped { color: #f38ba8; font-size: 12px; }
QLabel#lbl_status_paused  { color: #f9e2af; font-size: 12px; }
QLabel#lbl_info {
    color: #89b4fa;
    font-size: 12px;
    padding: 6px 12px;
    background-color: #1e2d3d;
    border: 1px solid #2a4a6b;
    border-radius: 6px;
}

/* ── Banner ────────────────────────────────────────────── */
QFrame#banner_autostart {
    background-color: #1a2f4a;
    border: 1px solid #89b4fa;
    border-radius: 10px;
}

/* ── Checkbox ──────────────────────────────────────────── */
QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
    padding: 3px 0;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 2px solid #585b70;
    border-radius: 4px;
    background: #313244;
}
QCheckBox::indicator:hover   { border-color: #cba6f7; }
QCheckBox::indicator:checked {
    background-color: #cba6f7;
    border-color: #cba6f7;
}
QCheckBox:disabled { color: #45475a; }
QCheckBox::indicator:disabled { border-color: #45475a; background: #24273a; }

/* ── ScrollArea ────────────────────────────────────────── */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

/* ── SpinBox ───────────────────────────────────────────── */
QSpinBox {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #cdd6f4;
    padding: 7px 12px;
    font-size: 14px;
    min-width: 80px;
}
QSpinBox:hover { border-color: #cba6f7; }
QSpinBox::up-button, QSpinBox::down-button {
    background: #45475a;
    border: none;
    border-radius: 3px;
    width: 20px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #585b70; }

/* ── Slider ────────────────────────────────────────────── */
QSlider::groove:horizontal {
    background: #313244;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #cba6f7;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #cba6f7);
    border-radius: 3px;
}

/* ── ComboBox ──────────────────────────────────────────── */
QComboBox {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #cdd6f4;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 200px;
}
QComboBox:hover { border-color: #cba6f7; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    color: #cdd6f4;
    selection-background-color: #45475a;
    outline: none;
    padding: 4px;
}

/* ── ListWidget ────────────────────────────────────────── */
QListWidget {
    background: #24273a;
    border: 1px solid #363a4f;
    border-radius: 10px;
    color: #cdd6f4;
    outline: none;
    padding: 4px;
}
QListWidget::item {
    padding: 9px 12px;
    border-radius: 6px;
    margin: 1px 0;
}
QListWidget::item:selected { background: #363a4f; color: #cba6f7; }
QListWidget::item:hover    { background: #2e3147; }

/* ── TextEdit (log) ────────────────────────────────────── */
QTextEdit {
    background: #181825;
    border: 1px solid #2e2e3e;
    border-radius: 10px;
    color: #cdd6f4;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    padding: 8px;
}

/* ── ProgressBar ───────────────────────────────────────── */
QProgressBar {
    background: #313244;
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    font-size: 10px;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89b4fa, stop:1 #cba6f7);
    border-radius: 5px;
}

/* ── Dividers ──────────────────────────────────────────── */
QFrame[frameShape="4"] { background-color: #313244; border: none; max-height: 1px; }
QFrame[frameShape="5"] { background-color: #313244; border: none; max-width:  1px; }

/* ── Tooltip ───────────────────────────────────────────── */
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ── Message/Dialog boxes ──────────────────────────────── */
QMessageBox, QDialog {
    background-color: #1e1e2e;
}
QMessageBox QLabel, QDialog QLabel { color: #cdd6f4; }
QMessageBox QPushButton {
    background-color: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    min-width: 80px;
}
QMessageBox QPushButton:hover { background-color: #d5b8ff; }

/* ── Line edit ─────────────────────────────────────────── */
QLineEdit {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #cdd6f4;
    padding: 8px 12px;
    font-size: 13px;
}
QLineEdit:hover  { border-color: #cba6f7; }
QLineEdit:focus  { border-color: #cba6f7; outline: none; }
"""
