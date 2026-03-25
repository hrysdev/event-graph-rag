import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from models.schema import VideoObject, VideoEvent, RAGResponse
from core.prompt import format_objects, format_events, build_context, build_messages


# 共通フィクスチャ
@pytest.fixture
def sample_objects():
    return [
        VideoObject(obj_id="cup_01", category="cup", first_seen_frame=3,
                    first_seen_timestamp="2024-01-15T10:23:45.100Z",
                    attributes={"color": "red", "material": "ceramic"}),
        VideoObject(obj_id="table_01", category="table", first_seen_frame=0,
                    first_seen_timestamp="2024-01-15T10:23:45.000Z",
                    attributes={}),
    ]


@pytest.fixture
def sample_events():
    return [
        VideoEvent(event_id="evt_002", frame=10, timestamp="2024-01-15T10:23:45.333Z",
                   action="place_on",
                   agent="person_01", target="cup_01",
                   source=None, destination="shelf_01"),
        VideoEvent(event_id="evt_001", frame=5, timestamp="2024-01-15T10:23:45.167Z",
                   action="pick_up",
                   agent="person_01", target="cup_01",
                   source="table_01", destination=None),
    ]


# --- format_objects() ---

def test_T4_01_each_object_on_one_line(sample_objects):
    result = format_objects(sample_objects)
    lines = result.splitlines()
    # ヘッダー行を除いてオブジェクト数分の行がある
    object_lines = [l for l in lines if l.startswith("-")]
    assert len(object_lines) == 2


def test_T4_02_header_line(sample_objects):
    result = format_objects(sample_objects)
    assert result.splitlines()[0] == "[登場オブジェクト]"


def test_T4_03_keys_and_values_in_output(sample_objects):
    result = format_objects(sample_objects)
    assert "cup_01" in result
    assert "cup" in result
    assert "3" in result  # first_seen_frame
    assert "color" in result
    assert "red" in result


def test_T4_03b_first_seen_timestamp_in_output(sample_objects):
    result = format_objects(sample_objects)
    assert "2024-01-15T10:23:45.100Z" in result


def test_T4_04_empty_attributes_no_error(sample_objects):
    result = format_objects(sample_objects)
    # table_01 は attributes={} なので属性部分が省略され、エラーにならない
    assert "table_01" in result


def test_T4_05_empty_objects_list():
    result = format_objects([])
    assert "(なし)" in result


# --- format_events() ---

def test_T4_06_each_event_on_one_line(sample_events):
    result = format_events(sample_events)
    event_lines = [l for l in result.splitlines() if l.startswith("-")]
    assert len(event_lines) == 2


def test_T4_07_header_line(sample_events):
    result = format_events(sample_events)
    assert "[イベントログ (時系列順)]" in result.splitlines()[0]


def test_T4_08_source_none_shows_unknown(sample_events):
    result = format_events(sample_events)
    assert "(不明)" in result


def test_T4_09_destination_none_shows_unknown(sample_events):
    result = format_events(sample_events)
    assert "(不明)" in result


def test_T4_09b_timestamp_in_output(sample_events):
    result = format_events(sample_events)
    assert "2024-01-15T10:23:45.167Z" in result
    assert "2024-01-15T10:23:45.333Z" in result


def test_T4_10_sorted_ascending(sample_events):
    # sample_events はフレーム降順 (10, 5) で渡している
    result = format_events(sample_events)
    lines = [l for l in result.splitlines() if l.startswith("-")]
    # 最初の行がフレーム5、次が10
    assert "Frame 5" in lines[0]
    assert "Frame 10" in lines[1]


def test_T4_11_empty_events_list():
    result = format_events([])
    assert "(なし)" in result


# --- build_context() ---

def test_T4_12_both_sections_present(sample_objects, sample_events):
    rag = RAGResponse(objects=sample_objects, events=sample_events)
    result = build_context(rag)
    assert "[登場オブジェクト]" in result
    assert "[イベントログ" in result


def test_T4_13_requirements_sample_data():
    # requirements.md § 4.3 のサンプルデータ: 3件のオブジェクトと2件のイベント
    objects = [
        VideoObject(obj_id="cup_01", category="cup", first_seen_frame=3,
                    first_seen_timestamp="2024-01-15T10:23:45.100Z",
                    attributes={"color": "red"}),
        VideoObject(obj_id="table_01", category="table", first_seen_frame=0,
                    first_seen_timestamp="2024-01-15T10:23:45.000Z",
                    attributes={}),
        VideoObject(obj_id="shelf_01", category="shelf", first_seen_frame=0,
                    first_seen_timestamp="2024-01-15T10:23:45.000Z",
                    attributes={}),
    ]
    events = [
        VideoEvent(event_id="evt_001", frame=5, timestamp="2024-01-15T10:23:45.167Z",
                   action="pick_up", agent="person_01", target="cup_01",
                   source="table_01", destination=None),
        VideoEvent(event_id="evt_002", frame=10, timestamp="2024-01-15T10:23:45.333Z",
                   action="place_on", agent="person_01", target="cup_01",
                   source=None, destination="shelf_01"),
    ]
    rag = RAGResponse(objects=objects, events=events)
    result = build_context(rag)
    object_lines = [l for l in result.splitlines() if l.startswith("-") and "Frame" not in l]
    event_lines = [l for l in result.splitlines() if l.startswith("- Frame")]
    assert len(object_lines) == 3
    assert len(event_lines) == 2


# --- build_messages() ---

@pytest.fixture
def simple_rag(sample_objects, sample_events):
    return RAGResponse(objects=sample_objects, events=sample_events)


def test_T4_14_first_message_is_system(simple_rag):
    messages = build_messages(simple_rag, "質問", [])
    assert isinstance(messages[0], SystemMessage)


def test_T4_15_empty_history_two_elements(simple_rag):
    messages = build_messages(simple_rag, "質問", [])
    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)


def test_T4_16_two_turn_history_six_elements(simple_rag):
    history = [("Q1", "A1"), ("Q2", "A2")]
    messages = build_messages(simple_rag, "Q3", history)
    assert len(messages) == 6
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert isinstance(messages[2], AIMessage)
    assert isinstance(messages[3], HumanMessage)
    assert isinstance(messages[4], AIMessage)
    assert isinstance(messages[5], HumanMessage)


def test_T4_17_last_human_message_contains_object_name(simple_rag):
    messages = build_messages(simple_rag, "質問", [])
    last_human = messages[-1]
    assert isinstance(last_human, HumanMessage)
    assert "cup_01" in last_human.content


def test_T4_18_history_truncated_to_10_turns(simple_rag):
    history = [(f"Q{i}", f"A{i}") for i in range(15)]
    messages = build_messages(simple_rag, "最終質問", history)
    # SystemMessage(1) + 最大10ターン×2(20) + HumanMessage(1) = 22要素以内
    assert len(messages) <= 22
    # history[-10:] が適用されるため 1 + 20 + 1 = 22
    assert len(messages) == 22
