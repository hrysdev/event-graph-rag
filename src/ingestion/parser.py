"""イベントパーサー: JSONL / 西川JSON → EventGraph リスト."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from src.models.event import DetectedObject, Event, EventGraph


def parse(path: str | Path) -> list[EventGraph]:
    """ファイルまたはディレクトリをパースし EventGraph のリストを返す.

    ディレクトリを渡すと配下の ``.json`` / ``.jsonl`` を全て読み込む.
    ファイルの場合は拡張子で形式を判定:
    - ``.json``  → 西川形式 (単一JSONに ``clips[]`` 配列)
    - ``.jsonl`` → 従来形式 (1行1 EventGraph)
    """
    path = Path(path)

    if path.is_dir():
        files = sorted(
            f for f in path.iterdir() if f.suffix in (".json", ".jsonl")
        )
        logger.info("ディレクトリ検出: {} ファイル ({})", len(files), path)
        graphs: list[EventGraph] = []
        for f in files:
            graphs.extend(_parse_file(f))
        return graphs

    return _parse_file(path)


def _parse_file(path: Path) -> list[EventGraph]:
    """単一ファイルをパース."""
    if path.suffix == ".json":
        return _parse_nishikawa_json(path)
    return _parse_jsonl(path)


# ── 従来 JSONL 形式 ──────────────────────────────────────────


def _parse_jsonl(path: Path) -> list[EventGraph]:
    """JSONLファイルをパースし EventGraph のリストを返す.

    不正な行はスキップしてログに記録する.
    """
    graphs: list[EventGraph] = []

    with path.open(encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                graphs.append(EventGraph.model_validate(data))
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("行 {} をスキップ: {}", line_num, e)

    logger.info("パース完了: {} レコード読み込み ({})", len(graphs), path.name)
    return graphs


# ── 西川 JSON 形式 ───────────────────────────────────────────


def _parse_nishikawa_json(path: Path) -> list[EventGraph]:
    """西川形式の単一JSONをパースし EventGraph のリストを返す.

    各クリップを1つの EventGraph に変換する.
    events が空のクリップはスキップする.
    """
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    source_fps: float = data["video_metadata"]["source_fps"]
    video_start = datetime.fromisoformat(data["video_metadata"]["video_start_time"])

    graphs: list[EventGraph] = []

    for clip in data["clips"]:
        events_raw = clip.get("events", [])
        if not events_raw:
            continue

        meta = clip["clip_metadata"]
        clip_index: int = meta["clip_index"]

        start_time_str = meta.get("start_time", "")
        if not start_time_str:
            logger.warning(
                "クリップ {} をスキップ (start_time が空): {}",
                clip_index, path.name,
            )
            continue
        clip_start = datetime.fromisoformat(start_time_str)

        frame_indices: list[int] = meta.get("frame_indices", [])
        first_frame = frame_indices[0] if frame_indices else 0

        # ── オブジェクト変換 ──
        objects: list[DetectedObject] = []
        for obj in clip.get("objects", []):
            obj_frame: int = obj["first_seen_frame"]
            obj_ts = _frame_to_timestamp(
                obj_frame, first_frame, source_fps, video_start, clip_start,
            )
            objects.append(
                DetectedObject(
                    obj_id=obj["obj_id"],
                    category=obj["category"],
                    first_seen_frame=obj_frame,
                    first_seen_timestamp=obj_ts,
                    attributes=obj.get("attributes", {}),
                )
            )

        # ── イベント変換 ──
        events: list[Event] = []
        for evt in events_raw:
            frame: int = evt["frame"]
            ts = _frame_to_timestamp(
                frame, first_frame, source_fps, video_start, clip_start,
            )
            unique_id = f"clip{clip_index:03d}_{evt['event_id']}"
            events.append(
                Event(
                    event_id=unique_id,
                    frame=frame,
                    timestamp=ts,
                    action=evt["action"],
                    agent=evt["agent"],
                    target=evt["target"],
                    source=evt.get("source"),
                    destination=evt.get("destination"),
                )
            )

        graphs.append(EventGraph(objects=objects, events=events))

    logger.info(
        "パース完了: {} クリップ読み込み ({})", len(graphs), path.name,
    )
    return graphs


def _frame_to_timestamp(
    frame: int,
    first_frame: int,
    source_fps: float,
    video_start: datetime,
    clip_start: datetime,
) -> str:
    """フレーム番号をISO形式のタイムスタンプに変換.

    frame >= first_frame の場合、動画先頭からの絶対フレーム番号とみなす.
    それ以外はクリップ先頭からの相対フレーム番号とみなす.
    """
    if frame >= first_frame and first_frame > 0:
        ts = video_start + timedelta(seconds=frame / source_fps)
    else:
        ts = clip_start + timedelta(seconds=frame / source_fps)
    return ts.isoformat()
