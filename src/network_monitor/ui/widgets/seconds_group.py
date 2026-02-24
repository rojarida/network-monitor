from __future__ import annotations

from PySide6.QtCore import Qt, QObject, QEvent, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QDoubleSpinBox,
    QHBoxLayout,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from network_monitor.ui.help.tooltips import apply_tooltip


def _repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class CheckRadioOnInteractFilter(QObject):
    """If user interacts with the spinbox, select the associated radio."""
    def __init__(self, radio_button: QRadioButton, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._radio_button = radio_button

    def eventFilter(self, watched, event) -> bool:
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn):
            if not self._radio_button.isChecked():
                self._radio_button.setChecked(True)

        return False


class SecondsGroup(QWidget):
    """Preset seconds radios and custom seconds spinbox."""
    changed = Signal()

    def __init__(
        self,
        preset_values: list[float],
        *,
        tooltip_text: str | None = None,
        minimum: float = 0.5,
        maximum: float = 60.0,
        step: float = 0.5,
        decimals: int = 1,
        default_seconds: float = 1.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        
        self.button_group = QButtonGroup(self)

        # Vertical root: presets on top, custom on bottom.
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)

        # Presets row (centered)
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
            radio = QRadioButton(f"{seconds_value:g} s")
            radio.setProperty("seconds_value", float(seconds_value))
            radio.setProperty("role", "preset_radio")
            self.button_group.addButton(radio)
            presets_layout.addWidget(radio)

            radio.toggled.connect(self.changed)

        # Custom row (centered)
        custom_widget = QWidget()
        custom_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        custom_layout = QHBoxLayout(custom_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(0)

        custom_row = QWidget()
        custom_row_layout = QHBoxLayout(custom_row)
        custom_row_layout.setContentsMargins(0, 0, 0, 0)
        custom_row_layout.setSpacing(0)

        self.custom_radio_button = QRadioButton()
        self.custom_radio_button.setProperty("role", "preset_radio")

        self.custom_spin_box = QDoubleSpinBox()
        self.custom_spin_box.setProperty("role", "custom_spin")
        self.custom_spin_box.setRange(minimum, maximum)
        self.custom_spin_box.setDecimals(decimals)
        self.custom_spin_box.setSingleStep(step)
        self.custom_spin_box.setSuffix(" s")
        self.custom_spin_box.setMaximumWidth(90)

        # Keep enabled so it can be clicked/focused
        self.custom_spin_box.setEnabled(True)
        self.custom_spin_box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Start inactive (muted but clickable)
        self.custom_spin_box.lineEdit().setReadOnly(True)
        self.custom_spin_box.setProperty("inactive", True)
        _repolish(self.custom_spin_box)

        def set_custom_active(active: bool) -> None:
            self.custom_spin_box.setProperty("inactive", not active)
            self.custom_spin_box.lineEdit().setReadOnly(not active)
            self.custom_spin_box.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.UpDownArrows
            )
            _repolish(self.custom_spin_box)
            self.changed.emit()

        self.custom_radio_button.toggled.connect(set_custom_active)

        # Clicking/focusing the spinbox selects custom automatically
        self.spin_filter = CheckRadioOnInteractFilter(self.custom_radio_button, self)
        self.custom_spin_box.installEventFilter(self.spin_filter)

        self.custom_spin_box.valueChanged.connect(lambda _v: self.custom_radio_button.setChecked(True))
        self.custom_spin_box.valueChanged.connect(lambda _v: self.changed.emit())
        self.custom_radio_button.toggled.connect(self.changed)

        if tooltip_text:
            apply_tooltip((self.custom_radio_button,), tooltip_text)
            apply_tooltip((self.custom_spin_box,), tooltip_text)

        self.button_group.addButton(self.custom_radio_button)

        custom_row_layout.addWidget(self.custom_radio_button)
        custom_row_layout.addWidget(self.custom_spin_box)
        custom_layout.addWidget(custom_row, 0, Qt.AlignmentFlag.AlignHCenter)

        custom_center = QWidget()
        custom_center_layout = QHBoxLayout(custom_center)
        custom_center_layout.setContentsMargins(0, 0, 0, 0)
        custom_center_layout.setSpacing(0)
        custom_center_layout.addStretch(1)
        custom_center_layout.addWidget(custom_widget)
        custom_center_layout.addStretch(1)

        # Combine the two columns
        root_layout.addWidget(presets_center)
        root_layout.addWidget(custom_center)
        root_layout.addStretch(1)

        # Default selection
        self.set_seconds(default_seconds)

    def seconds(self) -> float:
        if self.custom_radio_button.isChecked():
            return float(self.custom_spin_box.value())

        checked = self.button_group.checkedButton()
        if checked is None:
            return 1.0

        preset_value = checked.property("seconds_value")
        return float(preset_value)

    def set_seconds(self, value: float) -> None:
        # If it matches a preset, select that preset
        for button in self.button_group.buttons():
            preset_value = button.property("seconds_value")
            if preset_value is not None and float(preset_value) == float(value):
                button.setChecked(True)
                return

        # Otherwise, select custom
        self.custom_radio_button.setChecked(True)
        self.custom_spin_box.setValue(float(value))
