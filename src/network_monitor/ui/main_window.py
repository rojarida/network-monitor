from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QDialog

from network_monitor.persistence.settings_store import SettingsData, SettingsStore
from network_monitor.ui.views.monitor_view import MonitorView
from network_monitor.ui.dialogs.settings.dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self.setWindowTitle("Network Monitor")

        self._settings_store = settings_store

        self.monitor_view = MonitorView(self)
        self.setCentralWidget(self.monitor_view)
        self.setFixedSize(300, 350)

        # Load settings once at startup and apply to the view
        settings: SettingsData = self._settings_store.load_settings()
        self.monitor_view.apply_settings(settings)

        self.monitor_view.settings_requested.connect(self.open_settings)

    def open_settings(self) -> None:
        settings_dialog = SettingsDialog(settings_store=self._settings_store, parent=self)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            settings: SettingsData = self._settings_store.load_settings()
            self.monitor_view.apply_settings(settings)

    def closeEvent(self, event) -> None:
        self.monitor_view.shutdown()
        super().closeEvent(event)
