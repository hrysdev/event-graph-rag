import re
from collections.abc import Callable, Generator

from core import llm_client, prompt, rag_client
from models.schema import RAGResponse

THINK_PATTERN = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def parse_thinking(raw_text: str) -> tuple[str, str]:
    match = THINK_PATTERN.search(raw_text)
    thinking_text = match.group(1) if match else ""
    answer_text = THINK_PATTERN.sub("", raw_text).strip()
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
