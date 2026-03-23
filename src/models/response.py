"""菅野optiBot API出力モデル（スキーマ準拠必須）."""

from __future__ import annotations

from pydantic import BaseModel


class VideoObject(BaseModel):
    """検出オブジェクト情報."""

    obj_id: str
    category: str
    first_seen_frame: int
    first_seen_timestamp: str
    attributes: dict[str, object]


class VideoEvent(BaseModel):
    """イベント情報."""

    event_id: str
    frame: int
    timestamp: str
    action: str
    agent: str
    target: str
    source: str | None = None
    destination: str | None = None


class RAGResponse(BaseModel):
    """RAG検索結果（菅野optiBot連携用）."""

    objects: list[VideoObject]
    events: list[VideoEvent]
