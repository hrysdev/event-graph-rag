# D6: LangChainチェーン

## 参照ドキュメント
- `docs/technical_spec.md` § 6 (LangChainチェーン)
- `core/rag_client.py` (query, RAGResponse)
- `core/prompt.py` (build_context, build_messages)
- `core/llm_client.py` (stream_chat, langchain_messages_to_openai)
- `models/schema.py` (ChatMessage, RAGResponse)

## 作業概要
RAGクエリ → プロンプト構築 → LLM推論 → Thinkingパースを一連のフローとして
`core/chain.py` に実装する。

## 実装仕様

### ファイル: `core/chain.py`

#### Thinkingパーサー

```python
import re

THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)

def parse_thinking(raw_text: str) -> tuple[str, str]:
    """
    LLMの生出力から <think> タグを分離する。

    Returns:
      (thinking_text, answer_text)
      - thinking_text: <think>...</think> の内側テキスト（タグが存在しない場合は空文字列）
      - answer_text  : <think>タグ全体を除去した残りテキスト（前後の空白をstrip）

    考慮するケース:
      - <think> タグが存在しない場合
      - <think> タグが複数存在する場合（最初の1つのみを thinking_text として扱い、残りも除去する）
      - <think> タグが閉じていない場合（パターンにマッチしないため thinking_text は空文字列）
    """
```

#### チェーン実行関数（非ストリーミング）

```python
from collections.abc import Generator

def run(
    user_question: str,
    history: list[tuple[str, str]],
) -> Generator[str, None, tuple[str, str, RAGResponse]]:
    """
    チェーン全体を実行し、LLMの応答テキストをトークン単位で yield する。
    最終的に (thinking_text, answer_text, rag_response) を return する。

    フロー:
      1. rag_client.query(user_question) でRAGレスポンスを取得
      2. prompt.build_messages(rag_response, user_question, history) でメッセージを構築
      3. llm_client.langchain_messages_to_openai(messages) で変換
      4. llm_client.stream_chat(openai_messages) でストリーミング推論
      5. 全チャンクを yield しながら累積して raw_text を構築
      6. parse_thinking(raw_text) で (thinking_text, answer_text) に分離
      7. return (thinking_text, answer_text, rag_response)

    Note:
      Generator の return 値は StopIteration.value として取得できる。
      UI 層では for chunk in gen: ... で yield を消費し、
      最終値は next() の StopIteration をキャッチして取得するか、
      以下のヘルパー関数 run_collecting を使う。
    """
```

#### 結果収集ヘルパー

```python
def run_collecting(
    user_question: str,
    history: list[tuple[str, str]],
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[str, str, RAGResponse]:
    """
    run() を実行し、各チャンクを on_chunk コールバックに渡しながら
    最終的な (thinking_text, answer_text, rag_response) を返す。

    on_chunk が None の場合はコールバックを呼ばない。
    Streamlit の st.write_stream 互換のラッパーとして使用される。
    """
```

## 実装上の注意
- RAGクライアントのエラー（`RAGTimeoutError` 等）は chain.py では catch せず、
  呼び出し元（UI層）に伝播させる。
- LLMの接続エラーも同様に伝播させる。
- `history` は最大10ターン分を `build_messages` に渡す（超過分は古いものから切り捨て）。
  切り捨て処理は `build_messages` 側で行うため、chain.py では渡すだけでよい。

## 完了条件
- `python -c "from core.chain import run, run_collecting, parse_thinking"` がエラーなく通る。
- `parse_thinking("<think>思考</think>回答")` が `("思考", "回答")` を返す。
- `parse_thinking("タグなし回答")` が `("", "タグなし回答")` を返す。
