"""Dialog for creating and editing menu items."""

from collections.abc import Iterable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


class MenuItemDialog(QDialog):
    """Collect valid name, category, and price values for a menu item."""

    def __init__(
        self,
        title: str,
        categories: Iterable[str],
        name: str = "",
        category: str = "",
        price: float = 0.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(title)
        self.setMinimumWidth(340)

        self.name_input = QLineEdit(name)
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(categories)
        self.category_input.setCurrentText(category)

        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(2)
        self.price_input.setMaximum(999_999.99)
        self.price_input.setValue(price)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #b3261e;")

        form_layout = QFormLayout()
        form_layout.addRow("Name", self.name_input)
        form_layout.addRow("Category", self.category_input)
        form_layout.addRow("Price", self.price_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

        self.name_input.setFocus()

    @property
    def values(self) -> tuple[str, str, float]:
        """Return the values entered in the dialog."""
        return (
            self.name_input.text().strip(),
            self.category_input.currentText().strip(),
            self.price_input.value(),
        )

    def save(self) -> None:
        """Validate the inputs before closing with an accepted result."""
        name, category, price = self.values
        if not name:
            self.error_label.setText("Name is required.")
            return
        if not category:
            self.error_label.setText("Category is required.")
            return
        if price <= 0:
            self.error_label.setText("Price must be greater than 0.")
            return

        self.accept()
