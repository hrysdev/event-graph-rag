import pytest
from unittest.mock import patch, MagicMock
from core.chain import parse_thinking, run_collecting
from core.rag_client import RAGTimeoutError, MOCK_RAG_RESPONSE
from models.schema import RAGResponse


# --- parse_thinking のテスト ---

def test_parse_thinking_with_tag():
    # T6-01
    thinking, answer = parse_thinking("<think>思考内容</think>回答")
    assert thinking == "思考内容"
    assert answer == "回答"


def test_parse_thinking_without_tag():
    # T6-02
    thinking, answer = parse_thinking("タグなし回答")
    assert thinking == ""
    assert answer == "タグなし回答"


def test_parse_thinking_only_think_tag():
    # T6-03
    thinking, answer = parse_thinking("<think>思考</think>")
    assert thinking == "思考"
    assert answer == ""


def test_parse_thinking_unclosed_tag():
    # T6-04
    raw = "<think>閉じていない"
    thinking, answer = parse_thinking(raw)
    assert thinking == ""
    assert answer == raw


def test_parse_thinking_multiple_tags():
    # T6-05
    raw = "<think>思考1</think>回答<think>思考2</think>"
    thinking, answer = parse_thinking(raw)
    assert "<think>" not in answer
    assert "</think>" not in answer
    assert "思考1" not in answer
    assert "思考2" not in answer


def test_parse_thinking_whitespace_around_tags():
    # T6-06
    raw = "  \n<think>思考</think>\n  回答  "
    thinking, answer = parse_thinking(raw)
    assert thinking == "思考"
    assert answer == "回答"


def test_parse_thinking_empty_think_tag():
    # T6-07
    raw = "<think></think>回答テキスト"
    thinking, answer = parse_thinking(raw)
    assert thinking == ""
    assert answer == "回答テキスト"


# --- run_collecting のテスト ---

@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_success(mock_stream, mock_query):
    # T6-08
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    mock_stream.return_value = iter(["<think>思考</think>", "回答テキスト"])

    thinking, answer, rag = run_collecting("質問", history=[])
    assert thinking == "思考"
    assert "回答テキスト" in answer
    assert isinstance(rag, RAGResponse)


@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_on_chunk_called(mock_stream, mock_query):
    # T6-09
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    chunks = ["chunk1", "chunk2", "chunk3"]
    mock_stream.return_value = iter(chunks)

    received = []
    run_collecting("質問", history=[], on_chunk=received.append)
    assert received == chunks


@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_on_chunk_none(mock_stream, mock_query):
    # T6-10
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    mock_stream.return_value = iter(["chunk1", "chunk2"])

    # エラーなく実行される
    thinking, answer, rag = run_collecting("質問", history=[], on_chunk=None)
    assert isinstance(rag, RAGResponse)


@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_rag_timeout(mock_stream, mock_query):
    # T6-11
    mock_query.side_effect = RAGTimeoutError("timeout")

    with pytest.raises(RAGTimeoutError):
        run_collecting("質問", history=[])


@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_llm_exception(mock_stream, mock_query):
    # T6-12
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    mock_stream.side_effect = RuntimeError("LLM error")

    with pytest.raises(RuntimeError):
        run_collecting("質問", history=[])


@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_empty_history(mock_stream, mock_query):
    # T6-13
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    mock_stream.return_value = iter(["回答"])

    thinking, answer, rag = run_collecting("質問", history=[])
    assert isinstance(rag, RAGResponse)


@patch("core.chain.rag_client.query")
@patch("core.chain.llm_client.stream_chat")
def test_run_collecting_chunks_accumulated(mock_stream, mock_query):
    # T6-14
    mock_query.return_value = RAGResponse(**MOCK_RAG_RESPONSE)
    mock_stream.return_value = iter(["部分1", "部分2", "部分3"])

    thinking, answer, rag = run_collecting("質問", history=[])
    assert answer == "部分1部分2部分3"
