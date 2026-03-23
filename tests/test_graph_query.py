"""グラフクエリのテスト."""

from __future__ import annotations

from src.graph.builder import build
from src.graph.query import get_object_events, get_object_info, get_related_objects
from src.models.event import EventGraph


def test_get_object_events_cup(sample_graphs: list[EventGraph]) -> None:
    """cup_01の全イベント取得."""
    G = build(sample_graphs)
    events = get_object_events(G, "cup_01")
    # cup_01はevt_001,002,003,006,007に関連
    assert len(events) == 5


def test_get_object_events_sorted(sample_graphs: list[EventGraph]) -> None:
    """イベントがタイムスタンプ順にソートされる."""
    G = build(sample_graphs)
    events = get_object_events(G, "cup_01")
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps)


def test_get_object_events_nonexistent(sample_graphs: list[EventGraph]) -> None:
    """存在しないobj_idは空リスト."""
    G = build(sample_graphs)
    events = get_object_events(G, "nonexistent_99")
    assert events == []


def test_get_related_objects_person01(sample_graphs: list[EventGraph]) -> None:
    """person_01の隣接ノード."""
    G = build(sample_graphs)
    related = get_related_objects(G, "person_01")
    assert "cup_01" in related


def test_get_related_objects_cup01(sample_graphs: list[EventGraph]) -> None:
    """cup_01の隣接ノード（in-edge経由でperson_01）."""
    G = build(sample_graphs)
    related = get_related_objects(G, "cup_01")
    assert "person_01" in related


def test_get_related_objects_nonexistent(sample_graphs: list[EventGraph]) -> None:
    """存在しないobj_idは空集合."""
    G = build(sample_graphs)
    related = get_related_objects(G, "nonexistent_99")
    assert related == set()


def test_get_object_info(sample_graphs: list[EventGraph]) -> None:
    """ノード属性が取得できる."""
    G = build(sample_graphs)
    info = get_object_info(G, "cup_01")
    assert info is not None
    assert info["category"] == "cup"
    assert info["first_seen_frame"] == 10
    assert info["first_seen_timestamp"] == "2026-03-21T10:00:01"


def test_get_object_info_nonexistent(sample_graphs: list[EventGraph]) -> None:
    """存在しないobj_idはNone."""
    G = build(sample_graphs)
    info = get_object_info(G, "nonexistent_99")
    assert info is None
