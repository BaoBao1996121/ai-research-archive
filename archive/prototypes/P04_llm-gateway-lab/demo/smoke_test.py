"""00 · 烟雾测试 —— 用 OpenAI SDK 调网关，验证"改 base_url 即工作"。

R64 §二 印证：业务代码不需要改 SDK，只把 base_url 指向 Proxy 即可。
"""
from __future__ import annotations
import argparse
from demo._common import make_client, banner, kv, MockGateway


def main(mode: str = "dry") -> dict:
    banner(f"00 · 烟雾测试（mode={mode}）")
    gw = MockGateway() if mode == "dry" else None
    client = make_client(mode, gateway=gw)

    resp = client.chat.completions.create(
        model="fast",                         # ← 业务用别名，不绑定具体厂商
        messages=[{"role": "user", "content": "用一句话解释什么是 AI Gateway"}],
    )

    msg = resp.choices[0].message.content
    kv("回复内容", msg)
    kv("路由到底层模型", getattr(resp, "routed_to", resp.model))
    kv("Token 总量", resp.usage.total_tokens)
    kv("结论", "✅ OpenAI SDK 改 base_url 即可工作（业务零侵入）")

    return {
        "demo": "smoke_test",
        "ok": True,
        "model_alias": "fast",
        "routed_to": getattr(resp, "routed_to", resp.model),
        "tokens": resp.usage.total_tokens,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["dry", "local", "full"], default="dry")
    main(p.parse_args().mode)
