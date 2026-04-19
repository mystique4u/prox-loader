"""
__main__.py — Entry point: python3 -m prox_loader
"""

import os
import sys


def main():
    # Root check (Proxmox qm/config operations require root)
    if os.geteuid() != 0:
        print(
            "\033[1;33mWarning: prox-loader is not running as root.\033[0m\n"
            "VM operations (qm start/stop, config edits) will fail.\n"
            "Launch with:  sudo python3 -m prox_loader\n"
        )
        # Allow proceeding for UI development/preview

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from .styles import STYLESHEET
    from .main_window import MainWindow

    # HiDPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Prox Loader")
    app.setOrganizationName("prox-loader")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.showFullScreen()
    window.activateWindow()
    window.raise_()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
