"""01 · Fallback 演示 —— 主模型挂掉自动切备份，业务无感。

R64 §三-2 印证：fast 故障 → 自动切 smart → 再切 local。
"""
from __future__ import annotations
import argparse
from demo._common import make_client, banner, kv, MockGateway


def main(mode: str = "dry") -> dict:
    banner(f"01 · Fallback 链演示（mode={mode}）")

    if mode == "dry":
        # 模拟 openai/gpt-4o-mini 后端宕机
        gw = MockGateway(simulate_failure_for={"openai/gpt-4o-mini"})
        client = make_client(mode, gateway=gw)
    else:
        # local/full 模式无法在脚本里"杀"OpenAI；提示用户手动断网测试
        print("  [提示] local/full 模式请手动设置错误 API Key 或断网验证 fallback")
        client = make_client(mode)

    resp = client.chat.completions.create(
        model="fast",
        messages=[{"role": "user", "content": "fallback 测试请求"}],
    )

    routed = getattr(resp, "routed_to", resp.model)
    fb_used = getattr(resp, "fallback_used", False)
    kv("请求别名", "fast (主)")
    kv("实际路由", routed)
    kv("是否走了 fallback", "✅ 是" if fb_used else "❌ 否（主模型可用）")
    kv("业务感知", "无感——返回正常 OpenAI 兼容响应")

    return {"demo": "fallback", "ok": True, "fallback_used": fb_used, "routed_to": routed}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["dry", "local", "full"], default="dry")
    main(p.parse_args().mode)
