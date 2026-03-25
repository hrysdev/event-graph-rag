"""テキストビルダーのテスト."""

from __future__ import annotations

from src.ingestion.text_builder import ACTION_VERBS, build_texts, event_to_text
from src.models.event import Event


def _make_event(
    action: str = "pick_up",
    agent: str = "person_01",
    target: str = "cup_01",
    source: str | None = None,
    destination: str | None = None,
    timestamp: str = "2026-03-21T10:00:05",
) -> Event:
    return Event(
        event_id="evt_test",
        frame=50,
        timestamp=timestamp,
        action=action,
        agent=agent,
        target=target,
        source=source,
        destination=destination,
    )


def test_pick_up_with_source() -> None:
    """pick_up + source → 「〜から持ち上げた」."""
    event = _make_event(action="pick_up", source="table_01")
    text = event_to_text(event)
    assert text == "[2026-03-21T10:00:05] person_01がcup_01をtable_01から持ち上げた"


def test_place_on_with_destination() -> None:
    """place_on + destination → 「〜へ置いた」."""
    event = _make_event(action="place_on", destination="shelf_01")
    text = event_to_text(event)
    assert text == "[2026-03-21T10:00:05] person_01がcup_01をshelf_01へ置いた"


def test_move_no_source_no_dest() -> None:
    """move, source/destinationなし."""
    event = _make_event(action="move")
    text = event_to_text(event)
    assert text == "[2026-03-21T10:00:05] person_01がcup_01を移動した"


def test_unknown_action_fallback() -> None:
    """未知のアクション → 'アクション名した' にフォールバック."""
    event = _make_event(action="juggle")
    text = event_to_text(event)
    assert text == "[2026-03-21T10:00:05] person_01がcup_01を「juggle」した"


def test_all_known_actions_have_verbs() -> None:
    """ACTION_VERBSの全エントリで変換が成功する."""
    for action, verb in ACTION_VERBS.items():
        event = _make_event(action=action)
        text = event_to_text(event)
        assert verb in text, f"'{action}' → '{verb}' が含まれない: {text}"


def test_build_texts() -> None:
    """build_textsが複数イベントを一括変換する."""
    events = [
        _make_event(action="pick_up", source="table_01"),
        _make_event(action="move"),
    ]
    texts = build_texts(events)
    assert len(texts) == 2
    assert "持ち上げた" in texts[0]
    assert "移動した" in texts[1]


def test_source_and_destination() -> None:
    """source + destination 両方ある場合."""
    event = _make_event(action="move", source="room_A", destination="room_B")
    text = event_to_text(event)
    assert text == "[2026-03-21T10:00:05] person_01がcup_01をroom_Aからroom_Bへ移動した"


def test_no_prefix_in_text() -> None:
    """テキストにruri-v3のプレフィックスが含まれないこと（embedderで付与）."""
    event = _make_event(action="pick_up")
    text = event_to_text(event)
    assert "検索文書" not in text
    assert "検索クエリ" not in text


def test_nishikawa_action_verbs() -> None:
    """西川データ固有のアクション動詞が正しく変換される."""
    cases = {
        "use": "使った",
        "inspect": "確認した",
        "put_in": "入れた",
        "take_out": "取り出した",
        "attach": "取り付けた",
        "no_event": "何もしなかった",
    }
    for action, expected_verb in cases.items():
        event = _make_event(action=action)
        text = event_to_text(event)
        assert expected_verb in text, f"'{action}' → '{expected_verb}' が含まれない: {text}"
