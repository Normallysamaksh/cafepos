"""Application entry point."""

import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from app.database import initialize_database
from app.dialogs import FirstLaunchDialog
from app.runtime_paths import logs_directory
from app.services.configuration import configuration_exists, save_configuration
from app.ui.dashboard import DashboardWindow


APPLICATION_STYLESHEET = """
    QWidget, QDialog, QMessageBox {
        background-color: #f6f5f2;
        color: #2d2d2d;
        font-family: "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
    }
    QFrame#sidebar {
        background-color: #ede8e3;
        border-right: 1px solid #dfd8d0;
    }
    QFrame.card, QFrame#card {
        background-color: #ffffff;
        border: 1px solid #e0dad5;
        border-radius: 8px;
    }
    QLineEdit, QAbstractSpinBox, QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #2d2d2d;
        border: 1px solid #d4cecb;
        border-radius: 8px;
        padding: 6px 10px;
        font-size: 13px;
        selection-background-color: #f2e8de;
        selection-color: #2d2d2d;
    }
    QComboBox {
        background-color: #ffffff;
        color: #2d2d2d;
        border: 1px solid #d4cecb;
        border-radius: 8px;
        padding: 6px 24px 6px 10px;
        min-width: 120px;
        font-size: 13px;
        selection-background-color: #f2e8de;
        selection-color: #2d2d2d;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 22px;
        border-left: none;
    }
    QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus {
        border: 1px solid #8b5e3c;
    }
    QAbstractItemView {
        background-color: #ffffff;
        color: #2d2d2d;
        border: 1px solid #e0dad5;
        font-size: 13px;
        selection-background-color: #f2e8de;
        selection-color: #2d2d2d;
    }
    QHeaderView::section {
        background-color: #f0eae3;
        color: #2d2d2d;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #e0dad5;
        padding: 6px 8px;
    }
    QTabBar::tab {
        background-color: #ede8e3;
        color: #2d2d2d;
        border: 1px solid #d4cecb;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #8b5e3c;
        font-weight: 600;
    }
    QGroupBox {
        border: 1px solid #d4cecb;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 10px;
        font-size: 13px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #5c3d26;
        font-weight: 600;
        font-size: 13px;
    }
    QPushButton {
        background-color: #ffffff;
        color: #2d2d2d;
        border: 1px solid #d4cecb;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        padding: 7px 14px;
    }
    QPushButton:hover {
        background-color: #f4ece6;
        border-color: #c78a4a;
    }
    QPushButton:pressed {
        background-color: #e8ded6;
    }
    QPushButton:disabled {
        color: #9e9893;
        background-color: #ebe7e3;
        border-color: #e0dad5;
    }
"""


def configure_application_appearance(application: QApplication) -> None:
    """Keep controls readable regardless of the operating-system color scheme."""
    palette = application.palette()
    for group in (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    ):
        palette.setColor(group, QPalette.ColorRole.Window, QColor("#f6f5f2"))
        palette.setColor(group, QPalette.ColorRole.WindowText, QColor("#2d2d2d"))
        palette.setColor(group, QPalette.ColorRole.Base, QColor("#ffffff"))
        palette.setColor(group, QPalette.ColorRole.Text, QColor("#2d2d2d"))
        palette.setColor(group, QPalette.ColorRole.Button, QColor("#ffffff"))
        palette.setColor(group, QPalette.ColorRole.ButtonText, QColor("#2d2d2d"))
        palette.setColor(group, QPalette.ColorRole.PlaceholderText, QColor("#7a7571"))
        palette.setColor(group, QPalette.ColorRole.Highlight, QColor("#f2e8de"))
        palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor("#2d2d2d"))
    application.setPalette(palette)
    application.setStyleSheet(APPLICATION_STYLESHEET)


def complete_first_launch_setup(parent: QWidget | None = None) -> bool:
    """Create config.json before showing the application for the first time."""
    if configuration_exists():
        return True

    dialog = FirstLaunchDialog(parent)
    if not dialog.exec():
        return False

    try:
        save_configuration(*dialog.values)
    except OSError:
        QMessageBox.critical(parent, "CafePOS", "Configuration could not be saved.")
        return False
    return True


def main() -> int:
    """Start the CafePOS desktop application."""
    logs_directory()
    initialize_database()

    application = QApplication(sys.argv)
    application.setApplicationName("CafePOS")
    configure_application_appearance(application)

    if not complete_first_launch_setup():
        return 0

    window = DashboardWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
