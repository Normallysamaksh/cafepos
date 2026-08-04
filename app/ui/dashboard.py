"""CafePOS's single-window navigation shell and dashboard."""

from datetime import date, datetime

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.database import session_scope
from app.services import get_menu_items, get_report_summary
from app.services.configuration import load_configuration
from app.services.printing import get_default_printer
from app.ui.billing import BillingWindow
from app.ui.menu_management import MenuManagementWindow
from app.ui.reports import ReportsWindow
from app.ui.settings import SettingsWindow


class DashboardWindow(QMainWindow):
    """Host every CafePOS screen in one stacked main window."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CafePOS")
        self.resize(1000, 650)
        self.setMinimumSize(800, 500)

        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)

        # Dashboard / Home Screen layout with left vertical navigation sidebar
        self.dashboard_page = QWidget()
        main_layout = QHBoxLayout(self.dashboard_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Vertical Navigation Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(12)

        # CafePOS title / logo at the top
        title_label = QLabel("CafePOS")
        title_font = title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(12)

        style = self.style()
        icon_size = QSize(18, 18)

        # Sidebar navigation buttons with icons
        self.new_order_button = QPushButton("New Order")
        self.new_order_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        self.new_order_button.setIconSize(icon_size)
        self.new_order_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_order_button.clicked.connect(self.open_new_order)
        sidebar_layout.addWidget(self.new_order_button)

        self.reports_button = QPushButton("Reports")
        self.reports_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.reports_button.setIconSize(icon_size)
        self.reports_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reports_button.clicked.connect(self.open_reports)
        sidebar_layout.addWidget(self.reports_button)

        self.menu_management_button = QPushButton("Menu Management")
        self.menu_management_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
        self.menu_management_button.setIconSize(icon_size)
        self.menu_management_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_management_button.clicked.connect(self.open_menu_management)
        sidebar_layout.addWidget(self.menu_management_button)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.settings_button.setIconSize(icon_size)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.clicked.connect(self.open_settings)
        sidebar_layout.addWidget(self.settings_button)

        sidebar_layout.addStretch()
        sidebar.setMinimumWidth(220)

        # Main content area on the home screen
        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(12)

        # Top Header Card
        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(4)

        header_top_row = QHBoxLayout()
        self.header_cafe_name = QLabel("CafePOS")
        header_name_font = self.header_cafe_name.font()
        header_name_font.setPointSize(18)
        header_name_font.setBold(True)
        self.header_cafe_name.setFont(header_name_font)
        self.header_cafe_name.setStyleSheet("color: #5c3d26;")

        self.header_datetime = QLabel()
        self.header_datetime.setStyleSheet("color: #7a7571; font-weight: 500;")

        header_top_row.addWidget(self.header_cafe_name)
        header_top_row.addStretch()
        header_top_row.addWidget(self.header_datetime)

        welcome_sub = QLabel("Welcome back! Here is your daily overview.")
        welcome_sub.setStyleSheet("color: #2d2d2d;")

        header_layout.addLayout(header_top_row)
        header_layout.addWidget(welcome_sub)
        content_layout.addWidget(header_card)

        # Summary Metric Cards Grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)

        self.orders_count_val = QLabel("0")
        self.revenue_val = QLabel("₹0.00")
        self.menu_count_val = QLabel("0")
        self.avg_bill_val = QLabel("₹0.00")

        card_configs = (
            ("Today's Orders", self.orders_count_val, QStyle.StandardPixmap.SP_FileIcon, 0, 0),
            ("Today's Revenue", self.revenue_val, QStyle.StandardPixmap.SP_DialogSaveButton, 0, 1),
            ("Menu Items", self.menu_count_val, QStyle.StandardPixmap.SP_FileDialogListView, 1, 0),
            ("Average Bill Value", self.avg_bill_val, QStyle.StandardPixmap.SP_FileDialogDetailedView, 1, 1),
        )

        for label_text, val_widget, icon_type, row, col in card_configs:
            card = QFrame()
            card.setObjectName("card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(6)

            title_row = QHBoxLayout()
            title_lbl = QLabel(label_text)
            title_lbl.setStyleSheet("color: #7a7571; font-weight: 600; font-size: 12px;")
            icon_lbl = QLabel()
            icon_lbl.setPixmap(style.standardIcon(icon_type).pixmap(16, 16))

            title_row.addWidget(title_lbl)
            title_row.addStretch()
            title_row.addWidget(icon_lbl)

            val_font = val_widget.font()
            val_font.setPointSize(16)
            val_font.setBold(True)
            val_widget.setFont(val_font)
            val_widget.setStyleSheet("color: #2d2d2d;")

            card_layout.addLayout(title_row)
            card_layout.addWidget(val_widget)
            metrics_grid.addWidget(card, row, col)

        content_layout.addLayout(metrics_grid)

        # System Status Section
        status_card = QFrame()
        status_card.setObjectName("card")
        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(16, 12, 16, 12)
        status_layout.setSpacing(16)

        db_status = QLabel("Database: Connected")
        db_status.setStyleSheet("color: #2d2d2d; font-size: 12px;")

        self.status_printer_label = QLabel("Printer: Not Configured")
        self.status_printer_label.setStyleSheet("color: #2d2d2d; font-size: 12px;")

        version_status = QLabel("Version: v1.0 (Offline)")
        version_status.setStyleSheet("color: #7a7571; font-size: 12px;")

        status_layout.addWidget(db_status)
        status_layout.addStretch()
        status_layout.addWidget(self.status_printer_label)
        status_layout.addStretch()
        status_layout.addWidget(version_status)

        content_layout.addWidget(status_card)
        content_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_panel, 1)

        self.billing_window = BillingWindow()
        self.menu_management_window = MenuManagementWindow()
        self.reports_window = ReportsWindow()
        self.settings_window = SettingsWindow()

        for page in (
            self.dashboard_page,
            self.billing_window,
            self.menu_management_window,
            self.reports_window,
            self.settings_window,
        ):
            self.add_page(page)

        self.billing_window.set_back_callback(self.return_to_dashboard)
        self.menu_management_window.set_back_callback(self.return_to_dashboard)
        self.reports_window.set_back_callback(self.return_to_dashboard)
        self.settings_window.set_back_callback(self.return_to_dashboard)
        self.refresh_dashboard_data()

    def add_page(self, page: QWidget) -> None:
        """Add a CafePOS screen to the single-window page stack."""
        self.pages.addWidget(page)

    def show_page(self, page: QWidget) -> None:
        """Display a screen already registered in the page stack."""
        self.pages.setCurrentWidget(page)

    def refresh_dashboard_data(self) -> None:
        """Refresh summary metrics, header info, and system status."""
        config = load_configuration()
        cafe_name = config.get("cafe_name") or "CafePOS"
        self.header_cafe_name.setText(str(cafe_name))
        self.header_datetime.setText(datetime.now().strftime("%B %d, %Y · %I:%M %p"))

        today = date.today()
        try:
            with session_scope() as session:
                summary = get_report_summary(session, today, today)
                items = get_menu_items(session)
                orders_count = summary.order_count
                revenue = summary.total_revenue
                menu_count = len(items)
                avg_bill = (revenue / orders_count) if orders_count > 0 else 0.0
        except Exception:
            orders_count = 0
            revenue = 0.0
            menu_count = 0
            avg_bill = 0.0

        self.orders_count_val.setText(str(orders_count))
        self.revenue_val.setText(f"₹{revenue:.2f}")
        self.menu_count_val.setText(str(menu_count))
        self.avg_bill_val.setText(f"₹{avg_bill:.2f}")

        printer = get_default_printer() or "Not Configured"
        self.status_printer_label.setText(f"Printer: {printer}")

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

        self.refresh_dashboard_data()
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

    def open_settings(self) -> None:
        """Open the Settings window."""
        self.settings_window.load_settings()
        self.show_page(self.settings_window)

    def showEvent(self, event: object) -> None:
        """Refresh metrics whenever the dashboard becomes visible."""
        super().showEvent(event)
        self.refresh_dashboard_data()
