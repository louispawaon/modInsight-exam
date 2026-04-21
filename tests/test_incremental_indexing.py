from __future__ import annotations

from datetime import datetime
from pathlib import Path

from receipt_intel.models import Receipt
from receipt_intel.pipeline import (
    build_index_manifest,
    compute_receipt_hashes,
    diff_manifest_receipts,
)


def _receipt(tmp_path: Path, receipt_id: str, filename: str, text: str) -> Receipt:
    source = tmp_path / filename
    source.write_text(text, encoding="utf-8")
    return Receipt(
        receipt_id=receipt_id,
        source_file=str(source),
        merchant="Store",
        category="grocery",
        date=datetime(2023, 12, 1),
        total=10.0,
    )


def test_diff_manifest_marks_unchanged_and_changed(tmp_path: Path) -> None:
    r1 = _receipt(tmp_path, "receipt_001", "r1.txt", "A")
    r2 = _receipt(tmp_path, "receipt_002", "r2.txt", "B")
    receipts = [r1, r2]
    hashes = compute_receipt_hashes(receipts)
    manifest = build_index_manifest(receipts, hashes, "receipt_level")

    changed, unchanged, deleted = diff_manifest_receipts(manifest, receipts, hashes)
    assert len(changed) == 0
    assert len(unchanged) == 2
    assert deleted == []

    (tmp_path / "r2.txt").write_text("B changed", encoding="utf-8")
    new_hashes = compute_receipt_hashes(receipts)
    changed, unchanged, deleted = diff_manifest_receipts(manifest, receipts, new_hashes)
    assert {r.receipt_id for r in changed} == {"receipt_002"}
    assert {r.receipt_id for r in unchanged} == {"receipt_001"}
    assert deleted == []

