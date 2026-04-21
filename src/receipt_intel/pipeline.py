from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from receipt_intel.chunking import build_chunks
from receipt_intel.config import Settings
from receipt_intel.embeddings import OllamaEmbedder
from receipt_intel.ingestion import ReceiptParser, load_receipt_files
from receipt_intel.logging import configure_logging
from receipt_intel.models import Receipt
from receipt_intel.vectorstore import QdrantStore

logger = logging.getLogger(__name__)


def parse_receipts(settings: Settings) -> list[Receipt]:
    parser = ReceiptParser()
    parsed: list[Receipt] = []
    for path in load_receipt_files(settings.receipts_dir):
        parsed.append(parser.parse_file(path))
    return parsed


def save_parsed_receipts(receipts: list[Receipt], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for receipt in receipts:
            handle.write(receipt.model_dump_json() + "\n")


def ingest_and_index(settings: Settings, *, force: bool = False) -> None:
    configure_logging(settings.log_level)
    started = time.perf_counter()
    receipts = parse_receipts(settings)
    save_parsed_receipts(receipts, settings.parsed_output_path)

    if force:
        if settings.index_manifest_path.exists():
            settings.index_manifest_path.unlink()

    manifest = load_index_manifest(settings.index_manifest_path)
    current_hashes = compute_receipt_hashes(receipts)

    changed_receipts, unchanged_receipts, deleted_receipts = diff_manifest_receipts(
        manifest, receipts, current_hashes
    )

    all_chunks = []
    for receipt in changed_receipts:
        all_chunks.extend(build_chunks(receipt, strategy=settings.chunking_strategy))

    vector_size = _resolve_vector_size(settings)
    store = QdrantStore(
        path=str(settings.qdrant_path),
        collection_name=settings.qdrant_collection,
        vector_size=vector_size,
    )

    if force:
        store.reset(vector_size)
        stale_receipt_ids: list[str] = []
    else:
        stale_receipt_ids = [r.receipt_id for r in changed_receipts] + deleted_receipts
    store.delete_by_receipt_ids(stale_receipt_ids)

    upserted_count = 0
    if all_chunks:
        embedder = OllamaEmbedder(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )
        vectors = embedder.embed_documents([chunk.content for chunk in all_chunks])
        if vectors:
            store.upsert_chunks(all_chunks, vectors)
            upserted_count = len(all_chunks)

    updated_manifest = build_index_manifest(receipts, current_hashes, settings.chunking_strategy)
    save_index_manifest(settings.index_manifest_path, updated_manifest)

    elapsed = time.perf_counter() - started
    logger.info(
        "Index complete | receipts_total=%d changed=%d unchanged=%d deleted=%d chunks_upserted=%d elapsed_s=%.2f",
        len(receipts),
        len(changed_receipts),
        len(unchanged_receipts),
        len(deleted_receipts),
        upserted_count,
        elapsed,
    )


def load_parsed_receipts(path: Path) -> list[Receipt]:
    if not path.exists():
        return []
    receipts: list[Receipt] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            receipts.append(Receipt.model_validate(json.loads(line)))
    return receipts


def compute_receipt_hashes(receipts: list[Receipt]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for receipt in receipts:
        source_path = Path(receipt.source_file)
        content = source_path.read_text(encoding="utf-8")
        hashes[receipt.receipt_id] = hashlib.sha1(content.encode("utf-8")).hexdigest()
    return hashes


def load_index_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"receipts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_index_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def diff_manifest_receipts(
    manifest: dict[str, Any],
    receipts: list[Receipt],
    current_hashes: dict[str, str],
) -> tuple[list[Receipt], list[Receipt], list[str]]:
    previous = manifest.get("receipts", {})
    current_ids = {receipt.receipt_id for receipt in receipts}

    changed: list[Receipt] = []
    unchanged: list[Receipt] = []
    for receipt in receipts:
        previous_meta = previous.get(receipt.receipt_id)
        if not previous_meta:
            changed.append(receipt)
            continue
        if previous_meta.get("receipt_hash") != current_hashes.get(receipt.receipt_id):
            changed.append(receipt)
        else:
            unchanged.append(receipt)

    deleted = sorted(set(previous.keys()) - current_ids)
    return changed, unchanged, deleted


def build_index_manifest(
    receipts: list[Receipt],
    current_hashes: dict[str, str],
    chunking_strategy: str,
) -> dict[str, Any]:
    data: dict[str, Any] = {"receipts": {}}
    for receipt in receipts:
        chunks = build_chunks(receipt, strategy=chunking_strategy)
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        chunk_hashes = {
            chunk.chunk_id: hashlib.sha1(chunk.content.encode("utf-8")).hexdigest()
            for chunk in chunks
        }
        data["receipts"][receipt.receipt_id] = {
            "source_file": receipt.source_file,
            "receipt_hash": current_hashes[receipt.receipt_id],
            "chunk_ids": chunk_ids,
            "chunk_hashes": chunk_hashes,
        }
    return data


def _resolve_vector_size(settings: Settings) -> int:
    # Keep collection creation deterministic even when no chunks are changed.
    embedder = OllamaEmbedder(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )
    probe = embedder.embed_query("receipt-index-probe")
    if not probe:
        raise RuntimeError("Could not resolve embedding vector size.")
    return len(probe)

