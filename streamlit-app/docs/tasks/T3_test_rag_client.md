# T3: RAGクライアント テスト

## 対象工程
D3: RAGクライアント

## テスト対象ファイル
- `core/rag_client.py`

## 前提
- `core/rag_client.py`、`models/schema.py`、`config.py` が実装済みであること。
- テストエージェントは対象ファイルを **読むが変更しない**。
- 実RAGサーバーへの接続は不要。`respx` または `unittest.mock` でHTTPをモック化する。

## テストケース一覧

### `query()` 正常系
| テストID | 内容 |
|---|---|
| T3-01 | RAGサーバーが200を返したとき、`RAGResponse` インスタンスが返る |
| T3-02 | 返ってきた `RAGResponse` の `objects` と `events` の件数が正しい |
| T3-03 | リクエストボディに `{"query": user_question}` が含まれている |
| T3-04 | リクエストのURLが `settings.rag_api_url` と一致する |

### `query()` エラー系
| テストID | 内容 |
|---|---|
| T3-05 | タイムアウト発生時に `RAGTimeoutError` が raise される |
| T3-06 | HTTP 404 返却時に `RAGAPIError` が raise される |
| T3-07 | HTTP 500 返却時に `RAGAPIError` が raise される |
| T3-08 | `RAGAPIError` が `status_code` 属性を持つ |
| T3-09 | 不正なJSONが返ってきたとき `RAGParseError` が raise される |
| T3-10 | Pydanticバリデーション失敗（必須フィールド欠け）時に `RAGParseError` が raise される |

### `mock_query()`
| テストID | 内容 |
|---|---|
| T3-11 | 任意の文字列引数で `RAGResponse` インスタンスを返す |
| T3-12 | 返却される `RAGResponse` が `MOCK_RAG_RESPONSE` の内容と一致する |

## テストファイル

### `tests/test_rag_client.py`

```python
import pytest
import httpx
import respx  # pip install respx
from core.rag_client import query, mock_query, RAGTimeoutError, RAGAPIError, RAGParseError
from models.schema import RAGResponse

VALID_RESPONSE = {
    "objects": [
        {
            "obj_id": "person_01", "category": "person",
            "first_seen_frame": 0, "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {}
        }
    ],
    "events": [
        {
            "event_id": "evt_001", "frame": 1, "timestamp": "2024-01-15T10:23:45.033Z",
            "action": "stand",
            "agent": "person_01", "target": "person_01",
            "source": None, "destination": None
        }
    ]
}

@respx.mock
def test_query_success():
    respx.post(...).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))
    result = query("テスト質問")
    assert isinstance(result, RAGResponse)
    assert len(result.objects) == 1

# 上記テストケース一覧に従い実装すること。
# respx が利用不可の場合は unittest.mock.patch("httpx.Client.post") で代替する。
```

## 実行コマンド
```bash
pytest tests/test_rag_client.py -v
```

## 合格条件
- 全テストがパスすること。
- 実RAGサーバーへの接続なしで実行できること。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
