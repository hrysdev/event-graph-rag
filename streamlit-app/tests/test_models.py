import pytest
from pydantic import ValidationError
from models.schema import VideoObject, VideoEvent, RAGResponse, ChatMessage

SAMPLE_RAG_JSON = {
    "objects": [
        {
            "obj_id": "person_01", "category": "person", "first_seen_frame": 0,
            "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
            "attributes": {"pose": "standing", "orientation": "upright"}
        },
        {
            "obj_id": "cup_01", "category": "cup", "first_seen_frame": 3,
            "first_seen_timestamp": "2024-01-15T10:23:45.100Z",
            "attributes": {"color": "red", "material": "ceramic"}
        },
    ],
    "events": [
        {
            "event_id": "evt_001", "frame": 5, "timestamp": "2024-01-15T10:23:45.167Z",
            "action": "pick_up",
            "agent": "person_01", "target": "cup_01",
            "source": "table_01", "destination": None
        }
    ]
}


# --- VideoObject ---

def test_T1_01_video_object_valid():
    obj = VideoObject(
        obj_id="person_01",
        category="person",
        first_seen_frame=0,
        first_seen_timestamp="2024-01-15T10:23:45.000Z",
        attributes={"pose": "standing"}
    )
    assert obj.obj_id == "person_01"
    assert obj.category == "person"
    assert obj.first_seen_frame == 0
    assert obj.first_seen_timestamp == "2024-01-15T10:23:45.000Z"
    assert obj.attributes == {"pose": "standing"}


def test_T1_02_video_object_arbitrary_attributes():
    obj = VideoObject(
        obj_id="x",
        category="thing",
        first_seen_frame=1,
        first_seen_timestamp="2024-01-15T10:00:00.000Z",
        attributes={"unknown_key": 42, "another": True, "nested": {"a": 1}}
    )
    assert obj.attributes["unknown_key"] == 42
    assert obj.attributes["another"] is True
    assert obj.attributes["nested"] == {"a": 1}


def test_T1_03_video_object_missing_obj_id():
    with pytest.raises(ValidationError):
        VideoObject(
            category="person",
            first_seen_frame=0,
            first_seen_timestamp="2024-01-15T10:00:00.000Z",
            attributes={}
        )


def test_T1_04_video_object_first_seen_frame_as_string():
    # pydantic v2 coerces "5" -> 5 by default
    try:
        obj = VideoObject(
            obj_id="x",
            category="thing",
            first_seen_frame="5",  # type: ignore
            first_seen_timestamp="2024-01-15T10:00:00.000Z",
            attributes={}
        )
        assert obj.first_seen_frame == 5  # coerced to int
    except ValidationError:
        pass  # also acceptable


def test_T1_04b_video_object_first_seen_timestamp_iso8601():
    obj = VideoObject(
        obj_id="cup_01",
        category="cup",
        first_seen_frame=3,
        first_seen_timestamp="2024-01-15T10:23:45.100Z",
        attributes={}
    )
    assert obj.first_seen_timestamp == "2024-01-15T10:23:45.100Z"


def test_T1_04c_video_object_missing_first_seen_timestamp():
    with pytest.raises(ValidationError):
        VideoObject(
            obj_id="x",
            category="thing",
            first_seen_frame=0,
            attributes={}
        )


# --- VideoEvent ---

def test_T1_05_video_event_minimal():
    evt = VideoEvent(
        event_id="evt_001",
        frame=5,
        timestamp="2024-01-15T10:23:45.167Z",
        action="pick_up",
        agent="person_01",
        target="cup_01"
    )
    assert evt.source is None
    assert evt.destination is None


def test_T1_06_video_event_source_string():
    evt = VideoEvent(
        event_id="evt_001",
        frame=5,
        timestamp="2024-01-15T10:23:45.167Z",
        action="pick_up",
        agent="person_01",
        target="cup_01",
        source="table_01"
    )
    assert evt.source == "table_01"


def test_T1_07_video_event_destination_omitted():
    evt = VideoEvent(
        event_id="evt_001",
        frame=5,
        timestamp="2024-01-15T10:23:45.167Z",
        action="pick_up",
        agent="person_01",
        target="cup_01"
    )
    assert evt.destination is None


def test_T1_08_video_event_missing_frame():
    with pytest.raises(ValidationError):
        VideoEvent(
            event_id="evt_001",
            timestamp="2024-01-15T10:23:45.167Z",
            action="pick_up",
            agent="person_01",
            target="cup_01"
        )


def test_T1_08b_video_event_timestamp_iso8601():
    evt = VideoEvent(
        event_id="evt_001",
        frame=5,
        timestamp="2024-01-15T10:23:45.167Z",
        action="pick_up",
        agent="person_01",
        target="cup_01"
    )
    assert evt.timestamp == "2024-01-15T10:23:45.167Z"


def test_T1_08c_video_event_missing_timestamp():
    with pytest.raises(ValidationError):
        VideoEvent(
            event_id="evt_001",
            frame=5,
            action="pick_up",
            agent="person_01",
            target="cup_01"
        )


# --- RAGResponse ---

def test_T1_09_rag_response_sample_json():
    rag = RAGResponse(**SAMPLE_RAG_JSON)
    assert len(rag.objects) == 2
    assert len(rag.events) == 1
    assert rag.objects[0].obj_id == "person_01"
    assert rag.events[0].event_id == "evt_001"


def test_T1_10_rag_response_empty_lists():
    rag = RAGResponse(objects=[], events=[])
    assert rag.objects == []
    assert rag.events == []


def test_T1_11_rag_response_invalid_object():
    with pytest.raises(ValidationError):
        RAGResponse(
            objects=[{"category": "person"}],  # missing obj_id etc.
            events=[]
        )


# --- ChatMessage ---

def test_T1_12_chat_message_user():
    msg = ChatMessage(role="user", content="test")
    assert msg.role == "user"
    assert msg.content == "test"


def test_T1_13_chat_message_assistant_with_thinking_and_rag():
    rag = RAGResponse(**SAMPLE_RAG_JSON)
    msg = ChatMessage(
        role="assistant",
        content="Here is my analysis.",
        thinking="I should summarize the events.",
        raw_rag=rag
    )
    assert msg.role == "assistant"
    assert msg.thinking == "I should summarize the events."
    assert msg.raw_rag is not None
    assert len(msg.raw_rag.objects) == 2


def test_T1_14_chat_message_optional_fields_default_none():
    msg = ChatMessage(role="user", content="hello")
    assert msg.thinking is None
    assert msg.raw_rag is None


def test_T1_15_chat_message_invalid_role():
    # role is Literal["user", "assistant"], so invalid value raises ValidationError
    with pytest.raises(ValidationError):
        ChatMessage(role="system", content="test")  # type: ignore
