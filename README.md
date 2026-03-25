# Video-RAG

空間イベント記憶の RAG システム。

```
video-rag/
├── rag-server/       # RAG検索サーバ (FastAPI, port 9000)
└── streamlit-app/    # optiBot UI (Streamlit, port 8501)
```

## Quick Start

### RAG サーバ

```bash
cd rag-server
uv sync --all-extras
uv run pytest -v
uv run python scripts/ingest.py --input <annotations_dir> --output <index_dir>
uv run python scripts/serve.py --index <index_dir>
```

詳細は [rag-server/README.md](rag-server/README.md) を参照。

### optiBot (Streamlit)

```bash
cd streamlit-app
uv sync
uv run streamlit run app/main.py --server.port 8501
```
