"""LLM client factory and a thin provider-agnostic wrapper.

Both Azure OpenAI and a local Llama server are reached through the OpenAI SDK
(`chat.completions`), so a single `LLMClient` wrapper covers both. The heavy
`openai` import is deferred into the factory branches so the deterministic
``demo`` path never needs the dependency installed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from packages.llm.config import LLMSettings, get_llm_settings
from packages.llm.router import TASK_MODEL_ROUTING


class LLMConfigurationError(RuntimeError):
    """Raised when a non-demo mode is selected without valid configuration."""


def get_model_name(task_name: str) -> str:
    return TASK_MODEL_ROUTING.get(task_name, "gpt-4o-mini")


@dataclass
class LLMClient:
    """Provider-agnostic chat wrapper over an OpenAI-compatible client."""

    client: Any
    model: str
    temperature: float
    max_tokens: int

    def complete(self, *, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"{system} Respond with a single JSON object only.",
                },
                {"role": "user", "content": user},
            ],
        )
        return _loads_json(response.choices[0].message.content or "{}")


def _loads_json(content: str) -> dict[str, Any]:
    content = content.strip()
    try:
        parsed: Any = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(content[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from the model.")
    return parsed


def get_llm_client(settings: LLMSettings | None = None) -> LLMClient | None:
    """Return a configured client, or ``None`` for the credential-free demo mode."""

    settings = settings or get_llm_settings()
    mode = settings.llm_mode

    if mode == "demo":
        return None

    if mode == "azure":
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            raise LLMConfigurationError(
                "azure mode requires AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY."
            )
        from openai import AzureOpenAI

        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            timeout=settings.llm_timeout_seconds,
        )
        return LLMClient(
            client=client,
            model=settings.azure_openai_deployment,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    if mode == "llama":
        from openai import OpenAI

        client = OpenAI(
            base_url=settings.llama_base_url,
            api_key=settings.llama_api_key,
            timeout=settings.llm_timeout_seconds,
        )
        return LLMClient(
            client=client,
            model=settings.llama_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    raise LLMConfigurationError(f"Unknown llm_mode: {mode!r}")
