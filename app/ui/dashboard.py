"""CafePOS's single-window navigation shell and dashboard."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.ui.billing import BillingWindow
from app.ui.menu_management import MenuManagementWindow
from app.ui.reports import ReportsWindow


class DashboardWindow(QMainWindow):
    """Host every CafePOS screen in one stacked main window."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CafePOS")
        self.resize(800, 600)
        self.setMinimumSize(480, 360)

        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)

        self.dashboard_page = QWidget()
        layout = QVBoxLayout(self.dashboard_page)
        layout.setContentsMargins(64, 64, 64, 64)
        layout.setSpacing(20)

        for label in ("New Order", "Reports", "Menu Management"):
            tile = QPushButton(label)
            tile.setMinimumHeight(100)
            tile.setCursor(Qt.CursorShape.PointingHandCursor)
            if label == "New Order":
                tile.clicked.connect(self.open_new_order)
            elif label == "Reports":
                tile.clicked.connect(self.open_reports)
            elif label == "Menu Management":
                tile.clicked.connect(self.open_menu_management)
            layout.addWidget(tile)

        self.billing_window = BillingWindow()
        self.menu_management_window = MenuManagementWindow()
        self.reports_window = ReportsWindow()

        for page in (
            self.dashboard_page,
            self.billing_window,
            self.menu_management_window,
            self.reports_window,
        ):
            self.add_page(page)

        self.billing_window.set_back_callback(self.return_to_dashboard)
        self.menu_management_window.set_back_callback(self.return_to_dashboard)
        self.reports_window.set_back_callback(self.return_to_dashboard)

    def add_page(self, page: QWidget) -> None:
        """Add a CafePOS screen to the single-window page stack."""
        self.pages.addWidget(page)

    def show_page(self, page: QWidget) -> None:
        """Display a screen already registered in the page stack."""
        self.pages.setCurrentWidget(page)

    def return_to_dashboard(self) -> None:
        """Return to the dashboard, confirming before discarding a cart."""
        if self.pages.currentWidget() is self.billing_window and self.billing_window.has_active_cart():
            discard = QMessageBox.question(
                self,
                "CafePOS",
                "Discard current order?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if discard != QMessageBox.StandardButton.Yes:
                return
            self.billing_window.reset_order()

        self.show_page(self.dashboard_page)

    def open_new_order(self) -> None:
        """Open billing, optionally discarding an existing unfinished cart."""
        if self.billing_window.has_active_cart():
            discard = QMessageBox.question(
                self,
                "CafePOS",
                "Discard current order?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if discard == QMessageBox.StandardButton.Yes:
                self.billing_window.reset_order()

        self.billing_window.load_menu()
        self.show_page(self.billing_window)

    def open_menu_management(self) -> None:
        """Open the Menu Management window."""
        self.menu_management_window.load_items()
        self.show_page(self.menu_management_window)

    def open_reports(self) -> None:
        """Open the reports window with current local order data."""
        self.reports_window.refresh_reports()
        self.show_page(self.reports_window)
