"""
LangChain & LangGraph 学习脚本 07 —— 流式输出

对应文档：第七章 7.4
学习目标：
  1. 事件级流式（stream_mode="updates"）—— 看到每个节点的执行
  2. Token 级流式（stream_mode="messages"）—— 逐字输出
  3. 理解两种流式模式的适用场景

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\07_streaming_agent.py
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
from langgraph.checkpoint.memory import MemorySaver

# ━━━ 模型 + 工具 ━━━

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
        "langchain": "LangChain 是一个 LLM 应用开发框架，133K GitHub Stars，支持多种模型。",
        "langgraph": "LangGraph 是基于 Pregel 模型的图编排框架，29K Stars。",
        "agent": "Agent 是具有推理、工具使用、记忆和规划能力的 AI 系统。",
    }
    for key, value in kb.items():
        if key in query.lower():
            return value
    return f"未找到关于 '{query}' 的信息。"


tools = [search_knowledge]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)


# ━━━ State + Nodes + Graph ━━━

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


def llm_node(state: AgentState) -> dict:
    system = SystemMessage(content="你是一个有用的 AI 助手。可以搜索知识库。用中文回答。")
    response = model_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        result = tools_by_name[tc["name"]].invoke(tc["args"])
        results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return {"messages": results}


def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


graph_builder = StateGraph(AgentState)
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tool_node", tool_node)
graph_builder.add_edge(START, "llm_node")
graph_builder.add_conditional_edges("llm_node", should_continue)
graph_builder.add_edge("tool_node", "llm_node")

agent = graph_builder.compile(checkpointer=MemorySaver())


# ══════════════════════════════════════
# 演示
# ══════════════════════════════════════

if __name__ == "__main__":
    # ━━━ 方式 1：事件级流式 ━━━
    print("=" * 60)
    print("📡 方式 1：事件级流式（stream_mode='updates'）")
    print("   每个节点完成时报告一次")
    print("=" * 60)

    config1 = {"configurable": {"thread_id": "stream-updates"}}

    for event in agent.stream(
        {"messages": [HumanMessage(content="LangGraph 是什么？")]},
        config=config1,
        stream_mode="updates",  # 每个节点更新一次
    ):
        for node_name, node_output in event.items():
            print(f"\n  📦 节点 [{node_name}] 输出:")
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    role = type(msg).__name__
                    content = msg.content[:120] if msg.content else "(无文本)"
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"     {role} → 调用工具: {tc['name']}({tc['args']})")
                    else:
                        print(f"     {role}: {content}")

    print()

    # ━━━ 方式 2：Token 级流式（逐字输出） ━━━
    print("=" * 60)
    print("📡 方式 2：Token 级流式（stream_mode='messages'）")
    print("   像打字机一样逐字输出")
    print("=" * 60)

    config2 = {"configurable": {"thread_id": "stream-messages"}}

    print("\n  问题：写一首关于编程的四行短诗")
    print("  回答：", end="", flush=True)

    for msg, metadata in agent.stream(
        {"messages": [HumanMessage(content="写一首关于编程的四行短诗，不需要搜索知识库")]},
        config=config2,
        stream_mode="messages",  # 消息级（Token by Token）
    ):
        # 只打印 AI 的文本内容（跳过工具调用等）
        if msg.content and metadata.get("langgraph_node") == "llm_node":
            print(msg.content, end="", flush=True)

    print("\n")  # 换行

    # ━━━ 方式 3：带工具调用的流式 ━━━
    print("=" * 60)
    print("📡 方式 3：带工具调用的事件级流式")
    print("   观察完整的 ReAct 循环过程")
    print("=" * 60)

    config3 = {"configurable": {"thread_id": "stream-with-tools"}}

    print("\n  问题：帮我查一下 Agent 的定义\n")

    for event in agent.stream(
        {"messages": [HumanMessage(content="帮我查一下 Agent 的定义")]},
        config=config3,
        stream_mode="updates",
    ):
        for node_name, node_output in event.items():
            print(f"  ⏱️  [{node_name}]", end=" → ")
            if "messages" in node_output:
                msg = node_output["messages"][-1]
                role = type(msg).__name__
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tc = msg.tool_calls[0]
                    print(f"调用 {tc['name']}({tc['args']})")
                elif role == "ToolMessage":
                    print(f"工具返回: {msg.content[:60]}...")
                else:
                    print(f"{msg.content[:80]}...")

    print("""
┌─────────────────────────────────────────────────────────┐
│ 💡 两种流式模式的选择                                    │
│                                                         │
│ stream_mode="updates"（事件级）：                        │
│   - 每个节点完成时触发                                   │
│   - 适合：展示执行进度、调试、日志                       │
│   - 粒度：节点级                                         │
│                                                         │
│ stream_mode="messages"（Token 级）：                     │
│   - 每个 Token 生成时触发                                │
│   - 适合：ChatUI 逐字显示回答                            │
│   - 粒度：Token 级                                       │
│                                                         │
│ 下一步：完整实战项目 → 08_research_assistant.py           │
└─────────────────────────────────────────────────────────┘
""")

    print("✅ 脚本 07 完成！下一步：08_research_assistant.py")
