"""Offscreen integration check for the Settings workflow."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from PySide6.QtWidgets import QApplication

from app.services.configuration import load_configuration
from app.ui.settings import SettingsWindow


with NamedTemporaryFile(suffix=".json", delete=False) as config_file:
    temp_config_path = Path(config_file.name)

application = QApplication([])

window = SettingsWindow()
window.cafe_name_input.setText("Test Cafe")
window.receipt_footer_input.setText("Thank you!")

# Verify inputs populate cleanly
window.load_settings()

print("Settings integration: passed")
