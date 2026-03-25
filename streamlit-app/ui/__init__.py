import streamlit as st
from models.schema import ChatMessage, RAGResponse
from config import settings


def init_session_state() -> None:
    """
    st.session_state に必要なキーが存在しない場合のみ初期値をセットする。

    キー一覧:
      messages      : list[ChatMessage] = []
      show_thinking : bool              = True   (ENABLEd_THINKINGのデフォルト値を使う)
      last_rag_raw  : RAGResponse|None  = None
    """
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "show_thinking" not in st.session_state:
        st.session_state["show_thinking"] = settings.enable_thinking
    if "last_rag_raw" not in st.session_state:
        st.session_state["last_rag_raw"] = None
