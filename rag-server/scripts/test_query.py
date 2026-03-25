"""CLI: 手動テスト用クエリ送信.

Usage:
    python scripts/test_query.py --query "赤いカップはどこ？"
    python scripts/test_query.py --query "赤いカップはどこ？" --url http://localhost:9000/query
"""

from __future__ import annotations

import argparse
import json

import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(description="Video-RAG: テストクエリ送信")
    parser.add_argument("--query", required=True, help="検索クエリ")
    parser.add_argument("--url", default="http://localhost:9000/query", help="APIエンドポイント")
    args = parser.parse_args()

    data = json.dumps({"query": args.query}).encode("utf-8")
    req = urllib.request.Request(
        args.url,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
