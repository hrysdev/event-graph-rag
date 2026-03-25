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
