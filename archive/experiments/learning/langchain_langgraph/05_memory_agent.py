"""
LangChain & LangGraph 学习脚本 05 —— Checkpoint 持久化记忆

对应文档：第七章 7.2
学习目标：
  1. 理解 Checkpoint（检查点）的工作原理
  2. 用 MemorySaver 让 Agent 记住上一轮对话
  3. 理解 thread_id 的作用 —— 区分不同的对话线程
  4. 体验 Time Travel —— 查看历史检查点

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\05_memory_agent.py

类比：
  Checkpoint 就像游戏的存档系统。
  每次对话结束，Agent 的完整状态（所有消息）被"存档"。
  下次用同一个 thread_id 来对话时，从最新存档继续。
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
from langchain_core.messages import (
    AnyMessage, SystemMessage, HumanMessage, ToolMessage
)
from typing_extensions import TypedDict, Annotated
from typing import Literal
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver  # 内存检查点

# ━━━ 模型 + 工具（复用脚本 04 的内容） ━━━

model = ChatOpenAI(
    model=os.getenv("MODEL", "qwen-plus"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0,
)


@tool
def search_knowledge(query: str) -> str:
    """搜索知识库获取信息。

    Args:
        query: 搜索关键词
    """
    kb = {
        "langchain": "LangChain 是一个 LLM 应用开发框架，133K GitHub Stars。",
        "langgraph": "LangGraph 是一个图编排框架，29K Stars，基于 Pregel 模型。",
        "qwen": "Qwen（通义千问）是阿里云推出的大语言模型系列。",
    }
    for key, value in kb.items():
        if key in query.lower():
            return value
    return f"未找到关于 '{query}' 的信息。"


tools = [search_knowledge]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)


# ━━━ State + Node + Edge（同脚本 04） ━━━

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


def llm_node(state: AgentState) -> dict:
    system = SystemMessage(
        content="你是一个有用的 AI 助手。可以搜索知识库。用中文简洁回答。"
    )
    response = model_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    results = []
    for tc in last_message.tool_calls:
        result = tools_by_name[tc["name"]].invoke(tc["args"])
        results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        print(f"  🔧 {tc['name']}({tc['args']}) → {result}")
    return {"messages": results}


def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


# ━━━ 组装图 ━━━

graph_builder = StateGraph(AgentState)
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tool_node", tool_node)
graph_builder.add_edge(START, "llm_node")
graph_builder.add_conditional_edges("llm_node", should_continue)
graph_builder.add_edge("tool_node", "llm_node")

# ══════════════════════════════════════
# 关键区别！编译时加上 checkpointer
# ══════════════════════════════════════

memory = MemorySaver()  # 内存存储（开发用，重启就没了）
# 生产环境用 SqliteSaver 或 PostgresSaver

agent = graph_builder.compile(checkpointer=memory)


# ══════════════════════════════════════
# 演示：有记忆的多轮对话
# ══════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 有记忆的 Agent（Checkpoint 演示）")
    print("=" * 60)

    # thread_id 标识一个对话线程
    # 同一个 thread_id 的对话共享记忆
    config = {"configurable": {"thread_id": "user-xiaoming"}}

    # --- 第一轮对话 ---
    print("\n--- 第一轮 ---")
    result = agent.invoke(
        {"messages": [HumanMessage(content="我叫小明，我在学 LangGraph")]},
        config=config,  # 带上 thread_id！
    )
    print(f"🤖 AI: {result['messages'][-1].content}")

    # --- 第二轮对话 —— Agent 记得你是谁！ ---
    print("\n--- 第二轮（Agent 应该记得你叫小明） ---")
    result = agent.invoke(
        {"messages": [HumanMessage(content="我叫什么名字？我在学什么？")]},
        config=config,  # 同一个 thread_id
    )
    print(f"🤖 AI: {result['messages'][-1].content}")

    # --- 第三轮：使用工具 + 记忆 ---
    print("\n--- 第三轮（使用工具 + 依然记得上下文） ---")
    result = agent.invoke(
        {"messages": [HumanMessage(content="帮我查一下 LangGraph 的信息")]},
        config=config,
    )
    print(f"🤖 AI: {result['messages'][-1].content}")

    # ══════════════════════════════════════
    # 演示：不同 thread_id = 独立的对话
    # ══════════════════════════════════════

    print("\n" + "=" * 60)
    print("🔀 不同 thread_id = 独立记忆")
    print("=" * 60)

    config_other = {"configurable": {"thread_id": "user-xiaohua"}}
    result = agent.invoke(
        {"messages": [HumanMessage(content="我叫什么名字？")]},
        config=config_other,  # 不同的 thread_id
    )
    print(f"🤖 AI（新线程）: {result['messages'][-1].content}")
    print("   （预期：Agent 不知道你叫什么，因为这是新的对话线程）")

    # ══════════════════════════════════════
    # 演示：查看历史检查点（Time Travel）
    # ══════════════════════════════════════

    print("\n" + "=" * 60)
    print("⏰ Time Travel —— 查看历史检查点")
    print("=" * 60)

    print(f"\n对话线程 'user-xiaoming' 的检查点历史：")
    for i, state in enumerate(agent.get_state_history(config)):
        msg_count = len(state.values.get("messages", []))
        checkpoint_id = state.config["configurable"]["checkpoint_id"]
        print(f"  #{i}: checkpoint={checkpoint_id[:20]}... 消息数={msg_count}")

    print("""
┌─────────────────────────────────────────────────────────┐
│ 💡 Checkpoint 的工作原理                                 │
│                                                         │
│ 每次 invoke 完成后，Agent 的完整 State 被保存到          │
│ checkpointer 中（这里是内存，生产用数据库）。            │
│                                                         │
│ 下次用同一个 thread_id 调用时：                          │
│   1. 从 checkpointer 加载最新 State                      │
│   2. 把新消息追加到 State.messages                        │
│   3. 执行图 → 生成回复                                   │
│   4. 保存新的 State 到 checkpointer                      │
│                                                         │
│ Time Travel：可以回到任何历史检查点重新开始               │
│ 用途：调试、回滚、从某个点分叉出新对话                    │
│                                                         │
│ 下一步：Human-in-the-Loop → 06_hitl_agent.py            │
└─────────────────────────────────────────────────────────┘
""")

    print("✅ 脚本 05 完成！下一步：06_hitl_agent.py")
