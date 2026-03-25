# D3: RAGクライアント

## 参照ドキュメント
- `docs/requirements.md` § 4 (データインターフェース仕様)
- `docs/technical_spec.md` § 4 (RAGクライアント)
- `models/schema.py` (RAGResponse)
- `config.py` (RAG_API_URL, RAG_API_TIMEOUT)

## 作業概要
RAGサーバーへHTTPリクエストを投げ、レスポンスを `RAGResponse` に変換して返す
クライアントを `core/rag_client.py` に実装する。

## 事前準備
```
mkdir -p core
touch core/__init__.py
```

## 実装仕様

### ファイル: `core/rag_client.py`

#### 例外クラス

```python
class RAGTimeoutError(Exception):
    """RAGサーバーへのリクエストがタイムアウトした"""

class RAGAPIError(Exception):
    """RAGサーバーが 4xx/5xx を返した"""
    def __init__(self, status_code: int, message: str): ...

class RAGParseError(Exception):
    """レスポンスのJSONパースまたはPydanticバリデーションが失敗した"""
    def __init__(self, raw_response: str): ...
```

#### メイン関数

```python
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
```

#### HTTPクライアント

`httpx` を使用する（同期版 `httpx.Client`）。
タイムアウトは `settings.rag_api_timeout` を使用する。

#### モックフィクスチャ

開発・テスト用に、実サーバーなしで動作確認できるモックデータを定数として定義する。

```python
MOCK_RAG_RESPONSE: dict = {
    "objects": [
        {
            "obj_id": "person_01",
            "category": "person",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"pose": "standing", "orientation": "upright"}
        },
        {
            "obj_id": "cup_01",
            "category": "cup",
            "first_seen_frame": 3,
            "first_seen_timestamp": "2024-01-15T10:23:45.100Z",
            "attributes": {
                "color": "red", "material": "ceramic",
                "position": "on_desk", "size": "small", "state": "filled"
            }
        },
        {
            "obj_id": "table_01",
            "category": "table",
            "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"material": "wooden", "size": "large"}
        }
    ],
    "events": [
        {
            "event_id": "evt_001", "frame": 5, "timestamp": "2024-01-15T10:23:45.167Z",
            "action": "pick_up",
            "agent": "person_01", "target": "cup_01",
            "source": "table_01", "destination": None
        },
        {
            "event_id": "evt_002", "frame": 10, "timestamp": "2024-01-15T10:23:45.333Z",
            "action": "place_on",
            "agent": "person_01", "target": "cup_01",
            "source": None, "destination": "shelf_01"
        }
    ]
}

def mock_query(user_question: str) -> RAGResponse:
    """テスト用: 常に MOCK_RAG_RESPONSE を返す"""
    return RAGResponse(**MOCK_RAG_RESPONSE)
```

## 完了条件
- `python -c "from core.rag_client import query, mock_query, RAGTimeoutError, RAGAPIError, RAGParseError"` がエラーなく通る。
- `mock_query("テスト")` が `RAGResponse` インスタンスを返す。
