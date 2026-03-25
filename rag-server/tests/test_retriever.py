"""リトリーバーのテスト.

実際のruri-v3モデルは使わず、モックembedderでテスト.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import networkx as nx
import numpy as np
import pytest

from src.graph.builder import build
from src.ingestion.parser import parse
from src.ingestion.text_builder import build_texts
from src.models.event import Event, EventGraph
from src.models.response import RAGResponse
from src.retrieval.retriever import Retriever
from src.store.vector_store import VectorStore

SAMPLE_JSONL = "tests/fixtures/sample_events.jsonl"


def _build_test_env(
    graphs: list[EventGraph],
) -> tuple[MagicMock, VectorStore, dict, nx.MultiDiGraph, np.ndarray]:
    """テスト用のembedder, vector_store, metadataを構築."""
    graph = build(graphs)

    all_events: list[Event] = []
    for eg in graphs:
        all_events.extend(eg.events)
    texts = build_texts(all_events)

    # モックembedder: ランダムだが正規化されたベクトルを返す
    dim = 16
    embedder = MagicMock()
    embedder.dim = dim
    embedder.model_name = "test-model"

    # 文書embedding: 各イベントに固定ベクトルを割り当て
    rng = np.random.RandomState(42)
    doc_embeddings = rng.randn(len(texts), dim).astype(np.float32)
    # L2正規化
    norms = np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
    doc_embeddings = doc_embeddings / norms

    embedder.encode_documents.return_value = doc_embeddings

    # vector_store構築
    vs = VectorStore()
    vs.build(doc_embeddings)

    # メタデータ
    metadata = {
        "model_name": "test-model",
        "embedding_dim": dim,
        "entries": [
            {
                "faiss_idx": i,
                "event_id": evt.event_id,
                "timestamp": evt.timestamp,
                "object_ids": [evt.agent, evt.target],
                "text": text,
            }
            for i, (evt, text) in enumerate(zip(all_events, texts))
        ],
    }

    return embedder, vs, metadata, graph, doc_embeddings


def test_retrieve_returns_rag_response(sample_graphs: list[EventGraph]) -> None:
    """retrieveがRAGResponseを返す."""
    embedder, vs, metadata, graph, doc_embs = _build_test_env(sample_graphs)

    # クエリベクトルを最初の文書ベクトルと同じにする → 高いスコアでヒット
    embedder.encode_query.return_value = doc_embs[0:1]

    retriever = Retriever(
        embedder=embedder,
        vector_store=vs,
        graph=graph,
        metadata=metadata,
        similarity_threshold=0.5,
    )

    result = retriever.retrieve("テストクエリ")
    assert isinstance(result, RAGResponse)
    assert len(result.events) > 0
    assert len(result.objects) > 0


def test_retrieve_empty_result(sample_graphs: list[EventGraph]) -> None:
    """高い閾値で何もヒットしない場合、空のRAGResponse."""
    embedder, vs, metadata, graph, _ = _build_test_env(sample_graphs)

    # 直交ベクトル → スコア≈0
    dim = 16
    query_vec = np.zeros((1, dim), dtype=np.float32)
    query_vec[0, 0] = 1.0
    embedder.encode_query.return_value = query_vec

    retriever = Retriever(
        embedder=embedder,
        vector_store=vs,
        graph=graph,
        metadata=metadata,
        similarity_threshold=0.99,
    )

    result = retriever.retrieve("存在しないクエリ")
    assert isinstance(result, RAGResponse)
    assert len(result.events) == 0
    assert len(result.objects) == 0


def test_retrieve_max_expanded_events(sample_graphs: list[EventGraph]) -> None:
    """max_expanded_eventsで展開上限が効く."""
    embedder, vs, metadata, graph, doc_embs = _build_test_env(sample_graphs)

    # 全文書ベクトルの平均を取ることで多くのイベントを閾値0.0でヒットさせる
    mean_vec = doc_embs.mean(axis=0, keepdims=True)
    mean_vec = mean_vec / np.linalg.norm(mean_vec)
    embedder.encode_query.return_value = mean_vec

    retriever = Retriever(
        embedder=embedder,
        vector_store=vs,
        graph=graph,
        metadata=metadata,
        similarity_threshold=0.0,
        top_k=20,
        max_expanded_events=3,
    )

    result = retriever.retrieve("テスト")
    assert len(result.events) <= 3
    assert len(result.events) > 0


def test_retrieve_deduplicates_events(sample_graphs: list[EventGraph]) -> None:
    """event_idで重複排除される."""
    embedder, vs, metadata, graph, doc_embs = _build_test_env(sample_graphs)
    embedder.encode_query.return_value = doc_embs[0:1]

    retriever = Retriever(
        embedder=embedder,
        vector_store=vs,
        graph=graph,
        metadata=metadata,
        similarity_threshold=0.0,
        top_k=20,
    )

    result = retriever.retrieve("テスト")
    event_ids = [e.event_id for e in result.events]
    assert len(event_ids) == len(set(event_ids)), "イベントに重複がある"


def test_retrieve_deduplicates_objects(sample_graphs: list[EventGraph]) -> None:
    """obj_idで重複排除される."""
    embedder, vs, metadata, graph, doc_embs = _build_test_env(sample_graphs)
    embedder.encode_query.return_value = doc_embs[0:1]

    retriever = Retriever(
        embedder=embedder,
        vector_store=vs,
        graph=graph,
        metadata=metadata,
        similarity_threshold=0.0,
        top_k=20,
    )

    result = retriever.retrieve("テスト")
    obj_ids = [o.obj_id for o in result.objects]
    assert len(obj_ids) == len(set(obj_ids)), "オブジェクトに重複がある"


def test_parse_query_time_filter() -> None:
    """時間表現パースのテスト."""
    embedder = MagicMock()
    vs = VectorStore()
    graph_mock = MagicMock()
    metadata = {"entries": []}

    retriever = Retriever(
        embedder=embedder,
        vector_store=vs,
        graph=graph_mock,
        metadata=metadata,
    )

    parsed = retriever._parse_query("過去2時間のイベント")
    assert parsed["time_start"] is not None

    parsed_no_time = retriever._parse_query("赤いカップはどこ？")
    assert parsed_no_time["time_start"] is None
