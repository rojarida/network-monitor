from __future__ import annotations

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QWidget, 
    QLabel, 
    QGridLayout,
    QVBoxLayout,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
)

from network_monitor.monitor.thread import MonitorThread
from network_monitor.state import MonitorState, CheckResult
from network_monitor.ui.settings_dialog import MonitorConfig


def format_seconds_as_hhmmss(seconds: float) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


class MonitorView(QWidget):
    settings_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("monitor_view")

        self.monitor_state = MonitorState(server="1.1.1.1", port=443)
        self.monitor_state.start()

        root_layout = QVBoxLayout(self)
        root_layout.setObjectName("root_layout")

        grid_layout = QGridLayout()
        grid_layout.setObjectName("stats_grid")
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setContentsMargins(8, 8, 8, 8)
        grid_layout.setVerticalSpacing(8)
        root_layout.addLayout(grid_layout)

        self.status_label = QLabel("...")
        self.status_label.setObjectName("status_label")
        self.status_label.setProperty("status", "unknown")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(28)
        self.status_label.setMinimumWidth(110)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        status_separator = QFrame()
        status_separator.setObjectName("separator_line")
        status_separator.setFrameShape(QFrame.Shape.NoFrame)

        self.server_label = QLabel(f"Server: {self.monitor_state.server}:{self.monitor_state.port}")
        self.server_label.setObjectName("server_label")

        self.latency_label = QLabel("Latency (ms): -")
        self.latency_label.setObjectName("latency_label")

        self.disconnects_label = QLabel("Disconnects: 0")
        self.disconnects_label.setObjectName("disconnects_label")

        self.total_uptime_label = QLabel("Total uptime: 00:00:00")
        self.total_uptime_label.setObjectName("total_uptime_label")

        self.total_downtime_label = QLabel("Total downtime: 00:00:00")
        self.total_downtime_label.setObjectName("total_downtime_label")

        self.current_phase_label = QLabel("Current phase: ...")
        self.current_phase_label.setObjectName("current_phase_label")

        other_labels = [
            self.server_label,
            self.latency_label,
            self.disconnects_label,
            self.total_uptime_label,
            self.total_downtime_label,
            self.current_phase_label,
        ]

        grid_layout.addWidget(self.status_label, 0, 0, alignment=Qt.AlignmentFlag.AlignHCenter)
        grid_layout.setRowMinimumHeight(1, 6)
        grid_layout.addWidget(status_separator, 2, 0)

        for row, label in enumerate(other_labels, start=3):
            grid_layout.addWidget(label, row, 0)


        root_layout.addStretch(1)

        # Separator between Current Phase and Settings button
        separator_line = QFrame()
        separator_line.setObjectName("separator_line")
        separator_line.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(separator_line)

        bottom_bar = QFrame()
        bottom_bar.setObjectName("bottom_bar")
        bottom_bar_layout = QHBoxLayout(bottom_bar)
        bottom_bar_layout.setContentsMargins(8, 8, 8, 8)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settings_button")
        self.settings_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.settings_button.clicked.connect(self.settings_requested.emit)

        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(self.settings_button)
        bottom_bar_layout.addStretch(1)

        root_layout.addWidget(bottom_bar)

        self.monitor_thread = MonitorThread(
            server=self.monitor_state.server,
            port=self.monitor_state.port,
            interval_s=1.0,
            timeout_s=1.0,
        )

        self.monitor_thread.result.connect(self.on_check_result)
        self.monitor_thread.start()

        self.ui_refresh_timer = QTimer(self)
        self.ui_refresh_timer.setInterval(250)
        self.ui_refresh_timer.timeout.connect(self.refresh_labels)
        self.ui_refresh_timer.start()


    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def on_check_result(self, result_object: object) -> None:
        check_result = result_object
        assert isinstance(check_result, CheckResult)

        self.monitor_state.apply(check_result)


    def refresh_labels(self) -> None:
        last_status = self.monitor_state.last_status_ok

        if last_status is None:
            self.status_label.setText("...")
            new_status = "unknown"
        else:
            self.status_label.setText('UP' if last_status else 'DOWN')
            new_status = "up" if last_status else "down"

        if self.status_label.property("status") != new_status:
            self.status_label.setProperty("status", new_status)
            self._repolish(self.status_label)

        if self.monitor_state.last_latency_ms is None:
            self.latency_label.setText("Latency: - ms")
        else:
            self.latency_label.setText(f"Latency: {round(self.monitor_state.last_latency_ms)} ms")

        self.disconnects_label.setText(f"Disconnects: {self.monitor_state.disconnects}")

        total_uptime_seconds, total_downtime_seconds = self.monitor_state.totals_including_current_phase()

        self.total_uptime_label.setText(
            f"Total uptime: {format_seconds_as_hhmmss(total_uptime_seconds)}"
        )

        self.total_downtime_label.setText(
            f"Total downtime: {format_seconds_as_hhmmss(total_downtime_seconds)}"
        )

        current_phase_seconds = self.monitor_state.current_phase_seconds()
        self.current_phase_label.setText(
            f"Current phase: {format_seconds_as_hhmmss(current_phase_seconds)}"
        )


    def apply_config(self, config: MonitorConfig) -> None:
        # Stop current monitor
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)

        # Reset state
        self.monitor_state = MonitorState(server=config.server, port=config.port)
        self.monitor_state.start()

        # Restart thread with new configuration
        self.monitor_thread = MonitorThread(
            server=config.server,
            port=config.port,
            interval_s=config.interval_s,
            timeout_s=config.timeout_s,
        )

        self.monitor_thread.result.connect(self.on_check_result)
        self.monitor_thread.start()

        # Update label
        self.server_label.setText(f"Server: {config.server}:{config.port}")
        self.status_label.setText("...")
        self.status_label.setProperty("status", "unknown")
        self._repolish(self.status_label)
        self.refresh_labels()


    def shutdown(self) -> None:
        self.ui_refresh_timer.stop()
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)
