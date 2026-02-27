from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from network_monitor.ui import MainWindow
from network_monitor.ui.assets import resources_rc # noqa: F401
from network_monitor.ui.themes import ThemeManager
from network_monitor.persistence import SettingsStore


def main() -> int:
    application = QApplication(sys.argv)
    icon = QIcon.fromTheme("network-monitor")

    if not icon:
        icon = QIcon(":/icons/network-monitor")

    application.setWindowIcon(icon)
    QCoreApplication.setOrganizationName("RomanJay")
    QCoreApplication.setApplicationName("Network Monitor")
    QCoreApplication.setApplicationVersion("0.8.3")

    settings_store = SettingsStore()
    theme_manager = ThemeManager(application)
    theme_manager.enable_live_reload()

    window = MainWindow(settings_store=settings_store, theme_manager=theme_manager)
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
