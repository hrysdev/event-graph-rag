import streamlit as st


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
    for message in st.session_state["messages"]:
        with st.chat_message(message.role):
            if message.role == "assistant":
                if st.session_state["show_thinking"] and message.thinking:
                    with st.expander("思考プロセス (Thinking)", expanded=False):
                        st.write(message.thinking)
                st.write(message.content)
            else:
                st.write(message.content)


def render_input() -> str | None:
    """
    st.chat_input("メッセージを入力...") を表示し、入力があれば文字列を返す。
    入力がなければ None を返す。
    """
    return st.chat_input("メッセージを入力...")


def render_error(error: Exception) -> None:
    """
    st.error() でエラーメッセージを表示する。
    エラー詳細は st.expander("詳細") 内に str(error) を表示する。
    """
    st.error("エラーが発生しました。")
    with st.expander("詳細"):
        st.write(str(error))
