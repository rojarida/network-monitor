from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

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

from network_monitor.ui.widgets.section_card import make_titled_card
from network_monitor.ui.widgets.seconds_group import SecondsGroup
from network_monitor.ui.help.tooltips import SETTINGS_TOOLTIPS
from network_monitor.ui.dialogs.settings.sections.target_section import TargetSection


class SettingsDialog(QDialog):
    def __init__(self, settings_store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._settings_store = settings_store

        self.setWindowTitle("Settings")
        self.setFixedSize(650, 500)
        self.setObjectName("settings_dialog")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.target_section_widget = TargetSection()
        self.target_section = make_titled_card(
            "Target",
            self.target_section_widget,
            "target_card",
            center_horizontally=False,
        )

        preset_values_seconds = [1.0, 2.0, 5.0]
        self.interval_group = SecondsGroup(
            preset_values_seconds,
            tooltip_text=SETTINGS_TOOLTIPS.get("custom_interval", ""),
        )
        self.timeout_group = SecondsGroup(
            preset_values_seconds,
            tooltip_text=SETTINGS_TOOLTIPS.get("custom_timeout", ""),
        )

        self.interval_section = make_titled_card("Check Interval", self.interval_group, "interval_card")
        self.timeout_section = make_titled_card("Timeout Interval", self.timeout_group, "timeout_card")

        # Validation + buttons
        self.validation_label = QLabel("")
        self.validation_label.setObjectName("validation_label")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        self.button_box.accepted.connect(self._save_and_close)
        self.button_box.rejected.connect(self.reject)

        # Layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)
        root_layout.addWidget(self.target_section)
        root_layout.addWidget(self.interval_section)
        root_layout.addWidget(self.timeout_section)
        root_layout.addWidget(self.validation_label)
        root_layout.addWidget(self.button_box)

        self.target_section_widget.changed.connect(self._update_validation_ui)
        self.interval_group.changed.connect(self._update_validation_ui)
        self.timeout_group.changed.connect(self._update_validation_ui)
        
        self._load_settings()
        self._update_validation_ui()

    def _load_settings(self) -> None:
        settings = self._settings_store.load_settings()
        dialog_state = self._settings_store.load_dialog_state()

        # If no raw inputs were ever saved, fall back to stored settings
        if not dialog_state.ip_address and not dialog_state.hostname and not dialog_state.url:
            inferred_method = settings.target_method or TargetSection.infer_method_from_server(settings.host)
            dialog_state = SettingsDialogState(
                method=inferred_method,
                ip_address=settings.host if inferred_method == METHOD_IP else "",
                ip_port=int(settings.port),
                hostname=settings.target_text if inferred_method == METHOD_HOSTNAME else "",
                url=settings.target_text if inferred_method == METHOD_URL else "", 
            )

        self.target_section_widget.set_state(dialog_state)

        self.interval_group.set_seconds(settings.interval_seconds)
        self.timeout_group.set_seconds(settings.timeout_seconds)

        self._update_validation_ui()

    def _collect_dialog_state(self) -> SettingsDialogState:
        return self.target_section_widget.state()

    def _update_validation_ui(self, *_: object) -> None:
        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        if save_button is None:
            return

        self.target_section_widget.clear_invalid()
        self.target_section_widget.clear_previews()
        self.validation_label.setText("")
        self.validation_label.setVisible(False)

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
            self.target_section_widget.mark_current_input_invalid()
            save_button.setEnabled(False)
            return

        preview = f"Checking target: {format_host_port(normalized.host, normalized.port)}"
        self.target_section_widget.set_preview_for_current_method(preview)
        save_button.setEnabled(True)

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
