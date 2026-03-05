from __future__ import annotations

from PySide6.QtGui import QFontMetrics, QPainter, QPalette, QIcon
from PySide6.QtCore import QTimer, Signal, Qt, QSize
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
    QToolButton,
)

from network_monitor.core.models import SettingsData
from network_monitor.ui.workers import MonitorThread
from network_monitor.core.monitor import MonitorState, CheckResult
from network_monitor.ui.help import (
    METRIC_TOOLTIPS,
    THEME_TOOLTIPS,
    apply_tooltip,
    status_value_tooltip,
)


_STATUS_UI = {
    None: ("...", "unknown", "-"),
    "online": ("Online", "online", "Online for"),
    "offline": ("Offline", "offline", "Offline for"),
    "unreachable": ("Unreachable", "unreachable", "Unreachable for"),
}


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
    theme_toggle_requested = Signal()
    monitor_toggle_requested = Signal()

    # Widgets
    status_pill: QLabel
    status_label: QLabel
    phase_label: QLabel

    server_value: ElidedLabel
    phase_value: QLabel
    latency_value: QLabel
    disconnects_value: QLabel
    total_uptime_value: QLabel
    total_downtime_value: QLabel

    theme_button: QToolButton
    settings_button: QPushButton
    monitor_toggle_button: QToolButton

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._stopping_threads: list[MonitorThread] = []
        self._settings: SettingsData | None = None
        self._pill_labels: list[QLabel] = []
        self._metric_value_labels: list[QLabel] = []
        self._monitoring_enabled = True

        # Icons
        self._sun_icon          = QIcon(":/icons/sun.svg")
        self._moon_icon         = QIcon(":/icons/moon.svg")
        self._dark_play_icon    = QIcon(":/icons/dark-play.svg")
        self._light_play_icon   = QIcon(":/icons/light-play.svg")
        self._dark_pause_icon   = QIcon(":/icons/dark-pause.svg")
        self._light_pause_icon  = QIcon(":/icons/light-pause.svg")

        # Widget configuration
        self.setObjectName("monitor_view")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Domain state
        self.monitor_state = MonitorState(server="google.com", port=443)
        self.monitor_state.start()

        # UI
        self._build_ui()

        # Thread and timers
        self.monitor_thread: MonitorThread | None = None

        self.ui_refresh_timer = QTimer(self)
        self.ui_refresh_timer.setInterval(250)
        self.ui_refresh_timer.timeout.connect(self.refresh_labels)
        self.ui_refresh_timer.start()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setObjectName("root_layout")
        root_layout.setContentsMargins(0, 0, 0, 0)

        stats_container = QWidget()
        stats_container.setObjectName("stats_container")

        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(8, 6, 8, 6)

        # Metrics
        metric_widgets = self._build_metrics()
        self._add_stats_items(
            stats_layout,
            *metric_widgets,
            "separator_bottom",
        )

        # Settings bar
        settings_bar = self._build_settings_bar()
        stats_layout.addStretch(1)
        stats_layout.addWidget(settings_bar)
        stats_layout.addStretch(1)

        root_layout.addWidget(stats_container)

    def _build_metrics(self) -> list[QWidget | str]:
        # Status
        status_row, _status_key, status_value = self._make_metric_row(
            "Status",
            center_value=True,
            value_object_name="status_label",
        )
        self.status_pill = status_value
        self.status_label = status_value
        self.status_label.setText("...")
        self.status_label.setProperty("status", "unknown")

        # Remaining metrics
        metric_specs: list[tuple[str, str, str, type[QLabel] | None]] = [
            ("Server", "server_value", "server", ElidedLabel),
            ("Current phase", "phase_value", "phase", None),
            ("Latency", "latency_value", "latency", None),
            ("Disconnects", "disconnects_value", "disconnects", None),
            ("Total uptime", "total_uptime_value", "uptime", None),
            ("Total downtime", "total_downtime_value", "downtime", None),
        ]

        rows: dict[str, QWidget] = {}
        for key_text, attr_name, metric_key, value_factory in metric_specs:
            row, key_label, value_label = self._make_metric_row(
                key_text,
                metric_key=metric_key,
                value_factory=value_factory,
            )
            setattr(self, attr_name, value_label)
            rows[attr_name] = row

            if metric_key == "phase":
                self.phase_label = key_label

        return [
            status_row,
            "separator_top",
            rows["server_value"],
            "separator_top",
            rows["phase_value"],
            rows["latency_value"],
            rows["disconnects_value"],
            "separator_middle",
            rows["total_uptime_value"],
            rows["total_downtime_value"],
        ]

    def _build_settings_bar(self) -> QFrame:
        settings_bar = QFrame()
        settings_bar.setObjectName("settings_bar")
        settings_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(settings_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.theme_button = self._make_icon_button("theme_button", size=35)
        self.theme_button.clicked.connect(self.theme_toggle_requested.emit)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settings_button")
        self.settings_button.setProperty("kind", "pill")
        self.settings_button.clicked.connect(self.settings_requested.emit)

        self.monitor_toggle_button = self._make_icon_button(
            "monitor_toggle_button",
            size=35,
            checkable=True
        )
        self.monitor_toggle_button.toggled.connect(self._on_monitor_toggled)

        # Make "running" the default
        self.monitor_toggle_button.blockSignals(True)
        self.monitor_toggle_button.setChecked(True)
        self.monitor_toggle_button.blockSignals(False)
        self._refresh_monitor_toggle_icon()

        layout.addStretch(1)
        layout.addWidget(self.theme_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.settings_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.monitor_toggle_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch(1)

        return settings_bar

    def _add_stats_items(self, layout: QVBoxLayout, *items: QWidget | str) -> None:
        for item in items:
            if isinstance(item, str):
                layout.addWidget(self._make_separator(item))
            else:
                layout.addWidget(item)

    def apply_settings(self, settings: SettingsData) -> None:
        self._settings = settings
        self.monitor_state.set_endpoint(settings.host, settings.port)
        self._update_server()

        # Restart status UI
        self._set_text_if_changed(self.status_label, "...")
        self._set_property_if_changed(self.status_label, "status", "unknown")

        if self._should_monitor_run():
            self._restart_monitor_thread()
            self._set_paused_mode(False)
        else:
            self._stop_monitor_thread(blocking=False)
            self._set_paused_mode(True)
        
        self.refresh_labels()

    def _set_text_if_changed(self, label: QLabel, text: str) -> None:
        if label.text() != text:
            label.setText(text)

    def _set_tooltip_if_changed(self, widget: QWidget, tooltip: str) -> None:
        if widget.toolTip() != tooltip:
            widget.setToolTip(tooltip)

    def _set_property_if_changed(
        self,
        widget: QWidget,
        name: str,
        value: object,
        *,
        repolish: bool = True,
    ) -> bool:
        if widget.property(name) != value:
            widget.setProperty(name, value)
            if repolish:
                self._repolish(widget)
            return True
        return False

    def refresh_labels(self) -> None:
        if self.property("paused") is True:
            return

        self._update_status_and_phase()
        self._update_server()
        self._update_latency()
        self._update_disconnects()
        self._update_durations()

    def _update_status_and_phase(self) -> None:
        last_status = self.monitor_state.last_status
        text, new_status, phase_text = _STATUS_UI.get(last_status, _STATUS_UI["unreachable"])

        self._set_text_if_changed(self.status_label, text)
        self._set_tooltip_if_changed(self.status_label, status_value_tooltip(last_status))

        if self._set_property_if_changed(self, "status", new_status, repolish=False):
            for label in self._metric_value_labels:
                self._repolish(label)

        self._set_property_if_changed(self.status_label, "status", new_status, repolish=True)
        self._set_text_if_changed(self.phase_label, phase_text)

    def _update_latency(self) -> None:
        latency_ms = self.monitor_state.last_latency_ms
        if latency_ms is None:
            self._set_text_if_changed(self.latency_value, "-")
            level = "na"
        else:
            rounded = round(latency_ms)
            self._set_text_if_changed(self.latency_value, f"{rounded} ms")
            level = "good" if rounded < 100 else (
                "warn" if rounded < 200 else "bad"
            )

        self._set_property_if_changed(self.latency_value, "level", level, repolish=True)

    def _update_disconnects(self) -> None:
        disconnects = self.monitor_state.disconnects
        self._set_text_if_changed(self.disconnects_value, str(disconnects))
        level = "good" if disconnects == 0 else (
            "warn" if disconnects < 10 else "bad"
        )
        self._set_property_if_changed(self.disconnects_value, "level", level, repolish=True)

    def _update_durations(self) -> None:
        total_uptime, total_downtime = self.monitor_state.totals_including_current_phase()
        self._set_text_if_changed(self.total_uptime_value, format_seconds_as_hhmmss(total_uptime))
        self._set_text_if_changed(self.total_downtime_value, format_seconds_as_hhmmss(total_downtime))

        current_phase = self.monitor_state.current_phase_seconds()
        self._set_text_if_changed(self.phase_value, format_seconds_as_hhmmss(current_phase))

    def _update_server(self) -> None:
        if self._settings is None:
            return
        self._set_text_if_changed(self.server_value, self._settings.display_target)
        self._set_tooltip_if_changed(self.server_value, self._settings.full_target)


    def _set_paused_mode(self, paused: bool) -> None:
        """Overwrites the current labels used by `refresh_labels()`"""
        if self.property("paused") != paused:
            self.setProperty("paused", paused)
            self._repolish(self)

        pill_labels = self._pill_labels
        self.status_pill.setProperty("paused", paused)

        if paused:
            self.status_pill.setText("Paused")
            self.status_pill.setToolTip("Monitoring paused")
            self.phase_label.setText("Paused")
            
            for widget in pill_labels:
                if widget is self.status_pill or widget is self.server_value:
                    continue
                widget.setText("-")

            self.latency_value.setProperty("level", "na")
            self.disconnects_value.setProperty("level", "na")

        for widget in pill_labels:
            self._repolish(widget)

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
        metric_key: str | None = None,
        value_factory: type[QLabel] | None = None,
        center_value: bool = False,
        value_object_name: str = "metric_value"
    ) -> tuple[QWidget, QLabel, QLabel]:
        row = QWidget()
        row.setObjectName("metric_row")
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        key_label = QLabel(key_text)
        key_label.setObjectName("metric_key")

        value_label: QLabel = (value_factory() if value_factory else QLabel("-"))
        if not value_label.text():
            value_label.setText("-")

        value_label.setObjectName(value_object_name)
        value_label.setProperty("kind", "pill")

        self._pill_labels.append(value_label)
        if value_object_name == "metric_value":
            self._metric_value_labels.append(value_label)

        if metric_key is not None and value_object_name == "metric_value":
            value_label.setProperty("metric", metric_key)
            if metric_key == "server":
                value_label.setSizePolicy(
                    QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
                )

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

    def _make_icon_button(
        self,
        object_name: str,
        *,
        size: int,
        icon_size: QSize = QSize(25, 25),
        checkable: bool = False,
    ) -> QToolButton:
        button = QToolButton()
        button.setObjectName(object_name)
        button.setAutoRaise(False)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setIconSize(icon_size)
        button.setFixedSize(size, size)
        button.setCheckable(checkable)
        
        return button

    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def on_check_result(self, result_object: object) -> None:
        if self.property("paused"):
            return
        if not isinstance(result_object, CheckResult):
            return
        self.monitor_state.apply(result_object)
        self.refresh_labels()

    def _on_monitor_toggled(self, monitoring_enable: bool) -> None:
        if monitoring_enable:
            self._resume_monitoring()
        else:
            self._pause_monitoring()

    def _resume_monitoring(self) -> None:
        self.monitor_state.resume()
        self._monitoring_enabled = True

        if not self.ui_refresh_timer.isActive():
            self.ui_refresh_timer.start()

        self._set_paused_mode(False)
        self._start_monitor_thread()
        self._refresh_monitor_toggle_icon()

    def _pause_monitoring(self) -> None:
        self.monitor_state.pause()
        self._monitoring_enabled = False
        self._stop_monitor_thread()

        if self.ui_refresh_timer.isActive():
            self.ui_refresh_timer.stop()

        self._set_paused_mode(True)
        self._refresh_monitor_toggle_icon()

    def _should_monitor_run(self) -> bool:
        return (
            bool(self._settings) 
            and self._monitoring_enabled 
            and not self.property("paused")
        )

    def _restart_monitor_thread(self) -> None:
        self._stop_monitor_thread(blocking=False)
        self._start_monitor_thread()

    def _start_monitor_thread(self) -> None:
        if self.monitor_thread is not None:
            return

        if self._settings is None:
            return

        self.monitor_thread = MonitorThread(
            server=self._settings.host,
            port=self._settings.port,
            interval_seconds=self._settings.interval_seconds,
            timeout_seconds=self._settings.timeout_seconds,
        )
        self.monitor_thread.result.connect(self.on_check_result)
        self.monitor_thread.start()

    def _stop_monitor_thread(self, *, blocking: bool = False) -> None:
        thread = getattr(self, "monitor_thread", None)
        if not thread:
            return
        
        thread.stop()

        # Worst-case
        timeout_s = getattr(thread, "timeout_s", 1.0)

        # Apply-config
        # Shutown: Wait long enough for the in-flight connect to return
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

    def _current_theme(self) -> str:
        target_theme = self.theme_button.property("target_theme")
        if target_theme not in ("light", "dark"):
            return "dark"

        return "dark" if target_theme == "light" else "light"

    def _refresh_monitor_toggle_icon(self) -> None:
        current_theme = self._current_theme()
        monitor_running = self.monitor_toggle_button.isChecked()

        if current_theme == "light":
            icon = self._dark_pause_icon if monitor_running else self._dark_play_icon
        else:
            icon = self._light_pause_icon if monitor_running else self._light_play_icon

        self.monitor_toggle_button.setIcon(icon)

        # TODO: Fix tooltip
        self.monitor_toggle_button.setToolTip(
            "Pause monitoring" if monitor_running else "Resume monitoring"
        )

    def set_theme_toggle_target(self, target_theme: str) -> None:
        # target_theme is the theme that will be activated when clicked
        if target_theme == "light":
            self.theme_button.setIcon(self._sun_icon)
        else:
            self.theme_button.setIcon(self._moon_icon)

        apply_tooltip((self.theme_button,), THEME_TOOLTIPS.get(target_theme, ""))
        self.theme_button.setProperty("target_theme", target_theme)
        self.monitor_toggle_button.setProperty("target_theme", target_theme)
        self._repolish(self.theme_button)
        self._refresh_monitor_toggle_icon()

    def shutdown(self) -> None:
        if getattr(self, "ui_refresh_timer", None):
            self.ui_refresh_timer.stop()
        self._stop_monitor_thread(blocking=True)
