from collections.abc import Iterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from openai import OpenAI

from config import settings


def get_client() -> OpenAI:
    return OpenAI(base_url=settings.vllm_base_url, api_key="dummy")


def stream_chat(messages: list[dict]) -> Iterator[str]:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.vllm_model_name,
        messages=messages,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        stream=True,
    )
    for chunk in response:
        text = chunk.choices[0].delta.content
        if text:
            yield text


def langchain_messages_to_openai(messages: list[BaseMessage]) -> list[dict]:
    role_map = {
        SystemMessage: "system",
        HumanMessage: "user",
        AIMessage: "assistant",
    }
    return [{"role": role_map[type(m)], "content": m.content} for m in messages]
