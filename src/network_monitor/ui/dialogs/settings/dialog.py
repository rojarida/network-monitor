from __future__ import annotations

import ipaddress

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
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
from network_monitor.core.normalize_target import (
    normalize_target,
    format_host_port,
    METHOD_IP,
    METHOD_HOSTNAME,
    METHOD_URL
)
from network_monitor.persistence.settings_store import (
    SettingsStore,
    SettingsData,
    SettingsDialogState,
)
from network_monitor.ui.widgets.seconds_group import SecondsGroup


class SettingsDialog(QDialog):
    def __init__(self, settings_store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._settings_store = settings_store

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

        self.interval_group = SecondsGroup(
            preset_values_seconds,
            tooltip_text=SETTINGS_TOOLTIPS.get("custom_interval", "")
        )
        self.timeout_group = SecondsGroup(
            preset_values_seconds,
            tooltip_text=SETTINGS_TOOLTIPS.get("custom_timeout", "")
        )

        self.interval_section = self._make_titled_card("Check Interval", self.interval_group, "interval_card")
        self.timeout_section = self._make_titled_card("Timeout Interval", self.timeout_group, "timeout_card")

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
        self.interval_group.changed.connect(self._update_validation_ui)
        self.timeout_group.changed.connect(self._update_validation_ui)


        self._load_settings()


    def _ensure_default_target_for_method(self) -> None:
        method = self._current_method()

        if method == METHOD_IP and not self.ip_target_line_edit.text().strip():
            self.ip_target_line_edit.setText("1.1.1.1")
            self.ip_port_spin_box.setValue(443)

        elif method == METHOD_HOSTNAME and not self.hostname_target_line_edit.text().strip():
            self.hostname_target_line_edit.setText("google.com")

        elif method == METHOD_URL and not self.url_target_line_edit.text().strip():
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

    def _centered_row(self, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(widget)
        layout.addStretch(1)

        return wrapper

    def _current_method(self) -> str:
        if self.hostname_method_radio_button.isChecked():
            return METHOD_HOSTNAME
        if self.url_method_radio_button.isChecked():
            return METHOD_URL
        return METHOD_IP

    def _on_target_method_changed(self, *_: object) -> None:
        method = self._current_method()
        if method == METHOD_IP:
            self.target_stack_widget.setCurrentIndex(0)
        elif method == METHOD_HOSTNAME:
            self.target_stack_widget.setCurrentIndex(1)
        else:
            self.target_stack_widget.setCurrentIndex(2)

        self._clear_invalid_markers()
        self._ensure_default_target_for_method()
        self._update_validation_ui()


    def _load_settings(self) -> None:
        settings = self._settings_store.load_settings()
        dialog_state = self._settings_store.load_dialog_state()

        # If no raw inputs were ever saved, fall back to stored settings
        if not dialog_state.ip_address and not dialog_state.hostname and not dialog_state.url:
            inferred_method = settings.target_method or self._infer_method_from_server(settings.host)
            dialog_state = SettingsDialogState(
                method=inferred_method,
                ip_address=settings.host if inferred_method == METHOD_IP else "",
                ip_port=int(settings.port),
                hostname=settings.target_text if inferred_method == METHOD_HOSTNAME else "",
                url=settings.target_text if inferred_method == METHOD_URL else "", 
            )

        # Target method
        if dialog_state.method == METHOD_HOSTNAME:
            self.hostname_method_radio_button.setChecked(True)
        elif dialog_state.method == METHOD_URL:
            self.url_method_radio_button.setChecked(True)
        else:
            self.ip_method_radio_button.setChecked(True)

        # Restore raw inputs
        self.ip_target_line_edit.setText(dialog_state.ip_address)
        self.ip_port_spin_box.setValue(int(dialog_state.ip_port))
        self.hostname_target_line_edit.setText(dialog_state.hostname)
        self.url_target_line_edit.setText(dialog_state.url)

        self.interval_group.set_seconds(settings.interval_seconds)
        self.timeout_group.set_seconds(settings.timeout_seconds)

        self._clear_invalid_markers()
        self._ensure_default_target_for_method()
        self._update_validation_ui()


    def _collect_dialog_state(self) -> SettingsDialogState:
        return SettingsDialogState(
            method=self._current_method(),
            ip_address=self.ip_target_line_edit.text().strip(),
            ip_port=int(self.ip_port_spin_box.value()),
            hostname=self.hostname_target_line_edit.text().strip(),
            url=self.url_target_line_edit.text().strip(),
        )

    def _update_validation_ui(self, *_: object) -> None:
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        if save_button is None:
            return

        self._clear_invalid_markers()
        self.validation_label.setText("")
        self.validation_label.setVisible(False)
        self.ip_preview_label.setText("")
        self.hostname_preview_label.setText("")
        self.url_preview_label.setText("")

        state = self._collect_dialog_state()

        try:
            normalized = normalize_target(
                state.method,
                ip_address=state.ip_address,
                ip_port=state.ip_port,
                hostname=state.hostname,
                url=state.url
            )
        except ValueError as exc:
            self.validation_label.setText(str(exc))
            self.validation_label.setVisible(True)
            self._mark_activate_input_invalid()
            save_button.setEnabled(False)
            return

        preview = f"Checking target: {format_host_port(normalized.host, normalized.port)}"
        if state.method == METHOD_IP:
            self.ip_preview_label.setText(preview)
        elif state.method == METHOD_HOSTNAME:
            self.hostname_preview_label.setText(preview)
        else:
            self.url_preview_label.setText(preview)

        save_button.setEnabled(True)

    def _infer_method_from_server(self, server: str) -> str:
        try:
            ipaddress.ip_address(server.strip("[]"))
            return METHOD_IP
        except ValueError:
            return METHOD_HOSTNAME

    def _clear_invalid_markers(self) -> None:
        for widget in (self.ip_target_line_edit, self.hostname_target_line_edit, self.url_target_line_edit):
            widget.setProperty("invalid", False)
            self._repolish(widget)

    def _mark_activate_input_invalid(self) -> None:
        method = self._current_method()
        if method == METHOD_IP:
            active_widget = self.ip_target_line_edit
        elif method == METHOD_HOSTNAME:
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

        state = self._collect_dialog_state()

        try:
            normalized = normalize_target(
                state.method,
                ip_address=state.ip_address,
                ip_port=state.ip_port,
                hostname=state.hostname,
                url=state.url,
            )
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid target", str(exc))
            return

        interval_seconds = self.interval_group.seconds()
        timeout_seconds = self.timeout_group.seconds()

        # Store raw target text for the chosen method
        if state.method == METHOD_IP:
            target_text = state.ip_address
        elif state.method == METHOD_HOSTNAME:
            target_text = state.hostname
        else:
            target_text = state.url

        settings = SettingsData(
            target_method=state.method,
            target_text=target_text,
            host=normalized.host,
            port=int(normalized.port),
            display_target=normalized.display_target,
            full_target=normalized.full_target,
            port_was_explicit=normalized.port_was_explicit,
            interval_seconds=float(interval_seconds),
            timeout_seconds=float(timeout_seconds),
        )

        self._settings_store.save_dialog_state(state)
        self._settings_store.save_settings(settings)
        self.accept()
