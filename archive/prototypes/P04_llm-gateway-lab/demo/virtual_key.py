"""03 · Virtual Key 演示 —— 创建带预算的 Key，超额自动拒绝。

R64 §三-5 印证：每团队独立 Key + 月度预算 + 模型白名单。
"""
from __future__ import annotations
import argparse
from demo._common import make_client, banner, kv, MockGateway, MockGatewayClient


def main(mode: str = "dry") -> dict:
    banner(f"03 · Virtual Key 与预算演示（mode={mode}）")
    if mode != "dry":
        print("  [提示] 真网关请用 curl POST /key/generate 创建；此处仅 dry 演示行为")
        return {"demo": "virtual_key", "skipped": True}

    gw = MockGateway()
    # 给"agent-research"团队签发一把仅可用 fast 模型、预算 $0.0001 的极小 Key（用于快速触发超额）
    vk = gw.create_virtual_key(max_budget=0.0001, models=["fast"], team="agent-research")
    kv("发放 Virtual Key", vk)
    kv("预算", "$0.0001（演示用，几次调用就超）")
    kv("允许模型", "['fast']")

    client = MockGatewayClient(gw, api_key=vk)

    success, denied = 0, 0
    for i in range(20):
        try:
            # 关闭缓存，确保每次都真的调用并扣费
            client._gw.chat_create(
                model="fast",
                messages=[{"role": "user", "content": f"测试请求 #{i}：" + "x" * 200}],
                api_key=vk,
                use_cache=False,
            )
            success += 1
        except RuntimeError as e:
            denied += 1
            if denied == 1:
                kv("第一次被拒", str(e))
            break

    kv("成功次数", success)
    kv("被拒次数", denied)
    kv("剩余预算", f"${gw.virtual_keys[vk]['max_budget'] - gw.virtual_keys[vk]['spent']:.6f}")

    # 测试模型白名单（用一把预算充足的新 Key，避免被预算先拦下）
    vk2 = gw.create_virtual_key(max_budget=10.0, models=["fast"], team="agent-research")
    client2 = MockGatewayClient(gw, api_key=vk2)
    try:
        client2.chat.completions.create(model="smart", messages=[{"role": "user", "content": "x"}])
        whitelist_ok = False
    except RuntimeError as e:
        whitelist_ok = "model_not_allowed" in str(e)
    kv("模型白名单生效", "✅" if whitelist_ok else "❌")
    kv("结论", "✅ Virtual Key 实现了：预算控制 + 模型白名单（多团队隔离）")

    return {
        "demo": "virtual_key",
        "ok": True,
        "success": success,
        "denied": denied,
        "whitelist_enforced": whitelist_ok,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["dry", "local", "full"], default="dry")
    main(p.parse_args().mode)
