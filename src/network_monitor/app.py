from __future__ import annotations

import sys
from importlib import resources
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from network_monitor.ui.main_window import MainWindow


def load_stylesheet() -> str:
    stylesheet_path = resources.files("network_monitor.ui.themes").joinpath("base.qss")
    return stylesheet_path.read_text(encoding="utf-8")


def main() -> int:
    application = QApplication(sys.argv)
    QCoreApplication.setOrganizationName("RomanJay")
    QCoreApplication.setApplicationName("Network Monitor")
    application.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
