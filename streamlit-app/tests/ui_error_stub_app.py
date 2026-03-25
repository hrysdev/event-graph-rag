import streamlit as st
from ui import init_session_state
from ui.chat import render_error

st.set_page_config(page_title="エラーテスト用スタブ")
init_session_state()
render_error(ValueError("テストエラー"))
