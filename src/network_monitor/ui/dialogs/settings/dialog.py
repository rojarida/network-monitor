from __future__ import annotations

import ipaddress
import re

from urllib.parse import urlsplit
from typing import Any
from dataclasses import dataclass

from PySide6.QtCore import QSettings, Qt, QObject, QEvent
from PySide6.QtWidgets import (
    QFrame,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QStackedWidget,
    QWidget,
    QSizePolicy,
)

from network_monitor.ui.help.tooltips import SETTINGS_TOOLTIPS, apply_tooltip


# Regex for handling URLs
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


class CheckRadioOnInteractFilter(QObject):
    def __init__(self, radio_button: QRadioButton, parent=None) -> None:
        super().__init__(parent)
        self._radio_button = radio_button


    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn):
            if self._radio_button is not None and self._radio_button.isChecked():
                self._radio_button.setChecked(True)

        return False


@dataclass(frozen=True)
class NormalizedTarget:
    host: str
    port: int
    display_target: str
    full_target: str | None = None


@dataclass(frozen=True)
class MonitorConfig:
    server: str
    port: int
    interval_s: float
    timeout_s: float


    def save(self) -> None:
        settings = QSettings()
        settings.setValue("endpoint/server", self.server)
        settings.setValue("endpoint/port", self.port)
        settings.setValue("monitor/interval_s", self.interval_s)
        settings.setValue("monitor/timeout_s", self.timeout_s)
        settings.sync()


    @classmethod
    def load(cls) -> "MonitorConfig":
        settings = QSettings()

        server_raw: Any = settings.value("endpoint/server", "1.1.1.1")
        port_raw: Any = settings.value("endpoint/port", 443)
        interval_raw: Any = settings.value("monitor/interval_s", 1.0)
        timeout_raw: Any = settings.value("monitor/timeout_s", 1.0)

        return cls(
            server=str(server_raw),
            port=int(port_raw),
            interval_s=float(interval_raw),
            timeout_s=float(timeout_raw)
        )


def parse_endpoint(raw_text: str, default_port: int) -> tuple[str, int]:
    """
    Accepts:
        - IP=           1.1.1.1
        - Hostname=     google.com, localhost
        - Host:Port=    google.com:443, 1.1.1.1:443
        - URL=          https://google.com, http://example.com:8080/path

    Returns (host, port) normalized for a TCP socket.
    """
    text = raw_text.strip()
    if not text:
        raise ValueError("Endpoint is empty")

    # Full URL (https://example.com or http://example.com:1234)
    if "://" in text:
        parts = urlsplit(text)
        if not parts.hostname:
            raise ValueError("Invalid URL")

        host = parts.hostname
        if parts.port is not None:
            port = parts.port
        else:
            if parts.scheme == "https":
                port = 443
            elif parts.scheme == "http":
                port = 80
            else:
                port = default_port

        if not (1 <= int(port) <= 65535):
            raise ValueError("Port out of range")

        return host, int(port)

    try:
        ipaddress.ip_address(text)
        if not (1 <= int(default_port) <= 65535):
            raise ValueError("Port out of range")
        return text, int(default_port)
    except ValueError:
        pass

    # Host:Port
    parts = urlsplit(f"dummy://{text}")
    if not parts.hostname:
        raise ValueError("Invalid target")

    host = parts.hostname
    port = parts.port if parts.port is not None else default_port

    if not (1 <= int(port) <= 65535):
        raise ValueError("Port out of range")

    # Valdiate host (IP or hostname)
    try:
        ipaddress.ip_address(host)
        return host, int(port)
    except ValueError:
        pass

    try:
        ascii_host = host.encode("idna").decode("ascii")
    except Exception as exc:
        raise ValueError("Invalid hostname") from exc

    if not _HOSTNAME_RE.match(ascii_host.rstrip(".")):
        raise ValueError("Invalid hostname")

    return host, int(port)


class SettingsDialog(QDialog):
    METHOD_IP = "ip"
    METHOD_HOSTNAME = "hostname"
    METHOD_URL = "url"


    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._event_filters: list[QObject] = []
        self.settings: QSettings = QSettings()
        self.setWindowTitle("Settings")
        self.setFixedSize(650, 500)
        self.setObjectName("settings_dialog")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Target method
        self.target_method_group = QButtonGroup(self)
        self.target_method_group.setExclusive(True)

        self.ip_method_radio_button = QRadioButton("IP Address")
        self.hostname_method_radio_button = QRadioButton("Hostname")
        self.url_method_radio_button = QRadioButton("URL")

        for radio in (
            self.ip_method_radio_button,
            self.hostname_method_radio_button,
            self.url_method_radio_button
        ):
            radio.setProperty("role", "method_radio")

        self.target_method_group.addButton(self.ip_method_radio_button, 0)
        self.target_method_group.addButton(self.hostname_method_radio_button, 1)
        self.target_method_group.addButton(self.url_method_radio_button, 2)

        method_label = QLabel("Method")
        method_label.setProperty("role", "method_heading")
        method_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        target_method_group_box = QGroupBox()
        target_method_group_box.setTitle("")
        target_method_group_box.setObjectName("method_box")
        target_method_group_box.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True
        )
        target_method_group_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        target_method_layout = QVBoxLayout(target_method_group_box)
        target_method_layout.setContentsMargins(12, 12, 12, 12)
        target_method_layout.setSpacing(8)
        target_method_layout.addWidget(self.ip_method_radio_button)
        target_method_layout.addWidget(self.hostname_method_radio_button)
        target_method_layout.addWidget(self.url_method_radio_button)

        method_container = QWidget()
        method_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        method_container_layout = QVBoxLayout(method_container)
        method_container_layout.setContentsMargins(0, 0, 0, 0)
        method_container_layout.setSpacing(6) # Space between label and box
        method_container_layout.addWidget(method_label)
        method_container_layout.addWidget(target_method_group_box)

        # IP Page
        self.ip_target_line_edit = QLineEdit()
        self.ip_target_line_edit.setPlaceholderText("e.g., 1.1.1.1 or 2606:4700:4700::1111")
        self.ip_target_line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ip_port_spin_box = QSpinBox()
        self.ip_port_spin_box.setRange(1, 65535)
        self.ip_port_spin_box.setValue(443)
        self.ip_port_spin_box.setMaximumWidth(100)
        self.ip_preview_label = QLabel()
        self.ip_preview_label.setObjectName("ip_preview_label")
        self.ip_preview_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.ip_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ip_form_container = QWidget()
        ip_page_form_layout = QFormLayout(ip_form_container)
        ip_page_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ip_page_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        ip_address_label = QLabel("IP:")
        ip_address_label.setProperty("role", "field_label")
        ip_port_label = QLabel("Port:")
        ip_port_label.setProperty("role", "field_label")

        apply_tooltip((ip_address_label,), SETTINGS_TOOLTIPS["ip_input"])
        apply_tooltip((ip_port_label,), SETTINGS_TOOLTIPS["ip_port"])

        ip_page_form_layout.addRow(ip_address_label, self.ip_target_line_edit)
        ip_page_form_layout.addRow(ip_port_label, self.ip_port_spin_box)

        ip_page_widget = QWidget()
        ip_page_layout = QVBoxLayout(ip_page_widget)
        ip_page_layout.setContentsMargins(0, 0, 0, 0)
        ip_page_layout.setSpacing(0)

        ip_page_layout.addStretch(1)
        ip_page_layout.addWidget(ip_form_container)
        ip_page_layout.addStretch(1)
        ip_page_layout.addWidget(self._centered_row(self.ip_preview_label))

        # Hostname Page
        self.hostname_target_line_edit = QLineEdit()
        self.hostname_target_line_edit.setPlaceholderText("e.g., google.com (optional: :443)")
        self.hostname_target_line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.hostname_preview_label = QLabel()
        self.hostname_preview_label.setObjectName("hostname_preview_label")
        self.hostname_preview_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.hostname_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hostname_form_container = QWidget()
        hostname_page_form_layout = QFormLayout(hostname_form_container)
        hostname_page_form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        hostname_page_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        hostname_label = QLabel("Hostname:")
        hostname_label.setProperty("role", "field_label")

        apply_tooltip((hostname_label,), SETTINGS_TOOLTIPS["hostname_input"])
        hostname_page_form_layout.addRow(hostname_label, self.hostname_target_line_edit)

        hostname_page_widget = QWidget()
        hostname_page_layout = QVBoxLayout(hostname_page_widget)
        hostname_page_layout.setContentsMargins(0, 0, 0, 0)
        hostname_page_layout.setSpacing(0)

        hostname_page_layout.addStretch(1)
        hostname_page_layout.addWidget(hostname_form_container)
        hostname_page_layout.addStretch(1)
        hostname_page_layout.addWidget(self._centered_row(self.hostname_preview_label))

        # URL Page
        self.url_target_line_edit = QLineEdit()
        self.url_target_line_edit.setPlaceholderText("e.g., https://www.google.com:443/path")
        self.url_target_line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_preview_label = QLabel()
        self.url_preview_label.setObjectName("url_preview_label")
        self.url_preview_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.url_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        url_page_widget = QWidget()
        url_page_layout = QVBoxLayout(url_page_widget)
        url_page_form_layout = QFormLayout()
        url_page_form_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        url_page_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        url_page_layout.setContentsMargins(0, 0, 0, 0)
        url_page_layout.setSpacing(0)

        url_label = QLabel("URL:")
        url_label.setProperty("role", "field_label")
        
        apply_tooltip((url_label,), SETTINGS_TOOLTIPS["url_input"])
        url_page_layout.addStretch(1)
        url_page_form_layout.addRow(url_label, self.url_target_line_edit)

        url_page_layout.addLayout(url_page_form_layout)
        url_page_layout.addStretch(1)
        url_page_layout.addWidget(self._centered_row(self.url_preview_label))

        self.target_stack_widget = QStackedWidget()
        self.target_stack_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.target_stack_widget.addWidget(ip_page_widget)          # Index 0
        self.target_stack_widget.addWidget(hostname_page_widget)    # Index 1
        self.target_stack_widget.addWidget(url_page_widget)         # Index 2

        target_body = QWidget()
        target_body_layout = QHBoxLayout(target_body)
        target_body_layout.setContentsMargins(0, 0, 0, 0)
        target_body_layout.setSpacing(16)

        target_method_group_box.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        target_body_layout.addWidget(
            method_container, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )

        # Let input fields fill the space centered vertically/horizontally
        inputs_wrapper = QWidget()
        inputs_wrapper_layout = QVBoxLayout(inputs_wrapper)
        inputs_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        inputs_wrapper_layout.setSpacing(0)

        inputs_wrapper_layout.addWidget(self.target_stack_widget)

        target_body_layout.addWidget(inputs_wrapper, 1, Qt.AlignmentFlag.AlignVCenter)
        self.target_section = self._make_titled_card(
            "Target", target_body, "target_card", center_horizontally=False
        )

        # Radio groups for interval/timeout (presets and custom)
        preset_values_seconds = [1.0, 2.0, 5.0]

        (
            interval_body,
            self.interval_button_group,
            self.interval_custom_radio_button,
            self.interval_custom_spin_box,
        ) = self._build_seconds_radio_group(
            preset_values=preset_values_seconds,
            custom_tooltip_key="custom_interval",
        )

        (
            timeout_body,
            self.timeout_button_group,
            self.timeout_custom_radio_button,
            self.timeout_custom_spin_box,
        ) = self._build_seconds_radio_group(
            preset_values=preset_values_seconds,
            custom_tooltip_key="custom_timeout",
        )

        self.interval_section = self._make_titled_card("Check Interval", interval_body, "interval_card")
        self.timeout_section = self._make_titled_card("Timeout Interval", timeout_body, "timeout_card")

        self.validation_label = QLabel()
        self.validation_label.setObjectName("validation_label")
        self.validation_label.setWordWrap(True)
        self.validation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.validation_label.setVisible(False)

        validation_container = QWidget()
        validation_layout = QVBoxLayout(validation_container)
        validation_layout.setContentsMargins(0, 0, 0, 0)
        validation_layout.setSpacing(0)
        validation_layout.addWidget(self.validation_label)
        validation_layout.addStretch(1)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )

        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        if save_button is not None:
            save_button.setObjectName("save_button")

        if cancel_button is not None:
            cancel_button.setObjectName("cancel_button")

        self.button_box.accepted.connect(self._save_and_close)
        self.button_box.rejected.connect(self.reject)

        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setHorizontalSpacing(12)
        main_layout.setSpacing(12)

        # TODO: Implement tooltips after UI
        # apply_tooltip((target_method_group_box,), SETTINGS_TOOLTIPS["target_method"])
        # apply_tooltip((self.interval_group_box,), SETTINGS_TOOLTIPS["check_interval"])
        # apply_tooltip((self.timeout_group_box,), SETTINGS_TOOLTIPS["timeout"])

        # Row 0: Target spans 2 columns
        main_layout.addWidget(self.target_section, 0, 0, 1, 2)

        # Row 1: Interval (left) and Timeout (right)
        row_1 = QWidget()
        row_1_layout = QHBoxLayout(row_1)
        row_1_layout.setContentsMargins(0, 0, 0, 0)
        row_1_layout.setSpacing(main_layout.horizontalSpacing() or 12)

        row_1_layout.addWidget(self.interval_section)
        row_1_layout.addWidget(self.timeout_section)
        row_1_layout.setStretch(0, 1)
        row_1_layout.setStretch(1, 1)

        main_layout.addWidget(row_1, 1, 0, 1, 2)

        # Make both columns share space evenly
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)

        # Keep rows same space
        main_layout.setRowStretch(0, 0)  # Target
        main_layout.setRowStretch(1, 0)  # Interval/Timeout (stable)
        main_layout.setRowStretch(2, 1)  # Validation (takes leftover space)
        main_layout.setRowStretch(3, 0)  # Buttons

        # Row 2: Validation spans 2 columns
        main_layout.addWidget(validation_container, 2, 0, 1, 2)

        # Row 3: Cancel and Save buttons bottom right
        main_layout.addWidget(self.button_box, 3, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignRight)

        # Signals
        self.target_method_group.idToggled.connect(self._on_target_method_changed)

        self.ip_target_line_edit.textChanged.connect(self._update_validation_ui)
        self.hostname_target_line_edit.textChanged.connect(self._update_validation_ui)
        self.url_target_line_edit.textChanged.connect(self._update_validation_ui)

        self.ip_port_spin_box.valueChanged.connect(self._update_validation_ui)

        self._load_settings()


    def _ensure_default_target_for_method(self) -> None:
        method = self._current_method()

        if method == self.METHOD_IP and not self.ip_target_line_edit.text().strip():
            self.ip_target_line_edit.setText("1.1.1.1")
            self.ip_port_spin_box.setValue(443)

        elif method == self.METHOD_HOSTNAME and not self.hostname_target_line_edit.text().strip():
            self.hostname_target_line_edit.setText("google.com")

        elif method == self.METHOD_URL and not self.url_target_line_edit.text().strip():
            self.url_target_line_edit.setText("https://google.com")


    def _make_titled_card(
        self,
        title_text: str,
        body_widget: QWidget,
        card_name: str,
        *,
        center_horizontally: bool = True,
    ) -> QWidget:
        section = QWidget()
        section.setObjectName(f"{card_name}_section")

        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(8)

        title_label = QLabel(title_text)
        title_label.setProperty("role", "section_heading")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        section_card = QFrame()
        section_card.setObjectName(card_name)
        section_card.setProperty("role", "section_card")
        section_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        section_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        card_layout = QVBoxLayout(section_card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(12)

        center_wrapper = QWidget()
        center_layout = QVBoxLayout(center_wrapper)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        center_layout.addStretch(1)
        if center_horizontally:
            center_layout.addWidget(body_widget, 0, Qt.AlignmentFlag.AlignHCenter)
        else:
            center_layout.addWidget(body_widget)
        center_layout.addStretch(1)

        card_layout.addWidget(center_wrapper)
        section_layout.addWidget(title_label)
        section_layout.addWidget(section_card)

        return section


    def _build_seconds_radio_group(
        self,
        preset_values: list[float],
        *,
        custom_tooltip_key: str | None = None,
    ) -> tuple[QWidget, QButtonGroup, QRadioButton, QDoubleSpinBox]:
        body = QWidget()

        # Vertical root. Presets on the top, custom on the bottom
        root_layout = QVBoxLayout(body)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)
        
        button_group = QButtonGroup(self)

        # Top row: Preset radio buttons
        presets_widget = QWidget()
        presets_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        presets_layout = QHBoxLayout(presets_widget)
        presets_layout.setContentsMargins(0, 0, 0, 0)
        presets_layout.setSpacing(10)

        presets_center = QWidget()
        presets_center_layout = QHBoxLayout(presets_center)
        presets_center_layout.setContentsMargins(0, 0, 0, 0)
        presets_center_layout.setSpacing(0)
        presets_center_layout.addStretch(1)
        presets_center_layout.addWidget(presets_widget)
        presets_center_layout.addStretch(1)

        for seconds_value in preset_values:
            preset_radio_button = QRadioButton(f"{seconds_value:g} s")
            preset_radio_button.setProperty("seconds_value", seconds_value)
            preset_radio_button.setProperty("role", "preset_radio")
            button_group.addButton(preset_radio_button)
            presets_layout.addWidget(preset_radio_button)

        # Bottom row: Custom radio and spinbox centered vertically
        custom_widget = QWidget()
        custom_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        custom_layout = QHBoxLayout(custom_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(0)

        custom_row = QWidget()
        custom_row_layout = QHBoxLayout(custom_row)
        custom_row_layout.setContentsMargins(0, 0, 0, 0)
        custom_row_layout.setSpacing(0)

        custom_radio_button = QRadioButton()
        custom_radio_button.setProperty("role", "preset_radio")

        custom_spin_box = QDoubleSpinBox()
        custom_spin_box.setProperty("role", "custom_spin")
        custom_spin_box.setRange(0.5, 60)
        custom_spin_box.setDecimals(1)
        custom_spin_box.setSingleStep(0.5)
        custom_spin_box.setSuffix(" s")
        custom_spin_box.setMaximumWidth(90)

        # Keep enabled so it can be clicked/focused
        custom_spin_box.setEnabled(True)
        custom_spin_box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Start inactive
        custom_spin_box.lineEdit().setReadOnly(True)
        custom_spin_box.setProperty("inactive", True)
        self._repolish(custom_spin_box)

        def set_custom_active(active: bool) -> None:
            # Active -> Editable and Arrows
            # Inactive -> Muted but clickable
            custom_spin_box.setProperty("inactive", not active)
            custom_spin_box.lineEdit().setReadOnly(not active)
            custom_spin_box.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.UpDownArrows
            )
            self._repolish(custom_spin_box)

        custom_radio_button.toggled.connect(set_custom_active)

        # If user clicks the spinbox, select custom automatically
        spin_filter = CheckRadioOnInteractFilter(custom_radio_button, self)
        custom_spin_box.installEventFilter(spin_filter)
        self._event_filters.append(spin_filter)

        custom_spin_box.valueChanged.connect(lambda _v: custom_radio_button.setChecked(True))

        custom_center = QWidget()
        custom_center_layout = QHBoxLayout(custom_center)
        custom_center_layout.setContentsMargins(0, 0, 0, 0)
        custom_center_layout.setSpacing(0)
        custom_center_layout.addStretch(1)
        custom_center_layout.addWidget(custom_widget)
        custom_center_layout.addStretch(1)

        if custom_tooltip_key:
            tooltip_text = SETTINGS_TOOLTIPS.get(custom_tooltip_key, "")
            apply_tooltip((custom_radio_button,), tooltip_text)
            apply_tooltip((custom_spin_box,), tooltip_text)

        button_group.addButton(custom_radio_button)

        custom_row_layout.addWidget(custom_radio_button)
        custom_row_layout.addWidget(custom_spin_box)

        custom_layout.addWidget(custom_row, 0, Qt.AlignmentFlag.AlignHCenter)

        # Combine the two columns
        root_layout.addWidget(presets_center)
        root_layout.addWidget(custom_center)
        root_layout.addStretch(1)

        # Default selection (1s if present, otherwise first preset)
        default_set = False
        for button in button_group.buttons():
            preset_value = button.property("seconds_value")
            if preset_value is not None and float(preset_value) == 1.0:
                button.setChecked(True)
                default_set = True
                break

        if not default_set and button_group.buttons():
            button_group.buttons()[0].setChecked(True)

        return body, button_group, custom_radio_button, custom_spin_box


    def _selected_seconds(
        self,
        button_group: QButtonGroup,
        custom_radio_button: QRadioButton,
        custom_spin_box: QDoubleSpinBox,
    ) -> float:
        if custom_radio_button.isChecked():
            return float(custom_spin_box.value())

        checked_button = button_group.checkedButton()
        if checked_button is None:
            return 1.0

        preset_value = checked_button.property("seconds_value")
        return float(preset_value)


    def _centered_row(self, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(widget)
        layout.addStretch(1)

        return wrapper


    def _set_seconds_group_value(
        self,
        button_group: QButtonGroup,
        custom_radio_button: QRadioButton,
        custom_spin_box: QDoubleSpinBox,
        value: float,
    ) -> None:
        # If it matches a preset, select that preset
        for button in button_group.buttons():
            preset_value = button.property("seconds_value")
            if preset_value is not None and float(preset_value) == float(value):
                button.setChecked(True)
                return

        # Otherwise, select custom
        custom_radio_button.setChecked(True)
        custom_spin_box.setValue(float(value))


    def _get_setting_str(self, key: str, default: str = "") -> str:
        value: Any = self.settings.value(key, default)
        if value is None:
            return default
        return value if isinstance(value, str) else str(value)


    def _get_setting_int(self, key: str, default: int) -> int:
        value: Any = self.settings.value(key, default)
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


    def _current_method(self) -> str:
        if self.hostname_method_radio_button.isChecked():
            return self.METHOD_HOSTNAME
        if self.url_method_radio_button.isChecked():
            return self.METHOD_URL
        return self.METHOD_IP


    def _on_target_method_changed(self) -> None:
        method = self._current_method()
        if method == self.METHOD_IP:
            self.target_stack_widget.setCurrentIndex(0)
        elif method == self.METHOD_HOSTNAME:
            self.target_stack_widget.setCurrentIndex(1)
        else:
            self.target_stack_widget.setCurrentIndex(2)

        self._clear_invalid_markers()
        self._ensure_default_target_for_method()
        self._update_validation_ui()


    def _load_settings(self) -> None:
        config = MonitorConfig.load()

        saved_method = self._get_setting_str("endpoint/method", "")

        # Restore raw inputs
        ip_text = self._get_setting_str("endpoint/ip_text", "")
        hostname_text = self._get_setting_str("endpoint/hostname_text", "")
        url_text = self._get_setting_str("endpoint/url_text", "")

        if not ip_text and not hostname_text and not url_text:
            # First Run / Older Config: Infer from saved server
            inferred_method = self._infer_method_from_server(config.server)
            saved_method = saved_method or inferred_method

            if inferred_method == self.METHOD_IP:
                self.ip_target_line_edit.setText(config.server)
                self.ip_port_spin_box.setValue(int(config.port))
            else:
                self.hostname_target_line_edit.setText(config.server)

        else:
            self.ip_target_line_edit.setText(ip_text)
            self.hostname_target_line_edit.setText(hostname_text)
            self.url_target_line_edit.setText(url_text)
        
            self.ip_port_spin_box.setValue(int(self._get_setting_int("endpoint/ip_port", int(config.port))))

        # Select method
        if saved_method == self.METHOD_HOSTNAME:
            self.hostname_method_radio_button.setChecked(True)
        elif saved_method == self.METHOD_URL:
            self.url_method_radio_button.setChecked(True)
        else:
            self.ip_method_radio_button.setChecked(True)

        # Interval/Timeout
        self._set_seconds_group_value(
            self.interval_button_group,
            self.interval_custom_radio_button,
            self.interval_custom_spin_box,
            float(config.interval_s),
        )
        self._set_seconds_group_value(
            self.timeout_button_group,
            self.timeout_custom_radio_button,
            self.timeout_custom_spin_box,
            float(config.timeout_s)
        )

        self._clear_invalid_markers()
        self._ensure_default_target_for_method()
        self._update_validation_ui()


    def _update_validation_ui(self) -> None:
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        if save_button is None:
            return

        self._clear_invalid_markers()
        self.validation_label.setText("")
        self.validation_label.setVisible(False)
        self.ip_preview_label.setText("")
        self.hostname_preview_label.setText("")
        self.url_preview_label.setText("")

        try:
            normalized = self._normalized_target_from_ui(validate_only=True)
            host, port = normalized.host, normalized.port
        except ValueError as exc:
            self.validation_label.setText(str(exc))
            self.validation_label.setVisible(True)
            self._mark_activate_input_invalid()
            save_button.setEnabled(False)
            return

        if self._current_method() == self.METHOD_IP:
            self.ip_preview_label.setText(f"Checking target: {host}:{port}")

        if self._current_method() == self.METHOD_HOSTNAME:
            self.hostname_preview_label.setText(f"Checking target: {host}:{port}")

        # For URL, show the normalized connection target
        if self._current_method() == self.METHOD_URL:
            self.url_preview_label.setText(f"Checking target: {host}:{port}")

        save_button.setEnabled(True)


    def _format_host_port(self, host: str, port: int) -> str:
    # Bracket IPv6 when showing host:port
        if ":" in host and not host.startswith("[") and host.count(":") >= 2:
            return f"[{host}]:{port}"
        return f"{host}:{port}"
    

    def _normalized_target_from_ui(self, validate_only: bool = False) -> NormalizedTarget:
        method = self._current_method()

        # Target method is IP
        if method == self.METHOD_IP:
            raw_ip_text = self.ip_target_line_edit.text().strip()
            if not raw_ip_text:
                raise ValueError("Please enter an IP address.")
            ip_text = raw_ip_text.strip("[]") # Allow IPv6 style
            try:
                ipaddress.ip_address(ip_text)
            except ValueError as exc:
                raise ValueError("Please enter a valid IPv4 or IPv6 address.") from exc

            port = int(self.ip_port_spin_box.value())
            display_target = self._format_host_port(ip_text, port)

            return NormalizedTarget(host=ip_text, port=port, display_target=display_target)

        # Target method is hostname
        if method == self.METHOD_HOSTNAME:
            hostname = self.hostname_target_line_edit.text().strip()

            if self._looks_like_url(hostname):
                raise ValueError("Format is similar to URL. Switch Target Method to URL.")

            host, port, explicit_port = self._parse_host_optional_port(hostname, default_port=443)

            # Accept IPs as well
            try:
                ipaddress.ip_address(host.strip("[]"))
                clean_ip = host.strip("[]")
                display_target = clean_ip if not explicit_port else self._format_host_port(clean_ip, port)
                return NormalizedTarget(host=clean_ip, port=port, display_target=display_target)
            except ValueError:
                pass

            # Validate as hostname
            try:
                ascii_host = host.encode("idna").decode("ascii")
            except Exception as exc:
                raise ValueError("Invalid hostname.") from exc

            # Normalize trailing dot
            ascii_host = ascii_host.rstrip(".")

            if not _HOSTNAME_RE.match(ascii_host.rstrip(".")):
                raise ValueError(
                    'Enter a hostname (e.g., "romanjay-srv or "google.com") or an IP address.\n'
                    '"localhost" is permitted.'
                )

            display_target = host if not explicit_port else self._format_host_port(host, port)
            return NormalizedTarget(host=host, port=port, display_target=display_target)


        # Target method is URL
        raw_url_text = self.url_target_line_edit.text().strip()
        if not raw_url_text:
            raise ValueError("Please enter a URL.")

        # Allow scheme to be omitted (assume https)
        url_text = raw_url_text if "://" in raw_url_text else f"https://{raw_url_text}"

        try:
            parts = urlsplit(url_text)
        except Exception as exc:
            raise ValueError("Please enter a valid URL.") from exc

        if parts.scheme not in ("http", "https"):
            raise ValueError('Only "http" and "https" URLs are supported.')

        if not parts.hostname:
            raise ValueError("Please enter a valid URL (must include a host).")

        host = parts.hostname
        explicit_port = False

        try:
            port = parts.port
        except ValueError as exc:
            raise ValueError("Invalid port in URL.") from exc

        if port is None:
            port = 80 if parts.scheme == "http" else 443
        else:
            explicit_port = True

        if not (1 <= port <= 65535):
            raise ValueError("Port out of range.")

        display_target = host if not explicit_port else self._format_host_port(host, port)
        return NormalizedTarget(host=host, port=port, display_target=display_target, full_target=url_text)


    def _looks_like_url(self, text: str) -> bool:
        stripped_text = text.strip()
        if not stripped_text:
            return False

        # If it contains any of these, it's in the form of a URL
        return (
            "://" in stripped_text
            or "/" in stripped_text
            or "?" in stripped_text
            or "#" in stripped_text
        )


    def _parse_host_optional_port(self, text: str, default_port: int = 443) -> tuple[str, int, bool]:
        raw_text = text.strip()

        if not raw_text:
            raise ValueError("Please enter a hostname.")

        explicit_port = False

        # Handle IPv6 ([::1]:443)
        if raw_text.startswith("["):
            closing_index = raw_text.find("]")
            if closing_index == -1:
                raise ValueError("Invalid bracketed host. Example: [::1]:443")

            host = raw_text[1:closing_index].strip()
            remainder = raw_text[closing_index + 1 :].strip()

            if remainder.startswith(":"):
                port_text = remainder[1:].strip()
                if not port_text.isdigit():
                    raise ValueError("Port must be a number (1 - 65535).")
                port = int(port_text)
                explicit_port = True
            else:
                port = default_port

            if not (1 <= port <= 65535):
                raise ValueError("Port must be in the range 1 - 65535")

            return host, port, explicit_port

        # Normal hostname with optional port
        host = raw_text
        port = default_port

        if ":" in raw_text:
            possible_host, possible_port = raw_text.rsplit(":", 1)
            if possible_port.isdigit():
                host = possible_host.strip()
                port = int(possible_port)
                explicit_port = True

        if not host:
            raise ValueError("Hostname cannot be empty.")
        if not (1 <= port <= 65535):
            raise ValueError("Port must be in the range 1 - 65535")

        return host, port, explicit_port


    def _infer_method_from_server(self, server: str) -> str:
        try:
            ipaddress.ip_address(server.strip("[]"))
            return self.METHOD_IP
        except ValueError:
            return self.METHOD_HOSTNAME


    def _clear_invalid_markers(self) -> None:
        for widget in (self.ip_target_line_edit, self.hostname_target_line_edit, self.url_target_line_edit):
            widget.setProperty("invalid", False)
            self._repolish(widget)


    def _mark_activate_input_invalid(self) -> None:
        method = self._current_method()
        if method == self.METHOD_IP:
            active_widget = self.ip_target_line_edit
        elif method == self.METHOD_HOSTNAME:
            active_widget = self.hostname_target_line_edit
        else:
            active_widget = self.url_target_line_edit

        active_widget.setProperty("invalid", True)
        self._repolish(active_widget)


    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()


    def _save_and_close(self) -> None:
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None and not save_button.isEnabled():
            return

        try:
            normalized = self._normalized_target_from_ui()
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid target", str(exc))
            return

        interval_s = self._selected_seconds(
            self.interval_button_group,
            self.interval_custom_radio_button,
            self.interval_custom_spin_box,
        )
        
        timeout_s = self._selected_seconds(
            self.timeout_button_group,
            self.timeout_custom_radio_button,
            self.timeout_custom_spin_box,
        )

        # Persist raw UI state
        method = self._current_method()
        full_target = normalized.full_target
        if method != self.METHOD_URL:
            full_target = None

        self.settings.setValue("endpoint/method", method)
        self.settings.setValue("endpoint/ip_text", self.ip_target_line_edit.text().strip())
        self.settings.setValue("endpoint/ip_port", self.ip_port_spin_box.value())
        self.settings.setValue("endpoint/hostname_text", self.hostname_target_line_edit.text().strip())
        self.settings.setValue("endpoint/url_text", self.url_target_line_edit.text().strip())
        self.settings.setValue("endpoint/display_target", normalized.display_target)
        self.settings.setValue("endpoint/full_target", full_target)

        config = MonitorConfig(
            server=normalized.host,
            port=int(normalized.port),
            interval_s=float(interval_s),
            timeout_s=float(timeout_s),
        )

        config.save()
        self.accept()
