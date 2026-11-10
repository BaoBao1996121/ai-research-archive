"""verify.py — 验证 Ollama + Qwen3.6 本地部署是否就绪。

用法:
    python verify.py                          # 默认 qwen3.6:35b
    python verify.py --model qwen3.6:27b
    python verify.py --model qwen3:8b         # 保底基线

退出码:
    0 全部通过
    1 Ollama 服务不可达
    2 模型未拉取
    3 推理失败
"""
from __future__ import annotations

import argparse
import sys
import time

import requests
from openai import OpenAI

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.6:35b"  # Qwen3.6-35B-A3B MoE 是 8GB 显卡甜点
FALLBACK_MODEL = "qwen3:8b"     # 未 pull qwen3.6 时的保底


def check_service() -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/version", timeout=3)
        if r.status_code == 200:
            print(f"[OK] Ollama 服务可达，版本: {r.json().get('version', 'unknown')}")
            return True
    except Exception as e:
        print(f"[FAIL] Ollama 服务不可达: {e}")
    return False


def check_model(model: str) -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        names = [m["name"] for m in r.json().get("models", [])]
        if model in names or any(n.startswith(model + ":") for n in names):
            print(f"[OK] 模型已就绪: {model}")
            return True
        print(f"[FAIL] 模型未拉取: {model}\n  已有模型: {names or '(无)'}")
        print(f"  请执行: ollama pull {model}")
    except Exception as e:
        print(f"[FAIL] 列表模型失败: {e}")
    return False


def hello_inference(model: str) -> bool:
    """调用模型讲一句话。Qwen3.6 关闭 thinking 走 API 参数。"""
    client = OpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
    is_qwen36 = model.startswith("qwen3.6")

    extra_body: dict = {"options": {"num_ctx": 8192}}
    if is_qwen36:
        # Qwen3.6 专用：关闭 thinking 以获得快响应、干净输出
        extra_body["chat_template_kwargs"] = {"enable_thinking": False}
        sys_prompt = "你是简洁助手。"
    else:
        # Qwen3 时代用 /nothink 软切换
        sys_prompt = "你是简洁助手。/nothink"

    try:
        t0 = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "用一句话说你是谁。"},
            ],
            max_tokens=128,
            temperature=0.7,
            extra_body=extra_body,
        )
        dt = time.time() - t0
        msg = resp.choices[0].message.content or "(空)"
        # 清掉可能漏出的 <think> 块
        import re
        clean = re.sub(r'<think>.*?</think>\s*', '', msg, flags=re.DOTALL).strip()
        print(f"[OK] 推理成功 ({dt:.2f}s)")
        print(f"     回复: {clean[:200]}")
        if clean != msg.strip():
            print(f"     ⚠️ 检测到未被 API 参数压制的 thinking 块，已本地剩底")
        return True
    except Exception as e:
        print(f"[FAIL] 推理失败: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"默认 {DEFAULT_MODEL}，未拉取时可用 --model {FALLBACK_MODEL}")
    args = parser.parse_args()

    print(f"=== 验证 Qwen 本地部署 (模型: {args.model}) ===\n")
    if not check_service():
        print("\n提示：请启动 Ollama（桌面图标或 `ollama serve`）")
        return 1
    if not check_model(args.model):
        print(f"\n提示：未拉取？请 `ollama pull {args.model}`。")
        if args.model == DEFAULT_MODEL:
            print(f"      或使用保底基线：python verify.py --model {FALLBACK_MODEL}")
        return 2
    if not hello_inference(args.model):
        return 3
    print("\n=== 全部通过 ✅ ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

