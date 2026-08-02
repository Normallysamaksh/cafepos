"""Offscreen integration check for the Billing workflow."""

from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.database.database as database
import app.models  # noqa: F401
import app.ui.billing as billing
from app.database.base import Base
from app.database import session_scope
from app.dialogs.discount_dialog import DiscountDialog
from app.models import Order, OrderItem, SplitPayment
from app.services import (
    CartLine,
    Discount,
    add_menu_item,
    calculate_order_totals,
    save_order,
)
from app.ui.billing import BillingWindow


with NamedTemporaryFile(suffix=".db", delete=False) as database_file:
    test_database_path = Path(database_file.name)

original_engine = database.engine
original_session_local = database.SessionLocal
database.engine = create_engine(f"sqlite:///{test_database_path}")
database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
Base.metadata.create_all(database.engine)

with session_scope() as session:
    espresso = add_menu_item(session, "Espresso", "Coffee", 100.0)
    latte = add_menu_item(session, "Latte", "Coffee", 120.0)
    add_menu_item(session, "Tea", "Tea", 50.0)
    espresso_id = espresso.id
    latte_id = latte.id

application = QApplication([])
printed_order_ids: list[int] = []
original_print_receipt = billing.print_receipt
billing.print_receipt = lambda order_id, _parent: printed_order_ids.append(order_id) or True
window = BillingWindow()
assert [window.categories_list.item(index).text() for index in range(window.categories_list.count())] == ["Coffee", "Tea"]
assert [window.items_list.item(index).data(256) for index in range(window.items_list.count())] == [espresso_id, latte_id]

window.add_menu_item(window.items_list.item(0))
window.add_menu_item(window.items_list.item(0))
assert window.cart[espresso_id].quantity == 1
window.change_quantity(espresso_id, 1)
assert window.cart[espresso_id].quantity == 2
window.change_quantity(espresso_id, -2)
assert espresso_id not in window.cart
window.add_menu_item(window.items_list.item(0))

window.search_input.setText("latte")
assert window.items_list.count() == 1
window.add_menu_item(window.items_list.item(0))
window.set_note(espresso_id, "  No sugar  ")
assert window.done_button.isEnabled()

discount_dialog = DiscountDialog(list(window.cart.values()), None)
discount_dialog.type_input.setCurrentIndex(discount_dialog.type_input.findData("percentage"))
discount_dialog.target_input.setCurrentIndex(discount_dialog.target_input.findData(latte_id))
discount_dialog.value_input.setValue(10)
discount_dialog.apply_discount()
assert discount_dialog.discount is not None
assert discount_dialog.discount.scope == "item"
window.discount = discount_dialog.discount
subtotal, discount_amount, total = calculate_order_totals(list(window.cart.values()), window.discount)
assert (subtotal, discount_amount, total) == (220.0, 12.0, 208.0)

invalid_discount = DiscountDialog(list(window.cart.values()), None)
invalid_discount.type_input.setCurrentIndex(invalid_discount.type_input.findData("percentage"))
invalid_discount.value_input.setValue(101)
invalid_discount.apply_discount()
assert invalid_discount.error_label.text() == "Discount cannot exceed the bill value."

window.split_radio.setChecked(True)
window.split_cash_input.setValue(100)
window.split_upi_input.setValue(108)

original_question = QMessageBox.question
original_information = QMessageBox.information
QMessageBox.question = lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes
QMessageBox.information = lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok
window.complete_order()
QMessageBox.question = original_question
QMessageBox.information = original_information
assert not window.cart
assert not window.done_button.isEnabled()
assert printed_order_ids == [1]

with session_scope() as session:
    order = session.scalar(select(Order).order_by(Order.id))
    assert order is not None
    assert order.bill_number == 1
    assert order.payment_mode == "Split"
    assert (order.subtotal, order.discount_value, order.total) == (220.0, 10.0, 208.0)
    assert order.discount_type == "percentage_item"
    assert order.discount_scope == "item"
    assert order.discount_menu_item_id == latte_id
    order_items = list(session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)))
    payments = list(session.scalars(select(SplitPayment).where(SplitPayment.order_id == order.id)))
    assert {item.item_name for item in order_items} == {"Espresso", "Latte"}
    assert any(
        item.menu_item_id == order.discount_menu_item_id and item.item_name == "Latte"
        for item in order_items
    )
    assert next(item.note for item in order_items if item.item_name == "Espresso") == "No sugar"
    assert {(payment.payment_mode, payment.amount) for payment in payments} == {("Cash", 100.0), ("UPI", 108.0)}

database.engine.dispose()
database.engine = create_engine(f"sqlite:///{test_database_path}")
database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
with session_scope() as session:
    persisted_order = session.scalar(select(Order).where(Order.bill_number == 1))
    assert persisted_order is not None
    assert persisted_order.total == 208.0

same_day = datetime(2031, 5, 20, 10, 0, 0)
next_day = datetime(2031, 5, 21, 10, 0, 0)
with session_scope() as session:
    first_daily_order = save_order(
        session,
        [CartLine(espresso_id, "Espresso", 100.0, note="Staff note")],
        None,
        "Cash",
        completed_at=same_day,
    )
    second_daily_order = save_order(
        session,
        [CartLine(espresso_id, "Espresso", 100.0)],
        None,
        "UPI",
        completed_at=same_day,
    )
    next_daily_order = save_order(
        session,
        [CartLine(espresso_id, "Espresso", 100.0)],
        None,
        "Cash",
        completed_at=next_day,
    )
    assert (first_daily_order.bill_number, second_daily_order.bill_number, next_daily_order.bill_number) == (1, 2, 1)
    note = session.scalar(select(OrderItem.note).where(OrderItem.order_id == first_daily_order.id))
    assert note == "Staff note"

database.engine.dispose()
database.engine = original_engine
database.SessionLocal = original_session_local
billing.print_receipt = original_print_receipt

print("Billing integration: passed")
