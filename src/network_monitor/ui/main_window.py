from __future__ import annotations

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
        QMainWindow, 
        QMessageBox, 
        QStyle, 
        QToolBar, 
        QWidget, 
        QSizePolicy,
)

from network_monitor.ui.monitor_view import MonitorView
from network_monitor.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Network Monitor")

        self.monitor_view = MonitorView(self)
        self.setCentralWidget(self.monitor_view)

        self._add_toolbar()


    def _add_toolbar(self) -> None:
        main_tool_bar = QToolBar("Main Toolbar", self)
        main_tool_bar.setMovable(False)
        self.addToolBar(main_tool_bar)

        settings_icon = QIcon.fromTheme("preferences-system")
        if settings_icon.isNull():
            settings_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)

        settings_action = QAction(settings_icon, "Settings", self)
        settings_action.setToolTip("Settings")
        settings_action.triggered.connect(self.open_settings)

        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        main_tool_bar.addWidget(right_spacer)
        main_tool_bar.addAction(settings_action)


    def open_settings(self) -> None:
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            new_config = settings_dialog.current_config()
            self.monitor_view.apply_config(new_config)


    def closeEvent(self, event) -> None:
        self.monitor_view.shutdown()
        super().closeEvent(event)
