"""Offscreen integration check for first-launch configuration."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication, QDialog

import app.main as main
import app.services.configuration as configuration
from app.dialogs import FirstLaunchDialog


application = QApplication([])

dialog = FirstLaunchDialog()
dialog.save()
assert dialog.error_label.text() == "Cafe Name is required."
dialog.cafe_name_input.setText("Cafe Test")
dialog.receipt_footer_input.setText("Thank you!")
dialog.save()
assert dialog.result() == QDialog.DialogCode.Accepted
assert dialog.values == ("Cafe Test", "Thank you!")


class FakeSetupDialog:
    """Supply accepted setup values without displaying a native dialog."""

    def __init__(self, _parent: object = None) -> None:
        pass

    def exec(self) -> int:
        return QDialog.DialogCode.Accepted

    @property
    def values(self) -> tuple[str, str]:
        return "Test Cafe", "See you again"


with TemporaryDirectory() as temporary_directory:
    original_config_path = configuration.CONFIG_PATH
    original_setup_dialog = main.FirstLaunchDialog
    configuration.CONFIG_PATH = Path(temporary_directory) / "config.json"
    main.FirstLaunchDialog = FakeSetupDialog

    assert not configuration.configuration_exists()
    assert main.complete_first_launch_setup()
    assert configuration.configuration_exists()
    assert json.loads(configuration.CONFIG_PATH.read_text(encoding="utf-8")) == {
        "cafe_name": "Test Cafe",
        "receipt_footer": "See you again",
    }

    configuration.save_default_printer("Thermal 80mm")
    assert configuration.get_default_printer() == "Thermal 80mm"
    assert json.loads(configuration.CONFIG_PATH.read_text(encoding="utf-8")) == {
        "cafe_name": "Test Cafe",
        "receipt_footer": "See you again",
        "default_printer": "Thermal 80mm",
    }

    main.FirstLaunchDialog = original_setup_dialog
    configuration.CONFIG_PATH = original_config_path

print("Configuration integration: passed")
