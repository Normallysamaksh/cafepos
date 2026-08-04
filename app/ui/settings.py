"""Settings window for editing cafe configuration and viewing app info."""

from collections.abc import Callable
import platform
import sys

from PySide6.QtCore import Qt
from PySide6.QtPrintSupport import QPrinterInfo
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.runtime_paths import application_directory
from app.services.configuration import (
    get_default_printer,
    load_configuration,
    save_configuration,
    save_default_printer,
)


class SettingsWindow(QWidget):
    """Manage application configuration and display system information."""

    def __init__(self) -> None:
        super().__init__()

        self._back_callback: Callable[[], None] | None = None

        self.setWindowTitle("Settings")
        self.resize(820, 560)
        self.setMinimumSize(620, 400)

        style = self.style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        navigation_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.back_button.clicked.connect(self.go_back)
        navigation_layout.addWidget(self.back_button)
        navigation_layout.addStretch()
        layout.addLayout(navigation_layout)

        # Section 1: Configuration Card
        config_card = QFrame()
        config_card.setObjectName("card")
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(20, 16, 20, 16)
        config_layout.setSpacing(12)

        config_title = QLabel("Configuration")
        config_title.setStyleSheet("font-weight: 600; color: #5c3d26; font-size: 14px;")
        config_layout.addWidget(config_title)

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)

        self.cafe_name_input = QLineEdit()
        self.cafe_name_input.setPlaceholderText("e.g. Daily Roast Cafe")

        self.receipt_footer_input = QLineEdit()
        self.receipt_footer_input.setPlaceholderText("e.g. Thank you for visiting!")

        self.printer_input = QComboBox()

        form_layout.addRow("Cafe Name", self.cafe_name_input)
        form_layout.addRow("Receipt Footer", self.receipt_footer_input)
        form_layout.addRow("Default Printer", self.printer_input)

        config_layout.addLayout(form_layout)

        self.save_button = QPushButton("Save Configuration")
        self.save_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.save_button.clicked.connect(self.save_settings)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.save_button)
        btn_row.addStretch()
        config_layout.addLayout(btn_row)

        layout.addWidget(config_card)

        # Section 2: Application Information Card
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(12)

        info_title = QLabel("Application Information")
        info_title.setStyleSheet("font-weight: 600; color: #5c3d26; font-size: 14px;")
        info_layout.addWidget(info_title)

        info_form = QFormLayout()
        info_form.setContentsMargins(0, 0, 0, 0)
        info_form.setHorizontalSpacing(12)
        info_form.setVerticalSpacing(10)

        app_dir = application_directory()
        db_path = app_dir / "cafepos.db"
        reports_dir = app_dir / "reports"

        self.db_label = QLabel(str(db_path))
        self.db_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.reports_label = QLabel(str(reports_dir))
        self.reports_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.version_label = QLabel("v1.0 (Offline Desktop POS)")
        self.platform_label = QLabel(f"{platform.system()} {platform.release()} ({sys.platform})")

        info_form.addRow("Database Location", self.db_label)
        info_form.addRow("Reports Folder", self.reports_label)
        info_form.addRow("Application Version", self.version_label)
        info_form.addRow("Platform", self.platform_label)

        info_layout.addLayout(info_form)
        layout.addWidget(info_card)

        layout.addStretch()
        self.load_settings()

    def set_back_callback(self, callback: Callable[[], None]) -> None:
        """Set the navigation action for the screen's Back button."""
        self._back_callback = callback

    def go_back(self) -> None:
        """Return to the dashboard shell."""
        if self._back_callback is not None:
            self._back_callback()

    def load_settings(self) -> None:
        """Load current configuration into inputs."""
        config = load_configuration()
        self.cafe_name_input.setText(str(config.get("cafe_name", "")))
        self.receipt_footer_input.setText(str(config.get("receipt_footer", "")))

        self.printer_input.clear()
        self.printer_input.addItem("None", "")
        available = [info.printerName() for info in QPrinterInfo.availablePrinters()]
        for p in available:
            self.printer_input.addItem(p, p)

        current_printer = get_default_printer()
        if current_printer:
            idx = self.printer_input.findData(current_printer)
            if idx >= 0:
                self.printer_input.setCurrentIndex(idx)
            else:
                self.printer_input.addItem(f"{current_printer} (Disconnected)", current_printer)
                self.printer_input.setCurrentIndex(self.printer_input.count() - 1)

    def save_settings(self) -> None:
        """Save settings entries to local config."""
        cafe_name = self.cafe_name_input.text().strip()
        receipt_footer = self.receipt_footer_input.text().strip()
        printer_name = str(self.printer_input.currentData() or "")

        if not cafe_name:
            QMessageBox.warning(self, "Settings", "Cafe Name cannot be empty.")
            return

        try:
            save_configuration(cafe_name, receipt_footer)
            if printer_name:
                save_default_printer(printer_name)
            QMessageBox.information(self, "Settings", "Settings saved successfully.")
        except Exception:
            QMessageBox.critical(self, "Settings", "Could not save configuration.")
