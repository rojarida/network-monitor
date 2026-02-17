from __future__ import annotations

import ipaddress
from typing import Any, ClassVar
from dataclasses import dataclass

from PySide6.QtCore import QSettings
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
)


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



def is_valid_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")

        self.server_line_edit = QLineEdit()
        self.server_line_edit.setPlaceholderText("e.g., 1.1.1.1")

        self.port_spin_box = QSpinBox()
        self.port_spin_box.setRange(1, 65535)
        
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

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        self.button_box.accepted.connect(self._save_and_close)
        self.button_box.rejected.connect(self.reject)

        form_layout = QFormLayout()
        form_layout.addRow("Server IP: ", self.server_line_edit)
        form_layout.addRow("Port: ", self.port_spin_box)
        form_layout.addRow("Check Interval: ", self.interval_group_box)
        form_layout.addRow("Timeout: ", self.timeout_group_box)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.validation_label)
        main_layout.addWidget(self.button_box)

        self.server_line_edit.textChanged.connect(self._update_validation_ui)

        self._load_settings()
        self._update_validation_ui()


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


    def _load_settings(self) -> None:
        config = MonitorConfig.load()

        self.server_line_edit.setText(config.server)
        self.port_spin_box.setValue(int(config.port))

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


    def _update_validation_ui(self) -> None:
        server_text = self.server_line_edit.text().strip()

        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        if save_button is None:
            return

        if server_text == "":
            self.validation_label.setText("")
            self.server_line_edit.setStyleSheet("")
            save_button.setEnabled(False)
            return

        is_valid = is_valid_ip_address(server_text)

        self.validation_label.setText("" if is_valid else "Please enter a valid IPv4 or IPv6 address.")
        self.server_line_edit.setStyleSheet("" if is_valid else "border: 1px solid #CC3333")
        save_button.setEnabled(is_valid)


    def current_config(self) -> MonitorConfig:
        interval_s = self._selected_seconds(
            self.interval_button_group,
            self.interval_custom_radio_button,
            self.interval_custom_spin_box,
        )
        timeout_s = self._selected_seconds(
            self.timeout_button_group,
            self.timeout_custom_radio_button,
            self.timeout_custom_spin_box
        )

        return MonitorConfig(
            server=self.server_line_edit.text().strip(),
            port=int(self.port_spin_box.value()),
            interval_s=float(interval_s),
            timeout_s=float(timeout_s),
        )

    
    def _save_and_close(self) -> None:
        config = self.current_config()

        if not is_valid_ip_address(config.server):
            QMessageBox.critical(self, "Invalid IP", f"'{config.server}' is not a valid IP address.")
            return

        config.save()
        self.accept()
