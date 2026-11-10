"""共享工具 —— Mock LiteLLM 行为，让 demo 在 dry-run 模式下零依赖跑通。

设计目标：
- dry: 用 MockGatewayClient 模拟 OpenAI SDK + LiteLLM 网关行为
- local/full: 用真 openai.OpenAI 指向 http://localhost:4000

这样所有 demo 脚本逻辑不变，只换 client 工厂。
"""
from __future__ import annotations
import os
import time
import random
import hashlib
from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────
# Mock 数据结构（模仿 openai.types.ChatCompletion）
# ──────────────────────────────────────────────
@dataclass
class _MockMessage:
    role: str
    content: str


@dataclass
class _MockChoice:
    message: _MockMessage
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class _MockUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class _MockCompletion:
    id: str
    model: str
    choices: list[_MockChoice]
    usage: _MockUsage
    cached: bool = False               # 网关扩展字段：是否命中缓存
    routed_to: str = ""                # 网关扩展字段：实际路由到哪个底层模型
    fallback_used: bool = False        # 是否走了 fallback


# ──────────────────────────────────────────────
# Mock Gateway —— 模拟 LiteLLM 关键行为
# ──────────────────────────────────────────────
class MockGateway:
    """模拟 LiteLLM Proxy 的行为：路由 / fallback / 语义缓存 / virtual key 计费。

    注意：这是教学用 mock，不是 LiteLLM 复刻。仅复现 R64 报告中的核心行为。
    """

    # 别名 → 候选底层模型列表（带权重）
    ROUTES: dict[str, list[tuple[str, int]]] = {
        "fast": [("openai/gpt-4o-mini", 1)],
        "smart": [("anthropic/claude-sonnet-4", 1)],
        "local": [("ollama/qwen2.5:7b", 1)],
        "fast-cheap": [("openai/gpt-4o-mini", 1)],
        "reasoning": [
            ("anthropic/claude-sonnet-4", 3),
            ("openai/o4-mini", 1),
            ("gemini/gemini-2.5-pro", 1),
        ],
    }
    FALLBACKS: dict[str, list[str]] = {
        "fast": ["smart", "local"],
        "smart": ["fast"],
        "reasoning": ["fast-cheap"],
    }

    def __init__(self, *, similarity_threshold: float = 0.95, simulate_failure_for: set[str] | None = None):
        self.cache: dict[str, _MockCompletion] = {}        # key=向量哈希，value=回复
        self.cache_index: list[tuple[str, str]] = []       # [(prompt, key)] 用于"语义"匹配
        self.similarity_threshold = similarity_threshold
        self.simulate_failure_for = simulate_failure_for or set()
        self.virtual_keys: dict[str, dict[str, Any]] = {}  # key → {budget, spent, models}
        self.route_counts: dict[str, int] = {}             # 实际路由统计
        self.call_count = 0

    # ─── Virtual Key 管理 ───
    def create_virtual_key(self, *, max_budget: float, models: list[str], team: str = "default") -> str:
        """模拟 POST /key/generate"""
        vk = f"sk-vk-{hashlib.sha1(team.encode() + str(time.time()).encode()).hexdigest()[:12]}"
        self.virtual_keys[vk] = {
            "max_budget": max_budget,
            "spent": 0.0,
            "models": models,
            "team": team,
        }
        return vk

    # ─── 语义"缓存"——用字符 bigram + Jaccard 近似 cosine（中文友好） ───
    @staticmethod
    def _ngrams(text: str, n: int = 2) -> set[str]:
        text = "".join(text.lower().split())
        return {text[i : i + n] for i in range(max(0, len(text) - n + 1))}

    def _semantic_match(self, prompt: str) -> str | None:
        prompt_grams = self._ngrams(prompt)
        if not prompt_grams:
            return None
        for past_prompt, key in self.cache_index:
            past_grams = self._ngrams(past_prompt)
            if not past_grams:
                continue
            jaccard = len(prompt_grams & past_grams) / len(prompt_grams | past_grams)
            # 中文 bigram Jaccard 0.15 ≈ cosine 0.95 上下，仅作演示
            if jaccard >= 0.15:
                return key
        return None

    # ─── 路由（带权重） ───
    def _pick_backend(self, alias: str) -> str:
        candidates = self.ROUTES.get(alias, [(alias, 1)])
        weights = [w for _, w in candidates]
        models = [m for m, _ in candidates]
        return random.choices(models, weights=weights, k=1)[0]

    # ─── 主调用 ───
    def chat_create(self, *, model: str, messages: list[dict], api_key: str = "", use_cache: bool = True) -> _MockCompletion:
        self.call_count += 1
        prompt = messages[-1]["content"]

        # 1) Virtual Key 检查
        if api_key.startswith("sk-vk-"):
            vk = self.virtual_keys.get(api_key)
            if vk is None:
                raise RuntimeError(f"401 invalid virtual key: {api_key}")
            if vk["spent"] >= vk["max_budget"]:
                raise RuntimeError(f"429 budget_exceeded: spent ${vk['spent']:.4f} >= ${vk['max_budget']}")
            if model not in vk["models"]:
                raise RuntimeError(f"403 model_not_allowed: {model} not in {vk['models']}")

        # 2) 语义缓存命中
        if use_cache:
            hit = self._semantic_match(prompt)
            if hit is not None:
                cached = self.cache[hit]
                # 返回缓存副本，标记 cached=True
                return _MockCompletion(
                    id=f"cached-{cached.id}",
                    model=cached.model,
                    choices=cached.choices,
                    usage=_MockUsage(0, 0, 0),  # 缓存命中不计 token
                    cached=True,
                    routed_to=cached.routed_to,
                )

        # 3) 路由 + Fallback
        chain = [model] + self.FALLBACKS.get(model, [])
        last_err = None
        for attempt_model in chain:
            backend = self._pick_backend(attempt_model)
            self.route_counts[backend] = self.route_counts.get(backend, 0) + 1
            if backend in self.simulate_failure_for:
                last_err = RuntimeError(f"503 backend_unavailable: {backend}")
                continue
            # 4) 模拟"调用成功"
            reply = self._fake_reply(prompt, backend)
            usage = _MockUsage(
                prompt_tokens=len(prompt) // 4 + 1,
                completion_tokens=len(reply) // 4 + 1,
                total_tokens=(len(prompt) + len(reply)) // 4 + 2,
            )
            comp = _MockCompletion(
                id=f"chatcmpl-{self.call_count:06d}",
                model=backend,
                choices=[_MockChoice(message=_MockMessage(role="assistant", content=reply))],
                usage=usage,
                cached=False,
                routed_to=backend,
                fallback_used=(attempt_model != model),
            )
            # 写缓存
            if use_cache:
                key = hashlib.sha1(prompt.encode()).hexdigest()
                self.cache[key] = comp
                self.cache_index.append((prompt, key))
            # 扣 Virtual Key 余额（按 token 粗算 $0.001/1k）
            if api_key.startswith("sk-vk-"):
                self.virtual_keys[api_key]["spent"] += usage.total_tokens * 0.000001
            return comp

        raise last_err or RuntimeError("500 all_backends_failed")

    @staticmethod
    def _fake_reply(prompt: str, backend: str) -> str:
        # 极简的 mock 回复，让 demo 看起来像那么回事
        sig = backend.split("/")[-1][:8]
        return f"[mock-{sig}] 回复: {prompt[:40]}..." if len(prompt) > 40 else f"[mock-{sig}] 回复: {prompt}"


# ──────────────────────────────────────────────
# 客户端工厂 —— dry / local / full 三种模式
# ──────────────────────────────────────────────
class _ChatCompletions:
    def __init__(self, gw: MockGateway, api_key: str):
        self._gw = gw
        self._api_key = api_key

    def create(self, *, model: str, messages: list[dict], **kwargs):
        # kwargs 接收但不用，模拟 LiteLLM 的 drop_params=True
        return self._gw.chat_create(model=model, messages=messages, api_key=self._api_key)


class _Chat:
    def __init__(self, gw: MockGateway, api_key: str):
        self.completions = _ChatCompletions(gw, api_key)


class MockGatewayClient:
    """API 形状与 openai.OpenAI 一致：client.chat.completions.create(...)"""

    def __init__(self, gateway: MockGateway, api_key: str = "sk-anything"):
        self._gw = gateway
        self.chat = _Chat(gateway, api_key)
        self.api_key = api_key

    @property
    def gateway(self) -> MockGateway:
        return self._gw


def make_client(mode: str, gateway: MockGateway | None = None, api_key: str | None = None):
    """根据模式返回 client。
    - dry: MockGatewayClient（零依赖）
    - local/full: 真 openai.OpenAI 指向 http://localhost:4000
    """
    if mode == "dry":
        gw = gateway or MockGateway()
        return MockGatewayClient(gw, api_key=api_key or "sk-mock")

    # local / full：用真 OpenAI SDK 指向 LiteLLM Proxy
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("local/full 模式需要 `pip install openai`") from e

    base_url = os.getenv("GATEWAY_BASE_URL", "http://localhost:4000")
    key = api_key or os.getenv("GATEWAY_API_KEY", "EXAMPLE_API_KEY")
    return OpenAI(base_url=base_url, api_key=key)


def banner(title: str) -> None:
    print()
    print("═" * 72)
    print(f"  {title}")
    print("═" * 72)


def kv(label: str, value: Any) -> None:
    print(f"  {label:<22} {value}")
