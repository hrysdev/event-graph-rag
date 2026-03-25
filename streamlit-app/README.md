# optiBot - ビデオイベント・チャット

ビデオデータを解析し、物体の動きやイベントについて自然言語で質問できるチャットアプリケーション。

## 概要

RAG（検索拡張生成）とローカルLLM（vLLM）を組み合わせ、ビデオ内のオブジェクトやイベントに関する質問に回答します。

```
ユーザー質問 → RAGサーバー → プロンプト構築 → vLLM推論 → 回答
```

## 技術スタック

| 役割 | 技術 |
|------|------|
| フロントエンド | Streamlit |
| LLM | vLLM (Qwen 3.5-Plus、OpenAI互換API) |
| オーケストレーション | LangChain |
| HTTPクライアント | httpx |
| データバリデーション | Pydantic v2 |
| テスト | pytest, respx |

## ディレクトリ構成

```
optiBot/
├── app.py              # Streamlitエントリーポイント
├── config.py           # 設定管理
├── mock_rag_server.py  # 開発用モックRAGサーバー
├── requirements.txt    # 依存パッケージ
├── .env.example        # 環境変数テンプレート
├── core/               # コアロジック
│   ├── rag_client.py   # RAG APIクライアント
│   ├── llm_client.py   # vLLMクライアント
│   ├── chain.py        # パイプライン処理
│   └── prompt.py       # プロンプトテンプレート
├── models/
│   └── schema.py       # Pydanticスキーマ定義
├── ui/                 # UIコンポーネント
│   ├── chat.py         # チャット表示
│   └── sidebar.py      # サイドバー
├── tests/              # テストスイート
└── docs/               # 設計ドキュメント
```

## セットアップ

### 1. 仮想環境の作成と依存パッケージのインストール

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して各サーバーのURLを設定
```

**主な設定項目:**

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `VLLM_BASE_URL` | `http://localhost:8000/v1` | vLLMサーバーURL |
| `VLLM_MODEL_NAME` | `qwen3.5-plus` | モデル名 |
| `RAG_API_URL` | `http://localhost:9000/query` | RAGサーバーURL |
| `RAG_API_TIMEOUT` | `30` | タイムアウト（秒） |
| `LLM_TEMPERATURE` | `0.6` | 生成温度 |
| `LLM_MAX_TOKENS` | `4096` | 最大トークン数 |
| `ENABLE_THINKING` | `true` | 思考プロセスの表示 |

### 3. 外部サーバーの起動

#### vLLMサーバー

Qwen 3.5-Plus モデルをOpenAI互換APIで提供するサーバー。

```bash
source .env
vllm serve "$VLLM_MODEL_NAME" --host 0.0.0.0 --port 8000
```

#### RAGサーバー

ビデオ解析データを提供するサーバー（`POST /query`）。本番用RAGサーバーが未整備の場合は、付属のモックサーバーで代替できます。

**モックRAGサーバー (`mock_rag_server.py`)**

クエリ内容にかかわらず固定のサンプルデータ（人物・カップ・テーブルの物体と把持イベント）を返す開発用スクリプトです。追加の依存パッケージは不要です。

```bash
# デフォルトポート 9000 で起動（.env の RAG_API_URL と一致）
python mock_rag_server.py

# ポートを変更する場合
python mock_rag_server.py --port 9001
```

起動確認:

```bash
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "テスト"}'
# -> {"objects": [...], "events": [...]} が返れば OK
```

レスポンスのスキーマは `models/schema.py` の `RAGResponse` と同一です。

## 起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセス。

## テスト

```bash
pytest tests/
```

## 機能

- **チャットUI**: ストリーミング回答表示
- **思考プロセス表示**: LLMの `<think>` タグを折りたたみ表示
- **RAGデータ表示**: サイドバーで最新の検索結果をJSON表示
- **会話リセット**: サイドバーのボタンで会話履歴をクリア
