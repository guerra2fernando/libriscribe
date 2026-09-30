"""Optional on-device sentence-transformer index. Imported only for semantic modes."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from libriscribe.retrieval.models import RetrievalChunk


class SemanticIndex:
    """Stores normalized local embeddings as JSON; no vector service is used."""

    def __init__(self, model_name: str, *, local_files_only: bool = True) -> None:
        self.model_name = model_name
        self.local_files_only = local_files_only
        self.vectors: dict[str, list[float]] = {}
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise RuntimeError(
                    "Semantic search requires the optional 'semantic' extra "
                    "(pip install libriscribe[semantic])."
                ) from None
            try:
                self._model = SentenceTransformer(
                    self.model_name, local_files_only=self.local_files_only
                )
            except Exception as exc:
                detail = " The model must already be available locally." if self.local_files_only else ""
                raise RuntimeError(f"Could not load local embedding model '{self.model_name}'.{detail}") from exc
        return self._model

    @staticmethod
    def _normalize(vector: Any) -> list[float]:
        values = [float(value) for value in vector]
        norm = math.sqrt(sum(value * value for value in values))
        return [value / norm for value in values] if norm else values

    def build(self, chunks: list[RetrievalChunk]) -> None:
        if not chunks:
            self.vectors = {}
            return
        model = self._load_model()
        encoded = model.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
        self.vectors = {
            chunk.chunk_id: self._normalize(vector)
            for chunk, vector in zip(chunks, encoded, strict=True)
        }

    def score(self, query: str) -> dict[str, float]:
        if not self.vectors:
            return {}
        vector = self._normalize(self._load_model().encode([query], normalize_embeddings=True)[0])
        return {
            chunk_id: sum(a * b for a, b in zip(vector, document_vector, strict=True))
            for chunk_id, document_vector in self.vectors.items()
        }

    def save_to_file(self, file_path: Path) -> None:
        payload = {"model": self.model_name, "vectors": self.vectors}
        with file_path.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False)

    def load_from_file(self, file_path: Path) -> None:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if payload.get("model") != self.model_name:
            raise ValueError("Semantic index model does not match project retrieval configuration; rebuild it.")
        vectors = payload.get("vectors")
        if not isinstance(vectors, dict):
            raise ValueError("Semantic index is invalid; rebuild it.")
        self.vectors = {
            str(chunk_id): [float(value) for value in vector]
            for chunk_id, vector in vectors.items()
        }
