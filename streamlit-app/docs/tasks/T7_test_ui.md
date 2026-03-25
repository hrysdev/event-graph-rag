# T7: UIコンポーネント テスト

## 対象工程
D7: UIコンポーネント

## テスト対象ファイル
- `ui/__init__.py` (`init_session_state`)
- `ui/sidebar.py` (`render_sidebar`)
- `ui/chat.py` (`render_history`, `render_input`, `render_error`)

## 前提
- `ui/` と `models/schema.py` が実装済みであること。
- テストエージェントは対象ファイルを **読むが変更しない**。
- `streamlit.testing.v1.AppTest` を使用する。
- チェーン (`core/chain.py`) の呼び出しは含まれないため、モック不要。

## テスト用アプリファイル

`tests/ui_stub_app.py` を新規作成してテスト用 Streamlit アプリとして使う。

```python
# tests/ui_stub_app.py
import streamlit as st
from ui import init_session_state
from ui.sidebar import render_sidebar
from ui.chat import render_history, render_input, render_error
from models.schema import ChatMessage

st.set_page_config(page_title="UIテスト用スタブ")
init_session_state()
render_sidebar()
render_history()
user_input = render_input()
```

## テストケース一覧

### `init_session_state()`
| テストID | 内容 |
|---|---|
| T7-01 | 初回呼び出し後、`messages` キーが空リストで存在する |
| T7-02 | 初回呼び出し後、`show_thinking` キーが bool 値で存在する |
| T7-03 | 初回呼び出し後、`last_rag_raw` キーが None で存在する |
| T7-04 | 既存の `messages` がある状態で `init_session_state` を呼んでも上書きされない |

### サイドバー
| テストID | 内容 |
|---|---|
| T7-05 | "思考プロセス (Thinking) を表示" というラベルのトグルが存在する |
| T7-06 | "会話をリセット" ボタンが存在する |
| T7-07 | リセットボタンをクリックしたとき `messages` が空リストになる |

### チャット画面
| テストID | 内容 |
|---|---|
| T7-08 | `messages` が空のとき、チャットバブルが表示されない |
| T7-09 | role="user" のメッセージが画面に表示される |
| T7-10 | role="assistant" のメッセージが画面に表示される |
| T7-11 | thinking が存在し `show_thinking=True` のとき、エクスパンダーが存在する |
| T7-12 | thinking が存在し `show_thinking=False` のとき、エクスパンダーが存在しない |

### エラー表示
| テストID | 内容 |
|---|---|
| T7-13 | `render_error` を呼んだとき、エラーコンポーネントが表示される |

## テストファイル

### `tests/test_ui.py`

```python
import pytest
from streamlit.testing.v1 import AppTest
from models.schema import ChatMessage, RAGResponse

STUB_APP_PATH = "tests/ui_stub_app.py"

def test_init_session_state_messages():
    at = AppTest.from_file(STUB_APP_PATH).run()
    assert at.session_state["messages"] == []

def test_init_session_state_show_thinking():
    at = AppTest.from_file(STUB_APP_PATH).run()
    assert isinstance(at.session_state["show_thinking"], bool)

def test_reset_button_clears_messages():
    at = AppTest.from_file(STUB_APP_PATH).run()
    at.session_state["messages"] = [
        ChatMessage(role="user", content="こんにちは")
    ]
    # リセットボタンをクリック
    at.button[0].click().run()  # ボタンのインデックスは実装に合わせて調整
    assert at.session_state["messages"] == []

# 上記テストケース一覧に従い実装すること。
# AppTest の API: https://docs.streamlit.io/develop/api-reference/app-testing
```

## 実行コマンド
```bash
pytest tests/test_ui.py -v
```

## 合格条件
- 全テストがパスすること。
- `streamlit` サーバーを起動せずに実行できること。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
