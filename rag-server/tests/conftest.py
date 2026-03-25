"""テスト用共通フィクスチャ."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ingestion.parser import parse
from src.models.event import EventGraph

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_JSONL = FIXTURES_DIR / "sample_events.jsonl"
SAMPLE_NISHIKAWA = FIXTURES_DIR / "sample_nishikawa.json"


@pytest.fixture
def sample_jsonl_path() -> Path:
    return SAMPLE_JSONL


@pytest.fixture
def sample_nishikawa_path() -> Path:
    return SAMPLE_NISHIKAWA


@pytest.fixture
def sample_graphs() -> list[EventGraph]:
    return parse(SAMPLE_JSONL)


@pytest.fixture
def sample_nishikawa_graphs() -> list[EventGraph]:
    return parse(SAMPLE_NISHIKAWA)
