# T2: 設定管理 テスト

## 対象工程
D2: 設定管理

## テスト対象ファイル
- `config.py`

## 前提
- `config.py` と `.env.example` が実装済みであること。
- テストエージェントは `config.py` を **読むが変更しない**。
- `.env` ファイルが存在しない状態でテストを実行すること（環境変数は `monkeypatch` で注入する）。

## テストケース一覧

| テストID | 内容 |
|---|---|
| T2-01 | 環境変数を設定しない状態でデフォルト値が返る（全フィールド） |
| T2-02 | `VLLM_BASE_URL` を任意の文字列に上書きしたとき、その値が返る |
| T2-03 | `RAG_API_TIMEOUT` を文字列 "60" で設定したとき、int 60 として返る |
| T2-04 | `LLM_TEMPERATURE` を "0.9" で設定したとき、float 0.9 として返る |
| T2-05 | `ENABLE_THINKING` を "false" で設定したとき、bool False として返る |
| T2-06 | `ENABLE_THINKING` を "true" で設定したとき、bool True として返る |
| T2-07 | `config` モジュールの import が副作用なしで行える（外部接続しない） |

## テストファイル

### `tests/test_config.py`

実装パターンに応じてテスト方法を選択すること。

**`pydantic-settings` を使った実装の場合:**
```python
import pytest
from pydantic_settings import BaseSettings

def test_default_values(monkeypatch):
    # 環境変数をクリアして Settings を再生成する
    # pydantic-settings は再インポートではなく再インスタンス化でテストする
    monkeypatch.delenv("VLLM_BASE_URL", raising=False)
    # ... 他の変数も削除
    from config import Settings
    s = Settings()
    assert s.vllm_base_url == "http://localhost:8000/v1"
    # ... 他フィールドも検証
```

**`os.getenv` を使った実装の場合:**
```python
import importlib
import config

def test_custom_url(monkeypatch):
    monkeypatch.setenv("VLLM_BASE_URL", "http://custom:1234/v1")
    importlib.reload(config)
    assert config.settings.vllm_base_url == "http://custom:1234/v1"
```

実際の実装方法に合わせてテストを調整すること。

## 実行コマンド
```bash
pytest tests/test_config.py -v
```

## 合格条件
- 全テストがパスすること。
- `.env` ファイルの有無によらず、`monkeypatch` 経由で設定を制御できること。

---

## フィードバック（テストエージェントが記入）

> 不備が発見された場合はここに記載する。
