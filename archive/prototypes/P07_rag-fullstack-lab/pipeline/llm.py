"""统一 LLM 客户端 - OpenAI 兼容协议（Ollama / DeepSeek / SiliconFlow / OpenAI 都通用）。"""
from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class LLMClient:
    model: str
    base_url: str
    api_key: str
    temperature: float = 0.3

    def __post_init__(self):
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def complete(self, prompt: str, *, max_tokens: int = 1024, temperature: float | None = None) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
        )
        return resp.choices[0].message.content or ""

    def chat(self, messages: list[dict], *, max_tokens: int = 1024, temperature: float | None = None) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
        )
        return resp.choices[0].message.content or ""


def build_llm(cfg: dict) -> LLMClient:
    """配置示例：
    {model: qwen3:8b, base_url: ${OLLAMA_BASE_URL}, api_key: ${OLLAMA_API_KEY}}
    支持 ${ENV} 占位符。
    """
    def resolve(v):
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            return os.environ.get(v[2:-1], "")
        return v

    return LLMClient(
        model=cfg["model"],
        base_url=resolve(cfg.get("base_url", "${OLLAMA_BASE_URL}")) or "http://localhost:11434/v1",
        api_key=resolve(cfg.get("api_key", "${OLLAMA_API_KEY}")) or "ollama",
        temperature=cfg.get("temperature", 0.3),
    )
