import pytest
from streamlit.testing.v1 import AppTest
from models.schema import ChatMessage, RAGResponse

STUB_APP_PATH = "tests/ui_stub_app.py"
ERROR_STUB_APP_PATH = "tests/ui_error_stub_app.py"


# T7-01
def test_init_session_state_messages():
    at = AppTest.from_file(STUB_APP_PATH).run()
    assert at.session_state["messages"] == []


# T7-02
def test_init_session_state_show_thinking():
    at = AppTest.from_file(STUB_APP_PATH).run()
    assert isinstance(at.session_state["show_thinking"], bool)


# T7-03
def test_init_session_state_last_rag_raw():
    at = AppTest.from_file(STUB_APP_PATH).run()
    assert at.session_state["last_rag_raw"] is None


# T7-04
def test_init_session_state_does_not_overwrite():
    at = AppTest.from_file(STUB_APP_PATH)
    at.session_state["messages"] = [ChatMessage(role="user", content="既存メッセージ")]
    at.run()
    assert len(at.session_state["messages"]) == 1
    assert at.session_state["messages"][0].content == "既存メッセージ"


# T7-05
def test_sidebar_toggle_exists():
    at = AppTest.from_file(STUB_APP_PATH).run()
    labels = [t.label for t in at.toggle]
    assert "思考プロセス (Thinking) を表示" in labels


# T7-06
def test_sidebar_reset_button_exists():
    at = AppTest.from_file(STUB_APP_PATH).run()
    labels = [b.label for b in at.button]
    assert "会話をリセット" in labels


# T7-07
def test_reset_button_clears_messages():
    at = AppTest.from_file(STUB_APP_PATH).run()
    at.session_state["messages"] = [ChatMessage(role="user", content="こんにちは")]
    reset_button = next(b for b in at.button if b.label == "会話をリセット")
    reset_button.click().run()
    assert at.session_state["messages"] == []


# T7-08
def test_no_chat_bubbles_when_empty():
    at = AppTest.from_file(STUB_APP_PATH).run()
    assert len(at.chat_message) == 0


# T7-09
def test_user_message_displayed():
    at = AppTest.from_file(STUB_APP_PATH)
    at.session_state["messages"] = [ChatMessage(role="user", content="ユーザーメッセージ")]
    at.session_state["show_thinking"] = False
    at.run()
    assert len(at.chat_message) == 1
    assert at.chat_message[0].name == "user"


# T7-10
def test_assistant_message_displayed():
    at = AppTest.from_file(STUB_APP_PATH)
    at.session_state["messages"] = [ChatMessage(role="assistant", content="アシスタント回答")]
    at.session_state["show_thinking"] = False
    at.run()
    assert len(at.chat_message) == 1
    assert at.chat_message[0].name == "assistant"


# T7-11
def test_expander_shown_when_thinking_and_show_thinking_true():
    at = AppTest.from_file(STUB_APP_PATH)
    at.session_state["messages"] = [
        ChatMessage(role="assistant", content="回答", thinking="思考内容")
    ]
    at.session_state["show_thinking"] = True
    at.run()
    thinking_expanders = [e for e in at.expander if "Thinking" in e.label]
    assert len(thinking_expanders) > 0


# T7-12
def test_expander_hidden_when_show_thinking_false():
    at = AppTest.from_file(STUB_APP_PATH)
    at.session_state["messages"] = [
        ChatMessage(role="assistant", content="回答", thinking="思考内容")
    ]
    at.session_state["show_thinking"] = False
    at.run()
    thinking_expanders = [e for e in at.expander if "Thinking" in e.label]
    assert len(thinking_expanders) == 0


# T7-13
def test_render_error_shows_error():
    at = AppTest.from_file(ERROR_STUB_APP_PATH).run()
    assert len(at.error) > 0
