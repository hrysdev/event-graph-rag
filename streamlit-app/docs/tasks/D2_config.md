# D2: 設定管理

## 参照ドキュメント
- `docs/technical_spec.md` § 2 (設定管理)

## 作業概要
環境変数を一元管理する `config.py` と、設定値の雛形 `.env.example` を作成する。

## 実装仕様

### ファイル: `config.py`

`python-dotenv` を使い、プロジェクトルートの `.env` を読み込む。
以下の変数をすべてサポートすること。

| 変数名 | 型 | デフォルト値 | 説明 |
|---|---|---|---|
| `VLLM_BASE_URL` | str | `http://localhost:8000/v1` | vLLMサーバーURL |
| `VLLM_MODEL_NAME` | str | `qwen3.5-plus` | モデル識別子 |
| `RAG_API_URL` | str | `http://localhost:9000/query` | RAGエンドポイント |
| `RAG_API_TIMEOUT` | int | `30` | RAG APIタイムアウト(秒) |
| `LLM_TEMPERATURE` | float | `0.6` | 生成温度 |
| `LLM_MAX_TOKENS` | int | `4096` | 最大生成トークン数 |
| `ENABLE_THINKING` | bool | `True` | Thinkingモード有効/無効 |

実装パターン（Pydantic Settings を推奨）:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    vllm_base_url: str = "http://localhost:8000/v1"
    # ... 他フィールド

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
```

`pydantic-settings` が利用不可の場合は `os.getenv` + デフォルト値で代替してよい。

### ファイル: `.env.example`

実際の値を含まないテンプレートとして以下を記載する。
```
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=qwen3.5-plus
RAG_API_URL=http://localhost:9000/query
RAG_API_TIMEOUT=30
LLM_TEMPERATURE=0.6
LLM_MAX_TOKENS=4096
ENABLE_THINKING=true
```

## 実装上の注意
- `.env` ファイル自体は作成しない (`.env.example` のみ作成する)。
- `ENABLE_THINKING` は文字列 `"true"` / `"false"` を bool に変換すること。
- `config.py` は副作用なしで import できること（モジュールロード時に外部接続しない）。
- `.gitignore` に `.env` が含まれていない場合は追記する。

## 完了条件
- `python -c "from config import settings; print(settings.vllm_base_url)"` が
  デフォルト値を出力してエラーなく終了する。
- `.env.example` が存在し、全変数の雛形が記載されている。
