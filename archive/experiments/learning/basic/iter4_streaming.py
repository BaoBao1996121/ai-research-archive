"""
Iter 4: 流式输出 — 让 Agent 实时响应（~180 行核心代码）
======================================================
目标：Agent 回复时逐字输出，而非等待完整响应后一次性显示。
新增：stream=True + 逐 chunk 处理 + 流式工具调用组装
学到：SSE 流式协议、流式工具调用的 delta 拼接、用户体验优化。

Claude Code 对照：
  - QueryEngine.ts: 所有 API 调用都是流式的，通过 async generator yield 每个 chunk
  - 流式不只是 UX 优化——它让工具执行可以与输出交织，像人类一样"边想边说"

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter4_streaming.py
"""

import os
import json
from config import client, MODEL

# ━━━ 工具（复用简化版） ━━━
TOOLS = [
    {"type": "function", "function": {
        "name": "calculator", "description": "计算数学表达式",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "get_current_time", "description": "获取当前时间",
        "parameters": {"type": "object", "properties": {}}}},
]

def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})

def get_current_time() -> str:
    from datetime import datetime
    return json.dumps({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

TOOL_MAP = {"calculator": calculator, "get_current_time": get_current_time}


# ━━━ 流式 Agent 循环（核心改动） ━━━
def stream_agent_loop(user_message: str, max_turns: int = 10) -> str:
    """
    与 Iter 1 的 agent_loop 核心区别：
    1. API 调用加 stream=True
    2. 文本 chunk 实时打印（逐字输出）
    3. 工具调用 chunk 需要拼接（delta.tool_calls 是增量的）
    """
    messages = [
        {"role": "system", "content": "你是一个有用的AI助手，可以调用工具。回答请尽量详细。"},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        print(f"\n  ⚡ 第 {turn + 1} 轮推理", end="")

        # ━━━ 流式调用 ━━━
        stream = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, stream=True,
        )

        # 需要从 delta 中累积完整的 message
        collected_content = ""
        tool_calls_buf: dict[int, dict] = {}  # index → {id, name, arguments}

        for chunk in stream:
            delta = chunk.choices[0].delta

            # 1) 文本流：有内容就立刻打印
            if delta.content:
                if not collected_content:
                    print("\n  💬 ", end="")
                print(delta.content, end="", flush=True)
                collected_content += delta.content

            # 2) 工具调用流：增量拼接
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_buf:
                        tool_calls_buf[idx] = {"id": "", "name": "", "arguments": ""}
                    buf = tool_calls_buf[idx]
                    # 调试：展示每个 chunk 带来的增量片段
                    print(f"\n    [chunk] index={idx}, id={tc_delta.id!r}, "
                          f"name={tc_delta.function.name if tc_delta.function else None!r}, "
                          f"args_delta={tc_delta.function.arguments if tc_delta.function else None!r}", end="")
                    if tc_delta.id:
                        buf["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            buf["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            buf["arguments"] += tc_delta.function.arguments

        if collected_content:
            print()  # 文本流结束换行

        # ━━━ 构建完整 assistant 消息 ━━━
        assistant_msg = {"role": "assistant", "content": collected_content or None}
        if tool_calls_buf:
            assistant_msg["tool_calls"] = [
                {
                    "id": buf["id"],
                    "type": "function",
                    "function": {"name": buf["name"], "arguments": buf["arguments"]},
                }
                for buf in tool_calls_buf.values()
            ]
        messages.append(assistant_msg)

        # ━━━ 无工具调用 → 完成 ━━━
        if not tool_calls_buf:
            print(f"  ✅ 完成（{turn + 1} 轮）")
            return collected_content

        # ━━━ 执行工具 ━━━
        print(f"\n  📦 拼接完成，共 {len(tool_calls_buf)} 个工具调用:")
        for idx, buf in tool_calls_buf.items():
            print(f"    [{idx}] id={buf['id']}, name={buf['name']}, args={buf['arguments']}")
        for buf in tool_calls_buf.values():
            fn_name = buf["name"]
            fn_args = json.loads(buf["arguments"]) if buf["arguments"] else {}
            print(f"  🔧 {fn_name}({fn_args})")
            result = TOOL_MAP[fn_name](**fn_args)
            print(f"  📋 → {result}")
            messages.append({
                "role": "tool", "tool_call_id": buf["id"], "content": result,
            })

    return "⚠️ 达到最大轮次限制"


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 4: 流式输出 — 实时响应")
    print("=" * 60)

    print("\n📝 测试 1: 纯文本流式输出")
    result = stream_agent_loop("用三段话介绍 AI Agent 的核心概念")
    print(f"\n最终长度: {len(result)} 字符")

    print("\n" + "-" * 60)
    print("📝 测试 2: 流式 + 工具调用")
    result = stream_agent_loop("现在几点了？再帮我算 365 * 24 * 60 等于多少分钟")
    print(f"\n🤖 最终回答:\n{result}")
