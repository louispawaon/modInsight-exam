from __future__ import annotations

from langchain_ollama import OllamaEmbeddings


class OllamaEmbedder:
    def __init__(self, model: str, base_url: str) -> None:
        self._client = OllamaEmbeddings(model=model, base_url=base_url)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)

