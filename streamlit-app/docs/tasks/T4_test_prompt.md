# T4: プロンプト設計 テスト

## 対象工程
D4: プロンプト設計

## テスト対象ファイル
- `core/prompt.py`

## 前提
- `core/prompt.py` と `models/schema.py` が実装済みであること。
- テストエージェントは対象ファイルを **読むが変更しない**。
- 外部サーバーへの接続は不要。

## テストケース一覧

### `format_objects()`
| テストID | 内容 |
|---|---|
| T4-01 | 複数の `VideoObject` を渡したとき、各オブジェクトが1行で出力される |
| T4-02 | 出力の先頭行が `[登場オブジェクト]` である |
| T4-03 | obj_id・category・first_seen_frame・attributes のキーと値が出力に含まれる |
| T4-03b | `first_seen_timestamp` の値（ISO 8601日時形式文字列）が出力に含まれる |
| T4-04 | `attributes` が空辞書のとき、属性部分が省略される（またはエラーにならない） |
| T4-05 | `objects` が空リストのとき `"(なし)"` が出力に含まれる |

### `format_events()`
| テストID | 内容 |
|---|---|
| T4-06 | 複数の `VideoEvent` を渡したとき、各イベントが1行で出力される |
| T4-07 | 出力の先頭行が `[イベントログ (時系列順)]` を含む |
| T4-08 | `source` が `None` のとき `"(不明)"` が出力に含まれる |
| T4-09 | `destination` が `None` のとき `"(不明)"` が出力に含まれる |
| T4-09b | `timestamp` の値（ISO 8601日時形式文字列）が出力に含まれる |
| T4-10 | フレーム番号の降順に渡した場合でも、出力は昇順にソートされる |
| T4-11 | `events` が空リストのとき `"(なし)"` が出力に含まれる |

### `build_context()`
| テストID | 内容 |
|---|---|
| T4-12 | `RAGResponse` を渡したとき、`[登場オブジェクト]` と `[イベントログ` の両セクションが出力に含まれる |
| T4-13 | `requirements.md` § 4.3 のサンプルデータで呼び出したとき、3件のオブジェクトと2件のイベントが含まれる |

### `build_messages()`
| テストID | 内容 |
|---|---|
| T4-14 | 返却リストの先頭が SystemMessage である |
| T4-15 | history が空のとき、メッセージは SystemMessage + HumanMessage の2要素 |
| T4-16 | history が2ターンのとき、SystemMessage + HumanMessage + AIMessage + HumanMessage + AIMessage + HumanMessage の6要素 |
| T4-17 | 最後の HumanMessage のコンテキスト部分にオブジェクト名が含まれる |
| T4-18 | history が10ターンを超えるとき、古いターンが切り捨てられ最大20要素（10ターン分）以内に収まる |

## テストファイル

### `tests/test_prompt.py`

```python
import pytest
from models.schema import VideoObject, VideoEvent, RAGResponse
from core.prompt import format_objects, format_events, build_context, build_messages

# 共通フィクスチャ
@pytest.fixture
def sample_objects():
    return [
        VideoObject(obj_id="cup_01", category="cup", first_seen_frame=3,
                    first_seen_timestamp="2024-01-15T10:23:45.100Z",
                    attributes={"color": "red", "material": "ceramic"}),
        VideoObject(obj_id="table_01", category="table", first_seen_frame=0,
                    first_seen_timestamp="2024-01-15T10:23:45.000Z",
                    attributes={}),
    ]

@pytest.fixture
def sample_events():
    return [
        VideoEvent(event_id="evt_002", frame=10, timestamp="2024-01-15T10:23:45.333Z",
                   action="place_on",
                   agent="person_01", target="cup_01",
                   source=None, destination="shelf_01"),
        VideoEvent(event_id="evt_001", frame=5, timestamp="2024-01-15T10:23:45.167Z",
                   action="pick_up",
                   agent="person_01", target="cup_01",
                   source="table_01", destination=None),
    ]

# 上記テストケース一覧に従い実装すること。
```

## 実行コマンド
```bash
pytest tests/test_prompt.py -v
```

## 合格条件
- 全テストがパスすること。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
