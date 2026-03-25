from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class VideoObject(BaseModel):
    obj_id: str
    category: str
    first_seen_frame: int
    first_seen_timestamp: str
    attributes: Dict[str, Any]


class VideoEvent(BaseModel):
    event_id: str
    frame: int
    timestamp: str
    action: str
    agent: str
    target: str
    source: Optional[str] = None
    destination: Optional[str] = None


class RAGResponse(BaseModel):
    objects: List[VideoObject]
    events: List[VideoEvent]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    thinking: Optional[str] = None
    raw_rag: Optional[RAGResponse] = None
