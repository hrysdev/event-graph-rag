"""NetworkX MultiDiGraph 構築."""

from __future__ import annotations

import networkx as nx
from loguru import logger

from src.models.event import EventGraph


def build(graphs: list[EventGraph]) -> nx.MultiDiGraph:
    """EventGraph リストから MultiDiGraph を構築.

    ノード: オブジェクト（obj_id, category, attributes）
    エッジ: イベント（agent→target, key=event_id）
    重複オブジェクトは後勝ち（attributesを上書き）.
    """
    G = nx.MultiDiGraph()

    for eg in graphs:
        # ノード追加（後勝ちマージ）
        for obj in eg.objects:
            G.add_node(
                obj.obj_id,
                category=obj.category,
                first_seen_frame=obj.first_seen_frame,
                first_seen_timestamp=obj.first_seen_timestamp,
                attributes=obj.attributes,
            )

        # エッジ追加（agent/targetが未登録ノードならデフォルト属性で作成）
        for evt in eg.events:
            for node_id in (evt.agent, evt.target):
                if node_id not in G:
                    logger.warning("objectsに未定義のノード '{}' をデフォルト属性で作成", node_id)
                    G.add_node(
                        node_id,
                        category="unknown",
                        first_seen_frame=evt.frame,
                        first_seen_timestamp=evt.timestamp,
                        attributes={},
                    )
            G.add_edge(
                evt.agent,
                evt.target,
                key=evt.event_id,
                event_id=evt.event_id,
                frame=evt.frame,
                timestamp=evt.timestamp,
                action=evt.action,
                source=evt.source,
                destination=evt.destination,
            )

    logger.info(
        "グラフ構築完了: {} ノード, {} エッジ",
        G.number_of_nodes(),
        G.number_of_edges(),
    )
    return G
