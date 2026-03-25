import streamlit as st


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
    with st.sidebar:
        st.session_state["show_thinking"] = st.toggle(
            "思考プロセス (Thinking) を表示",
            value=st.session_state["show_thinking"],
        )

        if st.button("会話をリセット"):
            st.session_state["messages"] = []
            st.session_state["last_rag_raw"] = None
            st.rerun()

        st.divider()

        st.subheader("直近のRAG取得データ")
        if st.session_state["last_rag_raw"] is None:
            st.write("まだRAGデータがありません")
        else:
            st.json(st.session_state["last_rag_raw"].model_dump())
