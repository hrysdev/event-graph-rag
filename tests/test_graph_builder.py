"""グラフビルダーのテスト."""

from __future__ import annotations

from src.graph.builder import build
from src.models.event import EventGraph


def test_build_node_count(sample_graphs: list[EventGraph]) -> None:
    """ユニークなオブジェクト数がノード数と一致."""
    G = build(sample_graphs)
    # person_01, person_02, cup_01, table_01, shelf_01, book_01 = 6
    assert G.number_of_nodes() == 6


def test_build_edge_count(sample_graphs: list[EventGraph]) -> None:
    """全イベント数がエッジ数と一致."""
    G = build(sample_graphs)
    assert G.number_of_edges() == 9


def test_multiple_edges_between_same_pair(sample_graphs: list[EventGraph]) -> None:
    """同じペア間に複数エッジが存在する（MultiDiGraph）."""
    G = build(sample_graphs)
    # person_01 → cup_01: evt_001, evt_002, evt_003, evt_006, evt_007 = 5
    edges = G.get_edge_data("person_01", "cup_01")
    assert edges is not None
    assert len(edges) == 5


def test_node_attributes(sample_graphs: list[EventGraph]) -> None:
    """ノード属性が正しく設定される."""
    G = build(sample_graphs)
    cup = G.nodes["cup_01"]
    assert cup["category"] == "cup"
    assert cup["first_seen_frame"] == 10


def test_node_attribute_last_wins(sample_graphs: list[EventGraph]) -> None:
    """同じobj_idが複数レコードに出現 → 後勝ち."""
    G = build(sample_graphs)
    cup = G.nodes["cup_01"]
    # 最後のレコード(4番目)でcontents: coffeeが追加される
    assert cup["attributes"]["color"] == "red"
    assert cup["attributes"]["contents"] == "coffee"


def test_edge_attributes(sample_graphs: list[EventGraph]) -> None:
    """エッジ属性が正しく設定される."""
    G = build(sample_graphs)
    edge_data = G.get_edge_data("person_01", "cup_01", key="evt_001")
    assert edge_data is not None
    assert edge_data["action"] == "pick_up"
    assert edge_data["source"] == "table_01"
    assert edge_data["destination"] is None


def test_build_empty() -> None:
    """空リストでもエラーにならない."""
    G = build([])
    assert G.number_of_nodes() == 0
    assert G.number_of_edges() == 0
