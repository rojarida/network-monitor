from __future__ import annotations

import sys
from importlib import resources

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from network_monitor.ui import MainWindow
from network_monitor.ui.themes import ThemeManager
from network_monitor.persistence import SettingsStore


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

    settings_store = SettingsStore()

    window = MainWindow(settings_store=settings_store)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
