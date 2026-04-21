from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    receipts_dir: Path = Field(
        default=Path("Notes/receipt_samples_100"),
        description="Directory with raw receipt txt files.",
    )
    parsed_output_path: Path = Field(
        default=Path("data/parsed_receipts.jsonl"),
        description="Serialized parsed receipts for debug and incremental indexing.",
    )
    index_manifest_path: Path = Field(default=Path("data/index_manifest.json"))
    qdrant_path: Path = Field(default=Path("data/qdrant"))
    qdrant_collection: str = Field(default="receipt_chunks")

    chunking_strategy: str = Field(default="hybrid")
    max_chunk_chars: int = Field(default=1200)

    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_embedding_model: str = Field(default="nomic-embed-text")
    ollama_chat_model: str = Field(default="llama3.1:8b")
    ollama_intent_timeout_s: int = Field(default=20)
    ollama_answer_timeout_s: int = Field(default=12)

    date_parse_order: str = Field(default="mdy")
    date_ambiguity_strategy: str = Field(default="flag")

    retrieval_k: int = Field(default=12)
    retrieval_sparse_threshold: int = Field(default=4)
    answer_style: str = Field(default="hybrid")
    log_level: str = Field(default="INFO")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

