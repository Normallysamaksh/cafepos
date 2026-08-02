"""Verify the expected PyInstaller distribution layout after a Windows build."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    distribution = Path("dist") / "CafePOS"
    required_paths = (
        distribution / "CafePOS.exe",
        distribution / "cafepos.db",
        distribution / "config.json",
        distribution / "logs",
    )
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        print("Packaging verification failed. Missing:")
        print(*missing, sep="\n")
        return 1

    print("Packaging verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
