from __future__ import annotations

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QWidget, 
    QLabel, 
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

    if seconds <= 0:
        return "-"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


class MonitorView(QWidget):
    settings_requested = Signal()


    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("monitor_view")

        startup_config = MonitorConfig.load()
        self.monitor_state = MonitorState(
            server=startup_config.server,
            port=startup_config.port,
        )
        self.monitor_state.start()

        root_layout = QVBoxLayout(self)
        root_layout.setObjectName("root_layout")
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Statistic container
        stats_container = QWidget()
        stats_container.setObjectName("stats_container")
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(8, 8, 8, 0)

        # Status
        self.status_label = QLabel("...")
        self.status_label.setObjectName("status_label")
        self.status_label.setProperty("status", "unknown")
        self.status_label.setProperty("kind", "pill")

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(0)
        status_row.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        stats_layout.addLayout(status_row)

        # Separator between status and stats
        stats_layout.addWidget(self._make_separator("separator_top"))

        # Metric rows
        server_row, self.server_value = self._make_metric_row("Server")
        self.server_value.setProperty("metric", "server")

        latency_row, self.latency_value = self._make_metric_row("Latency")
        self.latency_value.setProperty("metric", "latency")

        disconnects_row, self.disconnects_value = self._make_metric_row("Disconnects")
        self.disconnects_value.setProperty("metric", "disconnects")

        uptime_row, self.total_uptime_value = self._make_metric_row("Total uptime")
        self.total_uptime_value.setProperty("metric", "uptime")

        downtime_row, self.total_downtime_value = self._make_metric_row("Total downtime")
        self.total_downtime_value.setProperty("metric", "downtime")

        phase_row, self.current_phase_value = self._make_metric_row("Current phase")
        self.current_phase_value.setProperty("metric", "phase")

        stats_layout.addWidget(server_row)
        stats_layout.addWidget(latency_row)
        stats_layout.addWidget(disconnects_row)
        stats_layout.addWidget(uptime_row)
        stats_layout.addWidget(downtime_row)
        stats_layout.addWidget(phase_row)
        stats_layout.addSpacing(8)

        root_layout.addWidget(stats_container)

        # Separator between current phase and settings button
        root_layout.addWidget(self._make_inset_separator_row("separator_bottom", inset=8))

        # Settings bar
        settings_bar = QFrame()
        settings_bar.setObjectName("settings_bar")
        settings_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        settings_bar_layout = QHBoxLayout(settings_bar)
        settings_bar_layout.setContentsMargins(8, 4, 8, 0)
        settings_bar_layout.setSpacing(8)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settings_button")
        self.settings_button.setProperty("kind", "pill")
        self.settings_button.clicked.connect(self.settings_requested.emit)

        settings_bar_layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        root_layout.addWidget(settings_bar)

        # Monitor thread and UI refresh
        self.monitor_thread = MonitorThread(
            server=startup_config.server,
            port=startup_config.port,
            interval_s=startup_config.interval_s,
            timeout_s=startup_config.timeout_s,
        )

        self.monitor_thread.result.connect(self.on_check_result)
        self.monitor_thread.start()

        self.ui_refresh_timer = QTimer(self)
        self.ui_refresh_timer.setInterval(250)
        self.ui_refresh_timer.timeout.connect(self.refresh_labels)
        self.ui_refresh_timer.start()


    def _make_separator(self, name: str) -> QFrame:
        line = QFrame()
        line.setObjectName(name)
        line.setFrameShape(QFrame.Shape.NoFrame)
        line.setFixedHeight(1)
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        return line


    def _make_inset_separator_row(self, name: str, inset: int = 8) -> QWidget:
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(inset, 0, inset, 0)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addWidget(self._make_separator(name))

        return wrapper


    def _make_metric_row(self, key_text: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        row.setObjectName("metric_row")
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        key_label = QLabel(key_text)
        key_label.setObjectName("metric_key")

        value_label = QLabel("-")
        value_label.setObjectName("metric_value")
        value_label.setProperty("kind", "pill")

        layout.addWidget(key_label)
        layout.addStretch(1)
        layout.addWidget(value_label)

        return row, value_label


    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def on_check_result(self, result_object: object) -> None:
        if not isinstance(result_object, CheckResult):
            return
        self.monitor_state.apply(result_object)
        self.refresh_labels()


    def refresh_labels(self) -> None:
        last_status = self.monitor_state.last_status_ok

        if last_status is None:
            self.status_label.setText("...")
            new_status = "unknown"
        else:
            self.status_label.setText('Online' if last_status else 'Offline')
            new_status = "online" if last_status else "offline"

        if self.property("status") != new_status:
            self.setProperty("status", new_status)
            self._repolish(self)
            self._repolish(self.total_downtime_value)
            self._repolish(self.current_phase_value)
            self._repolish(self.latency_value)
            self._repolish(self.disconnects_value)

        if self.status_label.property("status") != new_status:
            self.status_label.setProperty("status", new_status)
            self._repolish(self.status_label)

        # Server
        self.server_value.setText(f"{self.monitor_state.server}:{self.monitor_state.port}")

        # Latency
        latency_ms = self.monitor_state.last_latency_ms

        if latency_ms is None:
            self.latency_value.setText("-")
            latency_level = "na"
        else:
            rounded_latency_ms = round(latency_ms)
            self.latency_value.setText(f"{rounded_latency_ms} ms")

            if rounded_latency_ms < 100:
                latency_level = "good"
            elif rounded_latency_ms < 200:
                latency_level = "warn"
            else:
                latency_level = "bad"

        if self.latency_value.property("level") != latency_level:
            self.latency_value.setProperty("level", latency_level)
            self._repolish(self.latency_value)

        # Disconnects
        self.disconnects_value.setText(str(self.monitor_state.disconnects))
        disconnects = self.monitor_state.disconnects

        # Track disconnect count and create a property level
        if disconnects == 0:
            disconnects_level = "good"
        elif disconnects < 10:
            disconnects_level = "warn"
        else:
            disconnects_level = "bad"

        if self.disconnects_value.property("level") != disconnects_level:
            self.disconnects_value.setProperty("level", disconnects_level)
            self._repolish(self.disconnects_value)

        # Total uptime/downtime
        total_uptime_seconds, total_downtime_seconds = self.monitor_state.totals_including_current_phase()
        self.total_uptime_value.setText(format_seconds_as_hhmmss(total_uptime_seconds))
        self.total_downtime_value.setText(format_seconds_as_hhmmss(total_downtime_seconds))

        # Phase
        current_phase_seconds = self.monitor_state.current_phase_seconds()
        self.current_phase_value.setText(format_seconds_as_hhmmss(current_phase_seconds))


    def apply_config(self, config: MonitorConfig) -> None:
        # Stop current monitor
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)

        self.monitor_state.server = config.server
        self.monitor_state.port = config.port
        self.monitor_state.endpoint_changed()

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
        self.server_value.setText(f"Server: {config.server}:{config.port}")
        self.status_label.setText("...")
        self.status_label.setProperty("status", "unknown")
        self._repolish(self.status_label)
        self.refresh_labels()


    def shutdown(self) -> None:
        self.ui_refresh_timer.stop()
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)
