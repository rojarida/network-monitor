from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

from network_monitor.ui.monitor_view import MonitorView
from network_monitor.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Network Monitor")

        self.monitor_view = MonitorView(self)
        self.setCentralWidget(self.monitor_view)
        self.setMinimumSize(240, 310)

        self.monitor_view.settings_requested.connect(self.open_settings)


    def open_settings(self) -> None:
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            new_config = settings_dialog.current_config()
            self.monitor_view.apply_config(new_config)


    def closeEvent(self, event) -> None:
        self.monitor_view.shutdown()
        super().closeEvent(event)
