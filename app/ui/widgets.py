"""Custom UI widgets for CafePOS."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QDoubleSpinBox


class AutoSelectDoubleSpinBox(QDoubleSpinBox):
    """A QDoubleSpinBox that automatically selects all text when focused."""

    def focusInEvent(self, event: QFocusEvent) -> None:
        """Select all text on focus so typing replaces the existing value."""
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)
