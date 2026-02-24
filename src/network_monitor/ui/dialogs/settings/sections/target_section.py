from __future__ import annotations

import ipaddress

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy
)

from network_monitor.core.normalize_target import (
    METHOD_IP,
    METHOD_HOSTNAME,
    METHOD_URL
)
from network_monitor.core.models import SettingsDialogState
from network_monitor.ui.help.tooltips import SETTINGS_TOOLTIPS, apply_tooltip


class TargetSection(QWidget):
    """Target Method UI: Method radios, stacked inputs, and preview labels."""
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

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
        target_method_group_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
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
        method_container_layout.setSpacing(6)
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
        self.ip_preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
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

        ip_page = QWidget()
        ip_page_layout = QVBoxLayout(ip_page)
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
        self.hostname_preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.hostname_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hostname_form_container = QWidget()
        hostname_form_layout = QFormLayout(hostname_form_container)
        hostname_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hostname_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        hostname_label = QLabel("Hostname:")
        hostname_label.setProperty("role", "field_label")
        apply_tooltip((hostname_label,), SETTINGS_TOOLTIPS["hostname_input"])

        hostname_form_layout.addRow(hostname_label, self.hostname_target_line_edit)

        hostname_page = QWidget()
        hostname_page_layout = QVBoxLayout(hostname_page)
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
        self.url_preview_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.url_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        url_page = QWidget()
        url_page_layout = QVBoxLayout(url_page)
        url_page_layout.setContentsMargins(0, 0, 0, 0)
        url_page_layout.setSpacing(0)

        url_form_layout = QFormLayout()
        url_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        url_form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        url_label = QLabel("URL:")
        url_label.setProperty("role", "field_label")
        apply_tooltip((url_label,), SETTINGS_TOOLTIPS["url_input"])
        
        url_page_layout.addStretch(1)
        url_form_layout.addRow(url_label, self.url_target_line_edit)
        url_page_layout.addLayout(url_form_layout)
        url_page_layout.addStretch(1)
        url_page_layout.addWidget(self._centered_row(self.url_preview_label))

        # Stack
        self.target_stack_widget = QStackedWidget()
        self.target_stack_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.target_stack_widget.addWidget(ip_page)          # Index 0
        self.target_stack_widget.addWidget(hostname_page)    # Index 1
        self.target_stack_widget.addWidget(url_page)         # Index 2

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        root_layout.addWidget(method_container, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Let input fields fill the space centered vertically/horizontally
        inputs_wrapper = QWidget()
        inputs_wrapper_layout = QVBoxLayout(inputs_wrapper)
        inputs_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        inputs_wrapper_layout.setSpacing(0)
        inputs_wrapper_layout.addWidget(self.target_stack_widget)

        root_layout.addWidget(inputs_wrapper, 1)

        # Signals
        self.target_method_group.idToggled.connect(self._on_target_method_changed)
        self.ip_target_line_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.hostname_target_line_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.url_target_line_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.ip_port_spin_box.valueChanged.connect(lambda *_: self.changed.emit())

        # Default
        self.hostname_method_radio_button.setChecked(True)
        self.ensure_defaults()

    # ----- Public methods -----

    def current_method(self) -> str:
        if self.hostname_method_radio_button.isChecked():
            return METHOD_HOSTNAME
        elif self.url_method_radio_button.isChecked():
            return METHOD_URL
        else:
            return METHOD_IP

    def set_state(self, state: SettingsDialogState) -> None:
        if state.method == METHOD_HOSTNAME:
            self.hostname_method_radio_button.setChecked(True)
        elif state.method == METHOD_URL:
            self.url_method_radio_button.setChecked(True)
        else:
            self.ip_method_radio_button.setChecked(True)

        # Raw inputs
        self.ip_target_line_edit.setText(state.ip_address)
        self.ip_port_spin_box.setValue(int(state.ip_port))
        self.hostname_target_line_edit.setText(state.hostname)
        self.url_target_line_edit.setText(state.url)

        self.clear_invalid()
        self.clear_previews()
        self.ensure_defaults()

    def state(self) -> SettingsDialogState:
        return SettingsDialogState(
            method=self.current_method(),
            ip_address=self.ip_target_line_edit.text().strip(),
            ip_port=int(self.ip_port_spin_box.value()),
            hostname=self.hostname_target_line_edit.text().strip(),
            url=self.url_target_line_edit.text().strip()
        )

    def ensure_defaults(self) -> None:
        method = self.current_method()

        if method == METHOD_IP and not self.ip_target_line_edit.text().strip():
            self.ip_target_line_edit.setText("1.1.1.1")
            self.ip_port_spin_box.setValue(443)

        elif method == METHOD_HOSTNAME and not self.hostname_target_line_edit.text().strip():
            self.hostname_target_line_edit.setText("google.com")

        elif method == METHOD_URL and not self.url_target_line_edit.text().strip():
            self.url_target_line_edit.setText("https://google.com")

    def clear_previews(self) -> None:
        self.ip_preview_label.setText("")
        self.hostname_preview_label.setText("")
        self.url_preview_label.setText("")

    def set_preview_for_current_method(self, preview_text: str) -> None:
        method = self.current_method()

        if method == METHOD_IP:
            self.ip_preview_label.setText(preview_text)
        elif method == METHOD_HOSTNAME:
            self.hostname_preview_label.setText(preview_text)
        else:
            self.url_preview_label.setText(preview_text)

    def clear_invalid(self) -> None:
        for widget in (self.ip_target_line_edit, self.hostname_target_line_edit, self.url_target_line_edit):
            widget.setProperty("invalid", False)
            self._repolish(widget)

    def mark_current_input_invalid(self) -> None:
        method = self.current_method()

        if method == METHOD_IP:
            active_widget = self.ip_target_line_edit
        elif method == METHOD_HOSTNAME:
            active_widget = self.hostname_target_line_edit
        else:
            active_widget = self.url_target_line_edit

        active_widget.setProperty("invalid", True)
        self._repolish(active_widget)

    @staticmethod
    def infer_method_from_server(server: str) -> str:
        try:
            ipaddress.ip_address(server.strip("[]"))
            return METHOD_IP
        except ValueError:
            return METHOD_HOSTNAME

    # ----- Private methods -----
    def _on_target_method_changed(self, *_: object) -> None:
        method = self.current_method()

        if method == METHOD_IP:
            self.target_stack_widget.setCurrentIndex(0)
        elif method == METHOD_HOSTNAME:
            self.target_stack_widget.setCurrentIndex(1)
        else:
            self.target_stack_widget.setCurrentIndex(2)

        self.clear_invalid()
        self.ensure_defaults()
        self.changed.emit()

    def _centered_row(self, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(widget)
        layout.addStretch(1)

        return wrapper

    def _repolish(self, widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
