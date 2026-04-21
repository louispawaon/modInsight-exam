from receipt_intel.config import get_settings
from receipt_intel.pipeline import ingest_and_index


def main() -> None:
    ingest_and_index(get_settings())


if __name__ == "__main__":
    main()

