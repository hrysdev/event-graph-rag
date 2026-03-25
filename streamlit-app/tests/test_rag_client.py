import pytest
import httpx
import respx
from pydantic import ValidationError

from core.rag_client import query, mock_query, RAGTimeoutError, RAGAPIError, RAGParseError, MOCK_RAG_RESPONSE
from models.schema import RAGResponse
from config import settings

VALID_RESPONSE = {
    "objects": [
        {
            "obj_id": "person_01",
            "category": "person",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {},
        }
    ],
    "events": [
        {
            "event_id": "evt_001",
            "frame": 1,
            "timestamp": "2024-01-15T10:23:45.033Z",
            "action": "stand",
            "agent": "person_01",
            "target": "person_01",
            "source": None,
            "destination": None,
        }
    ],
}


# --- query() 正常系 ---

@respx.mock
def test_T3_01_query_returns_rag_response():
    """T3-01: 200レスポンス時にRAGResponseインスタンスが返る"""
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))
    result = query("テスト質問")
    assert isinstance(result, RAGResponse)


@respx.mock
def test_T3_02_query_correct_counts():
    """T3-02: objects と events の件数が正しい"""
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))
    result = query("テスト質問")
    assert len(result.objects) == 1
    assert len(result.events) == 1


@respx.mock
def test_T3_03_query_request_body():
    """T3-03: リクエストボディに {"query": user_question} が含まれる"""
    route = respx.post(settings.rag_api_url).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))
    query("テスト質問")
    import json
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {"query": "テスト質問"}


@respx.mock
def test_T3_04_query_correct_url():
    """T3-04: リクエストURLが settings.rag_api_url と一致する"""
    route = respx.post(settings.rag_api_url).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))
    query("テスト質問")
    assert str(route.calls[0].request.url) == settings.rag_api_url


# --- query() エラー系 ---

@respx.mock
def test_T3_05_timeout_raises_rag_timeout_error():
    """T3-05: タイムアウト時にRAGTimeoutErrorが raise される"""
    respx.post(settings.rag_api_url).mock(side_effect=httpx.TimeoutException("timeout"))
    with pytest.raises(RAGTimeoutError):
        query("テスト質問")


@respx.mock
def test_T3_06_http_404_raises_rag_api_error():
    """T3-06: HTTP 404 時に RAGAPIError が raise される"""
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(404, text="Not Found"))
    with pytest.raises(RAGAPIError):
        query("テスト質問")


@respx.mock
def test_T3_07_http_500_raises_rag_api_error():
    """T3-07: HTTP 500 時に RAGAPIError が raise される"""
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(500, text="Internal Server Error"))
    with pytest.raises(RAGAPIError):
        query("テスト質問")


@respx.mock
def test_T3_08_rag_api_error_has_status_code():
    """T3-08: RAGAPIError が status_code 属性を持つ"""
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(404, text="Not Found"))
    with pytest.raises(RAGAPIError) as exc_info:
        query("テスト質問")
    assert exc_info.value.status_code == 404


@respx.mock
def test_T3_09_invalid_json_raises_rag_parse_error():
    """T3-09: 不正なJSON返却時に RAGParseError が raise される"""
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(200, content=b"not-json"))
    with pytest.raises(RAGParseError):
        query("テスト質問")


@respx.mock
def test_T3_10_pydantic_validation_failure_raises_rag_parse_error():
    """T3-10: Pydanticバリデーション失敗時に RAGParseError が raise される"""
    invalid_response = {"objects": [{"obj_id": "x"}], "events": []}  # 必須フィールド欠け
    respx.post(settings.rag_api_url).mock(return_value=httpx.Response(200, json=invalid_response))
    with pytest.raises(RAGParseError):
        query("テスト質問")


# --- mock_query() ---

def test_T3_11_mock_query_returns_rag_response():
    """T3-11: 任意の文字列引数で RAGResponse インスタンスを返す"""
    result = mock_query("任意の質問")
    assert isinstance(result, RAGResponse)


def test_T3_12_mock_query_matches_mock_data():
    """T3-12: 返却内容が MOCK_RAG_RESPONSE と一致する"""
    result = mock_query("任意の質問")
    assert len(result.objects) == len(MOCK_RAG_RESPONSE["objects"])
    assert len(result.events) == len(MOCK_RAG_RESPONSE["events"])
    assert result.objects[0].obj_id == MOCK_RAG_RESPONSE["objects"][0]["obj_id"]
    assert result.events[0].event_id == MOCK_RAG_RESPONSE["events"][0]["event_id"]
