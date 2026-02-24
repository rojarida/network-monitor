from __future__ import annotations

from PySide6.QtGui import QFontMetrics, QPainter, QPalette
from PySide6.QtCore import QTimer, Signal, Qt
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

from network_monitor.persistence.settings_store import SettingsData
from network_monitor.services.monitor.thread import MonitorThread
from network_monitor.services.monitor.state import MonitorState, CheckResult
from network_monitor.ui.help.tooltips import (
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
        self._stopping_threads: list[MonitorThread] = []
        self._settings: SettingsData | None = None

        self.setObjectName("monitor_view")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.monitor_state = MonitorState(server="google.com", port=443)
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
        self.monitor_thread: MonitorThread | None = None

        self.ui_refresh_timer = QTimer(self)
        self.ui_refresh_timer.setInterval(250)
        self.ui_refresh_timer.timeout.connect(self.refresh_labels)
        self.ui_refresh_timer.start()

    def apply_settings(self, settings: SettingsData) -> None:
        """Apply settings and restart monitor thread"""
        self._settings = settings
        self._stop_monitor_thread(blocking=False)

        # Update state endpoint
        self.monitor_state.set_endpoint(settings.host, settings.port)

        # Restart thread with new configuration
        self.monitor_thread = MonitorThread(
            server=settings.host,
            port=settings.port,
            interval_s=settings.interval_seconds,
            timeout_s=settings.timeout_seconds,
        )

        self.monitor_thread.result.connect(self.on_check_result)
        self.monitor_thread.start()

        # Update UI from settings
        self.server_value.setText(settings.display_target)
        self.server_value.setToolTip(settings.full_target)

        self.status_label.setText("...")
        self.status_label.setProperty("status", "unknown")
        self._repolish(self.status_label)
        self.refresh_labels()

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
        if self._settings is not None:
            if self.server_value.text() != self._settings.display_target:
                self.server_value.setText(self._settings.display_target)

            desired_tooltip = self._settings.full_target
            if self.server_value.toolTip() != desired_tooltip:
                self.server_value.setToolTip(desired_tooltip)

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

    def _stop_monitor_thread(self, *, blocking: bool = False) -> None:
        thread = getattr(self, "monitor_thread", None)
        if not thread:
            return
        
        thread.stop()

        # Worst-case
        timeout_s = getattr(thread, "timeout_s", 1.0)

        # Apply-config
        # Shutdown: Wait long enough for the in-flight connect to return
        wait_ms = int(((timeout_s + 1.0) if blocking else min(timeout_s, 1.0)) * 1000)
        finished = thread.wait(wait_ms)

        try:
            thread.result.disconnect(self.on_check_result)
        except (TypeError, RuntimeError):
            pass

        if finished:
            thread.deleteLater()
        else:
            # If we didn't finish, keep it referenced until natural finish
            self._stopping_threads.append(thread)

            def _cleanup() -> None:
                if thread in self._stopping_threads:
                    self._stopping_threads.remove(thread)
                thread.deleteLater()

            thread.finished.connect(_cleanup)

        self.monitor_thread = None

    def shutdown(self) -> None:
        if getattr(self, "ui_refresh_timer", None):
            self.ui_refresh_timer.stop()
        self._stop_monitor_thread(blocking=True)
