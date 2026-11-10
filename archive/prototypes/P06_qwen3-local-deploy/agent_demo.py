"""agent_demo.py — Qwen-Agent 接 Ollama 本地 Qwen3.6 的最小 ReAct demo。

需要:
    pip install "qwen-agent[mcp]"

用法:
    python agent_demo.py                       # 默认 qwen3.6:35b
    python agent_demo.py --model qwen3:8b      # 用 8B 保底基线

注意:
    - Qwen3.6 已废弃 /think /nothink 软切换，必须用 chat_template_kwargs.enable_thinking
    - 本 demo 加载 code_interpreter 内置工具，无需 uv/uvx
"""
from __future__ import annotations

import argparse
import sys

try:
    from qwen_agent.agents import Assistant
except ImportError:
    print("请先安装: pip install 'qwen-agent[mcp]'")
    sys.exit(1)


def build_llm_cfg(model: str, enable_thinking: bool = False) -> dict:
    """根据模型自动构造 LLM 配置（Qwen3.6 vs Qwen3 thinking 机制不同）。"""
    is_qwen36 = model.startswith("qwen3.6")
    extra_body: dict = {"options": {"num_ctx": 16384}}
    if is_qwen36:
        # Qwen3.6 用 chat_template_kwargs.enable_thinking 控制思考
        extra_body["chat_template_kwargs"] = {
            "enable_thinking": enable_thinking,
            "preserve_thinking": True,  # Agent 多轮保留历史推理 trace
        }
    else:
        # Qwen3 用 options.think
        extra_body["options"]["think"] = enable_thinking

    return {
        "model": model,
        "model_server": "http://localhost:11434/v1",
        "api_key": "ollama",
        "generate_cfg": {
            "top_p": 0.8 if not enable_thinking else 0.95,
            "temperature": 0.7 if not enable_thinking else 1.0,
            "extra_body": extra_body,
        },
    }


TOOLS = ["code_interpreter"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.6:35b", help="模型名（默认 qwen3.6:35b）")
    ap.add_argument("--think", action="store_true", help="开启 thinking 模式")
    args = ap.parse_args()

    is_qwen36 = args.model.startswith("qwen3.6")
    sys_msg = "你是一个简洁的中文助手，需要计算时调用 code_interpreter。回答用中文。"
    if not is_qwen36 and not args.think:
        sys_msg += " /nothink"  # Qwen3 的旧软切换

    bot = Assistant(
        llm=build_llm_cfg(args.model, enable_thinking=args.think),
        system_message=sys_msg,
        function_list=TOOLS,
    )

    queries = [
        "帮我算一下 1234 * 5678 + sqrt(98765) 的结果。",
        "比较 Python 中 list 和 tuple 的内存占用，给个实测数字。",
    ]

    print(f"\n>> 模型: {args.model}  thinking: {args.think}")
    for q in queries:
        print(f"\n{'='*60}")
        print(f"用户: {q}")
        print(f"{'='*60}")
        last = ""
        for resp in bot.run([{"role": "user", "content": q}]):
            if isinstance(resp, list) and resp:
                msg = resp[-1]
                content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                if content and content != last:
                    print(content[len(last):], end="", flush=True)
                    last = content
        print()


if __name__ == "__main__":
    main()
