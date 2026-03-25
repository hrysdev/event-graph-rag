# T1: データモデル テスト

## 対象工程
D1: データモデル定義

## テスト対象ファイル
- `models/schema.py`

## 前提
- `models/schema.py` が実装済みであること。
- テストエージェントは `models/schema.py` を **読むが変更しない**。
  不備を発見した場合は本ファイル末尾の「フィードバック」セクションに記載すること。

## 事前準備
```
mkdir -p tests
touch tests/__init__.py
```
`pytest` と `pydantic` がインストール済みであること。

## テストケース一覧

### `VideoObject`
| テストID | 内容 |
|---|---|
| T1-01 | 必須フィールドがすべて揃っている正常データでインスタンスを生成できる |
| T1-02 | `attributes` に任意のキー/値を持てる（未知キーを受け入れる） |
| T1-03 | `obj_id` が欠けている場合に `ValidationError` が raise される |
| T1-04 | `first_seen_frame` に文字列を渡したとき、int に変換されるかエラーになる（どちらでも可、挙動を確認） |
| T1-04b | `first_seen_timestamp` に ISO 8601日時文字列（例: `"2024-01-15T10:23:45.100Z"`）を渡したとき正しく保持される |
| T1-04c | `first_seen_timestamp` が欠けている場合に `ValidationError` が raise される |

### `VideoEvent`
| テストID | 内容 |
|---|---|
| T1-05 | 必須フィールドのみで生成できる（source/destination は None） |
| T1-06 | `source` に文字列を渡したとき正しく保持される |
| T1-07 | `destination` が省略されたとき `None` になる |
| T1-08 | `frame` が欠けている場合に `ValidationError` が raise される |
| T1-08b | `timestamp` に ISO 8601日時文字列（例: `"2024-01-15T10:23:45.167Z"`）を渡したとき正しく保持される |
| T1-08c | `timestamp` が欠けている場合に `ValidationError` が raise される |

### `RAGResponse`
| テストID | 内容 |
|---|---|
| T1-09 | `requirements.md` § 4.3 のサンプルJSONをそのままパースできる |
| T1-10 | `objects` と `events` が空リストでも生成できる |
| T1-11 | `objects` に不正な要素（必須フィールド欠け）が含まれる場合に `ValidationError` が raise される |

### `ChatMessage`
| テストID | 内容 |
|---|---|
| T1-12 | role="user", content="test" で生成できる |
| T1-13 | role="assistant" で thinking と raw_rag を持てる |
| T1-14 | thinking と raw_rag は省略可能で、省略時は None になる |
| T1-15 | role に "user"/"assistant" 以外の値を渡したとき、ValidationError が raise される（Literal 型の場合）または通る（str 型の場合）ことを確認する |

## テストファイル

### `tests/test_models.py`

```python
import pytest
from pydantic import ValidationError
from models.schema import VideoObject, VideoEvent, RAGResponse, ChatMessage

SAMPLE_RAG_JSON = {
    "objects": [
        {
            "obj_id": "person_01", "category": "person", "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"pose": "standing", "orientation": "upright"}
        },
        {
            "obj_id": "cup_01", "category": "cup", "first_seen_frame": 3,
            "first_seen_timestamp": "2024-01-15T10:23:45.100Z",
            "attributes": {"color": "red", "material": "ceramic"}
        },
    ],
    "events": [
        {
            "event_id": "evt_001", "frame": 5, "timestamp": "2024-01-15T10:23:45.167Z",
            "action": "pick_up",
            "agent": "person_01", "target": "cup_01",
            "source": "table_01", "destination": None
        }
    ]
}

# 上記テストケース一覧に従い、各テストを実装すること。
```

## 実行コマンド
```bash
pytest tests/test_models.py -v
```

## 合格条件
- 全テストがパスすること。
- 実装の振る舞いと仕様の乖離があれば「フィードバック」セクションに記載すること。

---

## フィードバック（テストエージェントが記入）

全19テストがパス。不備なし。

- T1-04: `first_seen_frame` に文字列 `"5"` を渡した場合、pydantic v2 が int に自動変換する（coerce）動作を確認。
- T1-15: `role` は `Literal["user", "assistant"]` 型で定義されており、`"system"` 等の不正値では `ValidationError` が raise されることを確認。
