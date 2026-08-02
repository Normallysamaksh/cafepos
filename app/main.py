"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from app.database import initialize_database
from app.ui.dashboard import DashboardWindow


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

    window = DashboardWindow()
    window.show()

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
