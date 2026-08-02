"""Offscreen integration check for receipt printing and reprinting."""

import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.database.database as database
import app.dialogs.order_details_dialog as order_details
import app.models  # noqa: F401
import app.services.printing as printing
import app.ui.billing as billing
from app.database import session_scope
from app.database.base import Base
from app.dialogs import OrderDetailsDialog
from app.models import Order
from app.services import CartLine, add_menu_item, save_order, void_order
from app.services.printing import ReceiptPrintError
from app.ui.billing import BillingWindow


class FakePrinter:
    """Minimal printer substitute that records the selected printer name."""

    class PrinterMode:
        HighResolution = 1

    def __init__(self, _mode: object) -> None:
        self._name = ""

    def setPrinterName(self, printer_name: str) -> None:
        self._name = printer_name

    def printerName(self) -> str:
        return self._name


class FakePrinterInfo:
    """Expose both a thermal and A4 printer to the receipt service."""

    def __init__(self, printer_name: str) -> None:
        self._name = printer_name

    def printerName(self) -> str:
        return self._name

    @staticmethod
    def availablePrinters() -> list["FakePrinterInfo"]:
        return [FakePrinterInfo("Thermal 80mm"), FakePrinterInfo("Office A4")]


class FakePrintDialog:
    """Choose the thermal printer the first time a receipt is printed."""

    calls = 0

    def __init__(self, printer: FakePrinter, _parent: object) -> None:
        self.printer = printer

    def setWindowTitle(self, _title: str) -> None:
        pass

    def exec(self) -> int:
        self.__class__.calls += 1
        self.printer.setPrinterName("Thermal 80mm")
        return 1


class FakeTextDocument:
    """Capture printed receipt HTML without contacting an operating-system printer."""

    printed: list[tuple[str, str]] = []

    def __init__(self) -> None:
        self.html = ""

    def setDocumentMargin(self, _margin: float) -> None:
        pass

    def setHtml(self, receipt_html: str) -> None:
        self.html = receipt_html

    def print_(self, printer: FakePrinter) -> None:
        self.__class__.printed.append((self.html, printer.printerName()))


with NamedTemporaryFile(suffix=".db", delete=False) as database_file:
    test_database_path = Path(database_file.name)
with NamedTemporaryFile(suffix=".json", delete=False) as config_file:
    test_config_path = Path(config_file.name)

original_engine = database.engine
original_session_local = database.SessionLocal
original_config_path = printing.CONFIG_PATH
original_printer = printing.QPrinter
original_printer_info = printing.QPrinterInfo
original_print_dialog = printing.QPrintDialog
original_text_document = printing.QTextDocument
database.engine = create_engine(f"sqlite:///{test_database_path}")
database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
printing.CONFIG_PATH = test_config_path
printing.QPrinter = FakePrinter
printing.QPrinterInfo = FakePrinterInfo
printing.QPrintDialog = FakePrintDialog
printing.QTextDocument = FakeTextDocument
Base.metadata.create_all(database.engine)

with session_scope() as session:
    latte = add_menu_item(session, "Latte", "Coffee", 120.0)
    espresso = add_menu_item(session, "Espresso", "Coffee", 100.0)
    latte_order = save_order(
        session,
        [CartLine(latte.id, "Latte", 120.0, quantity=2, note="Oat milk")],
        None,
        "Cash",
        completed_at=datetime(2031, 5, 20, 10, 0),
    )
    espresso_order = save_order(
        session,
        [CartLine(espresso.id, "Espresso", 100.0)],
        None,
        "UPI",
        completed_at=datetime(2031, 5, 20, 11, 0),
    )

application = QApplication([])

assert printing.print_receipt(latte_order.id)
assert printing.get_default_printer() == "Thermal 80mm"
assert FakePrintDialog.calls == 1
assert FakeTextDocument.printed[-1][1] == "Thermal 80mm"
assert "Latte" in FakeTextDocument.printed[-1][0]
assert "Oat milk" in FakeTextDocument.printed[-1][0]

assert printing.print_receipt(latte_order.id)
assert FakePrintDialog.calls == 1
printing.save_default_printer("Office A4")
assert printing.print_receipt(latte_order.id)
assert FakeTextDocument.printed[-1][1] == "Office A4"

test_config_path.write_text(
    json.dumps({"cafe_name": "Cafe Test", "receipt_footer": "Thank you!"}),
    encoding="utf-8",
)
receipt_html = printing.receipt_html_for_order_id(latte_order.id)
assert "Cafe Test" in receipt_html
assert "Thank you!" in receipt_html
assert "max-width: 180mm" in receipt_html

reprinted_order_ids: list[int] = []
original_details_print_receipt = order_details.print_receipt
original_information = QMessageBox.information
order_details.print_receipt = lambda order_id, _parent: reprinted_order_ids.append(order_id) or True
QMessageBox.information = lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok
details = OrderDetailsDialog(latte_order.id)
details.reprint_order()
assert reprinted_order_ids == [latte_order.id]
order_details.print_receipt = original_details_print_receipt
QMessageBox.information = original_information

with session_scope() as session:
    assert void_order(session, espresso_order.id)

voided_details = OrderDetailsDialog(espresso_order.id)
assert not voided_details.reprint_button.isEnabled()
try:
    printing.print_receipt(espresso_order.id)
except ReceiptPrintError as error:
    assert "Voided orders" in str(error)
else:
    raise AssertionError("Voided orders must not print.")

warnings: list[str] = []
original_billing_print_receipt = billing.print_receipt
original_warning = QMessageBox.warning

def fail_print(_order_id: int, _parent: object) -> bool:
    raise ReceiptPrintError("Printer failed")


billing.print_receipt = fail_print
QMessageBox.warning = lambda _parent, _title, message: warnings.append(message)
billing_window = BillingWindow()
billing_window.print_completed_order(latte_order.id)
assert warnings == ["Receipt could not be printed."]
with session_scope() as session:
    assert session.scalar(select(Order.id).where(Order.id == latte_order.id)) == latte_order.id
billing.print_receipt = original_billing_print_receipt
QMessageBox.warning = original_warning

database.engine.dispose()
database.engine = original_engine
database.SessionLocal = original_session_local
printing.CONFIG_PATH = original_config_path
printing.QPrinter = original_printer
printing.QPrinterInfo = original_printer_info
printing.QPrintDialog = original_print_dialog
printing.QTextDocument = original_text_document
test_database_path.unlink()
test_config_path.unlink()

print("Printing integration: passed")
