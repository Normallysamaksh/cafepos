"""Offscreen integration check for Excel report exports."""

from datetime import date, datetime, time
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database.database as database
import app.models  # noqa: F401
from app.database import session_scope
from app.database.base import Base
from app.services import CartLine, add_menu_item, save_order, void_order
from app.ui.reports import ReportsWindow


with TemporaryDirectory() as temporary_directory:
    database_path = Path(temporary_directory) / "reports.db"
    original_engine = database.engine
    original_session_local = database.SessionLocal
    database.engine = create_engine(f"sqlite:///{database_path}")
    database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
    Base.metadata.create_all(database.engine)

    today = date.today()
    with session_scope() as session:
        coffee = add_menu_item(session, "Coffee", "Drinks", 75.0)
        live_order = save_order(
            session,
            [CartLine(coffee.id, "Coffee", 75.0)],
            None,
            "Cash",
            completed_at=datetime.combine(today, time(9, 0)),
        )
        voided_order = save_order(
            session,
            [CartLine(coffee.id, "Coffee", 75.0)],
            None,
            "UPI",
            completed_at=datetime.combine(today, time(10, 0)),
        )
        assert void_order(session, voided_order.id)

    application = QApplication([])
    reports = ReportsWindow()
    assert reports.export_button.text() == "Export Excel"

    original_file_dialog = QFileDialog.getSaveFileName
    original_information = QMessageBox.information
    original_warning = QMessageBox.warning
    success_messages: list[str] = []
    warnings: list[str] = []
    requested_filenames: list[str] = []
    QMessageBox.information = lambda _parent, _title, message: success_messages.append(message)
    QMessageBox.warning = lambda _parent, _title, message: warnings.append(message)

    for title in ("Today", "Weekly", "Monthly"):
        selected_path = Path(temporary_directory) / title
        target = selected_path.with_suffix(".xlsx")

        def select_export_path(*args: object, selected_path: Path = selected_path) -> tuple[str, str]:
            requested_filenames.append(str(args[2]))
            return str(selected_path), ""

        QFileDialog.getSaveFileName = staticmethod(select_export_path)
        reports.tabs.setCurrentIndex(reports.tabs.indexOf(reports.report_tabs[title]))
        reports.export_current_report()

        assert target.exists()
        with ZipFile(target) as workbook:
            assert set(workbook.namelist()) >= {
                "[Content_Types].xml",
                "xl/workbook.xml",
                "xl/styles.xml",
                "xl/worksheets/sheet1.xml",
            }
            worksheet = fromstring(workbook.read("xl/worksheets/sheet1.xml"))
            text = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        assert worksheet.tag.endswith("worksheet")
        assert f"CafePOS {title} Report" in text
        assert "2 (VOIDED)" in text
        assert "Coffee" in text

    QFileDialog.getSaveFileName = original_file_dialog
    QMessageBox.information = original_information
    QMessageBox.warning = original_warning
    assert success_messages == ["Export Successful"] * 3
    assert warnings == []
    assert requested_filenames == [f"CafePOS_Report_{today.isoformat()}.xlsx"] * 3

    database.engine.dispose()
    database.engine = original_engine
    database.SessionLocal = original_session_local
    assert live_order.id == 1

print("Excel export integration: passed")
