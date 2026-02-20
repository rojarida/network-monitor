from __future__ import annotations

import ipaddress
import re

from urllib.parse import urlsplit
from typing import Any
from dataclasses import dataclass

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QStackedLayout,
    QStackedWidget,
    QWidget,
    QSizePolicy,
)


# Regex for handling URLs
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


@dataclass(frozen=True)
class NormalizedTarget:
    host: str
    port: int
    display_target: str


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
        self.setWindowTitle("Settings")
        self.settings: QSettings = QSettings()
        self._has_user_edited_target = False

        # Target method
        self.target_method_group = QButtonGroup(self)

        self.ip_method_radio_button = QRadioButton("IP Address")
        self.hostname_method_radio_button = QRadioButton("Hostname")
        self.url_method_radio_button = QRadioButton("URL")

        self.target_method_group.addButton(self.ip_method_radio_button)
        self.target_method_group.addButton(self.hostname_method_radio_button)
        self.target_method_group.addButton(self.url_method_radio_button)

        target_method_group_box = QGroupBox("")
        target_method_layout = QVBoxLayout(target_method_group_box)
        target_method_layout.addWidget(self.ip_method_radio_button)
        target_method_layout.addWidget(self.hostname_method_radio_button)
        target_method_layout.addWidget(self.url_method_radio_button)

        self.target_stack_widget = QStackedLayout()

        # IP Page
        self.ip_target_line_edit = QLineEdit()
        self.ip_target_line_edit.setPlaceholderText("e.g., 1.1.1.1 or 2606:4700:4700::1111")
        self.ip_port_spin_box = QSpinBox()
        self.ip_port_spin_box.setRange(1, 65535)
        self.ip_port_spin_box.setValue(443)

        ip_page_widget = QWidget()
        ip_page_form_layout = QFormLayout(ip_page_widget)
        ip_page_form_layout.addRow("IP:", self.ip_target_line_edit)
        ip_page_form_layout.addRow("Port:", self.ip_port_spin_box)

        # Hostname Page
        self.hostname_target_line_edit = QLineEdit()
        self.hostname_target_line_edit.setPlaceholderText("e.g., google.com (optional: :443)")

        hostname_page_widget = QWidget()
        hostname_page_form_layout = QFormLayout(hostname_page_widget)
        hostname_page_form_layout.addRow("Hostname:", self.hostname_target_line_edit)

        # URL Page
        self.url_target_line_edit = QLineEdit()
        self.url_target_line_edit.setPlaceholderText("e.g., https://www.google.com:443/path")
        self.url_preview_label = QLabel("")
        self.url_preview_label.setTextInteractionFlags(
            self.url_preview_label.textInteractionFlags()
        )

        url_page_widget = QWidget()
        url_page_layout = QVBoxLayout(url_page_widget)
        url_page_form_layout = QFormLayout()
        url_page_form_layout.addRow("URL:", self.url_target_line_edit)
        url_page_layout.addLayout(url_page_form_layout)
        url_page_layout.addWidget(self.url_preview_label)

        self.target_stack_widget = QStackedWidget()
        self.target_stack_widget.addWidget(ip_page_widget)          # Index 0
        self.target_stack_widget.addWidget(hostname_page_widget)    # Index 1
        self.target_stack_widget.addWidget(url_page_widget)         # Index 2

        self.target_container_widget = QWidget()
        target_container_layout = QHBoxLayout(self.target_container_widget)
        target_container_layout.setContentsMargins(0, 0, 0, 0)
        target_container_layout.setSpacing(12)

        target_method_group_box.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        target_container_layout.addWidget(target_method_group_box, 0, Qt.AlignmentFlag.AlignTop)

        # Let input fields fill the space centered vertically/horizontally
        inputs_wrapper = QWidget()
        inputs_wrapper_layout = QVBoxLayout(inputs_wrapper)
        inputs_wrapper_layout.setContentsMargins(0, 0, 0, 0)

        inputs_wrapper_layout.addStretch(1)
        inputs_wrapper_layout.addWidget(self.target_stack_widget)
        inputs_wrapper_layout.addStretch(1)

        target_container_layout.addWidget(inputs_wrapper, 1)

        # Radio groups for interval/timeout (presets and custom)
        preset_values_seconds = [0.5, 1.0, 2.0, 5.0]

        (
            self.interval_group_box,
            self.interval_button_group,
            self.interval_custom_radio_button,
            self.interval_custom_spin_box,
        ) = self._build_seconds_radio_group(
            title="Check Interval",
            preset_values=preset_values_seconds,
        )

        (
            self.timeout_group_box,
            self.timeout_button_group,
            self.timeout_custom_radio_button,
            self.timeout_custom_spin_box,
        ) = self._build_seconds_radio_group(
            title="Timeout",
            preset_values=preset_values_seconds,
        )

        self.validation_label = QLabel("")

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )
        self.button_box.accepted.connect(self._save_and_close)
        self.button_box.rejected.connect(self.reject)

        form_layout = QFormLayout()
        form_layout.addRow("Target Method: ", self.target_container_widget)
        form_layout.addRow("Check Interval: ", self.interval_group_box)
        form_layout.addRow("Timeout: ", self.timeout_group_box)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.validation_label)
        main_layout.addWidget(self.button_box)

        # Signals
        self.ip_method_radio_button.toggled.connect(self._on_target_method_changed)
        self.hostname_method_radio_button.toggled.connect(self._on_target_method_changed)
        self.url_method_radio_button.toggled.connect(self._on_target_method_changed)

        self.ip_target_line_edit.textChanged.connect(self._update_validation_ui)
        self.hostname_target_line_edit.textChanged.connect(self._update_validation_ui)
        self.url_target_line_edit.textChanged.connect(self._update_validation_ui)

        self.ip_port_spin_box.valueChanged.connect(self._update_validation_ui)

        self.setFixedSize(600, 500)
        self._load_settings()
        self._on_target_method_changed()
        self._update_validation_ui()


    def _ensure_default_target_for_method(self) -> None:
        method = self._current_method()

        if method == self.METHOD_IP and not self.ip_target_line_edit.text().strip():
            self.ip_target_line_edit.setText("1.1.1.1")
            self.ip_port_spin_box.setValue(443)

        elif method == self.METHOD_HOSTNAME and not self.hostname_target_line_edit.text().strip():
            self.hostname_target_line_edit.setText("google.com")

        elif method == self.METHOD_URL and not self.url_target_line_edit.text().strip():
            self.url_target_line_edit.setText("https://google.com")


    def _build_seconds_radio_group(
        self,
        title: str,
        preset_values: list[float],
    ) -> tuple[QGroupBox, QButtonGroup, QRadioButton, QDoubleSpinBox]:
        # Title parameter not used, redundant at the moment
        group_box = QGroupBox("")
        outer_layout = QVBoxLayout(group_box)
        
        button_group = QButtonGroup(self)

        # Preset radio buttons
        for seconds_value in preset_values:
            preset_radio_button = QRadioButton(f"{seconds_value:g} s")
            preset_radio_button.setProperty("seconds_value", seconds_value)
            button_group.addButton(preset_radio_button)
            outer_layout.addWidget(preset_radio_button)

        # Custom option
        custom_row_layout = QHBoxLayout()
        custom_radio_button = QRadioButton("Custom: ")
        custom_spin_box = QDoubleSpinBox()
        custom_spin_box.setRange(1, 60)
        custom_spin_box.setSingleStep(0.5)
        custom_spin_box.setDecimals(1)
        custom_spin_box.setSuffix(" s")
        custom_spin_box.setEnabled(False)

        button_group.addButton(custom_radio_button)

        custom_row_layout.addWidget(custom_radio_button)
        custom_row_layout.addWidget(custom_spin_box)
        custom_row_layout.addStretch(1)
        outer_layout.addLayout(custom_row_layout)

        def on_button_clicked() -> None:
            custom_spin_box.setEnabled(custom_radio_button.isChecked())

        button_group.buttonClicked.connect(on_button_clicked)

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

        return group_box, button_group, custom_radio_button, custom_spin_box


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
                custom_spin_box.setEnabled(False)
                return

        # Otherwise, select Custom
        custom_radio_button.setChecked(True)
        custom_spin_box.setEnabled(True)
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
        self.url_preview_label.setText("")

        try:
            normalized = self._normalized_target_from_ui(validate_only=True)
            host, port = normalized.host, normalized.port
        except ValueError as exc:
            self.validation_label.setText(str(exc))
            self._mark_activate_input_invalid()
            save_button.setEnabled(False)
            return

        # For URL, show the normalized connection target
        if self._current_method == self.METHOD_URL:
            self.url_preview_label.setText(f"Will connect to: {host}:{port}")

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

            if ascii_host.lower() != "localhost" and "." not in ascii_host:
                raise ValueError(
                    'Please enter a fully qualified domain name (e.g., "google.com" or use IP Address).\n' 
                    '"localhost" is allowed.')

            if not _HOSTNAME_RE.match(ascii_host.rstrip(".")):
                raise ValueError("Invalid hostname.")

            display_target = host if not explicit_port else self._format_host_port(host, port)
            return NormalizedTarget(host=host, port=port, display_target=display_target)


        # Target method is URL
        raw_url_text = self.url_target_line_edit.text().strip()
        if not raw_url_text:
            raise ValueError("Please enter a URL.")

        # Allow scheme to be omitted (assume https)
        url_text = raw_url_text if "://" in raw_url_text else f"https://{raw_url_text}"
        parts = urlsplit(url_text)

        if not parts.hostname:
            raise ValueError("Please enter a valid URL (must include a host).")

        host = parts.hostname
        explicit_port = parts.port is not None

        if parts.port is not None:
            port = int(parts.port)
        else:
            if parts.scheme == "http":
                port = 80
            else:
                port = 443

        if not (1 <= port <= 65535):
            raise ValueError("Port out of range.")

        display_target = host if not explicit_port else self._format_host_port(host, port)
        return NormalizedTarget(host=host, port=port, display_target=display_target)


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
        self.settings.setValue("endpoint/method", method)
        self.settings.setValue("endpoint/ip_text", self.ip_target_line_edit.text().strip())
        self.settings.setValue("endpoint/ip_port", self.ip_port_spin_box.value())
        self.settings.setValue("endpoint/hostname_text", self.hostname_target_line_edit.text().strip())
        self.settings.setValue("endpoint/url_text", self.url_target_line_edit.text().strip())
        self.settings.setValue("endpoint/display_target", normalized.display_target)

        config = MonitorConfig(
            server=normalized.host,
            port=int(normalized.port),
            interval_s=float(interval_s),
            timeout_s=float(timeout_s),
        )

        config.save()
        self.accept()
