from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout

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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        self.monitor_state = MonitorState(server="1.1.1.1", port=443)
        self.monitor_state.start()

        layout = QGridLayout(self)

        self.status_label = QLabel("Status: ...")
        self.server_label = QLabel(f"Server: {self.monitor_state.server}:{self.monitor_state.port}")
        self.latency_label = QLabel("Latency (ms): -")
        self.disconnects_label = QLabel("Disconnects: 0")
        self.total_uptime_label = QLabel("Total uptime: 00:00:00")
        self.total_downtime_label = QLabel("Total downtime: 00:00:00")
        self.current_phase_label = QLabel("Current phase: ...")

        labels_in_order = [
            self.status_label,
            self.server_label,
            self.latency_label,
            self.disconnects_label,
            self.total_uptime_label,
            self.total_downtime_label,
            self.current_phase_label,
        ]

        for row, label in enumerate(labels_in_order):
            layout.addWidget(label, row, 0)

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


    def on_check_result(self, result_object: object) -> None:
        check_result = result_object
        assert isinstance(check_result, CheckResult)

        self.monitor_state.apply(check_result)
        self.refresh_labels()


    def refresh_labels(self) -> None:
        last_status = self.monitor_state.last_status_ok

        if last_status is None:
            self.status_label.setText("Status: ...")
        else:
            self.status_label.setText(f"Status: {'UP' if last_status else 'DOWN'}")

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


    def shutdown(self) -> None:
        self.ui_refresh_timer.stop()
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)
