from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QDialog

from network_monitor.ui.views.monitor_view import MonitorView
from network_monitor.ui.dialogs.settings.dialog import SettingsDialog, MonitorConfig


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Network Monitor")

        self.monitor_view = MonitorView(self)
        self.setCentralWidget(self.monitor_view)
        self.setFixedSize(300, 350)

        self.monitor_view.settings_requested.connect(self.open_settings)


    def open_settings(self) -> None:
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = MonitorConfig.load()
            self.monitor_view.apply_config(new_config)


    def closeEvent(self, event) -> None:
        self.monitor_view.shutdown()
        super().closeEvent(event)
