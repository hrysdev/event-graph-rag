import os
from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() == "true"


class Settings:
    vllm_base_url: str = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    vllm_model_name: str = os.getenv("VLLM_MODEL_NAME", "qwen3.5-plus")
    rag_api_url: str = os.getenv("RAG_API_URL", "http://localhost:9000/query")
    rag_api_timeout: int = int(os.getenv("RAG_API_TIMEOUT", "30"))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.6"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    enable_thinking: bool = _bool(os.getenv("ENABLE_THINKING"), True)

    def __init__(self):
        self.vllm_base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.vllm_model_name = os.getenv("VLLM_MODEL_NAME", "qwen3.5-plus")
        self.rag_api_url = os.getenv("RAG_API_URL", "http://localhost:9000/query")
        self.rag_api_timeout = int(os.getenv("RAG_API_TIMEOUT", "30"))
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.6"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        self.enable_thinking = _bool(os.getenv("ENABLE_THINKING"), True)


settings = Settings()
