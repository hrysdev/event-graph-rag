# 実装計画 — 全体作業フロー

## 前提
- 仕様書: `docs/requirements.md`
- 技術仕様: `docs/technical_spec.md`
- 各工程の詳細作業指示は `docs/tasks/` 以下に個別マークダウンとして存在する。
- **開発工程とテスト工程は別エージェントが担当する。**
  テスト工程のエージェントは対応する開発工程の成果物のみを読み、独立してテストを実装・実行する。

---

## 工程一覧

### 開発工程

| # | 工程名 | 作業指示ファイル | 依存工程 | 成果物 |
|---|---|---|---|---|
| D1 | データモデル定義 | `tasks/D1_models.md` | なし | `models/schema.py` |
| D2 | 設定管理 | `tasks/D2_config.md` | なし | `config.py`, `.env.example` |
| D3 | RAGクライアント | `tasks/D3_rag_client.md` | D1, D2 | `core/rag_client.py` |
| D4 | プロンプト設計 | `tasks/D4_prompt.md` | D1 | `core/prompt.py` |
| D5 | LLMクライアント | `tasks/D5_llm_client.md` | D2 | `core/llm_client.py` |
| D6 | LangChainチェーン | `tasks/D6_chain.md` | D3, D4, D5 | `core/chain.py` |
| D7 | UIコンポーネント | `tasks/D7_ui.md` | D1 | `ui/chat.py`, `ui/sidebar.py` |
| D8 | エントリポイント統合 | `tasks/D8_app.md` | D6, D7 | `app.py`, `requirements.txt` |

### テスト工程

| # | 工程名 | 作業指示ファイル | 依存工程 | 成果物 |
|---|---|---|---|---|
| T1 | データモデル テスト | `tasks/T1_test_models.md` | D1 | `tests/test_models.py` |
| T2 | 設定管理 テスト | `tasks/T2_test_config.md` | D2 | `tests/test_config.py` |
| T3 | RAGクライアント テスト | `tasks/T3_test_rag_client.md` | D3, T1, T2 | `tests/test_rag_client.py` |
| T4 | プロンプト設計 テスト | `tasks/T4_test_prompt.md` | D4, T1 | `tests/test_prompt.py` |
| T5 | LLMクライアント テスト | `tasks/T5_test_llm_client.md` | D5, T2 | `tests/test_llm_client.py` |
| T6 | LangChainチェーン テスト | `tasks/T6_test_chain.md` | D6, T3, T4, T5 | `tests/test_chain.py` |
| T7 | UIコンポーネント テスト | `tasks/T7_test_ui.md` | D7, T1 | `tests/test_ui.py` |
| T8 | E2E統合テスト | `tasks/T8_test_e2e.md` | D8, T6, T7 | `tests/test_e2e.py` |

---

## 依存グラフ

```
[D1: データモデル]        [D2: 設定管理]
        │                      │
        ▼                      ▼
      [T1]                   [T2]
        │                      │
        ├──────────────────────┤
        │                      │
        ▼                      ▼
[D3: RAGクライアント]    [D5: LLMクライアント]
[D4: プロンプト設計] ←───── T1 ──┤
        │                      │
        ▼                      ▼
      [T3]                   [T4]  [T5]
        └──────────┬──────────┘
                   ▼
         [D6: LangChainチェーン]    [D7: UIコンポーネント]
                   │                        │
                   ▼                        ▼
                 [T6]                     [T7]
                   └──────────┬───────────┘
                              ▼
                  [D8: エントリポイント統合]
                              │
                              ▼
                           [T8: E2E]
```

**並列実行可能な組み合わせ:**
- D1 と D2 は並列実行可。
- T1 と T2 は D1・D2 完了後に並列実行可。
- T1・T2 完了後: D3・D4・D5 を並列実行可。
- D3→T3、D4→T4、D5→T5 はそれぞれ独立して進行可。
- D7 は T1 完了後に D6 と並列実行可。
- T3・T4・T5 完了後に D6 を開始。D6→T6、D7→T7 は並列進行可。
- T6・T7 完了後に D8、その後 T8。

---

## 各工程の概要

### D1: データモデル定義
RAGサーバーのJSONレスポンスおよびチャット履歴をPydanticで型定義する。後続の全工程が参照する基盤。

### T1: データモデル テスト
Pydanticモデルのバリデーション動作（正常系・異常系・省略可能フィールド）をpytestで検証する。
外部依存なしで実行できること。

### D2: 設定管理
`python-dotenv` で `.env` を読み込み、全モジュールから参照できる設定オブジェクトを実装する。

### T2: 設定管理 テスト
環境変数の読み込み・デフォルト値・型変換が正しく機能するかを検証する。
`monkeypatch` で環境変数を制御し、外部ファイル非依存で実行できること。

### D3: RAGクライアント
RAGサーバーへHTTPリクエストを投げ、レスポンスをPydanticモデルに変換して返す。
エラーは専用例外クラスとして raise する。

### T3: RAGクライアント テスト
`httpx` のモック (`respx` 等) を用いて実サーバー不要で正常系・各エラー系を検証する。

### D4: プロンプト設計
`RAGResponse` を自然言語テキストに変換する関数と LangChain `ChatPromptTemplate` を実装する。

### T4: プロンプト設計 テスト
変換関数の出力フォーマット・境界値（空リスト、null フィールド等）を検証する。

### D5: LLMクライアント
`openai` SDK で vLLM の OpenAI互換エンドポイントに接続する薄いラッパーを実装する。
ストリーミング応答のイテレータを返すインターフェースを定義する。

### T5: LLMクライアント テスト
`openai` SDK をモック化し、ストリーミング・非ストリーミング双方の応答処理を検証する。
実 vLLM サーバーへの接続は不要。

### D6: LangChainチェーン
D3〜D5 を統合し「RAGクエリ → プロンプト構築 → LLM推論 → Thinkingパース」を実装する。
`<think>` タグの分離ロジックを含む。

### T6: LangChainチェーン テスト
RAGクライアント・LLMクライアントをモック化し、チェーン全体のデータフローと
Thinkingパーサーの動作（タグあり・なし・複数タグ等）を検証する。

### D7: UIコンポーネント
Streamlitのチャット画面とサイドバーをコンポーネントとして実装する。
チェーン呼び出しはスタブで代替する。

### T7: UIコンポーネント テスト
`streamlit.testing.v1` の `AppTest` を用いて、セッションステートの初期化・
Thinkingトグル・リセットボタンの動作を検証する。

### D8: エントリポイント統合
`app.py` でチェーンとUIを接続し、ストリーミング表示・エラーハンドリングを組み込む。
`requirements.txt` を整備する。

### T8: E2E統合テスト
チェーンをモック化した状態で `AppTest` によりアプリ全体のフローを検証する。
「入力 → RAGクエリ → LLM応答表示 → 履歴追加 → リセット」の一連の動作を確認する。

---

## テスト方針

| 項目 | 方針 |
|---|---|
| テストフレームワーク | `pytest` |
| テストディレクトリ | `tests/` |
| 外部依存の扱い | 各テスト工程は実サーバーに依存しない。HTTPモックに `respx`、openai モックに `unittest.mock` を使用 |
| カバレッジ | 各テスト工程で対象モジュールのカバレッジ 80% 以上を目標とする |
| テスト工程の合格条件 | `pytest tests/test_<対象>.py` がすべてパスすること |
| 開発工程との分離 | テスト工程のエージェントは対応する開発工程の成果物コードを **読むが変更しない** 。修正が必要な場合は開発工程エージェントへフィードバックを記載したレポートを出力する |

---

## 完了定義

- `pytest tests/` がすべてパスする（T8 含む）。
- `streamlit run app.py` でアプリが起動する。
- チャット入力に対してRAGクエリが実行され、LLMの回答がストリーミング表示される。
- Thinkingトグルで思考プロセスの表示/非表示が切り替わる。
- サイドバーに直近のRAG取得JSONが表示される。
- 会話履歴がリセットボタンで初期化できる。
