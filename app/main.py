"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from app.database import initialize_database
from app.dialogs import FirstLaunchDialog
from app.services.configuration import configuration_exists, save_configuration
from app.ui.dashboard import DashboardWindow


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
    initialize_database()

    application = QApplication(sys.argv)
    application.setApplicationName("CafePOS")
    application.setStyleSheet(
        """
        QWidget { background-color: #f7f7f7; color: #202124; }
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #d9d9d9;
            border-radius: 8px;
            font-size: 20px;
            font-weight: 600;
        }
        QPushButton:hover { background-color: #f0f4ff; }
        """
    )

    if not complete_first_launch_setup():
        return 0

    window = DashboardWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
