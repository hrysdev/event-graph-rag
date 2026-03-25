# D1: データモデル定義

## 参照ドキュメント
- `docs/requirements.md` § 4 (データインターフェース仕様)
- `docs/technical_spec.md` § 3 (データモデル)

## 作業概要
`models/schema.py` にPydanticモデルを定義する。
このファイルは後続の全工程が import する基盤となるため、破壊的変更を避けること。

## 事前準備
```
mkdir -p models
touch models/__init__.py
```

## 実装仕様

### ファイル: `models/schema.py`

以下のクラスをすべて定義すること。

#### `VideoObject`
```
フィールド:
  obj_id               : str
  category             : str
  first_seen_frame     : int
  first_seen_timestamp : str          # ISO 8601日時形式 例: "2024-01-15T10:23:45.100Z"
  attributes           : Dict[str, Any]   # 未知キーを許容
```

#### `VideoEvent`
```
フィールド:
  event_id   : str
  frame      : int
  timestamp  : str                    # ISO 8601日時形式 例: "2024-01-15T10:23:45.167Z"
  action     : str
  agent      : str
  target     : str
  source     : Optional[str] = None
  destination: Optional[str] = None
```

#### `RAGResponse`
```
フィールド:
  objects: List[VideoObject]
  events : List[VideoEvent]
```

#### `ChatMessage`
```
フィールド:
  role      : str                       # "user" | "assistant"
  content   : str
  thinking  : Optional[str] = None      # <think>タグ内テキスト
  raw_rag   : Optional[RAGResponse] = None
```

## 実装上の注意
- Pydantic v2 (`pydantic>=2.0`) を使用する。
- `VideoObject.attributes` は未知キーを許容するため `Dict[str, Any]` とし、
  モデル設定で `extra="allow"` は不要（`attributes` 自体が Any を受ける）。
- `ChatMessage.role` は `Literal["user", "assistant"]` に制限してよい。
- `models/__init__.py` から全クラスを re-export すること。

## 完了条件
- `python -c "from models.schema import VideoObject, VideoEvent, RAGResponse, ChatMessage"` がエラーなく通る。
- `requirements.md` § 4.3 のサンプルJSON（`first_seen_timestamp` / `timestamp` フィールドを含む）を `RAGResponse(**sample)` でパースできる。
