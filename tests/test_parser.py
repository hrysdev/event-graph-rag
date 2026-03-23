"""イベントパーサーのテスト."""

from __future__ import annotations

from pathlib import Path

from src.ingestion.parser import parse
from src.models.event import EventGraph


def test_parse_normal(sample_jsonl_path: Path) -> None:
    """正常なJSONLをパースできる."""
    graphs = parse(sample_jsonl_path)

    assert len(graphs) == 5
    assert all(isinstance(g, EventGraph) for g in graphs)

    # 最初のレコードの検証
    first = graphs[0]
    assert len(first.objects) == 3
    assert len(first.events) == 2
    assert first.objects[0].obj_id == "person_01"
    assert first.events[0].event_id == "evt_001"
    assert first.events[0].action == "pick_up"


def test_parse_total_events(sample_jsonl_path: Path) -> None:
    """全レコード合計のイベント数が正しい."""
    graphs = parse(sample_jsonl_path)
    total_events = sum(len(g.events) for g in graphs)
    assert total_events == 9


def test_parse_skips_invalid_lines(tmp_path: Path) -> None:
    """不正な行をスキップし、有効な行のみパースする."""
    content = (
        '{"objects": [], "events": []}\n'
        "this is not json\n"
        '{"objects": [], "events": []}\n'
    )
    f = tmp_path / "invalid.jsonl"
    f.write_text(content)
    graphs = parse(f)

    assert len(graphs) == 2


def test_parse_empty_file(tmp_path: Path) -> None:
    """空ファイルは空リストを返す."""
    f = tmp_path / "empty.jsonl"
    f.write_text("")
    graphs = parse(f)

    assert graphs == []


def test_parse_event_fields(sample_jsonl_path: Path) -> None:
    """イベントのsource/destinationフィールドが正しくパースされる."""
    graphs = parse(sample_jsonl_path)

    # evt_001: source=table_01, destination=None
    evt_001 = graphs[0].events[0]
    assert evt_001.source == "table_01"
    assert evt_001.destination is None

    # evt_003: source=None, destination=shelf_01
    evt_003 = graphs[1].events[0]
    assert evt_003.source is None
    assert evt_003.destination == "shelf_01"


# ── 西川JSON形式のテスト ─────────────────────────────────────


def test_nishikawa_parse(sample_nishikawa_path: Path) -> None:
    """西川JSON形式を正しくパースできる."""
    graphs = parse(sample_nishikawa_path)

    # 3クリップ中、events が空の clip_index=1 はスキップ → 2件
    assert len(graphs) == 2
    assert all(isinstance(g, EventGraph) for g in graphs)

    # clip 0: 3 objects, 2 events
    assert len(graphs[0].objects) == 3
    assert len(graphs[0].events) == 2
    assert graphs[0].events[0].action == "pick_up"
    assert graphs[0].events[1].action == "use"

    # clip 2: 2 objects, 1 event
    assert len(graphs[1].objects) == 2
    assert len(graphs[1].events) == 1
    assert graphs[1].events[0].action == "inspect"


def test_nishikawa_timestamp_calculation(sample_nishikawa_path: Path) -> None:
    """timestamp が frame / source_fps から正確に計算される."""
    graphs = parse(sample_nishikawa_path)

    # clip 0 (first_frame=0): frame は相対 → clip_start + frame/source_fps
    # frame=30, source_fps=10 → 10:00:00 + 3s = 10:00:03
    assert graphs[0].events[0].timestamp == "2025-12-09T10:00:03"
    # frame=80, source_fps=10 → 10:00:00 + 8s = 10:00:08
    assert graphs[0].events[1].timestamp == "2025-12-09T10:00:08"

    # clip 2 (first_frame=200): frame=250 >= 200 → 絶対フレーム
    # video_start + 250/10 = 10:00:00 + 25s = 10:00:25
    assert graphs[1].events[0].timestamp == "2025-12-09T10:00:25"


def test_nishikawa_unique_event_ids(sample_nishikawa_path: Path) -> None:
    """event_id がクリップ間でユニーク化される."""
    graphs = parse(sample_nishikawa_path)

    all_ids = [e.event_id for g in graphs for e in g.events]
    # clip 0 の evt_001 → clip000_evt_001
    assert "clip000_evt_001" in all_ids
    assert "clip000_evt_002" in all_ids
    # clip 2 の evt_001 → clip002_evt_001 (重複なし)
    assert "clip002_evt_001" in all_ids
    # 全IDがユニーク
    assert len(all_ids) == len(set(all_ids))


def test_nishikawa_skips_empty_clips(tmp_path: Path) -> None:
    """events が空のクリップはスキップされる."""
    import json

    data = {
        "video_id": "test",
        "video_metadata": {
            "video_start_time": "2025-01-01T00:00:00",
            "source_fps": 10.0,
            "target_fps": 1.0,
        },
        "clips": [
            {
                "objects": [],
                "events": [],
                "clip_metadata": {
                    "clip_index": 0,
                    "frame_indices": [0, 10],
                    "start_time": "2025-01-01T00:00:00",
                    "end_time": "2025-01-01T00:00:01",
                    "start_offset_sec": 0.0,
                    "end_offset_sec": 1.0,
                    "status": "motion_filtered",
                },
            },
            {
                "objects": [],
                "events": [],
                "clip_metadata": {
                    "clip_index": 1,
                    "frame_indices": [10, 20],
                    "start_time": "2025-01-01T00:00:01",
                    "end_time": "2025-01-01T00:00:02",
                    "start_offset_sec": 1.0,
                    "end_offset_sec": 2.0,
                    "status": "motion_filtered",
                },
            },
        ],
    }
    f = tmp_path / "all_empty.json"
    f.write_text(json.dumps(data))
    graphs = parse(f)

    assert graphs == []
