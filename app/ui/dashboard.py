"""CafePOS dashboard window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.ui.billing import BillingWindow
from app.ui.menu_management import MenuManagementWindow
from app.ui.reports import ReportsWindow


class DashboardWindow(QMainWindow):
    """The application's initial dashboard."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CafePOS")
        self.resize(800, 600)
        self.setMinimumSize(480, 360)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
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

        self.setCentralWidget(central_widget)

        self.menu_management_window: MenuManagementWindow | None = None
        self.billing_window: BillingWindow | None = None
        self.reports_window: ReportsWindow | None = None

    def open_new_order(self) -> None:
        """Open billing, optionally discarding an existing unfinished cart."""
        if self.billing_window is None:
            self.billing_window = BillingWindow()
        elif self.billing_window.has_active_cart():
            discard = QMessageBox.question(
                self,
                "CafePOS",
                "Discard current order?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if discard == QMessageBox.StandardButton.Yes:
                self.billing_window.reset_order()

        self.billing_window.show()
        self.billing_window.raise_()
        self.billing_window.activateWindow()

    def open_menu_management(self) -> None:
        """Open the Menu Management window."""
        if self.menu_management_window is None:
            self.menu_management_window = MenuManagementWindow()

        self.menu_management_window.load_items()
        self.menu_management_window.show()
        self.menu_management_window.raise_()
        self.menu_management_window.activateWindow()

    def open_reports(self) -> None:
        """Open the reports window with current local order data."""
        if self.reports_window is None:
            self.reports_window = ReportsWindow()

        self.reports_window.refresh_reports()
        self.reports_window.show()
        self.reports_window.raise_()
        self.reports_window.activateWindow()
