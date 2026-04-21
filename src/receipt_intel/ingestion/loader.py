from __future__ import annotations

from pathlib import Path


def load_receipt_files(receipts_dir: Path) -> list[Path]:
    return sorted(receipts_dir.glob("receipt_*.txt"))

