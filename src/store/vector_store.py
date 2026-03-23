"""FAISS ベクトルストア操作."""

from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np
from loguru import logger


class VectorStore:
    """FAISS IndexFlatIP によるベクトル検索."""

    def __init__(self) -> None:
        self._index: faiss.IndexFlatIP | None = None

    @property
    def is_built(self) -> bool:
        return self._index is not None

    @property
    def ntotal(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal

    def build(self, embeddings: np.ndarray) -> None:
        """embeddingからFAISSインデックスを構築."""
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings.astype(np.float32))
        logger.info("FAISSインデックス構築完了: {} ベクトル (dim={})", self._index.ntotal, dim)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> tuple[np.ndarray, np.ndarray]:
        """クエリベクトルで検索. (scores, indices) を返す."""
        if self._index is None:
            raise RuntimeError("インデックスが構築されていません")
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        effective_k = min(top_k, self._index.ntotal)
        if effective_k == 0:
            return np.array([], dtype=np.float32), np.array([], dtype=np.int64)
        scores, indices = self._index.search(query_vector, effective_k)
        return scores[0], indices[0]

    def save(self, path: str | Path) -> None:
        """FAISSインデックスをファイルに保存."""
        if self._index is None:
            raise RuntimeError("インデックスが構築されていません")
        faiss.write_index(self._index, str(path))
        logger.info("FAISSインデックス保存: {}", path)

    def load(self, path: str | Path) -> None:
        """ファイルからFAISSインデックスを読み込み."""
        self._index = faiss.read_index(str(path))
        logger.info("FAISSインデックス読み込み: {} ({} ベクトル)", path, self._index.ntotal)
