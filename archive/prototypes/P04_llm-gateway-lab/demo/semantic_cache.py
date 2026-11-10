"""02 · 语义缓存演示 —— 相似 Prompt 命中同一缓存条目。

R64 §三-4 印证：cosine ≥ 0.95（演示用 Jaccard 近似）即命中。
"""
from __future__ import annotations
import argparse
from demo._common import make_client, banner, kv, MockGateway


SIMILAR_PROMPTS = [
    "今天天气怎么样",
    "今天的天气如何",
    "今日天气状况怎样",
    "明天后天会下雨吗",       # 这个不应该命中
]


def main(mode: str = "dry") -> dict:
    banner(f"02 · 语义缓存演示（mode={mode}）")
    if mode != "dry":
        print("  [提示] 真网关的语义缓存需启用 advanced 配置 + Redis；此处仅 dry 验证逻辑")
        return {"demo": "semantic_cache", "skipped": True}

    gw = MockGateway()
    client = make_client(mode, gateway=gw)
    results = []
    for i, p in enumerate(SIMILAR_PROMPTS):
        resp = client.chat.completions.create(
            model="fast",
            messages=[{"role": "user", "content": p}],
        )
        cached = getattr(resp, "cached", False)
        kv(f"#{i+1} '{p[:14]}'", f"cached={'✅' if cached else '❌'}  tokens={resp.usage.total_tokens}")
        results.append({"prompt": p, "cached": cached, "tokens": resp.usage.total_tokens})

    hits = sum(1 for r in results if r["cached"])
    kv("命中率", f"{hits}/{len(results)}（mock 用字符 bigram，命中率仅作演示；真网关靠 embedding cosine 更准）")
    kv("结论", "✅ 相似 Prompt 命中缓存即可省掉重复 LLM 调用——真网关用 embedding 命中率会显著更高")

    return {"demo": "semantic_cache", "ok": True, "hits": hits, "total": len(results)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["dry", "local", "full"], default="dry")
    main(p.parse_args().mode)
