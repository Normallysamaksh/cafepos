"""Offscreen integration check for single-window CafePOS navigation."""

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

import app.ui.dashboard as dashboard
from app.services import CartLine
from app.ui.dashboard import DashboardWindow


application = QApplication([])
window = DashboardWindow()
window.show()

assert isinstance(window, QMainWindow)
assert isinstance(window.centralWidget(), QStackedWidget)
assert window.pages.count() == 4
assert all(
    not isinstance(page, QMainWindow)
    for page in (
        window.billing_window,
        window.menu_management_window,
        window.reports_window,
    )
)

window.open_new_order()
assert window.pages.currentWidget() is window.billing_window
window.billing_window.back_button.click()
assert window.pages.currentWidget() is window.dashboard_page

window.open_menu_management()
assert window.pages.currentWidget() is window.menu_management_window
window.menu_management_window.back_button.click()
assert window.pages.currentWidget() is window.dashboard_page

window.open_reports()
assert window.pages.currentWidget() is window.reports_window
window.reports_window.back_button.click()
assert window.pages.currentWidget() is window.dashboard_page

window.open_new_order()
window.billing_window.cart[1] = CartLine(1, "Coffee", 75.0)
window.billing_window.refresh_cart()

original_question = dashboard.QMessageBox.question
dashboard.QMessageBox.question = lambda *_args, **_kwargs: QMessageBox.StandardButton.No
window.billing_window.back_button.click()
assert window.pages.currentWidget() is window.billing_window
assert window.billing_window.has_active_cart()

dashboard.QMessageBox.question = lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes
window.billing_window.back_button.click()
dashboard.QMessageBox.question = original_question
assert window.pages.currentWidget() is window.dashboard_page
assert not window.billing_window.has_active_cart()

print("Navigation integration: passed")
