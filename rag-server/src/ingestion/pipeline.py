"""取り込みパイプライン: JSONL → インデックス一括構築."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.graph.builder import build as build_graph
from src.ingestion.parser import parse
from src.ingestion.text_builder import build_texts
from src.models.event import Event
from src.store.embedder import Embedder
from src.store.persistence import save
from src.store.vector_store import VectorStore


def ingest(input_path: str | Path, output_dir: str | Path, embedder: Embedder) -> None:
    """JSONLファイルからインデックスを構築し保存.

    1. parse → list[EventGraph]
    2. build_graph → MultiDiGraph
    3. build_texts → 各エッジの日本語テキスト
    4. encode_documents → ベクトル化
    5. build FAISS → インデックス構築
    6. save → 3ファイル一括保存
    """
    input_path = Path(input_path)

    # 1. パース
    logger.info("Step 1/6: パース中 ({})", input_path)
    graphs = parse(input_path)

    # 2. グラフ構築
    logger.info("Step 2/6: グラフ構築中")
    graph = build_graph(graphs)

    # 3. 全イベント収集 & テキスト生成
    logger.info("Step 3/6: テキスト生成中")
    all_events: list[Event] = []
    for eg in graphs:
        all_events.extend(eg.events)

    texts = build_texts(all_events)
    logger.info("テキスト生成完了: {} 件", len(texts))

    # 4. embedding
    logger.info("Step 4/6: Embedding中")
    embeddings = embedder.encode_documents(texts)

    # 5. FAISSインデックス構築
    logger.info("Step 5/6: FAISSインデックス構築中")
    vector_store = VectorStore()
    vector_store.build(embeddings)

    # 6. メタデータ作成 & 一括保存
    logger.info("Step 6/6: 保存中 ({})", output_dir)
    metadata = {
        "model_name": embedder.model_name,
        "embedding_dim": embedder.dim,
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

    save(output_dir, graph, vector_store, metadata)
    logger.info("取り込み完了: {} イベント → {}", len(all_events), output_dir)
