from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout
)

from network_monitor.core.normalize_target import (
    normalize_target,
    format_host_port,
    METHOD_IP,
    METHOD_HOSTNAME,
    METHOD_URL
)

from network_monitor.persistence.settings_store import SettingsStore
from network_monitor.core.models import SettingsData, SettingsDialogState
from network_monitor.ui.dialogs.settings.sections.target_section import TargetSection
from network_monitor.ui.dialogs.settings.view import SettingsDialogView


class SettingsDialog(QDialog):
    def __init__(self, settings_store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._settings_store = settings_store

        self.setWindowTitle("Settings")
        self.setFixedSize(650, 500)
        self.setObjectName("settings_dialog")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        self.view = SettingsDialogView(self)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.view)

        self.view.changed.connect(self._update_validation_ui)
        self.view.accepted.connect(self._save_and_close)
        self.view.rejected.connect(self.reject)

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

        self.view.target_section_widget.set_state(dialog_state)

        self.view.interval_group.set_seconds(settings.interval_seconds)
        self.view.timeout_group.set_seconds(settings.timeout_seconds)

        self._update_validation_ui()

    def _collect_dialog_state(self) -> SettingsDialogState:
        return self.view.target_section_widget.state()

    def _update_validation_ui(self, *_: object) -> None:
        save_button = self.view.button_box.button(QDialogButtonBox.StandardButton.Save)
        if save_button is None:
            return

        self.view.target_section_widget.clear_invalid()
        self.view.target_section_widget.clear_previews()
        self.view.validation_label.setText("")
        self.view.validation_label.setVisible(False)

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
            self.view.validation_label.setText(str(exc))
            self.view.validation_label.setVisible(True)
            self.view.target_section_widget.mark_current_input_invalid()
            save_button.setEnabled(False)
            return

        preview = f"Checking target: {format_host_port(normalized.host, normalized.port)}"
        self.view.target_section_widget.set_preview_for_current_method(preview)
        save_button.setEnabled(True)

    def _save_and_close(self) -> None:
        save_button = self.view.button_box.button(QDialogButtonBox.StandardButton.Save)
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

        interval_seconds = self.view.interval_group.seconds()
        timeout_seconds = self.view.timeout_group.seconds()

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
