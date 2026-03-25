# D5: LLMクライアント

## 参照ドキュメント
- `docs/technical_spec.md` § 5 (LangChainチェーン), § 2 (設定管理)
- `config.py` (VLLM_BASE_URL, VLLM_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS)

## 作業概要
`openai` SDK を使って vLLM の OpenAI互換エンドポイントに接続する薄いラッパーを
`core/llm_client.py` に実装する。

## 実装仕様

### ファイル: `core/llm_client.py`

#### クライアント初期化

```python
from openai import OpenAI

def get_client() -> OpenAI:
    """
    設定値を使って OpenAI クライアントを生成して返す。
    base_url = settings.vllm_base_url
    api_key  = "dummy"  # vLLM はAPIキー不要だが SDK の必須引数のため固定値を渡す
    """
```

#### ストリーミング推論

```python
from collections.abc import Iterator

def stream_chat(messages: list[dict]) -> Iterator[str]:
    """
    メッセージリストを受け取り、LLMのストリーミング応答をトークン単位で yield する。

    引数:
      messages: OpenAI形式のメッセージリスト
                [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, ...]

    yield:
      各チャンクのテキスト断片 (str)。空文字列のチャンクはスキップする。

    使用するパラメータ:
      model       = settings.vllm_model_name
      temperature = settings.llm_temperature
      max_tokens  = settings.llm_max_tokens
      stream      = True
    """
```

#### LangChainメッセージ変換ユーティリティ

```python
from langchain_core.messages import BaseMessage

def langchain_messages_to_openai(messages: list[BaseMessage]) -> list[dict]:
    """
    LangChain の BaseMessage リストを OpenAI API 形式の dict リストに変換する。

    対応するロール:
      SystemMessage  → "system"
      HumanMessage   → "user"
      AIMessage      → "assistant"
    """
```

## 実装上の注意
- `get_client()` は毎回新しいインスタンスを返す設計でよい（ステートレス）。
- `stream_chat` 内でのエラー（接続失敗等）は wrap せず、そのまま raise させる。
  エラーハンドリングは呼び出し元 (chain.py) の責務とする。
- vLLM サーバーが動作していなくても import だけはエラーなく通ること。

## 完了条件
- `python -c "from core.llm_client import get_client, stream_chat, langchain_messages_to_openai"` がエラーなく通る。
- `langchain_messages_to_openai` に SystemMessage・HumanMessage・AIMessage を渡したとき、
  対応するロール文字列に変換されて返る。
