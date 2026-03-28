# Event Graph RAG

映像イベントグラフに対する自然言語検索 (RAG) システム。

## 概要

Event Graph RAG は、映像から抽出された構造化イベントデータ (EventGraph JSON) に対して、自然言語で質問・検索できる RAG (Retrieval-Augmented Generation) システムです。

EventGraph JSON は、上流プロジェクト **[event-graph-generation](https://github.com/ChanYu1224/event-graph-generation)** によって生成されます。event-graph-generation は V-JEPA による映像特徴抽出、Qwen VL による合成アノテーション生成、DETR スタイルのイベントデコーダを組み合わせ、映像から「誰が・何を・どこで・いつ」行ったかをグラフ構造として出力します。

```
映像 ──→ event-graph-generation ──→ EventGraph JSON ──→ Event Graph RAG ──→ 自然言語Q&A
         (映像からイベント抽出)        (objects + events)    (検索 + 対話)
```

本システムは、この EventGraph JSON を取り込み、ベクトル検索とグラフ展開で関連情報を検索し、LLM を用いて自然言語で回答します。

## システム構成

```
┌──────────────────────────────────────────────────────────────┐
│                      Event Graph RAG                         │
│                                                              │
│  ┌──────────────────┐         ┌────────────────────────┐    │
│  │  streamlit-app    │  POST   │      rag-server         │    │
│  │  (port 8501)      │────────→│      (port 9000)        │    │
│  │                   │ /query  │                         │    │
│  │  Streamlit UI     │←────────│  FastAPI                │    │
│  │  + vLLM 連携      │ objects │  FAISS + NetworkX       │    │
│  │                   │ +events │                         │    │
│  └────────┬──────────┘         └───────────┬─────────────┘    │
│           │                                │                 │
│           ▼                                ▼                 │
│     vLLM Server                   EventGraph JSON           │
│   (Qwen3.5-35B-A3B)          (event-graph-generation 出力)  │
│     port 8000                                                │
└──────────────────────────────────────────────────────────────┘
```

- **rag-server** — FastAPI バックエンド。EventGraph JSON/JSONL をインジェストし、NetworkX MultiDiGraph (objects=ノード, events=エッジ) を構築。ruri-v3-310m (日本語最適化 Sentence Transformers) でベクトル化し、FAISS でインデックス。クエリに対してベクトル検索 → 類似度フィルタ → グラフ展開で関連オブジェクト・イベントを返却。
- **streamlit-app** — Streamlit チャット UI。ユーザーの質問を RAG サーバーに送り、取得したコンテキストでプロンプトを構築し、vLLM (OpenAI 互換 API) からストリーミング回答を生成・表示。

## 主な機能

- EventGraph JSON/JSONL のインジェスト (ファイル単体・ディレクトリ一括対応)
- 日本語最適化 embedding ([ruri-v3-310m](https://huggingface.co/cl-nagoya/ruri-v3-310m)) によるベクトル検索
- NetworkX グラフ展開による関連イベントの自動取得
- 時間表現の自然言語解析 ("過去3時間" 等によるフィルタリング)
- vLLM + Qwen3.5 によるストリーミング LLM 回答
- LLM 思考プロセスの折りたたみ表示 (`<think>` タグ対応)
- サイドバーでの RAG 検索結果 (生データ) 表示
- 開発用モック RAG サーバー (`mock_rag_server.py`)

## ディレクトリ構成

```
event-graph-rag/
├── README.md
├── LICENSE
├── rag-server/                    # RAG 検索サーバ
│   ├── pyproject.toml             # uv 依存管理
│   ├── scripts/
│   │   ├── ingest.py              # インデックス構築 CLI
│   │   ├── serve.py               # サーバー起動 CLI
│   │   └── test_query.py          # テストクエリ CLI
│   ├── src/
│   │   ├── config.py              # 設定 (VRAG_* 環境変数)
│   │   ├── dependencies.py        # FastAPI DI 管理
│   │   ├── server/app.py          # API エンドポイント
│   │   ├── ingestion/             # JSON/JSONL パーサー + パイプライン
│   │   ├── graph/                 # NetworkX グラフ構築・走査
│   │   ├── store/                 # Embedder + FAISS + 永続化
│   │   ├── retrieval/             # 検索エンジン
│   │   └── models/                # Pydantic モデル
│   └── tests/
└── streamlit-app/                 # チャット UI
    ├── app.py                     # Streamlit エントリーポイント
    ├── config.py                  # 設定管理 (.env)
    ├── mock_rag_server.py         # 開発用モック RAG サーバー
    ├── requirements.txt           # pip 依存
    ├── core/                      # RAG クライアント + LLM クライアント + チェーン
    ├── models/                    # Pydantic スキーマ
    ├── ui/                        # UI コンポーネント
    └── tests/
```

## 前提条件

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (rag-server の依存管理)
- vLLM サーバー (Qwen3.5-35B-A3B 等の LLM を提供)
- EventGraph JSON データ ([event-graph-generation](https://github.com/ChanYu1224/event-graph-generation) の出力)

> **Note:** 初回の `ingest.py` 実行時に ruri-v3-310m モデル (~1.2GB) が自動ダウンロードされます。

## クイックスタート

### 1. RAG サーバーのセットアップ

```bash
cd rag-server
uv sync --all-extras
```

### 2. インデックス構築

```bash
uv run python scripts/ingest.py \
  --input <EventGraph JSON ファイルまたはディレクトリ> \
  --output ./tmp/video-rag-index/
```

`--input` にファイルを渡すと拡張子で自動判定、ディレクトリを渡すと配下の `.json` / `.jsonl` を全て読み込みます。

### 3. RAG サーバー起動

```bash
uv run python scripts/serve.py --index ./tmp/video-rag-index/
# http://0.0.0.0:9000
```

### 4. Streamlit アプリのセットアップ

```bash
cd streamlit-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env を編集して各サーバーの URL を設定
```

### 5. vLLM サーバー起動

```bash
vllm serve Qwen/Qwen3.5-35B-A3B --host 0.0.0.0 --port 8000

# VRAM を節約する場合は fp8 量子化
vllm serve Qwen/Qwen3.5-35B-A3B --quantization fp8 --host 0.0.0.0 --port 8000
```

### 6. Streamlit アプリ起動

```bash
streamlit run app.py
# http://localhost:8501
```

### 開発用モックサーバー

vLLM や実際の RAG サーバーなしで UI 開発を行う場合:

```bash
cd streamlit-app
python mock_rag_server.py
# port 9000 で固定サンプルデータを返すモックが起動
```

## API リファレンス

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/query` | 自然言語クエリ → RAGResponse (objects + events) |
| POST | `/ingest` | JSONL ファイルアップロード → インデックス再構築 |
| GET | `/status` | インデックス状態 (ノード数, エッジ数, チャンク数) |

### POST /query

**リクエスト:**

```bash
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "スマートフォンを使った"}'
```

**レスポンス:**

```json
{
  "objects": [
    {
      "obj_id": "person_01",
      "category": "person",
      "first_seen_frame": 0,
      "first_seen_timestamp": "2026-03-21T10:00:00",
      "attributes": {}
    }
  ],
  "events": [
    {
      "event_id": "evt_001",
      "frame": 50,
      "timestamp": "2026-03-21T10:00:05",
      "action": "pick_up",
      "agent": "person_01",
      "target": "smartphone_01",
      "source": "desk_01",
      "destination": null
    }
  ]
}
```

CLI スクリプトでも確認可能:

```bash
cd rag-server
uv run python scripts/test_query.py --query "スマートフォンを使った"
```

## 対応入力フォーマット

| 形式 | 拡張子 | 説明 |
|------|--------|------|
| JSONL | `.jsonl` | 1行1 EventGraph |
| JSON | `.json` | `clips[]` 配列を含む単一 JSON ([event-graph-generation](https://github.com/ChanYu1224/event-graph-generation) 出力形式) |

## 環境変数

### rag-server (`VRAG_*` プレフィックス)

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VRAG_EMBEDDING_MODEL` | `cl-nagoya/ruri-v3-310m` | Embedding モデル名 |
| `VRAG_SIMILARITY_THRESHOLD` | `0.7` | 類似度閾値 |
| `VRAG_TOP_K` | `10` | FAISS 検索の上位件数 |
| `VRAG_MAX_EXPANDED_EVENTS` | `50` | グラフ展開の最大イベント数 |
| `VRAG_PORT` | `9000` | サーバーポート |

### streamlit-app (`.env` ファイル)

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | vLLM サーバー URL |
| `VLLM_MODEL_NAME` | `qwen3.5-plus` | モデル名 |
| `RAG_API_URL` | `http://localhost:9000/query` | RAG サーバー URL |
| `RAG_API_TIMEOUT` | `30` | タイムアウト (秒) |
| `LLM_TEMPERATURE` | `0.6` | 生成温度 |
| `LLM_MAX_TOKENS` | `4096` | 最大トークン数 |
| `ENABLE_THINKING` | `true` | 思考プロセス表示 |

## テスト

```bash
# rag-server
cd rag-server
uv run pytest -v

# streamlit-app
cd streamlit-app
pytest tests/
```

## 技術詳細

### 1. インジェスト

EventGraph JSON/JSONL → パース → NetworkX MultiDiGraph 構築 (objects=ノード, events=エッジ) → イベントを日本語テキストに変換 → ruri-v3-310m でベクトル化 → FAISS インデックス構築 → ディスク保存

### 2. 検索

クエリテキスト → 時間表現解析 → ruri-v3-310m でベクトル化 → FAISS 類似度検索 (top-k) → 類似度閾値フィルタ → 時間範囲フィルタ → グラフ展開 (関連オブジェクトの全イベント取得) → RAGResponse 返却

### 3. 回答生成

ユーザー質問 + RAGResponse → プロンプト構築 (objects + events をコンテキストとして整形) → vLLM ストリーミング推論 → thinking/answer 分離 → UI 表示

## 関連プロジェクト

- **[event-graph-generation](https://github.com/ChanYu1224/event-graph-generation)** — 映像から構造化イベントグラフを自動生成するディープラーニングフレームワーク。V-JEPA 2.1 による映像特徴抽出、Qwen 3.5 VL による合成アノテーション生成、DETR スタイルの Event Decoder (10-15M パラメータ) を組み合わせ、EventGraph JSON を出力します。本システムの入力データを生成する上流プロジェクトです。

## ライセンス

[MIT License](LICENSE) - Copyright (c) 2026 HrysDev, Kannlight, ChanYu1224
