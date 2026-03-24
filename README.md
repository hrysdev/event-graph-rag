# Video-RAG

空間イベント記憶の RAG システム。JSONL / 西川JSON からイベントを取り込み、FAISS + NetworkX で検索・グラフ展開して返す。

## Quick Start

```bash
# 依存インストール
uv sync --all-extras

# テスト
uv run pytest -v
```

### 1. インデックス構築

初回は ruri-v3 モデル (~1.2GB) のダウンロードあり。ファイル単体でもディレクトリでもOK。

```bash
uv run python scripts/ingest.py \
  --input ../../data/annotations/ \
  --output ../tmp/video-rag-index/
```

### 2. サーバー起動

```bash
uv run python scripts/serve.py --index ../tmp/video-rag-index/
# デフォルト: http://0.0.0.0:9000
```

### 3. リクエスト例

CLIスクリプト:

```bash
uv run python scripts/test_query.py --query "スマートフォンを使った"
```

curl:

```bash
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "スマートフォンを使った"}'
```

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/query` | クエリ → RAGResponse (objects + events) |
| POST | `/ingest` | JSONLファイルアップロード → インデックス再構築 |
| GET | `/status` | ノード数・エッジ数・チャンク数 |

## 対応フォーマット

| 形式 | 拡張子 | 説明 |
|------|--------|------|
| JSONL | `.jsonl` | 1行1 EventGraph |
| 西川JSON | `.json` | `clips[]` 配列を含む単一JSON |

`--input` にファイルを渡すと拡張子で自動判定、ディレクトリを渡すと配下の `.json` / `.jsonl` を全て読み込む。
