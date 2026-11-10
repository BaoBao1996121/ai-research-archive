"""
LangChain & LangGraph 学习脚本 04 —— 手搓 LangGraph ReAct Agent

对应文档：第五章 + 第六章（核心脚本！）
学习目标：
  1. 理解 LangGraph 四大核心概念：State / Node / Edge / Graph
  2. 手动实现 create_react_agent 内部做的事情
  3. 看清 ReAct 循环的每一个齿轮怎么转

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\04_langgraph_agent.py

类比（给 C++ 背景的你）：
  - State   ≈ struct（在所有函数间共享的数据结构）
  - Node    ≈ 函数（接收 State，返回更新后的部分 State）
  - Edge    ≈ 函数调用顺序（普通边 = 顺序调用，条件边 = if/switch 分支）
  - Graph   ≈ main()（把所有函数和调用关系组装起来）
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

# ══════════════════════════════════════
# 第一步：准备零件（模型 + 工具）
# ══════════════════════════════════════

model = ChatOpenAI(
    model=os.getenv("MODEL", "qwen-plus"),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    temperature=0,
)


@tool
def search_knowledge(query: str) -> str:
    """搜索知识库获取信息。当需要查找事实性信息时使用。

    Args:
        query: 搜索关键词
    """
    kb = {
        "langchain": "LangChain 是一个 LLM 应用开发框架，133K GitHub Stars。",
        "langgraph": "LangGraph 是一个图编排框架，29K Stars，基于 Pregel 模型。",
        "agent": "Agent 是具有推理、工具使用、记忆和规划能力的 AI 系统。",
        "qwen": "Qwen（通义千问）是阿里云推出的大语言模型系列。",
    }
    for key, value in kb.items():
        if key in query.lower():
            return value
    return f"未找到关于 '{query}' 的信息。"


@tool
def calculator(expression: str) -> str:
    """执行数学计算。当需要数学运算时使用。

    Args:
        expression: 数学表达式，如 '2 + 3 * 4'
    """
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return f"不支持的表达式: {expression}"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"


tools = [search_knowledge, calculator]
tools_by_name = {t.name: t for t in tools}

# 把工具绑定到模型（让 LLM 知道有哪些工具可用）
model_with_tools = model.bind_tools(tools)


# ══════════════════════════════════════
# 第二步：定义 State（Agent 的随身背包）
# ══════════════════════════════════════

class AgentState(TypedDict):
    """
    Agent 的状态，在所有节点之间共享。

    Annotated[list[AnyMessage], operator.add] 的含义：
      - messages 是一个消息列表
      - operator.add 是 Reducer：每次更新时，新消息"追加"到列表末尾
      - 类比 C++：就像 vector::insert(end, new_items.begin(), new_items.end())
      - 如果不用 operator.add，每次更新会"替换"整个列表
    """
    messages: Annotated[list[AnyMessage], operator.add]


# ══════════════════════════════════════
# 第三步：定义 Node（做具体事情的函数）
# ══════════════════════════════════════

def llm_node(state: AgentState) -> dict:
    """
    节点 1：调用 LLM

    LLM 看到当前所有消息，做出决策：
    - 要调工具 → 返回带 tool_calls 的 AIMessage
    - 直接回答 → 返回纯文本的 AIMessage
    """
    system = SystemMessage(
        content="你是一个有用的 AI 助手。可以搜索知识库和做计算。用中文简洁回答。"
    )
    messages = [system] + state["messages"]

    response = model_with_tools.invoke(messages)

    # 返回 {"messages": [新消息]}
    # 因为 State 的 messages 用了 operator.add Reducer，
    # 新消息会被追加到列表末尾，而不是替换
    return {"messages": [response]}


def tool_node(state: AgentState) -> dict:
    """
    节点 2：执行工具

    从 LLM 最后一条消息中取出 tool_calls，
    逐个执行，把结果包装成 ToolMessage 返回。
    """
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # 执行工具
        tool_fn = tools_by_name[tool_name]
        result = tool_fn.invoke(tool_args)

        # 包装成 ToolMessage（必须带 tool_call_id，LLM 靠它匹配）
        results.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )
        print(f"  🔧 调用工具 {tool_name}({tool_args}) → {result}")

    return {"messages": results}


# ══════════════════════════════════════
# 第四步：定义路由逻辑（条件边）
# ══════════════════════════════════════

def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """
    条件边的路由函数：

    检查 LLM 最后一条消息是否包含 tool_calls：
    - 有 tool_calls → 去 tool_node 执行工具
    - 没有 tool_calls → 结束（LLM 直接给出了最终回答）

    类比 C++：这就是一个 switch 语句，返回值决定下一步跳到哪个函数
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_node"
    return END  # "__end__" 是 LangGraph 的特殊标记


# ══════════════════════════════════════
# 第五步：组装图！！！
# ══════════════════════════════════════

# 1. 创建图，指定 State 类型
graph_builder = StateGraph(AgentState)

# 2. 添加节点（注册函数）
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tool_node", tool_node)

# 3. 添加边（定义执行顺序）
graph_builder.add_edge(START, "llm_node")           # 起点 → LLM
graph_builder.add_conditional_edges(                 # LLM → 工具或结束
    "llm_node",
    should_continue
)
graph_builder.add_edge("tool_node", "llm_node")     # 工具 → 回到 LLM（循环！）

# 4. 编译（把图定义变成可执行的对象）
agent = graph_builder.compile()

# 尝试打印图结构（Mermaid 格式）
print("📊 Agent 图结构（Mermaid）:")
print(agent.get_graph().draw_mermaid())
print()

# ══════════════════════════════════════
# 第六步：运行测试！
# ══════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 LangGraph Agent（手动版）")
    print("=" * 60)

    # --- 测试 1：需要查知识的问题 ---
    print("\n--- 测试 1：查询知识 ---")
    result = agent.invoke({
        "messages": [HumanMessage(content="LangGraph 是什么？")]
    })
    print(f"✅ 回答: {result['messages'][-1].content}")

    # --- 测试 2：需要计算的问题 ---
    print("\n--- 测试 2：数学计算 ---")
    result = agent.invoke({
        "messages": [HumanMessage(content="计算 (15 + 27) * 3")]
    })
    print(f"✅ 回答: {result['messages'][-1].content}")

    # --- 测试 3：不需要工具的问题 ---
    print("\n--- 测试 3：直接回答（不调工具） ---")
    result = agent.invoke({
        "messages": [HumanMessage(content="你好，用一句话介绍你自己")]
    })
    print(f"✅ 回答: {result['messages'][-1].content}")

    # --- 测试 4：链式推理（最精彩的部分！） ---
    print("\n--- 测试 4：链式推理（先查后算） ---")
    print("问题: 查一下 LangChain 的信息，然后告诉我它的 Stars 数翻倍会是多少")
    result = agent.invoke({
        "messages": [HumanMessage(
            content="帮我查一下 LangChain 的信息，然后告诉我如果它的 Stars 数翻倍会是多少"
        )]
    })
    print(f"✅ 回答: {result['messages'][-1].content}")

    print("""
┌─────────────────────────────────────────────────────────────┐
│ 💡 现在你理解了 create_react_agent 内部做的事情              │
│                                                             │
│ 整个流程就是一个循环：                                       │
│   START → llm_node → should_continue?                       │
│                       ├─ 有 tool_calls → tool_node → llm_node │
│                       └─ 无 tool_calls → END                │
│                                                             │
│ 所有 "智能" 来自 LLM 的决策                                 │
│ LangGraph 只负责编排这个决策循环                             │
│                                                             │
│ 下一步：给 Agent 加记忆 → 05_memory_agent.py                │
└─────────────────────────────────────────────────────────────┘
""")

    print("✅ 脚本 04 完成！下一步：05_memory_agent.py")
