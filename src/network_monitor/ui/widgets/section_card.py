from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def make_titled_card(
    title_text: str,
    body_widget: QWidget,
    card_name: str,
    *,
    center_horizontally: bool = True,
) -> QWidget:
    """
    Returns a widget containing:
      - a centered title label
      - a styled QFrame "card" (objectName=card_name)
      - body_widget placed inside the card (optionally centered horizontally)
    """
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
