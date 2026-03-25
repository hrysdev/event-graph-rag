import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.llm_client import get_client, stream_chat, langchain_messages_to_openai
from config import settings
from openai import OpenAI


def make_mock_chunk(text: str):
    """openai ストリーミングチャンクのモックを作成する"""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = text
    return chunk


# --- get_client() ---

@patch("core.llm_client.OpenAI")
def test_get_client_returns_openai_instance(mock_openai_cls):
    mock_instance = MagicMock(spec=OpenAI)
    mock_openai_cls.return_value = mock_instance
    client = get_client()
    assert client is mock_instance  # T5-01


@patch("core.llm_client.OpenAI")
def test_get_client_base_url(mock_openai_cls):
    get_client()
    _, kwargs = mock_openai_cls.call_args
    assert kwargs["base_url"] == settings.vllm_base_url  # T5-02


# --- stream_chat() ---

@patch("core.llm_client.get_client")
def test_stream_chat_yields_chunks(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        make_mock_chunk("Hello"),
        make_mock_chunk(""),       # 空チャンク（スキップされるはず）
        make_mock_chunk(" World"),
    ])
    messages = [{"role": "user", "content": "hi"}]
    chunks = list(stream_chat(messages))
    assert chunks == ["Hello", " World"]  # T5-03


@patch("core.llm_client.get_client")
def test_stream_chat_skips_empty_chunks(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([
        make_mock_chunk(""),
        make_mock_chunk(""),
        make_mock_chunk("only"),
    ])
    chunks = list(stream_chat([{"role": "user", "content": "hi"}]))
    assert "" not in chunks  # T5-04
    assert chunks == ["only"]


@patch("core.llm_client.get_client")
def test_stream_chat_uses_model_name(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([])
    list(stream_chat([{"role": "user", "content": "hi"}]))
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == settings.vllm_model_name  # T5-05


@patch("core.llm_client.get_client")
def test_stream_chat_stream_true(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([])
    list(stream_chat([{"role": "user", "content": "hi"}]))
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["stream"] is True  # T5-06


@patch("core.llm_client.get_client")
def test_stream_chat_uses_temperature(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([])
    list(stream_chat([{"role": "user", "content": "hi"}]))
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["temperature"] == settings.llm_temperature  # T5-07


@patch("core.llm_client.get_client")
def test_stream_chat_uses_max_tokens(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = iter([])
    list(stream_chat([{"role": "user", "content": "hi"}]))
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["max_tokens"] == settings.llm_max_tokens  # T5-08


# --- langchain_messages_to_openai() ---

def test_system_message_conversion():
    result = langchain_messages_to_openai([SystemMessage(content="sys")])
    assert result == [{"role": "system", "content": "sys"}]  # T5-09


def test_human_message_conversion():
    result = langchain_messages_to_openai([HumanMessage(content="hello")])
    assert result == [{"role": "user", "content": "hello"}]  # T5-10


def test_ai_message_conversion():
    result = langchain_messages_to_openai([AIMessage(content="hi there")])
    assert result == [{"role": "assistant", "content": "hi there"}]  # T5-11


def test_mixed_messages_preserve_order():
    msgs = [
        SystemMessage(content="sys"),
        HumanMessage(content="user msg"),
        AIMessage(content="ai msg"),
        HumanMessage(content="follow up"),
    ]
    result = langchain_messages_to_openai(msgs)
    assert result == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "user msg"},
        {"role": "assistant", "content": "ai msg"},
        {"role": "user", "content": "follow up"},
    ]  # T5-12


def test_empty_list_returns_empty():
    assert langchain_messages_to_openai([]) == []  # T5-13
