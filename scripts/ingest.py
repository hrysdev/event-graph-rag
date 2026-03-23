"""CLI: JSONLからインデックスを構築.

Usage:
    python scripts/ingest.py --input <jsonl> --output <dir>
"""

from __future__ import annotations

import argparse

from src.ingestion.pipeline import ingest
from src.store.embedder import Embedder


def main() -> None:
    parser = argparse.ArgumentParser(description="Video-RAG: JSONLからインデックスを構築")
    parser.add_argument("--input", required=True, help="入力JSONLファイルパス")
    parser.add_argument("--output", required=True, help="出力ディレクトリパス")
    parser.add_argument(
        "--model",
        default="cl-nagoya/ruri-v3-310m",
        help="Embeddingモデル名 (default: cl-nagoya/ruri-v3-310m)",
    )
    args = parser.parse_args()

    embedder = Embedder(model_name=args.model)
    ingest(args.input, args.output, embedder)


if __name__ == "__main__":
    main()
