from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QLabel, QDialogButtonBox, QGridLayout

from network_monitor.ui.widgets import make_titled_card
from network_monitor.ui.help import SETTINGS_TOOLTIPS

from .widgets import SecondsGroup
from .sections import TargetSection


class SettingsDialogView(QWidget):
    changed = Signal()
    accepted = Signal()
    rejected = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.target_section_widget = TargetSection()
        self.target_section = make_titled_card(
            "Target", self.target_section_widget, "target_card", center_horizontally=False
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

        self.validation_label = QLabel("")
        self.validation_label.setObjectName("validation_label")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )
        self.button_box.accepted.connect(self.accepted)
        self.button_box.rejected.connect(self.rejected)

        save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)

        if save_button is not None:
            save_button.setObjectName("save_button")
            save_button.setIcon(QIcon())

        if cancel_button is not None:
            cancel_button.setObjectName("cancel_button")
            cancel_button.setIcon(QIcon())

        root_layout = QGridLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setHorizontalSpacing(12)
        root_layout.setVerticalSpacing(12)

        root_layout.addWidget(self.target_section, 0, 0, 1, 2)
        root_layout.addWidget(self.interval_section, 1, 0)
        root_layout.addWidget(self.timeout_section, 1, 1)
        root_layout.setColumnStretch(0, 1)
        root_layout.setColumnStretch(1, 1)
        root_layout.setRowStretch(0, 0)
        root_layout.setRowStretch(1, 0)
        root_layout.setRowStretch(2, 1)
        root_layout.setRowStretch(3, 0)
        root_layout.addWidget(self.validation_label, 2, 0, 1, 2)
        root_layout.addWidget(self.button_box, 3, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignRight)

        self.target_section_widget.changed.connect(self.changed)
        self.interval_group.changed.connect(self.changed)
        self.timeout_group.changed.connect(self.changed)
