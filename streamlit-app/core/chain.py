from collections.abc import Callable, Generator

from core import llm_client, prompt, rag_client
from models.schema import RAGResponse

THINK_END_TAG = "</think>"


def parse_thinking(raw_text: str) -> tuple[str, str]:
    """
    モデルは <think> 開きタグを出力せず </think> のみ出力する。
    </think> をセパレーターとして思考部分と回答部分に分割する。
    </think> が存在しない場合は thinking_text="" として全文を回答とする。
    """
    idx = raw_text.find(THINK_END_TAG)
    if idx == -1:
        return "", raw_text.strip()
    thinking_text = raw_text[:idx].strip()
    answer_text = raw_text[idx + len(THINK_END_TAG):].strip()
    return thinking_text, answer_text


def run(
    user_question: str,
    history: list[tuple[str, str]],
) -> Generator[str, None, tuple[str, str, RAGResponse]]:
    rag_response = rag_client.query(user_question)
    messages = prompt.build_messages(rag_response, user_question, history)
    openai_messages = llm_client.langchain_messages_to_openai(messages)

    raw_text = ""
    for chunk in llm_client.stream_chat(openai_messages):
        yield chunk
        raw_text += chunk

    thinking_text, answer_text = parse_thinking(raw_text)
    return thinking_text, answer_text, rag_response


def run_collecting(
    user_question: str,
    history: list[tuple[str, str]],
    on_chunk: Callable[[str], None] | None = None,
) -> tuple[str, str, RAGResponse]:
    gen = run(user_question, history)
    try:
        while True:
            chunk = next(gen)
            if on_chunk is not None:
                on_chunk(chunk)
    except StopIteration as e:
        return e.value
