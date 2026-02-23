from __future__ import annotations

import sys
from importlib import resources
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from network_monitor.ui.main_window import MainWindow
from network_monitor.ui.themes.manager import ThemeManager


def load_stylesheet(theme: str | None = None) -> str:
    themes = resources.files("network_monitor.ui.themes")
    base = themes.joinpath("base.qss").read_text(encoding="utf-8")

    if not theme:
        return base

    overlay = themes.joinpath(f"{theme}.qss").read_text(encoding="utf-8")
    return f"{base}\n\n /* ---- Theme: {theme} ---- */\n\n{overlay}\n"


def main() -> int:
    application = QApplication(sys.argv)
    QCoreApplication.setOrganizationName("RomanJay")
    QCoreApplication.setApplicationName("Network Monitor")

    theme_manager = ThemeManager(application)
    theme_manager.apply_theme("dark")
    theme_manager.enable_live_reload()

    # application.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
