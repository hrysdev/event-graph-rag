from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from models.schema import RAGResponse, VideoEvent, VideoObject

SYSTEM_PROMPT: str = """\
あなたは動画解析アシスタントです。
提供された「登場オブジェクト」と「イベントログ」に基づいて、
ユーザーの質問に正確かつ論理的に回答してください。

ルール:
- 与えられたデータにない情報を推測・捏造しないこと。
- 因果関係の推論は、イベントの時系列を根拠として示すこと。
- 回答は日本語で行うこと。\
"""


def format_objects(objects: list[VideoObject]) -> str:
    if not objects:
        return "[登場オブジェクト]\n(なし)"
    lines = ["[登場オブジェクト]"]
    for obj in objects:
        base = f"- {obj.obj_id} ({obj.category}): 初登場フレーム={obj.first_seen_frame} ({obj.first_seen_timestamp})"
        if obj.attributes:
            attrs = ", ".join(f"{k}={v}" for k, v in obj.attributes.items())
            base += f", {attrs}"
        lines.append(base)
    return "\n".join(lines)


def format_events(events: list[VideoEvent]) -> str:
    if not events:
        return "[イベントログ (時系列順)]\n(なし)"
    sorted_events = sorted(events, key=lambda e: e.frame)
    lines = ["[イベントログ (時系列順)]"]
    for evt in sorted_events:
        source = evt.source if evt.source is not None else "(不明)"
        destination = evt.destination if evt.destination is not None else "(不明)"
        lines.append(
            f"- Frame {evt.frame} ({evt.timestamp}) [{evt.event_id}]: "
            f"{evt.agent} が {evt.target} を {source} から {destination} へ {evt.action} した。"
        )
    return "\n".join(lines)


def build_context(rag_response: RAGResponse) -> str:
    return f"{format_objects(rag_response.objects)}\n\n{format_events(rag_response.events)}"


def build_messages(
    rag_response: RAGResponse,
    user_question: str,
    history: list[tuple[str, str]],
) -> list:
    messages: list = [SystemMessage(content=SYSTEM_PROMPT)]
    for human_text, ai_text in history[-10:]:
        messages.append(HumanMessage(content=human_text))
        messages.append(AIMessage(content=ai_text))
    context = build_context(rag_response)
    messages.append(HumanMessage(content=f"{context}\n\n{user_question}"))
    return messages
