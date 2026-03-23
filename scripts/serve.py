"""CLI: サーバー起動.

Usage:
    python scripts/serve.py --index <dir> --port 9000
"""

from __future__ import annotations

import argparse

import uvicorn
from loguru import logger

from src.dependencies import AppState, get_embedder, set_state
from src.server.app import app
from src.store.persistence import load


def main() -> None:
    parser = argparse.ArgumentParser(description="Video-RAG: APIサーバー起動")
    parser.add_argument("--index", required=True, help="インデックスディレクトリパス")
    parser.add_argument("--port", type=int, default=9000, help="ポート番号 (default: 9000)")
    parser.add_argument("--host", default="0.0.0.0", help="ホスト (default: 0.0.0.0)")
    args = parser.parse_args()

    # インデックス読み込み → ステートにアトミックにセット
    logger.info("インデックス読み込み中: {}", args.index)
    graph, vector_store, metadata = load(args.index)
    set_state(AppState(graph=graph, vector_store=vector_store, metadata=metadata))

    # embedder を事前ロード
    get_embedder()

    logger.info("サーバー起動: {}:{}", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
