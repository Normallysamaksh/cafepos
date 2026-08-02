"""Billing window for creating completed cafe orders."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.database import session_scope
from app.dialogs.discount_dialog import DiscountDialog
from app.services import (
    CartLine,
    Discount,
    calculate_order_totals,
    get_categories,
    get_menu_items,
    save_order,
    validate_payment,
)


class BillingWindow(QMainWindow):
    """Build and complete one in-memory cafe order at a time."""

    def __init__(self) -> None:
        super().__init__()

        self.cart: dict[int, CartLine] = {}
        self.discount: Discount | None = None
        self.menu_items: dict[int, object] = {}

        self.setWindowTitle("New Order")
        self.resize(1100, 700)
        self.setMinimumSize(820, 520)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search menu items")
        self.search_input.textChanged.connect(self.load_menu)

        self.categories_list = QListWidget()
        self.categories_list.currentTextChanged.connect(self.refresh_item_list)

        self.items_list = QListWidget()
        self.items_list.itemClicked.connect(self.add_menu_item)

        menu_panel = self.create_menu_panel()
        cart_panel = self.create_cart_panel()
        splitter = QSplitter()
        splitter.addWidget(self.categories_list)
        splitter.addWidget(menu_panel)
        splitter.addWidget(cart_panel)
        splitter.setSizes([180, 430, 360])

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.search_input)
        layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.load_menu()
        self.refresh_cart()

    def create_menu_panel(self) -> QWidget:
        """Create the central menu item panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Items"))
        layout.addWidget(self.items_list)
        return panel

    def create_cart_panel(self) -> QWidget:
        """Create the cart and checkout controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Cart"))

        self.cart_content = QWidget()
        self.cart_layout = QVBoxLayout(self.cart_content)
        self.cart_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_layout.setSpacing(8)

        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setWidget(self.cart_content)
        layout.addWidget(self.cart_scroll)

        self.subtotal_label = QLabel()
        self.discount_label = QLabel()
        self.total_label = QLabel()
        self.discount_button = QPushButton("Discount")
        self.discount_button.clicked.connect(self.open_discount_dialog)

        summary_layout = QFormLayout()
        summary_layout.addRow("Subtotal", self.subtotal_label)
        summary_layout.addRow("Discount", self.discount_label)
        summary_layout.addRow("Total", self.total_label)
        layout.addLayout(summary_layout)
        layout.addWidget(self.discount_button)

        self.service_type_input = QComboBox()
        self.service_type_input.addItems(["Dine In", "Takeaway"])

        self.cash_radio = QRadioButton("Cash")
        self.upi_radio = QRadioButton("UPI")
        self.split_radio = QRadioButton("Split Payment")
        self.cash_radio.setChecked(True)
        self.payment_group = QButtonGroup(self)
        for button in (self.cash_radio, self.upi_radio, self.split_radio):
            self.payment_group.addButton(button)
            button.toggled.connect(self.update_payment_controls)

        self.split_cash_input = self.amount_input()
        self.split_upi_input = self.amount_input()
        self.split_form = QWidget()
        split_layout = QFormLayout(self.split_form)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.addRow("Cash", self.split_cash_input)
        split_layout.addRow("UPI", self.split_upi_input)

        payment_box = QGroupBox("Payment Method")
        payment_layout = QVBoxLayout(payment_box)
        payment_layout.addWidget(self.cash_radio)
        payment_layout.addWidget(self.upi_radio)
        payment_layout.addWidget(self.split_radio)
        payment_layout.addWidget(self.split_form)

        checkout_form = QFormLayout()
        checkout_form.addRow("Service Type", self.service_type_input)
        layout.addLayout(checkout_form)
        layout.addWidget(payment_box)

        self.done_button = QPushButton("Done")
        self.done_button.clicked.connect(self.complete_order)
        layout.addWidget(self.done_button)

        return panel

    @staticmethod
    def amount_input() -> QDoubleSpinBox:
        """Create a two-decimal payment amount input."""
        amount_input = QDoubleSpinBox()
        amount_input.setDecimals(2)
        amount_input.setMaximum(999_999.99)
        return amount_input

    def load_menu(self) -> None:
        """Load menu data and refresh the category and item lists."""
        selected_category = self.categories_list.currentItem()
        selected_category_name = selected_category.text() if selected_category else ""

        with session_scope() as session:
            categories = get_categories(session)
            items = get_menu_items(session, self.search_input.text().strip())

        self.menu_items = {item.id: item for item in items}
        self.categories_list.blockSignals(True)
        self.categories_list.clear()
        self.categories_list.addItems(categories)
        if categories:
            matching_items = self.categories_list.findItems(selected_category_name, Qt.MatchFlag.MatchExactly)
            self.categories_list.setCurrentItem(matching_items[0] if matching_items else self.categories_list.item(0))
        self.categories_list.blockSignals(False)
        self.refresh_item_list()

    def refresh_item_list(self) -> None:
        """Show items for the selected category or the current name search."""
        selected_category = self.categories_list.currentItem()
        category_name = selected_category.text() if selected_category else ""
        show_all_matching_items = bool(self.search_input.text().strip())

        self.items_list.clear()
        for menu_item in self.menu_items.values():
            if not show_all_matching_items and menu_item.category != category_name:
                continue

            item = QListWidgetItem(f"{menu_item.name}\n₹{menu_item.price:.2f}")
            item.setData(Qt.ItemDataRole.UserRole, menu_item.id)
            self.items_list.addItem(item)

    def add_menu_item(self, item: QListWidgetItem) -> None:
        """Add a clicked item to the cart unless it is already present."""
        menu_item_id = item.data(Qt.ItemDataRole.UserRole)
        if menu_item_id in self.cart:
            return

        menu_item = self.menu_items[menu_item_id]
        self.cart[menu_item_id] = CartLine(
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            unit_price=menu_item.price,
        )
        self.refresh_cart(scroll_to_bottom=True)

    def change_quantity(self, menu_item_id: int, amount: int) -> None:
        """Change a cart line quantity and remove it when it reaches zero."""
        line = self.cart.get(menu_item_id)
        if line is None:
            return

        line.quantity += amount
        if line.quantity <= 0:
            del self.cart[menu_item_id]
            if self.discount and self.discount.menu_item_id == menu_item_id:
                self.discount = None

        self.refresh_cart()

    def refresh_cart(self, scroll_to_bottom: bool = False) -> None:
        """Render the current cart, totals, and checkout state."""
        while self.cart_layout.count():
            item = self.cart_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        for line in sorted(self.cart.values(), key=lambda cart_line: cart_line.item_name.lower()):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            details = QLabel(f"{line.item_name}\n₹{line.unit_price:.2f} × {line.quantity}")
            note_input = QLineEdit(line.note or "")
            note_input.setPlaceholderText("Internal note")
            note_input.textChanged.connect(
                lambda note, item_id=line.menu_item_id: self.set_note(item_id, note)
            )
            decrease_button = QPushButton("-")
            decrease_button.setMaximumWidth(38)
            decrease_button.clicked.connect(lambda _checked=False, item_id=line.menu_item_id: self.change_quantity(item_id, -1))
            quantity_label = QLabel(str(line.quantity))
            quantity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            increase_button = QPushButton("+")
            increase_button.setMaximumWidth(38)
            increase_button.clicked.connect(lambda _checked=False, item_id=line.menu_item_id: self.change_quantity(item_id, 1))
            total = QLabel(f"₹{line.unit_price * line.quantity:.2f}")

            row_layout.addWidget(details, 1)
            row_layout.addWidget(note_input, 1)
            row_layout.addWidget(decrease_button)
            row_layout.addWidget(quantity_label)
            row_layout.addWidget(increase_button)
            row_layout.addWidget(total)
            self.cart_layout.addWidget(row)

        self.cart_layout.addStretch()
        if self.cart:
            subtotal, discount_amount, total = calculate_order_totals(list(self.cart.values()), self.discount)
        else:
            subtotal, discount_amount, total = 0.0, 0.0, 0.0

        self.subtotal_label.setText(f"₹{subtotal:.2f}")
        self.discount_label.setText(f"₹{discount_amount:.2f}")
        self.total_label.setText(f"₹{total:.2f}")
        self.discount_button.setText("Discount" if self.discount is None else "Edit Discount")
        self.done_button.setEnabled(bool(self.cart))
        self.update_payment_controls()

        if scroll_to_bottom:
            QTimer.singleShot(
                0,
                lambda: self.cart_scroll.verticalScrollBar().setValue(
                    self.cart_scroll.verticalScrollBar().maximum()
                ),
            )

    def open_discount_dialog(self) -> None:
        """Open the discount dialog for the current cart."""
        if not self.cart:
            return

        dialog = DiscountDialog(list(self.cart.values()), self.discount, self)
        if dialog.exec():
            self.discount = dialog.discount
            self.refresh_cart()

    def update_payment_controls(self) -> None:
        """Show split inputs only when Split Payment is selected."""
        self.split_form.setVisible(self.split_radio.isChecked())

    def payment_details(self) -> tuple[str, dict[str, float] | None]:
        """Return the selected payment mode and any split amounts."""
        if self.split_radio.isChecked():
            return "Split", {
                "Cash": self.split_cash_input.value(),
                "UPI": self.split_upi_input.value(),
            }
        if self.upi_radio.isChecked():
            return "UPI", None
        return "Cash", None

    def complete_order(self) -> None:
        """Validate, confirm, save, and clear the current order."""
        lines = list(self.cart.values())
        payment_mode, split_payments = self.payment_details()
        try:
            _subtotal, _discount_amount, total = calculate_order_totals(lines, self.discount)
            validate_payment(payment_mode, total, split_payments)
        except ValueError as error:
            title = "Payment mismatch" if str(error) == "Payment mismatch." else "Invalid discount"
            QMessageBox.warning(self, title, str(error))
            return

        confirmed = QMessageBox.question(
            self,
            "CafePOS",
            "Complete Order?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return

        with session_scope() as session:
            save_order(
                session,
                lines,
                self.discount,
                payment_mode,
                split_payments,
                service_type=self.service_type_input.currentText(),
            )

        QMessageBox.question(
            self,
            "CafePOS",
            "Print receipt?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        self.reset_order()

    def has_active_cart(self) -> bool:
        """Return whether the current unfinished order contains any items."""
        return bool(self.cart)

    def reset_order(self) -> None:
        """Discard the in-memory cart and return to a new empty order."""
        self.cart.clear()
        self.discount = None
        self.service_type_input.setCurrentIndex(0)
        self.cash_radio.setChecked(True)
        self.split_cash_input.setValue(0)
        self.split_upi_input.setValue(0)
        self.refresh_cart()

    def set_note(self, menu_item_id: int, note: str) -> None:
        """Store a cart line's internal note for the completed order snapshot."""
        line = self.cart.get(menu_item_id)
        if line is not None:
            line.note = note.strip() or None

    def showEvent(self, event: object) -> None:
        """Refresh menu availability whenever the billing window is shown."""
        super().showEvent(event)
        self.load_menu()
