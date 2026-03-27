import streamlit as st
from ui import init_session_state
from ui.chat import render_history, render_input, render_error
from ui.sidebar import render_sidebar
from core.chain import run_collecting
from core.rag_client import RAGTimeoutError, RAGAPIError, RAGParseError
from models.schema import ChatMessage, RAGResponse

st.set_page_config(page_title="ビデオイベント・チャット", layout="wide")

init_session_state()
render_sidebar()
render_history()

user_input = render_input()


def _build_history_tuples(
    messages: list[ChatMessage],
) -> list[tuple[str, str]]:
    """
    ChatMessage のリストから (human_content, ai_content) のペアリストを作る。
    最後のユーザーメッセージ（今回の入力）は除く。
    ロールが交互になっていない場合は安全にスキップする。
    """
    history: list[tuple[str, str]] = []
    # 最後のメッセージ（今回追加したユーザーメッセージ）は除く
    msgs = messages[:-1]
    i = 0
    while i < len(msgs) - 1:
        if msgs[i].role == "user" and msgs[i + 1].role == "assistant":
            history.append((msgs[i].content, msgs[i + 1].content))
            i += 2
        else:
            i += 1
    return history


def _run_with_streaming(
    user_input: str,
    history: list[tuple[str, str]],
) -> tuple[str, str, RAGResponse]:
    """
    run_collecting を呼び出し、Streamlit のストリーミング表示を行う。

    処理フェーズに応じてアシスタントバブル内のステータスを更新する:
      - RAG取得中: "🔍 データ取得中..."
      - 最初のチャンク受信〜</think>まで: "💭 思考中..."
      - </think>以降: ステータスを消してストリーミング回答を表示
    Thinking の表示ルール:
      show_thinking=True の場合:
        - st.expander("思考プロセス (Thinking)") を表示し、thinking テキストを書き込む。
      answer_text は累積テキストを st.empty() プレースホルダーに随時書き込む。
    """
    status_placeholder = st.empty()
    answer_placeholder = st.empty()
    accumulated = ""
    first_chunk = True
    think_end_idx = -1

    status_placeholder.markdown("🔍 データ取得中...")

    def on_chunk(chunk: str) -> None:
        nonlocal accumulated, first_chunk, think_end_idx
        accumulated += chunk

        if first_chunk:
            first_chunk = False
            status_placeholder.markdown("💭 思考中...")

        if think_end_idx == -1:
            think_end_idx = accumulated.find("</think>")
            if think_end_idx != -1:
                status_placeholder.empty()

        if think_end_idx != -1:
            display = accumulated[think_end_idx + len("</think>"):].strip()
            if display:
                answer_placeholder.markdown(display)

    thinking_text, answer_text, rag_response = run_collecting(
        user_input, history, on_chunk=on_chunk
    )

    status_placeholder.empty()
    answer_placeholder.empty()

    if st.session_state["show_thinking"] and thinking_text:
        with st.expander("思考プロセス (Thinking)", expanded=False):
            st.write(thinking_text)

    st.markdown(answer_text)

    return thinking_text, answer_text, rag_response


if user_input:
    # 1. ユーザーメッセージを履歴に追加して即座に再描画
    st.session_state["messages"].append(
        ChatMessage(role="user", content=user_input)
    )

    # 2. 会話履歴を (human_text, ai_text) のタプルリストに変換
    history = _build_history_tuples(st.session_state["messages"])

    # 3. ユーザーメッセージを即時表示
    with st.chat_message("user"):
        st.write(user_input)

    # 4. LLM応答をストリーミング表示しながらチェーン実行
    with st.chat_message("assistant"):
        try:
            thinking_text, answer_text, rag_response = _run_with_streaming(
                user_input, history
            )
        except RAGTimeoutError:
            render_error(Exception("RAGサーバーへの接続がタイムアウトしました。"))
            st.stop()
        except RAGAPIError as e:
            render_error(Exception(f"RAGサーバーがエラーを返しました (HTTP {e.status_code})。"))
            st.stop()
        except RAGParseError:
            render_error(Exception("RAGサーバーのレスポンスを解析できませんでした。"))
            st.stop()
        except Exception:
            render_error(Exception("予期しないエラーが発生しました。"))
            st.stop()

    # 5. セッションステートを更新
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
