from __future__ import annotations

from pathlib import Path

from receipt_intel.ingestion import ReceiptParser


def test_parser_extracts_city_state_from_grocery_sample() -> None:
    receipt = ReceiptParser().parse_file(
        Path("Notes/receipt_samples_100/receipt_001_grocery_20231107.txt")
    )
    assert receipt.city == "daly city"
    assert receipt.state == "CA"
    assert receipt.payment_method == "VISA"


def test_parser_extracts_tip_amount_and_pct(tmp_path: Path) -> None:
    sample = tmp_path / "receipt_999_restaurant_20231215.txt"
    sample.write_text(
        "\n".join(
            [
                "Tasty Spot",
                "San Francisco, CA",
                "Date: 2023-12-15",
                "Pasta                          $ 20.00",
                "SUBTOTAL:                      $ 20.00",
                "TAX (8.5%):                    $  1.70",
                "TIP (20%)                      $  4.00",
                "TOTAL:                         $ 25.70",
                "VISA ****0000                  $ 25.70",
            ]
        ),
        encoding="utf-8",
    )
    receipt = ReceiptParser().parse_file(sample)
    assert receipt.tip_amount == 4.00
    assert receipt.tip_pct == 20.0
    assert receipt.tax_rate == 8.5
    assert all("TIP" not in item.name.upper() for item in receipt.items)


def test_parser_flags_warranty_on_electronics_sample() -> None:
    receipt = ReceiptParser().parse_file(
        Path("Notes/receipt_samples_100/receipt_076_electronics_20231216.txt")
    )
    assert receipt.has_warranty is True


def test_parser_flags_prescription_on_pharmacy_sample_and_extracts_rx_item() -> None:
    receipt = ReceiptParser().parse_file(
        Path("Notes/receipt_samples_100/receipt_086_pharmacy_20240101.txt")
    )
    assert receipt.has_prescription is True
    assert any(item.name.lower().startswith("rx:") for item in receipt.items)


def test_parser_handles_missing_optional_metadata(tmp_path: Path) -> None:
    sample = tmp_path / "receipt_001_grocery_20231201.txt"
    sample.write_text(
        "\n".join(
            [
                "Tiny Mart",
                "Date: 2023-12-01",
                "Apple                          $  1.00",
                "TOTAL:                         $  1.00",
            ]
        ),
        encoding="utf-8",
    )
    receipt = ReceiptParser().parse_file(sample)
    assert receipt.city is None
    assert receipt.state is None
    assert receipt.tip_amount is None
    assert receipt.tax_rate is None
    assert receipt.has_warranty is False
    assert receipt.has_prescription is False
    assert receipt.loyalty_flag is False
