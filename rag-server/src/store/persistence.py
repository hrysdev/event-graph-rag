"""graph + FAISS + metadata の一括 save/load."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import networkx as nx
from loguru import logger

from src.store.vector_store import VectorStore

GRAPH_FILENAME = "graph.json"
FAISS_FILENAME = "events.faiss"
METADATA_FILENAME = "metadata.json"


def save(
    output_dir: str | Path,
    graph: nx.MultiDiGraph,
    vector_store: VectorStore,
    metadata: dict[str, Any],
) -> None:
    """3ファイルを一括保存（アトミック: 一時ディレクトリ経由）."""
    output_dir = Path(output_dir)

    # 同一ファイルシステム上の一時ディレクトリに書き込み
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(dir=parent, prefix=".video-rag-tmp-"))

    try:
        # グラフ → JSON（pickle非依存）
        graph_data = nx.node_link_data(graph, source="_nx_source", target="_nx_target")
        graph_path = tmp_dir / GRAPH_FILENAME
        graph_path.write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # FAISS インデックス
        faiss_path = tmp_dir / FAISS_FILENAME
        vector_store.save(faiss_path)

        # メタデータ
        meta_path = tmp_dir / METADATA_FILENAME
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        # 既存ディレクトリを削除してリネーム
        if output_dir.exists():
            import shutil

            shutil.rmtree(output_dir)
        os.rename(str(tmp_dir), str(output_dir))

        logger.info("保存完了: {}", output_dir)
    except BaseException:
        # 失敗時は一時ディレクトリを削除
        import shutil

        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


def load(
    index_dir: str | Path,
) -> tuple[nx.MultiDiGraph, VectorStore, dict[str, Any]]:
    """3ファイルを一括読み込み."""
    index_dir = Path(index_dir)

    # グラフ
    graph_path = index_dir / GRAPH_FILENAME
    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))
    graph = nx.node_link_graph(
        graph_data, directed=True, multigraph=True, source="_nx_source", target="_nx_target",
    )
    logger.info("グラフ読み込み: {} ノード, {} エッジ", graph.number_of_nodes(), graph.number_of_edges())

    # FAISS
    faiss_path = index_dir / FAISS_FILENAME
    vector_store = VectorStore()
    vector_store.load(faiss_path)

    # メタデータ
    meta_path = index_dir / METADATA_FILENAME
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    logger.info("メタデータ読み込み: {} エントリ", len(metadata.get("entries", [])))

    return graph, vector_store, metadata
