"""FAISS検索 → グラフ展開 → RAGResponse."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import networkx as nx
from loguru import logger

from src.graph.query import get_object_events, get_object_info
from src.models.response import RAGResponse, VideoEvent, VideoObject
from src.store.embedder import Embedder
from src.store.vector_store import VectorStore

# 時間表現の正規表現パターン
_TIME_PATTERN = re.compile(r"過去(\d+)(時間|分|秒)")
_TIME_UNITS = {"時間": "hours", "分": "minutes", "秒": "seconds"}


class Retriever:
    """検索エンジン: クエリ → RAGResponse."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        graph: nx.MultiDiGraph,
        metadata: dict[str, Any],
        *,
        similarity_threshold: float = 0.7,
        top_k: int = 10,
        max_expanded_events: int = 50,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._graph = graph
        self._metadata = metadata
        self._threshold = similarity_threshold
        self._top_k = top_k
        self._max_expanded = max_expanded_events
        self._entries = metadata.get("entries", [])

    def retrieve(self, query: str) -> RAGResponse:
        """クエリからRAGResponseを返す."""
        parsed = self._parse_query(query)
        hits = self._search(parsed)
        expanded = self._expand(hits)
        return self._to_response(expanded)

    def _parse_query(self, query: str) -> dict[str, Any]:
        """時間表現を解析."""
        result: dict[str, Any] = {"query": query, "time_start": None}

        match = _TIME_PATTERN.search(query)
        if match:
            amount = int(match.group(1))
            unit = _TIME_UNITS[match.group(2)]
            result["time_start"] = datetime.now() - timedelta(**{unit: amount})
            logger.debug("時間フィルタ検出: 過去{}{}", amount, match.group(2))

        return result

    def _search(self, parsed: dict[str, Any]) -> list[dict[str, Any]]:
        """FAISS検索 + 閾値フィルタ + 時間範囲フィルタ."""
        query_vec = self._embedder.encode_query(parsed["query"])
        scores, indices = self._vector_store.search(query_vec, self._top_k)

        hits: list[dict[str, Any]] = []
        for score, idx in zip(scores, indices):
            idx = int(idx)
            if idx < 0 or score < self._threshold:
                continue

            entry = self._entries[idx]

            # 時間範囲フィルタ
            if parsed["time_start"] is not None:
                ts = entry.get("timestamp")
                if ts is None:
                    continue
                try:
                    evt_time = datetime.fromisoformat(ts)
                    if evt_time < parsed["time_start"]:
                        continue
                except ValueError:
                    continue

            hits.append({**entry, "score": float(score)})

        logger.info("FAISS検索: {} ヒット (閾値={:.2f})", len(hits), self._threshold)
        return hits

    def _expand(self, hits: list[dict[str, Any]]) -> dict[str, Any]:
        """ヒットからobject_ids抽出 → グラフ展開."""
        # ヒットしたイベントID集合（直接ヒットは上限適用時にも保持）
        hit_event_ids: set[str] = {h["event_id"] for h in hits}

        # ヒットから全object_idsを収集
        object_ids: set[str] = set()
        for hit in hits:
            object_ids.update(hit.get("object_ids", []))

        # グラフ展開: 各オブジェクトの全イベントを取得
        hit_events: list[dict[str, Any]] = []
        expanded_events: list[dict[str, Any]] = []
        seen_event_ids: set[str] = set()

        for obj_id in object_ids:
            obj_events = get_object_events(self._graph, obj_id)
            for evt in obj_events:
                eid = evt.get("event_id", "")
                if eid not in seen_event_ids:
                    seen_event_ids.add(eid)
                    if eid in hit_event_ids:
                        hit_events.append(evt)
                    else:
                        expanded_events.append(evt)

        # 直接ヒットを優先しつつ、全体を max_expanded_events でキャップ
        remaining = max(0, self._max_expanded - len(hit_events))
        expanded_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        expanded_events = expanded_events[:remaining]

        all_events = hit_events + expanded_events
        all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        all_events = all_events[: self._max_expanded]
        all_events.sort(key=lambda e: e.get("timestamp", ""))

        logger.info(
            "グラフ展開: {} オブジェクト → {} イベント (上限={})",
            len(object_ids),
            len(all_events),
            self._max_expanded,
        )

        return {"object_ids": object_ids, "events": all_events}

    def _to_response(self, expanded: dict[str, Any]) -> RAGResponse:
        """重複排除 + RAGResponse変換."""
        # Events変換（event_idで重複排除済み）
        events: list[VideoEvent] = []
        for evt in expanded["events"]:
            events.append(
                VideoEvent(
                    event_id=evt["event_id"],
                    frame=evt["frame"],
                    timestamp=evt["timestamp"],
                    action=evt["action"],
                    agent=evt["agent"],
                    target=evt["target"],
                    source=evt.get("source"),
                    destination=evt.get("destination"),
                )
            )

        # Objects変換（obj_idで重複排除）
        objects: list[VideoObject] = []
        seen_obj_ids: set[str] = set()
        for obj_id in expanded["object_ids"]:
            if obj_id in seen_obj_ids:
                continue
            seen_obj_ids.add(obj_id)

            info = get_object_info(self._graph, obj_id)
            if info is None:
                continue

            objects.append(
                VideoObject(
                    obj_id=obj_id,
                    category=info["category"],
                    first_seen_frame=info["first_seen_frame"],
                    first_seen_timestamp=info["first_seen_timestamp"],
                    attributes=info.get("attributes", {}),
                )
            )

        return RAGResponse(objects=objects, events=events)
