import argparse

from receipt_intel.config import get_settings
from receipt_intel.pipeline import ingest_and_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest receipts and refresh the Qdrant index.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear the Qdrant collection and index manifest before re-embedding (full reindex).",
    )
    args = parser.parse_args()
    ingest_and_index(get_settings(), force=args.force)


if __name__ == "__main__":
    main()
