"""
LangChain & LangGraph 学习脚本 03 —— 你的第一个 Agent

对应文档：第四章
学习目标：
  1. 用 create_react_agent（LangGraph 预建）快速创建 Agent
  2. 观察 Agent 的 ReAct 循环：思考 → 调工具 → 观察 → 再思考
  3. 尝试"玩坏"它——边界测试是学习的最佳方式

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\03_hello_agent.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_root = Path(__file__).resolve().parent
while _root != _root.parent:
    if (_root / ".env").exists():
        break
    _root = _root.parent
load_dotenv(_root / ".env")

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# ━━━ 模型 ━━━
model = ChatOpenAI(
    model=os.getenv("MODEL", "qwen-plus"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0,
)

# ━━━ 工具 ━━━

@tool
def get_current_time() -> str:
    """获取当前时间。当用户问"现在几点"或"当前时间"时使用。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def reverse_string(text: str) -> str:
    """反转一个字符串。当用户要求反转文字时使用。

    Args:
        text: 要反转的字符串
    """
    return text[::-1]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 创建 Agent
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# create_react_agent 是 LangGraph 提供的高级 API
# 内部自动构建了 ReAct 循环图：LLM → 检查 tool_call → 执行工具 → 回到 LLM
# 文档中的 create_agent 实际上就是这个函数

agent = create_react_agent(
    model=model,
    tools=[get_current_time, reverse_string],
    # prompt 参数设定 Agent 的系统角色
    prompt="你是一个乐于助人的 AI 助手。可以查时间和反转字符串。用中文回答。",
)

# ━━━ 辅助函数：打印对话过程 ━━━
def print_conversation(result):
    """打印 Agent 对话的完整过程"""
    for msg in result["messages"]:
        role = type(msg).__name__
        if role == "HumanMessage":
            print(f"  👤 用户: {msg.content}")
        elif role == "AIMessage":
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  🤖 AI → 调用工具: {tc['name']}({tc['args']})")
            if msg.content:
                print(f"  🤖 AI: {msg.content}")
        elif role == "ToolMessage":
            print(f"  🔧 工具结果: {msg.content}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 测试 1：需要工具的问题
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("🧪 测试 1：现在几点了？（需要 get_current_time 工具）")
print("=" * 60)

result = agent.invoke({
    "messages": [HumanMessage(content="现在几点了？")]
})
print_conversation(result)
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 测试 2：不需要工具的问题
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("🧪 测试 2：解释递归（不需要工具，LLM 直接回答）")
print("=" * 60)

result = agent.invoke({
    "messages": [HumanMessage(content="用一句话解释什么是递归")]
})
print_conversation(result)
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 测试 3：工具用不上的问题
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("🧪 测试 3：查天气（没有天气工具，看 Agent 怎么应对）")
print("=" * 60)

result = agent.invoke({
    "messages": [HumanMessage(content="帮我查一下明天北京的天气")]
})
print_conversation(result)
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 测试 4：链式推理 —— 先调一个工具，再调另一个
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("🧪 测试 4：链式推理（先获取时间，再反转时间字符串）")
print("=" * 60)

result = agent.invoke({
    "messages": [HumanMessage(content="先告诉我现在几点，然后把时间字符串反转过来")]
})
print_conversation(result)

print("""
┌─────────────────────────────────────────────────────────┐
│ 💡 关键洞察                                             │
│                                                         │
│ create_react_agent 内部就是一个 LangGraph 图：          │
│                                                         │
│   START → LLM → [有 tool_call?]                        │
│                    ├─ 是 → 执行工具 → 回到 LLM          │
│                    └─ 否 → END                          │
│                                                         │
│ 测试 4 的执行过程（至少 3 次 LLM 调用）：               │
│   LLM #1：决定调 get_current_time                       │
│   执行工具 → 拿到时间字符串                              │
│   LLM #2：决定调 reverse_string(时间字符串)             │
│   执行工具 → 拿到反转结果                               │
│   LLM #3：综合两次工具结果，生成最终回答                │
│                                                         │
│ 下一个脚本我们打开这个黑盒，手动搓这个图！              │
└─────────────────────────────────────────────────────────┘
""")

print("✅ 脚本 03 完成！下一步：04_langgraph_agent.py")
