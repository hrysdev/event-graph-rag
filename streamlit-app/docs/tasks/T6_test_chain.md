# T6: LangChainチェーン テスト

## 対象工程
D6: LangChainチェーン

## テスト対象ファイル
- `core/chain.py`

## 前提
- `core/chain.py`、`core/rag_client.py`、`core/prompt.py`、`core/llm_client.py`、
  `models/schema.py` が実装済みであること。
- テストエージェントは対象ファイルを **読むが変更しない**。
- RAGクライアントと LLM クライアントは `unittest.mock` でモック化する。
- 実サーバーへの接続は不要。

## テストケース一覧

### `parse_thinking()`
| テストID | 内容 |
|---|---|
| T6-01 | `<think>思考内容</think>回答` → `("思考内容", "回答")` |
| T6-02 | `タグなし回答` → `("", "タグなし回答")` |
| T6-03 | `<think>思考</think>` のみ（回答テキストなし）→ `("思考", "")` |
| T6-04 | `<think>` タグが閉じていない → `("", 元のテキスト全体)` |
| T6-05 | 複数の `<think>` タグが存在するとき、すべてのタグが除去され answer_text に含まれない |
| T6-06 | `<think>` タグの前後に空白や改行があっても、正しく分離される |
| T6-07 | タグ内が空 `<think></think>` → `("", answer_text)` |

### `run_collecting()`
| テストID | 内容 |
|---|---|
| T6-08 | RAGクライアントと LLM をモック化したとき、`(thinking_text, answer_text, rag_response)` のタプルが返る |
| T6-09 | `on_chunk` コールバックが各チャンクに対して呼ばれる |
| T6-10 | `on_chunk=None` のとき、エラーなく実行される |
| T6-11 | RAGクライアントが `RAGTimeoutError` を raise したとき、`run_collecting` もそれを伝播させる |
| T6-12 | LLMが例外を raise したとき、`run_collecting` もそれを伝播させる |
| T6-13 | `history` が空リストのとき正常に実行される |
| T6-14 | チャンクが累積されて `answer_text` として返る（部分テキストが結合される） |

## テストファイル

### `tests/test_chain.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from core.chain import parse_thinking, run_collecting
from core.rag_client import RAGTimeoutError, MOCK_RAG_RESPONSE
from models.schema import RAGResponse

# parse_thinking のテスト（モック不要）
def test_parse_thinking_with_tag():
    thinking, answer = parse_thinking("<think>思考内容</think>回答")
    assert thinking == "思考内容"
    assert answer == "回答"

def test_parse_thinking_without_tag():
    thinking, answer = parse_thinking("タグなし回答")
    assert thinking == ""
    assert answer == "タグなし回答"

# run_collecting のテスト
@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_success(mock_stream, mock_query):
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    mock_stream.return_value = iter(["<think>思考</think>", "回答テキスト"])

    thinking, answer, rag = run_collecting("質問", history=[])
    assert thinking == "思考"
    assert "回答テキスト" in answer
    assert isinstance(rag, RAGResponse)

# 上記テストケース一覧に従い実装すること。
```

## 実行コマンド
```bash
pytest tests/test_chain.py -v
```

## 合格条件
- 全テストがパスすること。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
