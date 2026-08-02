"""Local configuration used by first-launch setup and receipt printing."""

import json
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


def configuration_exists() -> bool:
    """Return whether first-launch setup has already created a configuration file."""
    return CONFIG_PATH.is_file()


def load_configuration(config_path: Path | None = None) -> dict[str, object]:
    """Read local configuration, treating unreadable optional values as absent."""
    path = config_path or CONFIG_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_configuration(cafe_name: str, receipt_footer: str) -> None:
    """Create the first-launch configuration with the entered receipt details."""
    config = {
        "cafe_name": cafe_name.strip(),
        "receipt_footer": receipt_footer.strip(),
    }
    _write_configuration(config)


def get_default_printer(config_path: Path | None = None) -> str | None:
    """Return the stored receipt printer, if one has been selected."""
    return text_value(load_configuration(config_path), "default_printer", "Default Printer")


def save_default_printer(printer_name: str, config_path: Path | None = None) -> None:
    """Store a printer choice while preserving the existing café settings."""
    path = config_path or CONFIG_PATH
    config = load_configuration(path)
    key = "Default Printer" if "Default Printer" in config else "default_printer"
    config[key] = printer_name
    _write_configuration(config, path)


def text_value(config: dict[str, object], *keys: str) -> str | None:
    """Return the first non-empty string stored under the supplied keys."""
    for key in keys:
        value = config.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _write_configuration(config: dict[str, object], config_path: Path | None = None) -> None:
    path = config_path or CONFIG_PATH
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
