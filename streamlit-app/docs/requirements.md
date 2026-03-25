# ビデオイベント・チャット アプリケーション仕様書 (v1.0)

## 1. プロジェクト概要
長時間の動画から抽出された構造化データ（オブジェクト情報およびイベントログ）をRAG経由で取得し、ローカルLLMを用いて「物体の移動」「隠蔽」「状態変化」などの複雑な因果関係を推論し、自然言語で回答するチャットシステム。

## 2. システムアーキテクチャ
- **Frontend:** Streamlit (Python)
- **Orchestrator:** LangChain / Python (JSONデータのパースおよびプロンプト構築)
- **LLM Server:** vLLM (OpenAI互換APIモード)
- **RAG Server:** 外部API (JSONレスポンス形式)

## 3. インフラ・モデル仕様
### 3.1 演算リソース
- **GPU:** NVIDIA RTX A5000 (24GB) × 2基
- **推論設定:** `tensor-parallel-size: 2` (vLLMによる並列分散推論)

### 3.2 推論モデル
- **Model:** Qwen 3.5-Plus (MoE版)
- **Reasoning Mode:** 有効 (モデル内部での思考プロセス <think> 実行を推奨)
- **Context Window:** 32kトークン以上を確保

## 4. データインターフェース仕様 (RAG連携)
RAGサーバーは以下のJSON構造を返す。

### 4.1 オブジェクト定義 (Nodes)
`objects` リストには動画内に登場するエンティティが含まれる。
- `obj_id`: ユニーク識別子
- `category`: 物体カテゴリ
- `first_seen_frame`: 初登場フレーム番号
- `first_seen_timestamp`: 初登場タイムスタンプ（ISO 8601日時形式、例: `"2024-01-15T10:23:45.100Z"`）
- `attributes`: 属性情報（color, material, position, state等）

### 4.2 イベント定義 (Edges/Actions)
`events` リストには時系列の挙動が含まれる。
- `frame`: 発生フレーム番号（時系列順）
- `timestamp`: 発生タイムスタンプ（ISO 8601日時形式、例: `"2024-01-15T10:23:45.167Z"`）
- `action`: 実行されたアクション（pick_up, place_on等）
- `agent`: 実行主体
- `target`: 対象オブジェクト
- `source`: 移動元（null可）
- `destination`: 移動先（null可）

### 4.3 データ例
RAGサーバーから返ってくるJSONデータの例を以下に示す。
```
  {
    "objects": [
      {
        "obj_id": "person_01",
        "category": "person",
        "first_seen_frame": 0,
        "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
        "attributes": {
          "pose": "standing",
          "orientation": "upright"
        }
      },
      {
        "obj_id": "cup_01",
        "category": "cup",
        "first_seen_frame": 3,
        "first_seen_timestamp": "2024-01-15T10:23:45.100Z",
        "attributes": {
          "color": "red",
          "material": "ceramic",
          "position": "on_desk",
          "size": "small",
          "state": "filled"
        }
      },
      {
        "obj_id": "table_01",
        "category": "table",
        "first_seen_frame": 0,
        "first_seen_timestamp": "2024-01-15T10:23:45.000Z",
        "attributes": {
          "material": "wooden",
          "size": "large"
        }
      }
    ],
    "events": [
      {
        "event_id": "evt_001",
        "frame": 5,
        "timestamp": "2024-01-15T10:23:45.167Z",
        "action": "pick_up",
        "agent": "person_01",
        "target": "cup_01",
        "source": "table_01",
        "destination": null
      },
      {
        "event_id": "evt_002",
        "frame": 10,
        "timestamp": "2024-01-15T10:23:45.333Z",
        "action": "place_on",
        "agent": "person_01",
        "target": "cup_01",
        "source": null,
        "destination": "shelf_01"
      }
    ]
  }
```

## 5. ロジック・プロンプト設計
JSONデータをLLMが理解しやすい自然言語または構造化テキストへ変換して注入する。
- 例: "Frame [X]: [Agent] が [Target] を [Source] から [Destination] へ [Action] した。"

## 6. UI/UX 要件 (Streamlit)
- **チャット画面:** ユーザー質問に対し、LLMの思考プロセス（Thinking）を表示/非表示選択できる機能を備える。
- **デバッグ表示:** サイドバーに直近のRAG取得JSONをRawデータとして表示する機能。
- **履歴管理:** `st.session_state` を利用した会話コンテキストの維持。
