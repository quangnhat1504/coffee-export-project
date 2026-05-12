"""Path helpers for data scripts."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_COLLECT_DIR = PROJECT_ROOT / "collect_data"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def resolve_data_file(filename: str) -> Path:
    """Resolve a data file, preferring new data/raw and falling back to collect_data."""
    explicit = Path(filename)
    if explicit.exists():
        return explicit

    candidates = [
        RAW_DATA_DIR / filename,
        LEGACY_COLLECT_DIR / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find {filename} in data/raw or collect_data")
