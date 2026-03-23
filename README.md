# Video-RAG

空間イベント記憶の RAG システム。JSONL / 西川JSON からイベントを取り込み、FAISS + NetworkX で検索・グラフ展開して返す。

## Quick Start

```bash
# 依存インストール
uv sync --all-extras

# テスト
uv run pytest -v

# インデックス構築 (初回は ruri-v3 モデル ~1.2GB のダウンロードあり)
uv run python scripts/ingest.py \
  --input <イベントJSONファイル> \
  --output /tmp/video-rag-index/

# サーバー起動 (port 9000)
uv run python scripts/serve.py --index /tmp/video-rag-index/

# クエリテスト (別ターミナル)
uv run python scripts/test_query.py --query "スマートフォンを使った"
```

## 対応フォーマット

| 形式 | 拡張子 | 説明 |
|------|--------|------|
| JSONL | `.jsonl` | 1行1 EventGraph |
| 西川JSON | `.json` | `clips[]` 配列を含む単一JSON |

`--input` に渡すファイルの拡張子で自動判定される。
