from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from geoai_roman_spain.pipeline import run_pipeline  # noqa: E402
from tools.build_technical_report import build as build_technical_report  # noqa: E402


if __name__ == "__main__":
    run_pipeline(ROOT)
    build_technical_report()
