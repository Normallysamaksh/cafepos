"""Offscreen visual-regression checks for readable CafePOS controls and dialogs."""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QLineEdit

from app.dialogs import DiscountDialog, FirstLaunchDialog, MenuItemDialog, OrderDetailsDialog
from app.main import configure_application_appearance
from app.services import CartLine
from app.ui.dashboard import DashboardWindow


def color_distance(first: QColor, second: QColor) -> int:
    """Return a simple RGB contrast measurement for palette sanity checks."""
    return abs(first.red() - second.red()) + abs(first.green() - second.green()) + abs(first.blue() - second.blue())


application = QApplication([])

# Reapply the application appearance after both representative system palettes.
for system_background in (QColor("#ffffff"), QColor("#202124")):
    system_palette = application.palette()
    system_palette.setColor(QPalette.ColorRole.Window, system_background)
    system_palette.setColor(QPalette.ColorRole.Base, system_background)
    system_palette.setColor(QPalette.ColorRole.Text, system_background)
    application.setPalette(system_palette)
    configure_application_appearance(application)

    dashboard = DashboardWindow()
    dialogs = (
        FirstLaunchDialog(),
        MenuItemDialog("Add Item", ["Coffee"]),
        DiscountDialog([CartLine(1, "Coffee", 100.0)], None),
        OrderDetailsDialog(-1),
    )
    for widget in (dashboard, *dialogs):
        widget.show()
        widget.grab()

    inputs = dashboard.findChildren(QLineEdit)
    for dialog in dialogs:
        inputs.extend(dialog.findChildren(QLineEdit))
    assert inputs
    for input_widget in inputs:
        palette = input_widget.palette()
        assert color_distance(
            palette.color(QPalette.ColorRole.Text), palette.color(QPalette.ColorRole.Base)
        ) >= 120
        if input_widget.placeholderText():
            assert color_distance(
                palette.color(QPalette.ColorRole.PlaceholderText), palette.color(QPalette.ColorRole.Base)
            ) >= 80

    numeric_inputs = dashboard.findChildren(QDoubleSpinBox)
    for dialog in dialogs:
        numeric_inputs.extend(dialog.findChildren(QDoubleSpinBox))
    assert numeric_inputs
    for input_widget in numeric_inputs:
        assert input_widget.value() == 0
        assert input_widget.text().strip() == ""

print("UI rendering integration: passed")
