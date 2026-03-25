"""FastAPI サーバー（:9000）."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, UploadFile
from loguru import logger
from pydantic import BaseModel

from src.config import Settings
from src.dependencies import AppState, get_embedder, get_settings, get_state, set_state
from src.ingestion.pipeline import ingest
from src.models.response import RAGResponse
from src.retrieval.retriever import Retriever
from src.store.embedder import Embedder

app = FastAPI(title="Video-RAG", version="0.1.0")


class QueryRequest(BaseModel):
    query: str


class StatusResponse(BaseModel):
    nodes: int
    edges: int
    chunks: int


@app.post("/query", response_model=RAGResponse)
def query(
    request: QueryRequest,
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> RAGResponse:
    """クエリからRAGResponseを返す（菅野optiBot連携）."""
    state = get_state()

    retriever = Retriever(
        embedder=embedder,
        vector_store=state.vector_store,
        graph=state.graph,
        metadata=state.metadata,
        similarity_threshold=settings.similarity_threshold,
        top_k=settings.top_k,
        max_expanded_events=settings.max_expanded_events,
    )

    logger.info("クエリ受信: {}", request.query)
    response = retriever.retrieve(request.query)
    logger.info("応答: {} objects, {} events", len(response.objects), len(response.events))
    return response


@app.post("/ingest")
def ingest_endpoint(
    file: UploadFile,
    settings: Settings = Depends(get_settings),
    embedder: Embedder = Depends(get_embedder),
) -> dict:
    """JSONLファイルアップロード → インデックス構築."""
    output_dir = Path(tempfile.mkdtemp(prefix="video-rag-"))
    tmp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            content = file.file.read()
            tmp.write(content)
            tmp_path = tmp.name

        ingest(tmp_path, output_dir, embedder)

        # ステートをアトミックに入れ替え
        from src.store.persistence import load

        graph, vector_store, metadata = load(output_dir)
        set_state(AppState(graph=graph, vector_store=vector_store, metadata=metadata))

        return {"status": "ok", "events": len(metadata.get("entries", []))}
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        shutil.rmtree(output_dir, ignore_errors=True)


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    """ノード数/エッジ数/チャンク数を返す."""
    state = get_state()
    return StatusResponse(
        nodes=state.graph.number_of_nodes(),
        edges=state.graph.number_of_edges(),
        chunks=state.vector_store.ntotal,
    )
