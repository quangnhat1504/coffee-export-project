"""Path helpers for data scripts."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def resolve_data_file(filename: str) -> Path:
    """Resolve a data file from data/raw or an explicit path."""
    explicit = Path(filename)
    if explicit.exists():
        return explicit

    candidates = [RAW_DATA_DIR / filename]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find {filename} in data/raw")
