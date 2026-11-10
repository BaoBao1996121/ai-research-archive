"""
Iter 1: 最小 Agent — ReAct 循环（~90 行核心代码）
=================================================
目标：从"单次调用"跳跃到"Agent"——关键就是一个 while 循环。
新增：工具定义 + while 循环 + 工具调用分发
学到：ReAct 模式（Reasoning + Acting）、Function Calling 协议。

Claude Code 对照：
  - query.ts 主循环: while(true) { stream → 解析 → tool_use? → 执行 → 回填 → 继续 }
  - 这是 Agent 最核心的 30 行代码。其余一切（工具、上下文、安全）都是围绕这个循环展开的。

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter1_react_loop.py
"""

import json
from config import client, MODEL

# ━━━ 工具定义（OpenAI Function Calling 格式） ━━━
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式。支持加减乘除、括号、幂运算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '(1+2)*3'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

# ━━━ 工具实现 ━━━
def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "包含不允许的字符"}, ensure_ascii=False)
    try:
        return json.dumps({"result": eval(expression)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_current_time() -> str:
    from datetime import datetime
    return json.dumps({"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


TOOL_MAP = {"calculator": calculator, "get_current_time": get_current_time}

# ━━━ Agent 核心循环（这是从 LLM 到 Agent 的关键跳跃） ━━━
def agent_loop(user_message: str, max_turns: int = 3) -> str:
    """
    ReAct 循环的最小实现：
    1. 将用户消息发给 LLM（附带工具定义）
    2. LLM 返回文本回复 → 结束
    3. LLM 返回工具调用 → 执行 → 结果塞回 messages → 回到 1
    """
    messages = [
        {"role": "system", "content": "你是一个能使用工具的AI助手。需要计算时用 calculator，需要时间用 get_current_time。"},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        print(f"  ⚡ 第 {turn + 1} 轮推理...")
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg)

        # 没有工具调用 → LLM 认为任务完成，返回文本
        if not msg.tool_calls:
            print(f"  ✅ Agent 完成（共 {turn + 1} 轮）")
            return msg.content

        # 有工具调用 → 执行每个工具，将结果塞回
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            print(f"  🔧 调用: {fn_name}({fn_args})")

            result = TOOL_MAP[fn_name](**fn_args)
            print(f"  📋 结果: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "⚠️ 达到最大轮次限制"


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 1: 最小 Agent — ReAct 循环")
    print("=" * 60)

    print("\n📝 测试 1: 多步计算")
    result = agent_loop("先算 123 * 456，再把结果除以 7，保留两位小数")
    print(f"\n🤖 最终回答:\n{result}")

    print("\n" + "-" * 60)
    print("📝 测试 2: 混合工具调用")
    result = agent_loop("现在几点了？另外帮我算 2 的 10 次方是多少")
    print(f"\n🤖 最终回答:\n{result}")
