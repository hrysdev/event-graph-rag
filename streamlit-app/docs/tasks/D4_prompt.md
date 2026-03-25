# D4: プロンプト設計

## 参照ドキュメント
- `docs/requirements.md` § 5 (ロジック・プロンプト設計)
- `docs/technical_spec.md` § 5 (プロンプト設計)
- `models/schema.py` (RAGResponse, VideoObject, VideoEvent)

## 作業概要
`RAGResponse` を自然言語テキストに変換する関数と、
LangChain の `ChatPromptTemplate` を `core/prompt.py` に実装する。

## 実装仕様

### ファイル: `core/prompt.py`

#### 1. データ変換関数

```python
def format_objects(objects: list[VideoObject]) -> str:
    """
    VideoObjectのリストを以下の形式のテキストに変換する。

    出力例:
    [登場オブジェクト]
    - person_01 (person): 初登場フレーム=0 (2024-01-15T10:23:45.000Z), pose=standing, orientation=upright
    - cup_01 (cup): 初登場フレーム=3 (2024-01-15T10:23:45.100Z), color=red, material=ceramic, position=on_desk, size=small, state=filled
    - table_01 (table): 初登場フレーム=0 (2024-01-15T10:23:45.000Z), material=wooden, size=large

    ルール:
    - attributes が空の場合は属性部分を省略する。
    - objects が空リストの場合は "[登場オブジェクト]\n(なし)" を返す。
    """
```

```python
def format_events(events: list[VideoEvent]) -> str:
    """
    VideoEventのリストを以下の形式のテキストに変換する。

    出力例:
    [イベントログ (時系列順)]
    - Frame 5 (2024-01-15T10:23:45.167Z) [evt_001]: person_01 が cup_01 を table_01 から (不明) へ pick_up した。
    - Frame 10 (2024-01-15T10:23:45.333Z) [evt_002]: person_01 が cup_01 を (不明) から shelf_01 へ place_on した。

    ルール:
    - source/destination が None の場合は "(不明)" と表示する。
    - frame の昇順でソートして出力する。
    - events が空リストの場合は "[イベントログ (時系列順)]\n(なし)" を返す。
    """
```

```python
def build_context(rag_response: RAGResponse) -> str:
    """
    format_objects と format_events を結合してコンテキストブロックを返す。

    出力形式:
    {format_objects の出力}

    {format_events の出力}
    """
```

#### 2. システムプロンプト定数

```python
SYSTEM_PROMPT: str = """\
あなたは動画解析アシスタントです。
提供された「登場オブジェクト」と「イベントログ」に基づいて、
ユーザーの質問に正確かつ論理的に回答してください。

ルール:
- 与えられたデータにない情報を推測・捏造しないこと。
- 因果関係の推論は、イベントの時系列を根拠として示すこと。
- 回答は日本語で行うこと。\
"""
```

#### 3. プロンプトビルダー

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

def build_messages(
    rag_response: RAGResponse,
    user_question: str,
    history: list[tuple[str, str]],  # [(human_text, ai_text), ...]
) -> list:
    """
    LangChainのメッセージリストを構築して返す。

    構造:
      SystemMessage(SYSTEM_PROMPT)
      HumanMessage(history[0][0])  ← 過去ターン
      AIMessage(history[0][1])
      ...
      HumanMessage(context + "\n\n" + user_question)  ← 今回

    history は最大10ターンまでを使用する（古いものから切り捨て）。
    context = build_context(rag_response)
    """
```

## 実装上の注意
- `format_events` はフレーム番号の昇順でソートすること。
- `history` が空リストでも正常動作すること。
- LangChain のバージョンは `langchain>=0.3` を前提とする (`langchain_core` を使用)。

## 完了条件
- `python -c "from core.prompt import build_context, build_messages"` がエラーなく通る。
- `mock_query` のレスポンスを `build_context` に渡したとき、オブジェクト3件・イベント2件が出力テキストに含まれる。
