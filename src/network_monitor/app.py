from __future__ import annotations

import sys
from importlib import resources
from PySide6.QtWidgets import QApplication

from network_monitor.ui.main_window import MainWindow


def load_stylesheet() -> str:
    stylesheet_path = resources.files("network_monitor.ui.styles").joinpath("app.qss")
    return stylesheet_path.read_text(encoding="utf-8")


def main() -> None:
    application = QApplication(sys.argv)
    application.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    raise SystemExit(main())
