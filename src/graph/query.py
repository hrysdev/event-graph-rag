"""グラフ走査ユーティリティ."""

from __future__ import annotations

from typing import Any

import networkx as nx


def get_object_events(graph: nx.MultiDiGraph, obj_id: str) -> list[dict[str, Any]]:
    """指定オブジェクトに関連する全エッジ（in+out）を返す.

    タイムスタンプ順にソート.
    """
    if obj_id not in graph:
        return []

    events: list[dict[str, Any]] = []
    seen_eids: set[str] = set()

    # out-edges（agentとして）
    for _, target, data in graph.out_edges(obj_id, data=True):
        eid = data.get("event_id", "")
        if eid not in seen_eids:
            seen_eids.add(eid)
            events.append({**data, "agent": obj_id, "target": target})

    # in-edges（targetとして、self-loop重複を排除）
    for agent, _, data in graph.in_edges(obj_id, data=True):
        eid = data.get("event_id", "")
        if eid not in seen_eids:
            seen_eids.add(eid)
            events.append({**data, "agent": agent, "target": obj_id})

    # タイムスタンプ順ソート
    events.sort(key=lambda e: e.get("timestamp", ""))
    return events


def get_related_objects(graph: nx.MultiDiGraph, obj_id: str) -> set[str]:
    """1ホップ隣接ノードを返す（方向を問わず）."""
    if obj_id not in graph:
        return set()

    related: set[str] = set()
    related.update(graph.successors(obj_id))
    related.update(graph.predecessors(obj_id))
    related.discard(obj_id)
    return related


def get_object_info(graph: nx.MultiDiGraph, obj_id: str) -> dict[str, Any] | None:
    """ノード属性辞書を返す. 存在しない場合はNone."""
    if obj_id not in graph:
        return None
    return dict(graph.nodes[obj_id])
