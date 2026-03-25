import pytest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from core.rag_client import MOCK_RAG_RESPONSE, RAGTimeoutError, RAGAPIError
from models.schema import RAGResponse

MOCK_THINKING = "これは思考プロセスです。"
MOCK_ANSWER = "カップは棚の上に移動されました。"
MOCK_RAG = RAGResponse(**MOCK_RAG_RESPONSE)

MOCK_RETURN = (MOCK_THINKING, MOCK_ANSWER, MOCK_RAG)

PATCH_TARGET = "core.chain.run_collecting"


def make_app():
    return AppTest.from_file("app.py")


# T8-01
def test_app_starts():
    at = make_app().run()
    assert not at.exception


# T8-02
def test_initial_messages_empty():
    at = make_app().run()
    assert at.session_state["messages"] == []


# T8-03
def test_chat_input_exists():
    at = make_app().run()
    assert len(at.chat_input) > 0


# T8-04
def test_user_message_added():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        messages = at.session_state["messages"]
        user_msgs = [m for m in messages if m.role == "user"]
        assert len(user_msgs) >= 1


# T8-05
def test_assistant_message_added():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        messages = at.session_state["messages"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        assert len(assistant_msgs) >= 1


# T8-06
def test_assistant_message_content():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        messages = at.session_state["messages"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        assert assistant_msgs[0].content == MOCK_ANSWER


# T8-07
def test_assistant_message_thinking():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        messages = at.session_state["messages"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        assert assistant_msgs[0].thinking == MOCK_THINKING


# T8-08
def test_last_rag_raw_updated():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        assert isinstance(at.session_state["last_rag_raw"], RAGResponse)


# T8-09
def test_two_questions_four_messages():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("質問1").run()
        at.chat_input[0].set_value("質問2").run()
        messages = at.session_state["messages"]
        assert len(messages) == 4


# T8-10
def test_thinking_expander_shown_when_show_thinking_true():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app()
        at.session_state["show_thinking"] = True
        at.run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        thinking_expanders = [e for e in at.expander if "Thinking" in e.label]
        assert len(thinking_expanders) > 0


# T8-11
def test_thinking_expander_hidden_when_show_thinking_false():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app()
        at.session_state["show_thinking"] = False
        at.run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        thinking_expanders = [e for e in at.expander if "Thinking" in e.label]
        assert len(thinking_expanders) == 0


# T8-12
def test_reset_clears_messages():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        reset_button = next(b for b in at.button if b.label == "会話をリセット")
        reset_button.click().run()
        assert at.session_state["messages"] == []


# T8-13
def test_reset_clears_last_rag_raw():
    with patch(PATCH_TARGET, return_value=MOCK_RETURN):
        at = make_app().run()
        at.chat_input[0].set_value("カップはどこにありますか？").run()
        reset_button = next(b for b in at.button if b.label == "会話をリセット")
        reset_button.click().run()
        assert at.session_state["last_rag_raw"] is None


# T8-14
def test_rag_timeout_error_shows_error():
    with patch(PATCH_TARGET, side_effect=RAGTimeoutError()):
        at = make_app().run()
        at.chat_input[0].set_value("質問").run()
        assert len(at.error) > 0


# T8-15
def test_rag_api_error_shows_error():
    with patch(PATCH_TARGET, side_effect=RAGAPIError(500, "Internal Server Error")):
        at = make_app().run()
        at.chat_input[0].set_value("質問").run()
        assert len(at.error) > 0


# T8-16
def test_error_no_assistant_message():
    with patch(PATCH_TARGET, side_effect=RAGTimeoutError()):
        at = make_app().run()
        at.chat_input[0].set_value("質問").run()
        messages = at.session_state["messages"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]
        assert len(assistant_msgs) == 0
