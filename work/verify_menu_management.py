"""Offscreen integration check for Menu Management."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from PySide6.QtWidgets import QApplication, QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
import app.database.database as database
import app.ui.menu_management as menu_management
from app.database.base import Base
from app.dialogs.menu_item_dialog import MenuItemDialog
from app.services import get_categories, get_menu_items


class FakeMenuItemDialog:
    """Provide accepted dialog values for UI integration tests."""

    next_values = ("Latte", "Drinks", 120.0)

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def exec(self) -> int:
        return 1

    @property
    def values(self) -> tuple[str, str, float]:
        return self.next_values


with NamedTemporaryFile(suffix=".db", delete=False) as database_file:
    test_database_path = Path(database_file.name)

original_engine = database.engine
original_session_local = database.SessionLocal
database.engine = create_engine(f"sqlite:///{test_database_path}")
database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
Base.metadata.create_all(database.engine)

application = QApplication([])

validation_dialog = MenuItemDialog("Add Item", [])
validation_dialog.save()
assert validation_dialog.error_label.text() == "Name is required."
validation_dialog.name_input.setText("Tea")
validation_dialog.save()
assert validation_dialog.error_label.text() == "Category is required."
validation_dialog.category_input.setCurrentText("Drinks")
validation_dialog.save()
assert validation_dialog.error_label.text() == "Price must be greater than 0."
validation_dialog.price_input.setValue(10)
validation_dialog.save()
assert validation_dialog.result() == QDialog.DialogCode.Accepted

menu_management.MenuItemDialog = FakeMenuItemDialog
window = menu_management.MenuManagementWindow()
window.add_item()
FakeMenuItemDialog.next_values = ("Mocha", "Coffee", 110.0)
window.add_item()
assert window.table.rowCount() == 2
assert window.table.item(0, 0).text() == "Mocha"
assert window.table.item(1, 0).text() == "Latte"

database.engine.dispose()
database.engine = create_engine(f"sqlite:///{test_database_path}")
database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
window = menu_management.MenuManagementWindow()
assert window.table.rowCount() == 2
assert window.table.item(0, 0).text() == "Mocha"
assert window.table.item(1, 0).text() == "Latte"

FakeMenuItemDialog.next_values = ("Iced Latte", "Cold Drinks", 135.0)
window.table.selectRow(1)
window.edit_item()
assert window.table.item(1, 0).text() == "Iced Latte"
assert window.table.item(1, 1).text() == "Cold Drinks"
assert window.table.item(1, 2).text() == "135.00"

window.search_input.setText("iced")
assert window.table.rowCount() == 1
window.search_input.setText("tea")
assert window.table.rowCount() == 0
window.search_input.clear()
window.table.selectRow(0)
window.delete_item()
assert window.table.rowCount() == 1
window.table.selectRow(0)
window.delete_item()
assert window.table.rowCount() == 0

with database.session_scope() as session:
    assert get_menu_items(session) == []
    assert get_categories(session) == []

database.engine.dispose()
database.engine = original_engine
database.SessionLocal = original_session_local

print("Menu Management integration: passed")
