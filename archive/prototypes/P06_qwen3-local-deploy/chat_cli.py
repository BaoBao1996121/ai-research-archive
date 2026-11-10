"""chat_cli.py — 最小命令行 chat 客户端，适配 Qwen3.6 + Qwen3。

Qwen3.6 废弃了 /think /nothink 软切换，本 CLI 自动根据模型名选正确机制。

用法:
    python chat_cli.py --model qwen3.6:35b              # 默认关 thinking
    python chat_cli.py --model qwen3.6:35b --think      # 开 thinking
    python chat_cli.py --model qwen3:8b --no-think      # Qwen3 老错误
"""
from __future__ import annotations

import argparse
import re
import sys

from openai import OpenAI


def build_extra_body(model: str, think: bool, num_ctx: int) -> dict:
    options = {"num_ctx": num_ctx}
    if model.startswith("qwen3.6"):
        # Qwen3.6 走 API 参数
        return {
            "options": options,
            "chat_template_kwargs": {
                "enable_thinking": think,
                "preserve_thinking": think,  # Agent 多轮场景保留思考
            },
        }
    # Qwen3 时代仍使用 options.think（如后端支持）
    options["think"] = think
    return {"options": options}


def strip_think(text: str) -> str:
    """本地剩底：如果 API 参数未生效，清掉 <think>...</think>。"""
    return re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3.6:35b")
    parser.add_argument("--system", default="你是一个简洁、专业的中文助手。")
    parser.add_argument("--no-think", dest="think", action="store_false")
    parser.add_argument("--think", dest="think", action="store_true")
    parser.set_defaults(think=False)
    parser.add_argument("--num-ctx", type=int, default=16384)
    args = parser.parse_args()

    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    history = [{"role": "system", "content": args.system}]
    extra_body = build_extra_body(args.model, args.think, args.num_ctx)

    mode = "thinking" if args.think else "non-thinking"
    print(f"=== chat with {args.model} ({mode}, num_ctx={args.num_ctx}) ===")
    print("=== 输入 /exit 退出，/clear 清空历史，/think 切换思考模式 ===\n")

    while True:
        try:
            user = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user == "/exit":
            break
        if user == "/clear":
            history = history[:1]
            print("[历史已清空]")
            continue
        if user == "/think":
            args.think = not args.think
            extra_body = build_extra_body(args.model, args.think, args.num_ctx)
            print(f"[思考模式现为：{'开' if args.think else '关'}]")
            continue

        history.append({"role": "user", "content": user})
        print("AI> ", end="", flush=True)

        full = []
        in_think = False
        try:
            stream = client.chat.completions.create(
                model=args.model,
                messages=history,
                stream=True,
                temperature=1.0 if args.think else 0.7,
                top_p=0.95 if args.think else 0.8,
                max_tokens=2048,
                extra_body=extra_body,
            )
            for chunk in stream:
                d = chunk.choices[0].delta.content if chunk.choices else None
                if d is None:
                    continue
                full.append(d)
                # 漏出的 thinking 不实时展示，避免污染终端
                if not args.think:
                    if "<think>" in d:
                        in_think = True
                        continue
                    if "</think>" in d:
                        in_think = False
                        continue
                    if in_think:
                        continue
                sys.stdout.write(d)
                sys.stdout.flush()
            print()
        except Exception as e:
            print(f"\n[错误] {e}")
            history.pop()
            continue

        text = "".join(full)
        # 存入历史时为 non-thinking 去掉 think 块，节省后续上下文
        history.append({
            "role": "assistant",
            "content": text if args.think else strip_think(text),
        })


if __name__ == "__main__":
    main()

