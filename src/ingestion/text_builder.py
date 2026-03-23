"""イベント → 日本語テキスト変換（embedding用）."""

from __future__ import annotations

from src.models.event import Event

ACTION_VERBS: dict[str, str] = {
    "pick_up": "持ち上げた",
    "place_on": "置いた",
    "move": "移動した",
    "open": "開いた",
    "close": "閉じた",
    "pour": "注いだ",
    "push": "押した",
    "pull": "引いた",
    "throw": "投げた",
    "catch": "受け取った",
    "cut": "切った",
    "eat": "食べた",
    "drink": "飲んだ",
    "wear": "着た",
    "remove": "外した",
    "turn_on": "つけた",
    "turn_off": "消した",
    "sit_on": "座った",
    "stand_up": "立ち上がった",
    "enter": "入った",
    "exit": "出た",
    "hand_over": "手渡した",
    "receive": "受け取った",
    "drop": "落とした",
    "touch": "触った",
    "look_at": "見た",
    "point_at": "指差した",
    "write": "書いた",
    "read": "読んだ",
    "wash": "洗った",
    "clean": "掃除した",
    "stack": "積み重ねた",
    "fold": "畳んだ",
    "unfold": "広げた",
    "squeeze": "絞った",
    "stir": "かき混ぜた",
    "shake": "振った",
    "use": "使った",
    "inspect": "確認した",
    "put_in": "入れた",
    "take_out": "取り出した",
    "attach": "取り付けた",
    "no_event": "何もしなかった",
}


def event_to_text(event: Event) -> str:
    """単一イベントを日本語テキストに変換.

    フォーマット: [timestamp] agentがtargetをsourceからdestinationへ動詞
    """
    verb = ACTION_VERBS.get(event.action, f"「{event.action}」した")

    text = f"[{event.timestamp}] {event.agent}が{event.target}を"

    if event.source:
        text += f"{event.source}から"
    if event.destination:
        text += f"{event.destination}へ"

    text += verb

    return text


def build_texts(events: list[Event]) -> list[str]:
    """イベントリストを日本語テキストリストに変換."""
    return [event_to_text(e) for e in events]
