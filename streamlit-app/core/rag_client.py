import httpx

from config import settings
from models.schema import RAGResponse


class RAGTimeoutError(Exception):
    """RAGサーバーへのリクエストがタイムアウトした"""


class RAGAPIError(Exception):
    """RAGサーバーが 4xx/5xx を返した"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class RAGParseError(Exception):
    """レスポンスのJSONパースまたはPydanticバリデーションが失敗した"""

    def __init__(self, raw_response: str):
        self.raw_response = raw_response
        super().__init__(f"Failed to parse response: {raw_response[:200]}")


def query(user_question: str) -> RAGResponse:
    """
    RAGサーバーにクエリを投げ、RAGResponseを返す。

    リクエスト:
      POST {settings.rag_api_url}
      Content-Type: application/json
      Body: {"query": user_question}

    レスポンス:
      200 OK: {"objects": [...], "events": [...]}

    Raises:
      RAGTimeoutError: タイムアウト発生時
      RAGAPIError:     HTTP 4xx/5xx 受信時
      RAGParseError:   JSONパース失敗またはPydanticバリデーション失敗時
    """
    try:
        with httpx.Client(timeout=settings.rag_api_timeout) as client:
            response = client.post(
                settings.rag_api_url,
                json={"query": user_question},
            )
    except httpx.TimeoutException as e:
        raise RAGTimeoutError("RAG server request timed out") from e

    if response.status_code >= 400:
        raise RAGAPIError(response.status_code, response.text)

    try:
        return RAGResponse.model_validate(response.json())
    except Exception as e:
        raise RAGParseError(response.text) from e


MOCK_RAG_RESPONSE: dict = {
    "objects": [
        {
            "obj_id": "person_01",
            "category": "person",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"pose": "standing", "orientation": "upright"},
        },
        {
            "obj_id": "cup_01",
            "category": "cup",
            "first_seen_frame": 3,
            "first_seen_timestamp": "2024-01-15T10:23:45.100Z",
            "attributes": {
                "color": "red",
                "material": "ceramic",
                "position": "on_desk",
                "size": "small",
                "state": "filled",
            },
        },
        {
            "obj_id": "table_01",
            "category": "table",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"material": "wooden", "size": "large"},
        },
    ],
    "events": [
        {
            "event_id": "evt_001",
            "frame": 5,
            "timestamp": "2024-01-15T10:23:45.167Z",
            "action": "pick_up",
            "agent": "person_01",
            "target": "cup_01",
            "source": "table_01",
            "destination": None,
        },
        {
            "event_id": "evt_002",
            "frame": 10,
            "timestamp": "2024-01-15T10:23:45.333Z",
            "action": "place_on",
            "agent": "person_01",
            "target": "cup_01",
            "source": None,
            "destination": "shelf_01",
        },
    ],
}


def mock_query(user_question: str) -> RAGResponse:
    """テスト用: 常に MOCK_RAG_RESPONSE を返す"""
    return RAGResponse(**MOCK_RAG_RESPONSE)
