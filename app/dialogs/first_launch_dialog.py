"""First-launch configuration dialog."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class FirstLaunchDialog(QDialog):
    """Collect the café details required before the dashboard is shown."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("CafePOS Setup")
        self.setMinimumWidth(340)

        self.cafe_name_input = QLineEdit()
        self.receipt_footer_input = QLineEdit()
        self.receipt_footer_input.setPlaceholderText("Thank you for visiting")
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b3261e;")

        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)
        form_layout.addRow("Cafe Name", self.cafe_name_input)
        form_layout.addRow("Receipt Footer", self.receipt_footer_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

        self.cafe_name_input.setFocus()

    @property
    def values(self) -> tuple[str, str]:
        """Return normalized setup values."""
        return self.cafe_name_input.text().strip(), self.receipt_footer_input.text().strip()

    def save(self) -> None:
        """Require a café name before completing first-launch setup."""
        cafe_name, _receipt_footer = self.values
        if not cafe_name:
            self.error_label.setText("Cafe Name is required.")
            return
        self.accept()
