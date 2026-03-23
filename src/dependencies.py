"""共有インスタンス管理（@lru_cache + FastAPI Depends）."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import networkx as nx

from src.config import Settings
from src.store.embedder import Embedder
from src.store.vector_store import VectorStore


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_embedder() -> Embedder:
    settings = get_settings()
    return Embedder(model_name=settings.embedding_model)


@dataclass(frozen=True)
class AppState:
    """graph + vector_store + metadata をアトミックに管理."""

    graph: nx.MultiDiGraph
    vector_store: VectorStore
    metadata: dict[str, Any]


_state_lock = threading.Lock()
_state: AppState = AppState(
    graph=nx.MultiDiGraph(),
    vector_store=VectorStore(),
    metadata={},
)


def get_state() -> AppState:
    with _state_lock:
        return _state


def set_state(state: AppState) -> None:
    global _state
    with _state_lock:
        _state = state
