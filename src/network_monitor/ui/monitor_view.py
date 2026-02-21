from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from PySide6.QtGui import QFontMetrics, QPainter, QPalette
from PySide6.QtCore import QTimer, Signal, Qt, QSettings
from PySide6.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOption,
)

from network_monitor.monitor.thread import MonitorThread
from network_monitor.state import MonitorState, CheckResult
from network_monitor.ui.settings_dialog import MonitorConfig
from network_monitor.ui.tooltips import (
    METRIC_TOOLTIPS,
    apply_tooltip,
    status_value_tooltip
)


def format_seconds_as_hhmmss(seconds: float) -> str:
    seconds = int(seconds)

    if seconds <= 0:
        return "-"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


class ElidedLabel(QLabel):
    def __init__(
        self,
        parent: QWidget | None = None,
        elide_mode: Qt.TextElideMode = Qt.TextElideMode.ElideMiddle,
    ) -> None:
        super().__init__(parent)
        self._full_text = ""
        self._elide_mode = elide_mode
        self.setWordWrap(False)


    def setText(self, text: str) -> None:
        super().setText(text)
        self.setToolTip(text)
        self.update()


    def paintEvent(self, event) -> None:
        option = QStyleOption()
        option.initFrom(self)

        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, option, painter, self)

        rect = self.contentsRect()
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), self._elide_mode, rect.width())

        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        painter.drawText(rect, int(self.alignment()), elided)


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

        # Statistic container
        stats_container = QWidget()
        stats_container.setObjectName("stats_container")
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(8, 6, 8, 6)

        # Labels and metrics
        status_row, _status_key, status_pill = self._make_metric_row(
            "Status",
            center_value=True,
            value_object_name="status_label")
        self.status_label = status_pill
        self.status_label.setText("...")
        self.status_label.setProperty("status", "unknown")

        server_row, _server_label, self.server_value = self._make_metric_row("Server")
        self.server_value.setProperty("metric", "server")

        phase_row, self.phase_label, self.phase_value = self._make_metric_row("Current phase")
        self.phase_value.setProperty("metric", "phase")

        latency_row, _latency_label, self.latency_value = self._make_metric_row("Latency")
        self.latency_value.setProperty("metric", "latency")

        disconnects_row, _disconnects_label, self.disconnects_value = self._make_metric_row("Disconnects")
        self.disconnects_value.setProperty("metric", "disconnects")

        uptime_row, _uptime_label, self.total_uptime_value = self._make_metric_row("Total uptime")
        self.total_uptime_value.setProperty("metric", "uptime")

        downtime_row, _downtime_label, self.total_downtime_value = self._make_metric_row("Total downtime")
        self.total_downtime_value.setProperty("metric", "downtime")

        stats_layout.addWidget(status_row)
        stats_layout.addWidget(self._make_separator("separator_top"))
        stats_layout.addWidget(server_row)
        stats_layout.addWidget(self._make_separator("separator_top"))

        stats_layout.addWidget(phase_row)
        stats_layout.addWidget(latency_row)
        stats_layout.addWidget(disconnects_row)
        stats_layout.addWidget(self._make_separator("separator_middle"))
        stats_layout.addWidget(uptime_row)
        stats_layout.addWidget(downtime_row)

        # Separator between downtime and settings button
        stats_layout.addWidget(self._make_separator("separator_bottom"))

        # Settings bar
        settings_bar = QFrame()
        settings_bar.setObjectName("settings_bar")
        settings_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        settings_bar_layout = QVBoxLayout(settings_bar)
        settings_bar_layout.setContentsMargins(0, 0, 0, 0)
        settings_bar_layout.setSpacing(0)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settings_button")
        self.settings_button.setProperty("kind", "pill")
        self.settings_button.clicked.connect(self.settings_requested.emit)

        settings_bar_layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        stats_layout.addWidget(settings_bar)
        stats_layout.addStretch(1)
        root_layout.addWidget(stats_container)

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


    def _tooltip_key(self, label_text: str) -> str:
        return label_text.strip().casefold().replace(" ", "_")


    def _make_metric_row(
        self,
        key_text: str,
        *,
        center_value: bool = False,
        value_object_name: str = "metric_value") -> tuple[QWidget, QLabel, QLabel]:
        row = QWidget()
        row.setObjectName("metric_row")
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        key_label = QLabel(key_text)
        key_label.setObjectName("metric_key")

        value_label = ElidedLabel() if key_text == "Server" else QLabel("-")
        value_label.setObjectName(value_object_name)
        value_label.setProperty("kind", "pill")

        if key_text == "Server":
            value_label.setProperty("metric", "server")
            value_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        if center_value:
            key_label.hide()
            layout.addStretch(1)
            layout.addWidget(value_label, 0)
            layout.addStretch(1)
        else:
            layout.addWidget(key_label, 1)
            layout.addWidget(value_label, 0)

        tooltip_key = self._tooltip_key(key_text)
        tooltip_text = METRIC_TOOLTIPS.get(tooltip_key, "")
        apply_tooltip((key_label,), tooltip_text)

        return row, key_label, value_label


    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def on_check_result(self, result_object: object) -> None:
        if not isinstance(result_object, CheckResult):
            return
        self.monitor_state.apply(result_object)
        self.refresh_labels()


    def _get_setting_str(self, settings: QSettings, key: str, default: str = "") -> str:
        value: Any = settings.value(key, default)
        if value is None:
            return default
        return value if isinstance(value, str) else str(value)


    def _format_host_port(self, host: str, port: int) -> str:
        # Bracket IPv6 when showing host:port
        if ":" in host and not host.startswith("["):
            return f"[{host}]:{port}"
        return f"{host}:{port}"


    def _compute_full_target_tooltip(self) -> str:
        settings = QSettings()
        full_target = self._get_setting_str(settings, "endpoint/full_target", "").strip()
        if full_target:
            return full_target

        # Fallback
        host = self.monitor_state.server
        port = self.monitor_state.port
        return self._compute_display_target(host, port)


    def _compute_display_target(self, host: str, port: int) -> str:
        settings = QSettings()

        # Preferred: Use exact display saved by SettingsDialog
        saved_display = self._get_setting_str(settings, "endpoint/display_target", "").strip()
        if saved_display:
            return saved_display

        # Fallback
        method = self._get_setting_str(settings, "endpoint/method", "")

        # Target method is IP
        if method == "ip":
            return self._format_host_port(host, port)

        # Target method is hostname
        if method == "hostname":
            hostname = self._get_setting_str(settings, "endpoint/hostname_text", "").strip()
            explicit_port = False

            if hostname.startswith("["):
                closing = hostname.find("]")
                if closing != -1:
                    remainder = hostname[closing + 1 :].strip()
                    if remainder.startswith(":") and remainder[1:].strip().isdigit():
                        explicit_port = True
            else:
                if ":" in hostname:
                    possible_host, possible_port = hostname.rsplit(":", 1)
                    if possible_port.isdigit():
                        explicit_port = True

            return self._format_host_port(host, port) if explicit_port else host

        # Target method is URL
        if method == "url":
            raw = self._get_setting_str(settings, "endpoint/url_text", "").strip()
            if raw:
                url_text = raw if "://" in raw else f"https://{raw}"
                parts = urlsplit(url_text)
                explicit_port = parts.port is not None
                return self._format_host_port(host, port) if explicit_port else host
            
            return host
        
        # Unknown method
        return self._format_host_port(host, port)


    def refresh_labels(self) -> None:
        last_status = self.monitor_state.last_status

        if last_status is None:
            self.status_label.setText("...")
            new_status = "unknown"
        elif last_status == "online":
            self.status_label.setText("Online")
            new_status = "online"
        elif last_status == "offline":
            self.status_label.setText("Offline")
            new_status = "offline"
        else:
            # Unreachable
            self.status_label.setText("Unreachable")
            new_status = "unreachable"

        self.status_label.setToolTip(status_value_tooltip(last_status))

        # Root status 
        if self.property("status") != new_status:
            self.setProperty("status", new_status)
            for label in self.findChildren(QLabel, "metric_value"):
                self._repolish(label)

        # Status selectors
        if self.status_label.property("status") != new_status:
            self.status_label.setProperty("status", new_status)
            self._repolish(self.status_label)

        # Phase label
        if new_status == "online":
            phase_text = "Online for"
        elif new_status == "offline":
            phase_text = "Offline for"
        elif new_status == "unreachable":
            phase_text = "Unreachable for"
        else:
            phase_text = "-"

        if self.phase_label.text() != phase_text:
            self.phase_label.setText(phase_text)

        # Server
        server_text = self._compute_display_target(self.monitor_state.server, self.monitor_state.port)
        if self.server_value.text() != server_text:
            self.server_value.setText(server_text)

        full_target = self._compute_full_target_tooltip()
        tooltip_text = f"{full_target}\n\n Click to copy full URL"

        # Update tooltip
        if self.server_value.toolTip() != tooltip_text:
            self.server_value.setToolTip(tooltip_text)

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
        self.phase_value.setText(format_seconds_as_hhmmss(current_phase_seconds))


    def apply_config(self, config: MonitorConfig) -> None:
        # Stop current monitor
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)
        self.monitor_state.set_endpoint(config.server, config.port)

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
        self.server_value.setText(self._compute_display_target(config.server, config.port))
        self.status_label.setText("...")
        self.status_label.setProperty("status", "unknown")
        self._repolish(self.status_label)
        self.refresh_labels()


    def shutdown(self) -> None:
        self.ui_refresh_timer.stop()
        self.monitor_thread.stop()
        self.monitor_thread.wait(1500)
