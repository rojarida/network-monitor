from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QDialog

from network_monitor.persistence import SettingsStore
from network_monitor.core.models import SettingsData
from network_monitor.ui.themes import ThemeManager
from network_monitor.ui.views import MonitorView
from network_monitor.ui.dialogs.settings import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore, theme_manager: ThemeManager) -> None:
        super().__init__()
        self.monitor_view = MonitorView(self)

        self._settings_store = settings_store
        self._theme_manager = theme_manager

        self.setWindowTitle("Network Monitor")
        self.setCentralWidget(self.monitor_view)
        self.setFixedSize(300, 355)

        # Apply system theme at startup
        self._theme_manager.apply_system_theme()
        self._sync_theme_button()

        # Load settings once at startup and apply to the view
        settings: SettingsData = self._settings_store.load_settings()
        self.monitor_view.apply_settings(settings)

        self.monitor_view.settings_requested.connect(self.open_settings)
        self.monitor_view.theme_toggle_requested.connect(self.toggle_theme)

    def open_settings(self) -> None:
        settings_dialog = SettingsDialog(settings_store=self._settings_store, parent=self)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            settings: SettingsData = self._settings_store.load_settings()
            self.monitor_view.apply_settings(settings)

    def _sync_theme_button(self) -> None:
        current = self._theme_manager.effective_theme()
        target = "light" if current == "dark" else "dark"

        self.monitor_view.set_theme_toggle_target(target)

    def toggle_theme(self) -> None:
        self._theme_manager.toggle_theme()
        self._sync_theme_button()

    def closeEvent(self, event) -> None:
        self.monitor_view.shutdown()
        super().closeEvent(event)
