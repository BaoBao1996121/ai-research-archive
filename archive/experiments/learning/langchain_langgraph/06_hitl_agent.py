"""
LangChain & LangGraph 学习脚本 06 —— Human-in-the-Loop（人工审批）

对应文档：第七章 7.3
学习目标：
  1. 理解 interrupt() 如何暂停 Agent 执行
  2. 理解 Command(resume=...) 如何恢复执行
  3. 理解 HITL 为什么必须搭配 Checkpoint 使用
  4. 实现"危险操作前先审批"的工作流

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\06_hitl_agent.py

核心概念：
  interrupt() 不是 input()！
  - input() 阻塞进程等待输入（服务器会卡死）
  - interrupt() 保存状态到 Checkpoint → 程序退出
  - 用户审批后 → 加载 Checkpoint → 从暂停的地方继续
  - 这才是生产级 HITL 的正确实现方式
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
    AnyMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
)
from typing_extensions import TypedDict, Annotated
from typing import Literal
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

# ━━━ 模型 ━━━

model = ChatOpenAI(
    model=os.getenv("MODEL", "qwen-plus"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0,
)

# ━━━ 工具（包含一个"危险"操作） ━━━

@tool
def search_info(query: str) -> str:
    """搜索信息。安全操作，不需要审批。

    Args:
        query: 搜索关键词
    """
    return f"关于 '{query}' 的搜索结果：这是一个模拟的搜索结果。"


@tool
def delete_file(filename: str) -> str:
    """删除指定文件。这是一个危险操作，需要人工审批。

    Args:
        filename: 要删除的文件名
    """
    # 这里只是模拟，不会真的删除文件
    return f"已删除文件: {filename}"


tools = [search_info, delete_file]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)


# ━━━ State ━━━

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


# ━━━ 节点 ━━━

def llm_node(state: AgentState) -> dict:
    system = SystemMessage(
        content="你是一个文件管理助手。可以搜索信息和删除文件。用中文回答。"
    )
    response = model_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}


def tool_node_with_approval(state: AgentState) -> dict:
    """
    带人工审批的工具节点。

    对于危险操作（delete_file），用 interrupt() 暂停执行，
    等待用户确认后才继续。
    """
    last_message = state["messages"][-1]
    results = []

    for tc in last_message.tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]

        # 危险操作 → 需要人工审批
        if tool_name == "delete_file":
            print(f"  ⚠️  检测到危险操作: {tool_name}({tool_args})")
            print(f"  ⏸️  暂停执行，等待人工审批...")

            # interrupt() 做了三件事：
            # 1. 保存当前 State 到 Checkpoint
            # 2. 暂停图的执行
            # 3. 返回提示信息给调用者
            # 当用户通过 Command(resume=...) 恢复时，
            # human_response 接收到用户的回复
            human_response = interrupt(
                f"⚠️ Agent 要删除文件 '{tool_args.get('filename', '?')}'，是否允许？"
            )

            if human_response.strip().lower() not in ("yes", "y", "是"):
                results.append(ToolMessage(
                    content=f"用户拒绝了删除 {tool_args.get('filename', '?')} 的请求。",
                    tool_call_id=tc["id"]
                ))
                print(f"  ❌ 用户拒绝了删除操作")
                continue
            else:
                print(f"  ✅ 用户批准了删除操作")

        # 安全操作或已审批的操作 → 直接执行
        tool_fn = tools_by_name[tool_name]
        result = tool_fn.invoke(tool_args)
        results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        print(f"  🔧 执行: {tool_name}({tool_args}) → {result}")

    return {"messages": results}


def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END


# ━━━ 组装图 ━━━

graph_builder = StateGraph(AgentState)
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tool_node", tool_node_with_approval)  # 用带审批的版本！
graph_builder.add_edge(START, "llm_node")
graph_builder.add_conditional_edges("llm_node", should_continue)
graph_builder.add_edge("tool_node", "llm_node")

# 必须有 checkpointer！interrupt 需要存档才能暂停/恢复
agent = graph_builder.compile(checkpointer=MemorySaver())


# ══════════════════════════════════════
# 演示
# ══════════════════════════════════════

if __name__ == "__main__":
    # ━━━ 场景 1：安全操作（不需要审批） ━━━
    print("=" * 60)
    print("🧪 场景 1：安全操作（搜索，不触发审批）")
    print("=" * 60)

    config1 = {"configurable": {"thread_id": "safe-op"}}
    result = agent.invoke(
        {"messages": [HumanMessage(content="帮我搜索一下 Python 的最新版本")]},
        config=config1,
    )
    print(f"🤖 AI: {result['messages'][-1].content}")

    # ━━━ 场景 2：危险操作 → 暂停 → 批准 → 继续 ━━━
    print("\n" + "=" * 60)
    print("🧪 场景 2：危险操作 → 暂停 → 用户批准 → 继续执行")
    print("=" * 60)

    config2 = {"configurable": {"thread_id": "delete-approved"}}

    # 第一步：用户请求删除文件
    # Agent 执行到 interrupt() 时会暂停
    print("\n[Step 1] 用户请求删除文件...")
    result = agent.invoke(
        {"messages": [HumanMessage(content="帮我删除 temp.txt 文件")]},
        config=config2,
    )
    # 此时 agent 已暂停在 interrupt 处
    print(f"\n  ⏸️  Agent 已暂停，等待审批")

    # 第二步：用户审批通过
    print("\n[Step 2] 用户审批：yes（批准）")
    result = agent.invoke(
        Command(resume="yes"),
        config=config2,
    )
    print(f"🤖 AI: {result['messages'][-1].content}")

    # ━━━ 场景 3：危险操作 → 暂停 → 拒绝 ━━━
    print("\n" + "=" * 60)
    print("🧪 场景 3：危险操作 → 暂停 → 用户拒绝")
    print("=" * 60)

    config3 = {"configurable": {"thread_id": "delete-rejected"}}

    print("\n[Step 1] 用户请求删除文件...")
    result = agent.invoke(
        {"messages": [HumanMessage(content="帮我删除 important_data.db 文件")]},
        config=config3,
    )
    print(f"\n  ⏸️  Agent 已暂停，等待审批")

    print("\n[Step 2] 用户审批：no（拒绝）")
    result = agent.invoke(
        Command(resume="no"),
        config=config3,
    )
    print(f"🤖 AI: {result['messages'][-1].content}")

    print("""
┌─────────────────────────────────────────────────────────┐
│ 💡 HITL 的核心机制                                       │
│                                                         │
│ 为什么 interrupt() 需要 Checkpoint？                     │
│                                                         │
│   interrupt() ≠ input()                                  │
│   - input() 阻塞进程 → 服务器卡死                       │
│   - interrupt() 保存 State → 程序退出                    │
│   - Command(resume=...) 加载 State → 继续执行            │
│                                                         │
│ 执行流程：                                               │
│   1. invoke("删除 temp.txt") → 执行到 interrupt()       │
│   2. State 保存到 Checkpoint → 函数返回                  │
│   3. （时间流逝... 用户思考... 可能隔几小时）            │
│   4. invoke(Command(resume="yes")) → 加载 Checkpoint    │
│   5. 从 interrupt() 处继续 → 执行删除 → LLM 汇总        │
│                                                         │
│ 这就是企业级 Agent 的"审批工作流"的基础。               │
│                                                         │
│ 下一步：流式输出 → 07_streaming_agent.py                 │
└─────────────────────────────────────────────────────────┘
""")

    print("✅ 脚本 06 完成！下一步：07_streaming_agent.py")
