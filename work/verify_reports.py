"""Offscreen integration check for reports, order details, and voiding."""

from datetime import date, datetime, time
from pathlib import Path
from tempfile import NamedTemporaryFile

from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database.database as database
import app.models  # noqa: F401
from app.database import session_scope
from app.database.base import Base
from app.dialogs import OrderDetailsDialog
from app.services import CartLine, Discount, add_menu_item, save_order
from app.ui.dashboard import DashboardWindow
from app.ui.reports import ReportsWindow


with NamedTemporaryFile(suffix=".db", delete=False) as database_file:
    test_database_path = Path(database_file.name)

original_engine = database.engine
original_session_local = database.SessionLocal
database.engine = create_engine(f"sqlite:///{test_database_path}")
database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
Base.metadata.create_all(database.engine)

today = date.today()
with session_scope() as session:
    espresso = add_menu_item(session, "Espresso", "Coffee", 100.0)
    latte = add_menu_item(session, "Latte", "Coffee", 120.0)
    tea = add_menu_item(session, "Tea", "Tea", 50.0)

    latte_order = save_order(
        session,
        [CartLine(latte.id, "Latte", 120.0, quantity=2, note="Oat milk")],
        Discount("percentage", 10.0, "item", latte.id),
        "Split",
        {"Cash": 100.0, "UPI": 116.0},
        completed_at=datetime.combine(today, time(10, 0)),
    )
    save_order(
        session,
        [CartLine(tea.id, "Tea", 50.0)],
        None,
        "UPI",
        completed_at=datetime.combine(today, time(11, 0)),
    )
    espresso_order = save_order(
        session,
        [CartLine(espresso.id, "Espresso", 100.0, quantity=3)],
        None,
        "Cash",
        completed_at=datetime.combine(today, time(12, 0)),
    )
    latte.name = "Renamed Latte"

application = QApplication([])
reports = ReportsWindow()
today_tab = reports.report_tabs["Today"]
assert today_tab.orders_table.rowCount() == 3
assert reports.report_tabs["Weekly"].orders_table.rowCount() == 3
assert reports.report_tabs["Monthly"].orders_table.rowCount() == 3
assert today_tab.order_count_label.text() == "3"
assert today_tab.revenue_label.text() == "₹566.00"
assert today_tab.most_sold_item_label.text() == "Espresso"

details = OrderDetailsDialog(latte_order.id, reports.refresh_reports)
assert details.status_label.text() == "Completed"
assert details.items_table.item(0, 0).text() == "Latte"
assert details.items_table.item(0, 1).text() == "2"
assert details.items_table.item(0, 2).text() == "₹120.00"
assert details.items_table.item(0, 3).text() == "Oat milk"
assert details.discount_type_label.text() == "Percentage"
assert details.discount_scope_label.text() == "Item"
assert details.discount_value_label.text() == "10.00%"
assert details.payment_breakdown_label.text() == "Cash: ₹100.00\nUPI: ₹116.00"
assert details.service_type_label.text() == "Dine In"
assert details.bill_time_label.text() == f"{today.isoformat()} 10:00:00"

void_details = OrderDetailsDialog(espresso_order.id, reports.refresh_reports)
original_question = QMessageBox.question
QMessageBox.question = lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes
void_details.void_current_order()
QMessageBox.question = original_question
assert void_details.status_label.text() == "VOIDED"
assert not void_details.void_button.isEnabled()
assert not void_details.reprint_button.isEnabled()

assert today_tab.order_count_label.text() == "2"
assert today_tab.revenue_label.text() == "₹266.00"
assert today_tab.most_sold_item_label.text() == "Latte"
assert today_tab.orders_table.rowCount() == 3
assert any(
    "VOIDED" in today_tab.orders_table.item(row, 0).text()
    for row in range(today_tab.orders_table.rowCount())
)

dashboard = DashboardWindow()
dashboard.open_reports()
assert dashboard.reports_window is not None
assert dashboard.reports_window.report_tabs["Today"].revenue_label.text() == "₹266.00"

database.engine.dispose()
database.engine = original_engine
database.SessionLocal = original_session_local

print("Reports integration: passed")
