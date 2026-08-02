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
        background-color: #f7f7f7;
        color: #202124;
    }
    QLineEdit, QAbstractSpinBox, QComboBox {
        background-color: #ffffff;
        color: #202124;
        border: 1px solid #b8b8b8;
        border-radius: 6px;
        padding: 5px 7px;
        selection-background-color: #dbe7ff;
        selection-color: #202124;
    }
    QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus {
        border: 1px solid #4c7edb;
    }
    QAbstractItemView {
        background-color: #ffffff;
        color: #202124;
        border: 1px solid #d9d9d9;
        selection-background-color: #dbe7ff;
        selection-color: #202124;
    }
    QHeaderView::section {
        background-color: #eceff3;
        color: #202124;
        border: 1px solid #d9d9d9;
        padding: 5px;
    }
    QTabBar::tab {
        background-color: #eceff3;
        color: #202124;
        border: 1px solid #d9d9d9;
        border-bottom: none;
        padding: 7px 14px;
    }
    QTabBar::tab:selected { background-color: #ffffff; }
    QGroupBox {
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        margin-top: 8px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 3px;
    }
    QPushButton {
        background-color: #ffffff;
        color: #202124;
        border: 1px solid #b8b8b8;
        border-radius: 8px;
        font-size: 20px;
        font-weight: 600;
        padding: 6px 12px;
    }
    QPushButton:hover { background-color: #f0f4ff; }
    QPushButton:disabled { color: #777777; background-color: #ededed; }
"""


def configure_application_appearance(application: QApplication) -> None:
    """Keep controls readable regardless of the operating-system color scheme."""
    palette = application.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f7f7f7"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#202124"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#202124"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#202124"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#5f6368"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#dbe7ff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#202124"))
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
