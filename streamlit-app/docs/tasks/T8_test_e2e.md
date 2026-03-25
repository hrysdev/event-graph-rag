# T8: E2E統合テスト

## 対象工程
D8: エントリポイント統合

## テスト対象ファイル
- `app.py`（全体フロー）

## 前提
- `app.py` および全モジュールが実装済みであること。
- テストエージェントは `app.py` を **読むが変更しない**。
- `core.chain.run_collecting` を `unittest.mock` でモック化し、
  実RAGサーバー・LLMサーバーへの接続なしで実行する。
- `streamlit.testing.v1.AppTest` を使用する。

## モック設定

```python
from unittest.mock import patch
from core.rag_client import MOCK_RAG_RESPONSE
from models.schema import RAGResponse

MOCK_THINKING = "これは思考プロセスです。"
MOCK_ANSWER = "カップは棚の上に移動されました。"
MOCK_RAG = RAGResponse(**MOCK_RAG_RESPONSE)

# run_collecting のモック戻り値
MOCK_RETURN = (MOCK_THINKING, MOCK_ANSWER, MOCK_RAG)
```

## テスト用アプリ設定

`app.py` を直接 `AppTest.from_file("app.py")` でロードする。

## テストケース一覧

### アプリ起動
| テストID | 内容 |
|---|---|
| T8-01 | `app.py` が例外なく起動する |
| T8-02 | 初期状態で `messages` が空である |
| T8-03 | チャット入力フォームが存在する |

### チャットフロー（正常系）
| テストID | 内容 |
|---|---|
| T8-04 | ユーザーが質問を入力すると、ユーザーメッセージが `messages` に追加される |
| T8-05 | チェーン実行後、アシスタントメッセージが `messages` に追加される |
| T8-06 | アシスタントメッセージの `content` がモックの回答テキストと一致する |
| T8-07 | アシスタントメッセージの `thinking` がモックの思考テキストと一致する |
| T8-08 | `last_rag_raw` が `RAGResponse` インスタンスで更新される |
| T8-09 | 2回質問したとき `messages` に4件（user, assistant × 2）追加される |

### Thinkingトグル
| テストID | 内容 |
|---|---|
| T8-10 | `show_thinking=True` のとき、エクスパンダーが表示される |
| T8-11 | `show_thinking=False` に切り替えたとき、エクスパンダーが表示されない |

### リセット
| テストID | 内容 |
|---|---|
| T8-12 | リセットボタンをクリックしたとき `messages` が空になる |
| T8-13 | リセットボタンをクリックしたとき `last_rag_raw` が None になる |

### エラー系
| テストID | 内容 |
|---|---|
| T8-14 | `run_collecting` が `RAGTimeoutError` を raise したとき、エラー表示コンポーネントが現れる |
| T8-15 | `run_collecting` が `RAGAPIError` を raise したとき、エラー表示コンポーネントが現れる |
| T8-16 | エラー発生時、`messages` にアシスタントメッセージが追加されない |

## テストファイル

### `tests/test_e2e.py`

```python
import pytest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from core.rag_client import MOCK_RAG_RESPONSE, RAGTimeoutError
from models.schema import RAGResponse

MOCK_THINKING = "これは思考プロセスです。"
MOCK_ANSWER = "カップは棚の上に移動されました。"
MOCK_RAG = RAGResponse(**MOCK_RAG_RESPONSE)

def make_app():
    return AppTest.from_file("app.py")

def test_app_starts():
    at = make_app().run()
    assert not at.exception

def test_chat_flow(monkeypatch):
    with patch("app.run_collecting", return_value=(MOCK_THINKING, MOCK_ANSWER, MOCK_RAG)):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        messages = at.session_state["messages"]
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[1].content == MOCK_ANSWER

def test_error_handling(monkeypatch):
    with patch("app.run_collecting", side_effect=RAGTimeoutError()):
        at = make_app().run()
        at.chat_input[0].set_value("質問").run()
        # エラー表示が存在することを確認
        assert len(at.error) > 0
        # アシスタントメッセージが追加されていないことを確認
        messages = at.session_state["messages"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        assert len(assistant_msgs) == 0

# 上記テストケース一覧に従い実装すること。
```

## 実行コマンド
```bash
pytest tests/test_e2e.py -v
```

## 合格条件
- 全テストがパスすること。
- 実RAGサーバー・LLMサーバーへの接続なしで実行できること。
- `pytest tests/` で全テストスイートがパスすること（最終確認）。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
