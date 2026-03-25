import importlib
import pytest


ENV_VARS = [
    "VLLM_BASE_URL",
    "VLLM_MODEL_NAME",
    "RAG_API_URL",
    "RAG_API_TIMEOUT",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "ENABLE_THINKING",
]


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def make_settings():
    import config
    return config.Settings()


# T2-01: デフォルト値
def test_default_values():
    s = make_settings()
    assert s.vllm_base_url == "http://localhost:8000/v1"
    assert s.vllm_model_name == "qwen3.5-plus"
    assert s.rag_api_url == "http://localhost:9000/query"
    assert s.rag_api_timeout == 30
    assert s.llm_temperature == 0.6
    assert s.llm_max_tokens == 4096
    assert s.enable_thinking is True


# T2-02: VLLM_BASE_URL の上書き
def test_custom_vllm_base_url(monkeypatch):
    monkeypatch.setenv("VLLM_BASE_URL", "http://custom:1234/v1")
    s = make_settings()
    assert s.vllm_base_url == "http://custom:1234/v1"


# T2-03: RAG_API_TIMEOUT が int として返る
def test_rag_api_timeout_as_int(monkeypatch):
    monkeypatch.setenv("RAG_API_TIMEOUT", "60")
    s = make_settings()
    assert s.rag_api_timeout == 60
    assert isinstance(s.rag_api_timeout, int)


# T2-04: LLM_TEMPERATURE が float として返る
def test_llm_temperature_as_float(monkeypatch):
    monkeypatch.setenv("LLM_TEMPERATURE", "0.9")
    s = make_settings()
    assert s.llm_temperature == pytest.approx(0.9)
    assert isinstance(s.llm_temperature, float)


# T2-05: ENABLE_THINKING "false" -> False
def test_enable_thinking_false(monkeypatch):
    monkeypatch.setenv("ENABLE_THINKING", "false")
    s = make_settings()
    assert s.enable_thinking is False


# T2-06: ENABLE_THINKING "true" -> True
def test_enable_thinking_true(monkeypatch):
    monkeypatch.setenv("ENABLE_THINKING", "true")
    s = make_settings()
    assert s.enable_thinking is True


# T2-07: import が副作用なしで行える
def test_import_no_side_effects():
    import config  # noqa: F401
