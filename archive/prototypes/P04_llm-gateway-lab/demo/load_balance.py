"""04 · Load Balance 演示 —— 100 次请求按权重 3:1:1 分发到三个底层模型。

R64 §三-3 印证：reasoning 别名背后挂 3 副本，weight 决定分发概率。
"""
from __future__ import annotations
import argparse
import random
from collections import Counter
from demo._common import make_client, banner, kv, MockGateway, MockGatewayClient


def main(mode: str = "dry", n: int = 100) -> dict:
    banner(f"04 · Load Balance 演示（mode={mode}, n={n} 次请求）")
    if mode != "dry":
        print("  [提示] 真网关 LB 统计请看 /metrics；此处仅 dry 验证权重")
        return {"demo": "load_balance", "skipped": True}

    random.seed(42)  # 让结果可复现
    gw = MockGateway()
    client = MockGatewayClient(gw)
    counter: Counter[str] = Counter()
    for i in range(n):
        # 关掉缓存（直接走底层 API 传 use_cache=False），避免命中影响路由统计
        resp = gw.chat_create(
            model="reasoning",
            messages=[{"role": "user", "content": f"q-{i}-{random.random()}"}],
            use_cache=False,
        )
        counter[resp.routed_to] += 1

    kv("权重配置", "claude-sonnet-4 : o4-mini : gemini-2.5-pro = 3 : 1 : 1（理论 60% / 20% / 20%）")
    print()
    for backend, cnt in counter.most_common():
        pct = cnt / n * 100
        kv(f"  {backend}", f"{cnt} 次  ({pct:.1f}%)")

    # 简单容差检查
    claude_pct = counter.get("anthropic/claude-sonnet-4", 0) / n
    ok = 0.45 <= claude_pct <= 0.75   # 60% ± 15%
    kv("分发是否符合权重（容差±15%）", "✅" if ok else "❌")

    return {
        "demo": "load_balance",
        "ok": ok,
        "distribution": dict(counter),
        "total": n,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["dry", "local", "full"], default="dry")
    p.add_argument("-n", type=int, default=100)
    args = p.parse_args()
    main(args.mode, args.n)
