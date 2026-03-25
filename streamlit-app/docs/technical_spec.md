# ビデオイベント・チャット アプリケーション 技術仕様書 (v1.0)

## 1. ディレクトリ構成

```
optiBot/
├── app.py                    # Streamlitエントリポイント
├── config.py                 # 設定値の一元管理
├── requirements.txt
├── .env                      # 環境変数（APIエンドポイント等）
├── core/
│   ├── __init__.py
│   ├── rag_client.py         # RAGサーバーAPIクライアント
│   ├── llm_client.py         # vLLM (OpenAI互換API) クライアント
│   ├── chain.py              # LangChainオーケストレーション
│   └── prompt.py             # プロンプトテンプレート定義
├── models/
│   ├── __init__.py
│   └── schema.py             # Pydanticデータモデル
├── ui/
│   ├── __init__.py
│   ├── chat.py               # チャット画面コンポーネント
│   └── sidebar.py            # サイドバーコンポーネント
└── docs/
    ├── requirements.md
    └── technical_spec.md
```

---

## 2. 設定管理 (`config.py`)

環境変数ファイル (`.env`) から読み込む。`python-dotenv` を使用。

| 変数名 | 説明 | デフォルト値 |
|---|---|---|
| `VLLM_BASE_URL` | vLLMサーバーのベースURL | `http://localhost:8000/v1` |
| `VLLM_MODEL_NAME` | モデル識別子 | `qwen3.5-plus` |
| `RAG_API_URL` | RAGサーバーのエンドポイントURL | `http://localhost:9000/query` |
| `RAG_API_TIMEOUT` | RAG APIタイムアウト秒数 | `30` |
| `LLM_TEMPERATURE` | LLM生成温度 | `0.6` |
| `LLM_MAX_TOKENS` | 最大生成トークン数 | `4096` |
| `ENABLE_THINKING` | Thinkingモードデフォルト有効/無効 | `true` |

---

## 3. データモデル (`models/schema.py`)

Pydanticを用いてRAGレスポンスを型安全に扱う。

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ObjectAttributes(BaseModel):
    color: Optional[str] = None
    material: Optional[str] = None
    position: Optional[str] = None
    size: Optional[str] = None
    state: Optional[str] = None
    pose: Optional[str] = None
    orientation: Optional[str] = None
    # 未知の属性を許容するため model_config で extra="allow" を設定

class VideoObject(BaseModel):
    obj_id: str
    category: str
    first_seen_frame: int
    first_seen_timestamp: str          # ISO 8601日時形式 例: "2024-01-15T10:23:45.100Z"
    attributes: Dict[str, Any]

class VideoEvent(BaseModel):
    event_id: str
    frame: int
    timestamp: str                     # ISO 8601日時形式 例: "2024-01-15T10:23:45.167Z"
    action: str
    agent: str
    target: str
    source: Optional[str] = None
    destination: Optional[str] = None

class RAGResponse(BaseModel):
    objects: List[VideoObject]
    events: List[VideoEvent]

class ChatMessage(BaseModel):
    role: str           # "user" | "assistant"
    content: str
    thinking: Optional[str] = None   # Thinkingタグ内テキスト
    raw_rag: Optional[RAGResponse] = None
```

---

## 4. RAGクライアント (`core/rag_client.py`)

- HTTPクライアント: `httpx` (非同期対応可能)
- ユーザーの質問文字列をクエリとしてRAGサーバーに送信し、`RAGResponse` を返す。
- レスポンスのバリデーションは Pydantic で行う。

```python
# インターフェース
def query(user_question: str) -> RAGResponse:
    """
    POST {RAG_API_URL}
    Body: {"query": user_question}
    Returns: RAGResponse (Pydantic model)
    """
```

**エラーハンドリング:**
- タイムアウト → `RAGTimeoutError` を raise
- HTTP 4xx/5xx → `RAGAPIError` を raise (ステータスコードとメッセージを保持)
- バリデーション失敗 → `RAGParseError` を raise (生レスポンスを保持)

---

## 5. プロンプト設計 (`core/prompt.py`)

### 5.1 RAGデータの自然言語変換

`RAGResponse` → LLMが理解しやすいテキストブロックに変換する。

**オブジェクトセクション:**
```
[登場オブジェクト]
- person_01 (person): 初登場フレーム=0 (2024-01-15T10:23:45.000Z), pose=standing, orientation=upright
- cup_01 (cup): 初登場フレーム=3 (2024-01-15T10:23:45.100Z), color=red, material=ceramic, position=on_desk, size=small, state=filled
- table_01 (table): 初登場フレーム=0 (2024-01-15T10:23:45.000Z), material=wooden, size=large
```

**イベントセクション:**
```
[イベントログ (時系列順)]
- Frame 5 (2024-01-15T10:23:45.167Z) [evt_001]: person_01 が cup_01 を table_01 から (不明) へ pick_up した。
- Frame 10 (2024-01-15T10:23:45.333Z) [evt_002]: person_01 が cup_01 を (不明) から shelf_01 へ place_on した。
```

### 5.2 システムプロンプト

```
あなたは動画解析アシスタントです。
提供された「登場オブジェクト」と「イベントログ」に基づいて、
ユーザーの質問に正確かつ論理的に回答してください。

ルール:
- 与えられたデータにない情報を推測・捏造しないこと。
- 因果関係の推論は、イベントの時系列を根拠として示すこと。
- 回答は日本語で行うこと。
```

### 5.3 プロンプト構造 (LangChain `ChatPromptTemplate`)

```
SystemMessage: [システムプロンプト]
HumanMessage(1): [コンテキスト: オブジェクト + イベント]\n[ユーザー質問1]
AIMessage(1): [回答1]
...
HumanMessage(N): [コンテキスト: オブジェクト + イベント]\n[ユーザー質問N]
```

> 毎ターン、最新のRAG取得コンテキストをHumanMessageの先頭に付与する。
> 会話履歴は `st.session_state["messages"]` から取得し、最大直近 **10ターン** までコンテキストに含める（トークン節約）。

---

## 6. LangChainチェーン (`core/chain.py`)

```
ユーザー入力
    ↓
RAGClient.query()           # 1. RAGサーバーへクエリ
    ↓
prompt.build_context()      # 2. JSONを自然言語テキストに変換
    ↓
ChatPromptTemplate          # 3. 会話履歴 + コンテキスト + 質問を結合
    ↓
LLM (vLLM OpenAI互換)       # 4. ストリーミング推論
    ↓
ThinkingParser              # 5. <think>...</think> タグをパース・分離
    ↓
(thinking_text, answer_text, raw_rag)  # 6. UI層へ返却
```

### 6.1 ストリーミング

`openai` Python SDK の `stream=True` を利用し、Streamlitの `st.write_stream()` でリアルタイム表示。

### 6.2 Thinkingパーサー

vLLMから返却される全テキストを対象に正規表現でパース。

```python
import re

THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)

def parse_thinking(raw_text: str) -> tuple[str, str]:
    """
    Returns: (thinking_text, answer_text)
    - thinking_text: <think>タグ内のテキスト（存在しない場合は空文字）
    - answer_text: <think>タグを除去した残りのテキスト
    """
    match = THINK_PATTERN.search(raw_text)
    thinking = match.group(1).strip() if match else ""
    answer = THINK_PATTERN.sub("", raw_text).strip()
    return thinking, answer
```

---

## 7. UI仕様 (`app.py`, `ui/`)

### 7.1 セッションステート

`st.session_state` に以下のキーを保持する。

| キー | 型 | 説明 |
|---|---|---|
| `messages` | `List[ChatMessage]` | 会話履歴 |
| `show_thinking` | `bool` | Thinkingの表示/非表示フラグ |
| `last_rag_raw` | `Optional[RAGResponse]` | 直近のRAG取得JSONデータ |

### 7.2 チャット画面 (`ui/chat.py`)

1. 過去の `messages` をループしてバブル表示。
2. `show_thinking=True` かつ `message.thinking` が存在する場合、`st.expander("思考プロセス (Thinking)")` 内に表示。
3. ユーザー入力は `st.chat_input()` を使用。
4. LLM応答は `st.write_stream()` でストリーミング表示。

### 7.3 サイドバー (`ui/sidebar.py`)

```
[サイドバー]
- Thinkingの表示: [トグルスイッチ]
- 会話をリセット: [ボタン]
---
[直近のRAG取得データ]
  [JSONをst.json()で展開表示]
```

### 7.4 エラー表示

- RAGエラー / LLMエラー発生時は `st.error()` で画面上部に表示。
- エラー詳細はサイドバーの "詳細" エクスパンダー内に展開表示。

---

## 8. 主要ライブラリ

| ライブラリ | 用途 |
|---|---|
| `streamlit` | フロントエンドUI |
| `langchain` / `langchain-openai` | プロンプト管理・チェーン構築 |
| `openai` | vLLM (OpenAI互換API) への接続 |
| `httpx` | RAGサーバーへのHTTPリクエスト |
| `pydantic` | データバリデーション・スキーマ定義 |
| `python-dotenv` | 環境変数読み込み |

---

## 9. 実装順序

1. `models/schema.py` — データモデル定義
2. `config.py` + `.env` — 設定管理
3. `core/rag_client.py` — RAGクライアント (モックで単体テスト可能)
4. `core/prompt.py` — データ→テキスト変換 + プロンプトテンプレート
5. `core/llm_client.py` — vLLM接続確認
6. `core/chain.py` — チェーン統合 + Thinkingパーサー
7. `ui/sidebar.py` / `ui/chat.py` — UIコンポーネント
8. `app.py` — エントリポイント統合・結合テスト
