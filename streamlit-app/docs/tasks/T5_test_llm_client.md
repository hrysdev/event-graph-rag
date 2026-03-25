# T5: LLMクライアント テスト

## 対象工程
D5: LLMクライアント

## テスト対象ファイル
- `core/llm_client.py`

## 前提
- `core/llm_client.py` と `config.py` が実装済みであること。
- テストエージェントは対象ファイルを **読むが変更しない**。
- 実 vLLM サーバーへの接続は不要。`unittest.mock` で `openai.OpenAI` をモック化する。

## テストケース一覧

### `get_client()`
| テストID | 内容 |
|---|---|
| T5-01 | `OpenAI` インスタンスが返る |
| T5-02 | `base_url` が `settings.vllm_base_url` と一致する |

### `stream_chat()`
| テストID | 内容 |
|---|---|
| T5-03 | ストリーミング応答のチャンクが順に yield される |
| T5-04 | 空文字列のチャンクはスキップされる（yield されない） |
| T5-05 | `model` 引数に `settings.vllm_model_name` が使われる |
| T5-06 | `stream=True` が API に渡される |
| T5-07 | `temperature` に `settings.llm_temperature` が使われる |
| T5-08 | `max_tokens` に `settings.llm_max_tokens` が使われる |

### `langchain_messages_to_openai()`
| テストID | 内容 |
|---|---|
| T5-09 | `SystemMessage` が `{"role": "system", "content": "..."}` に変換される |
| T5-10 | `HumanMessage` が `{"role": "user", "content": "..."}` に変換される |
| T5-11 | `AIMessage` が `{"role": "assistant", "content": "..."}` に変換される |
| T5-12 | 混在したメッセージリストが順序を保って変換される |
| T5-13 | 空リストを渡したとき空リストが返る |

## テストファイル

### `tests/test_llm_client.py`

```python
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.llm_client import get_client, stream_chat, langchain_messages_to_openai

def make_mock_chunk(text: str):
    """openai ストリーミングチャンクのモックを作成する"""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = text
    return chunk

@patch("core.llm_client.get_client")
def test_stream_chat_yields_chunks(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        make_mock_chunk("Hello"),
        make_mock_chunk(""),      # 空チャンク（スキップされるはず）
        make_mock_chunk(" World"),
    ])
    messages = [{"role": "user", "content": "hi"}]
    chunks = list(stream_chat(messages))
    assert chunks == ["Hello", " World"]  # 空チャンクは含まれない

# 上記テストケース一覧に従い実装すること。
```

## 実行コマンド
```bash
pytest tests/test_llm_client.py -v
```

## 合格条件
- 全テストがパスすること。
- 実 vLLM サーバーへの接続なしで実行できること。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
