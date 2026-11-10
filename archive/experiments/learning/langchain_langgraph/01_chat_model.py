"""
LangChain & LangGraph 学习脚本 01 —— ChatModel + Messages

对应文档：第三章 3.2~3.3
学习目标：
  1. 理解 ChatOpenAI 如何连接 Qwen（DashScope）
  2. 理解 Messages 消息格式（System / Human / AI）
  3. 体验多轮对话消息的组织方式

运行：
  cd F:\\AI2025\\Agent研究
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\01_chat_model.py

前置：
  pip install langchain-openai python-dotenv
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ━━━ 加载 .env 配置 ━━━
_root = Path(__file__).resolve().parent
while _root != _root.parent:
    if (_root / ".env").exists():
        break
    _root = _root.parent
load_dotenv(_root / ".env")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 创建 ChatModel —— 连接 Qwen
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from langchain_openai import ChatOpenAI

# DashScope 提供 OpenAI 兼容接口，所以直接用 ChatOpenAI
# 类比 C++：ChatOpenAI 就像一个接口类（interface），
# 不管后面是 GPT-4o 还是 Qwen，调用方式完全一样
model = ChatOpenAI(
    model=os.getenv("MODEL", "qwen-plus"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0,  # 0 = 确定性输出，学习阶段推荐
)

print("=" * 60)
print("📚 示例 1：最简单的调用 —— 一句话问答")
print("=" * 60)

# invoke() 是 LangChain 的统一调用方法
# 传入字符串，返回 AIMessage 对象
response = model.invoke("什么是 Agent？用一句话解释。")
print(f"类型: {type(response).__name__}")  # AIMessage
print(f"回答: {response.content}")
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Messages —— 标准化的对话格式
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

print("=" * 60)
print("📚 示例 2：用 Messages 构建多轮对话")
print("=" * 60)

# LLM 的对话本质上是一串消息列表
# 类比 C++：这就像一个 std::vector<Message>，按顺序记录对话
messages = [
    # SystemMessage：给 AI 设定角色（相当于员工入职手册）
    SystemMessage(content="你是一个 AI Agent 领域的专家。回答简洁，不超过两句话。"),

    # HumanMessage：用户的输入
    HumanMessage(content="什么是 LangGraph？"),
]

response = model.invoke(messages)
print(f"Q: 什么是 LangGraph？")
print(f"A: {response.content}")
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 多轮对话 —— 把历史消息全部传入
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("📚 示例 3：多轮对话 —— LLM 如何 '记住' 上下文")
print("=" * 60)

# 关键理解：LLM 本身没有记忆！
# 所谓"记住"，其实是你把所有历史消息一起发给它
# 类比 C#：就像每次调 API 都把完整的 List<ChatMessage> 传过去

messages = [
    SystemMessage(content="你是一个乐于助人的 AI 助手。"),
    HumanMessage(content="我叫小明，我正在学习 LangGraph。"),
]

# 第一轮
response1 = model.invoke(messages)
print(f"用户: 我叫小明，我正在学习 LangGraph。")
print(f"AI:   {response1.content}")

# 把 AI 的回复也加入历史
messages.append(response1)  # response1 本身就是 AIMessage

# 第二轮 —— 追问
messages.append(HumanMessage(content="我叫什么名字？我在学什么？"))
response2 = model.invoke(messages)
print(f"\n用户: 我叫什么名字？我在学什么？")
print(f"AI:   {response2.content}")
print()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 消息类型总结
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 60)
print("📚 示例 4：四种消息类型一览")
print("=" * 60)

print("""
┌─────────────────┬──────────────────────┬─────────────────────┐
│ 类型            │ 用途                 │ 类比                │
├─────────────────┼──────────────────────┼─────────────────────┤
│ SystemMessage   │ 给 AI 设定角色和规则 │ 员工入职手册        │
│ HumanMessage    │ 用户的输入           │ 客户提的需求        │
│ AIMessage       │ AI 的回复            │ 员工的回答          │
│ ToolMessage     │ 工具执行的结果       │ 员工查完资料带回的  │
└─────────────────┴──────────────────────┴─────────────────────┘

关键洞察：LLM 没有真正的"记忆"，多轮对话是靠把完整的
messages 列表每次都传进去实现的。当对话很长时，消息列表
会超过模型的上下文限制 —— 这就是后面学 LangGraph 的
Checkpoint 和 Memory 要解决的问题。
""")

print("✅ 脚本 01 完成！下一步：02_tools_basics.py")
