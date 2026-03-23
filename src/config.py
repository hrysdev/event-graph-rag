"""アプリケーション設定（pydantic-settings）."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数 VRAG_* で上書き可能な設定."""

    model_config = SettingsConfigDict(env_prefix="VRAG_")

    embedding_model: str = "cl-nagoya/ruri-v3-310m"
    similarity_threshold: float = 0.7
    top_k: int = 10
    max_expanded_events: int = 50
    port: int = 9000
