# D8: エントリポイント統合

## 参照ドキュメント
- `docs/requirements.md` § 6 (UI/UX 要件)
- `docs/technical_spec.md` § 7 (UI仕様)
- `core/chain.py` (run_collecting)
- `core/rag_client.py` (RAGTimeoutError, RAGAPIError, RAGParseError)
- `ui/__init__.py` (init_session_state)
- `ui/chat.py` (render_history, render_input, render_error)
- `ui/sidebar.py` (render_sidebar)
- `models/schema.py` (ChatMessage)

## 作業概要
`app.py` で全コンポーネントを接続し、ストリーミング表示・エラーハンドリング・
会話履歴管理を実装する。また `requirements.txt` を整備する。

## 実装仕様

### ファイル: `app.py`

#### 全体構造

```python
import streamlit as st
from ui import init_session_state
from ui.chat import render_history, render_input, render_error
from ui.sidebar import render_sidebar
from core.chain import run_collecting
from core.rag_client import RAGTimeoutError, RAGAPIError, RAGParseError
from models.schema import ChatMessage

st.set_page_config(page_title="ビデオイベント・チャット", layout="wide")

init_session_state()
render_sidebar()
render_history()

user_input = render_input()

if user_input:
    # 1. ユーザーメッセージを履歴に追加して即座に再描画
    st.session_state["messages"].append(
        ChatMessage(role="user", content=user_input)
    )

    # 2. 会話履歴を (human_text, ai_text) のタプルリストに変換
    history = _build_history_tuples(st.session_state["messages"])

    # 3. LLM応答をストリーミング表示しながらチェーン実行
    with st.chat_message("assistant"):
        try:
            thinking_text, answer_text, rag_response = _run_with_streaming(
                user_input, history
            )
        except (RAGTimeoutError, RAGAPIError, RAGParseError, Exception) as e:
            render_error(e)
            st.stop()

    # 4. セッションステートを更新
    st.session_state["messages"].append(
        ChatMessage(
            role="assistant",
            content=answer_text,
            thinking=thinking_text or None,
            raw_rag=rag_response,
        )
    )
    st.session_state["last_rag_raw"] = rag_response

    st.rerun()
```

#### ヘルパー関数

```python
def _build_history_tuples(
    messages: list[ChatMessage],
) -> list[tuple[str, str]]:
    """
    ChatMessage のリストから (human_content, ai_content) のペアリストを作る。
    最後のユーザーメッセージ（今回の入力）は除く。
    ロールが交互になっていない場合は安全にスキップする。
    """

def _run_with_streaming(
    user_input: str,
    history: list[tuple[str, str]],
) -> tuple[str, str, RAGResponse]:
    """
    run_collecting を呼び出し、Streamlit のストリーミング表示を行う。

    Thinking の表示ルール:
      show_thinking=True の場合:
        - st.expander("思考プロセス (Thinking)") を先に表示し、
          思考テキストが確定したらその中に書き込む。
      answer_text は st.write_stream または st.markdown でストリーミング表示する。

    実装方針:
      on_chunk コールバックを使って st.empty() プレースホルダーに
      累積テキストを随時書き込む方式を推奨する。
    """
```

#### エラーハンドリング方針

| 例外 | 表示メッセージ |
|---|---|
| `RAGTimeoutError` | "RAGサーバーへの接続がタイムアウトしました。" |
| `RAGAPIError` | "RAGサーバーがエラーを返しました (HTTP {status_code})。" |
| `RAGParseError` | "RAGサーバーのレスポンスを解析できませんでした。" |
| その他の `Exception` | "予期しないエラーが発生しました。" |

いずれも `render_error(e)` を呼び、詳細はエクスパンダーに格納する。

### ファイル: `requirements.txt`

以下のライブラリをバージョン範囲付きで記載する。

```
streamlit>=1.35.0
langchain>=0.3.0
langchain-core>=0.3.0
openai>=1.30.0
httpx>=0.27.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-dotenv>=1.0.0
```

## 実装上の注意
- `st.set_page_config` は必ず最初の Streamlit 呼び出しにすること。
- `st.rerun()` は応答完了後に1回だけ呼ぶこと（ループしない）。
- ストリーミング中にエラーが起きた場合は、部分的に表示されたテキストを
  session_state に追加しないこと。

## 完了条件
- `streamlit run app.py` でアプリが起動し、ブラウザでアクセスできる。
- チャット入力に対してエラーなく応答が表示される（RAGと LLM は実際に接続不要：
  モックを使った動作確認でよい）。
- `requirements.txt` に全依存ライブラリが記載されている。
