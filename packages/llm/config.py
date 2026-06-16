"""Runtime LLM mode configuration.

A single selector (`LLM_MODE`) drives the whole pipeline:

- ``demo``  -> deterministic, credential-free path used for Render and tests.
- ``azure`` -> real Azure OpenAI deployment.
- ``llama`` -> a local, OpenAI-compatible server (e.g. Ollama / llama.cpp).

Settings load from environment variables or a local ``.env`` file. The default
mode is ``demo`` so a clean checkout (and the hosted demo) runs with no
credentials and no extra dependencies.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LLMMode = Literal["demo", "azure", "llama"]


class LLMSettings(BaseSettings):
    llm_mode: LLMMode = "demo"

    # Azure OpenAI -----------------------------------------------------------
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-10-21"

    # Local Llama (OpenAI-compatible server, e.g. Ollama) --------------------
    llama_base_url: str = "http://localhost:11434/v1"
    llama_model: str = "llama3.1"
    llama_api_key: str = "ollama"

    # Shared generation parameters ------------------------------------------
    llm_temperature: float = 0.2
    llm_max_tokens: int = 700
    llm_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_llm_settings() -> LLMSettings:
    return LLMSettings()
