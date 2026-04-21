from pathlib import Path

from receipt_intel.chunking import build_chunks
from receipt_intel.ingestion import ReceiptParser


def test_parse_receipt_sample() -> None:
    parser = ReceiptParser()
    receipt = parser.parse_file(
        Path("Notes/receipt_samples_100/receipt_001_grocery_20231107.txt")
    )
    assert receipt.receipt_id == "receipt_001"
    assert receipt.total > 0
    assert receipt.items


def test_hybrid_chunking_has_both_types() -> None:
    parser = ReceiptParser()
    receipt = parser.parse_file(
        Path("Notes/receipt_samples_100/receipt_001_grocery_20231107.txt")
    )
    chunks = build_chunks(receipt, strategy="hybrid")
    chunk_types = {c.chunk_type for c in chunks}
    assert "receipt" in chunk_types
    assert "item" in chunk_types


def test_parser_handles_iso_date_and_quantity_pattern(tmp_path: Path) -> None:
    sample = tmp_path / "receipt_999_grocery_20231201.txt"
    sample.write_text(
        "\n".join(
            [
                "Sample Mart",
                "San Jose, CA",
                "Date: 2023-12-01",
                "2x Protein Bar                 $  6.00",
                "SUBTOTAL:                      $  6.00",
                "TAX:                           $  0.51",
                "TOTAL:                         $  6.51",
                "VISA ****1111                  $  6.51",
            ]
        ),
        encoding="utf-8",
    )
    receipt = ReceiptParser().parse_file(sample)
    assert receipt.date.date().isoformat() == "2023-12-01"
    assert receipt.items[0].quantity == 2
    assert receipt.metadata.get("date_source") in {"date_line", "regex_scan"}
    assert receipt.metadata.get("date_policy")

