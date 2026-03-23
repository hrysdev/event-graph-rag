"""ruri-v3 embedding ラッパー."""

from __future__ import annotations

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer


class Embedder:
    """sentence-transformers による embedding.

    ruri-v3 のプレフィックス付与とL2正規化を行う.
    """

    DOCUMENT_PREFIX = "検索文書: "
    QUERY_PREFIX = "検索クエリ: "

    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-310m") -> None:
        logger.info("Embeddingモデルロード中: {}", model_name)
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        dim = self._model.get_sentence_embedding_dimension()
        if dim is None:
            raise RuntimeError(f"Embedding次元数を取得できません: {model_name}")
        self._dim: int = dim
        logger.info("モデルロード完了 (dim={})", self._dim)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        """文書テキストをembedding（プレフィックス自動付与、L2正規化）."""
        prefixed = [self.DOCUMENT_PREFIX + t for t in texts]
        return self._model.encode(prefixed, normalize_embeddings=True)

    def encode_query(self, query: str) -> np.ndarray:
        """クエリテキストをembedding（プレフィックス自動付与、L2正規化）."""
        prefixed = self.QUERY_PREFIX + query
        return self._model.encode([prefixed], normalize_embeddings=True)
