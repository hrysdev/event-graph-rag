# D7: UIコンポーネント

## 参照ドキュメント
- `docs/requirements.md` § 6 (UI/UX 要件)
- `docs/technical_spec.md` § 7 (UI仕様)
- `models/schema.py` (ChatMessage, RAGResponse)

## 作業概要
Streamlitのチャット画面とサイドバーをコンポーネント関数として実装する。
この工程ではチェーン呼び出しを行わない。チェーンの代わりにスタブ関数を使う。

## 事前準備
```
mkdir -p ui
touch ui/__init__.py
```

## 実装仕様

### セッションステート定義

`ui/__init__.py` に以下の初期化関数を定義する。

```python
import streamlit as st
from models.schema import ChatMessage

def init_session_state() -> None:
    """
    st.session_state に必要なキーが存在しない場合のみ初期値をセットする。

    キー一覧:
      messages      : list[ChatMessage] = []
      show_thinking : bool              = True   (ENABLEd_THINKINGのデフォルト値を使う)
      last_rag_raw  : RAGResponse|None  = None
    """
```

### ファイル: `ui/sidebar.py`

```python
def render_sidebar() -> None:
    """
    st.sidebar 内に以下を描画する。

    [Thinkingの表示]
      st.toggle で show_thinking を切り替える。
      ラベル: "思考プロセス (Thinking) を表示"

    [会話をリセット]
      ボタンクリック時に messages=[], last_rag_raw=None をセットして st.rerun() する。
      ラベル: "会話をリセット"

    --- (区切り線)

    [直近のRAG取得データ]
      last_rag_raw が None の場合: "まだRAGデータがありません" と表示。
      last_rag_raw がある場合: st.json(last_rag_raw.model_dump()) で展開表示。
    """
```

### ファイル: `ui/chat.py`

```python
def render_history() -> None:
    """
    st.session_state["messages"] の全メッセージをチャットバブルとして描画する。

    各メッセージの描画ルール:
      role="user"     → st.chat_message("user") で表示
      role="assistant" → st.chat_message("assistant") で以下を表示:
          - show_thinking=True かつ thinking が存在する場合:
              st.expander("思考プロセス (Thinking)", expanded=False) 内に thinking テキストを表示
          - content を通常テキストとして表示
    """

def render_input() -> str | None:
    """
    st.chat_input("メッセージを入力...") を表示し、入力があれば文字列を返す。
    入力がなければ None を返す。
    """

def render_error(error: Exception) -> None:
    """
    st.error() でエラーメッセージを表示する。
    エラー詳細は st.expander("詳細") 内に str(error) を表示する。
    """
```

## 実装上の注意
- `render_sidebar` と `render_history` は描画のみ行い、副作用（session_state の変更）は
  明示的なユーザー操作（ボタン/トグル）経由のみとする。
- `ui/chat.py` と `ui/sidebar.py` はチェーン (`core/chain.py`) を import しないこと。
- `show_thinking` の初期値は `config.settings.enable_thinking` を参照すること。

## 完了条件
- `python -c "from ui import init_session_state; from ui.sidebar import render_sidebar; from ui.chat import render_history, render_input, render_error"` がエラーなく通る。
- `render_sidebar`・`render_history`・`render_input`・`render_error` が Streamlit コンテキスト外で import だけはエラーなく通る。
