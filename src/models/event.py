"""西川JSONL入力のドメインモデル."""

from __future__ import annotations

from pydantic import BaseModel


class DetectedObject(BaseModel):
    """検出されたオブジェクト."""

    obj_id: str
    category: str
    first_seen_frame: int
    first_seen_timestamp: str
    attributes: dict[str, object]


class Event(BaseModel):
    """単一イベント."""

    event_id: str
    frame: int
    timestamp: str
    action: str
    agent: str
    target: str
    source: str | None = None
    destination: str | None = None


class EventGraph(BaseModel):
    """1レコード分のイベントグラフ（JSONL 1行に対応）."""

    objects: list[DetectedObject]
    events: list[Event]
