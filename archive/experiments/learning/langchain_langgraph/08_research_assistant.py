"""
LangChain & LangGraph 学习脚本 08 —— 实战项目：研究助手

对应文档：第八章
学习目标：
  综合运用前面学到的全部技能：
  1. 多节点图编排（5 个节点）
  2. 自定义复杂 State
  3. 条件路由（审批通过/拒绝走不同分支）
  4. Human-in-the-Loop（大纲审批）
  5. Checkpoint 持久化
  6. 循环图（审批不通过 → 修改大纲 → 再审批）

运行：
  .venv\\Scripts\\python.exe experiments\\learning\\langchain_langgraph\\08_research_assistant.py

图结构：
  START → understand → search → outline → review ─┐
                                    ↑              │
                                    └──── 拒绝 ────┘
                                           │
                                         通过
                                           ↓
                                         write → END
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
    AnyMessage, SystemMessage, HumanMessage, AIMessage
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

# ━━━ 工具 ━━━

@tool
def web_search(query: str) -> str:
    """搜索互联网获取信息。

    Args:
        query: 搜索关键词
    """
    # 模拟搜索结果（实际项目中接入 Tavily / SerpAPI 等）
    results = {
        "langgraph": """
LangGraph（29.2K⭐）是 LangChain 推出的图编排框架。
核心特性：基于 Pregel 图计算模型、持久化检查点、HITL。
使用者：Klarna、Replit、Elastic。
最新版本 1.1.7（2026-04-10）。
竞品：CrewAI（48.8K⭐）、OpenAI Agents SDK（20.8K⭐）。
""",
        "agent framework": """
2026 年 Agent 框架三大派系：
图编排派：LangGraph / Microsoft Agent Framework
角色编排派：CrewAI
轻量 SDK 派：OpenAI Agents SDK / Pydantic AI
""",
        "qwen": """
通义千问（Qwen）是阿里云推出的大语言模型系列。
Qwen-Plus 是主力模型，平衡效果和成本。
通过 DashScope API 提供 OpenAI 兼容接口。
""",
    }
    for key, value in results.items():
        if key in query.lower():
            return value.strip()
    return f"搜索 '{query}' 暂无结果。建议尝试更具体的关键词。"


# ━━━ State（比之前复杂——研究任务需要更多字段） ━━━

class ResearchState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    topic: str              # 研究主题
    search_results: str     # 搜索结果
    outline: str            # 生成的大纲
    report: str             # 最终报告
    revision_count: int     # 修改次数


# ━━━ 节点定义（5 个节点，各司其职） ━━━

def understand_topic(state: ResearchState) -> dict:
    """节点 1：理解用户的研究问题，提取核心主题"""
    user_question = state["messages"][-1].content

    response = model.invoke([
        SystemMessage(content=(
            "你是一个研究助手。从用户的问题中提取核心研究主题，"
            "用一个简短的词组概括。只输出主题，不要其他内容。"
        )),
        HumanMessage(content=user_question)
    ])

    topic = response.content.strip()
    print(f"  📌 识别研究主题: {topic}")

    return {
        "topic": topic,
        "messages": [AIMessage(content=f"好的，我将为你研究：{topic}")]
    }


def search_info(state: ResearchState) -> dict:
    """节点 2：搜索相关信息"""
    topic = state["topic"]
    print(f"  🔍 搜索中: {topic}")

    result = web_search.invoke({"query": topic})
    print(f"  📄 搜索完成，获取到 {len(result)} 字符的信息")

    return {
        "search_results": result,
        "messages": [AIMessage(content=f"已搜索到关于 {topic} 的信息。")]
    }


def generate_outline(state: ResearchState) -> dict:
    """节点 3：基于搜索结果生成大纲"""
    topic = state["topic"]
    search_results = state.get("search_results", "暂无搜索结果")
    revision_count = state.get("revision_count", 0)

    # 如果有修改反馈，加入 prompt
    feedback_context = ""
    if revision_count > 0:
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                feedback_context = f"\n\n用户的修改意见：{msg.content}"
                break

    response = model.invoke([
        SystemMessage(content=f"""你是一个研究报告大纲生成器。
基于以下信息，为 "{topic}" 生成一个结构化的研究大纲。

搜索结果：
{search_results}
{feedback_context}

要求：
- 3-5 个主要章节
- 每个章节 2-3 个要点
- 格式清晰，用 Markdown 列表
- 如果这是修改版，说明做了什么改动"""),
        HumanMessage(content=f"请为 {topic} 生成研究大纲。")
    ])

    outline = response.content
    print(f"  📋 大纲生成完成（第 {revision_count + 1} 版）")

    return {
        "outline": outline,
        "revision_count": revision_count + 1,
        "messages": [AIMessage(content=f"大纲已生成（第 {revision_count + 1} 版）：\n\n{outline}")]
    }


def human_review(state: ResearchState) -> dict:
    """节点 4：人工审批大纲（使用 interrupt 暂停）"""
    outline = state["outline"]
    revision_count = state.get("revision_count", 1)

    # interrupt 暂停执行，等待用户输入
    response = interrupt(
        f"📋 请审核大纲（第 {revision_count} 版）。\n"
        f"输入 'yes' 通过，或输入修改意见：\n\n{outline}"
    )

    return {
        "messages": [HumanMessage(content=response)]
    }


def write_report(state: ResearchState) -> dict:
    """节点 5：生成最终报告"""
    topic = state["topic"]
    outline = state["outline"]
    search_results = state.get("search_results", "")

    print(f"  📝 正在生成报告...")

    response = model.invoke([
        SystemMessage(content=f"""你是一个研究报告写作专家。
基于以下大纲和参考资料，写一篇完整的研究报告。

大纲：
{outline}

参考资料：
{search_results}

要求：
- 专业但易懂
- 每个章节有具体信息，不要空洞
- 结论部分给出明确建议
- 使用 Markdown 格式
- 控制在 500 字以内"""),
        HumanMessage(content=f"请撰写 {topic} 的研究报告。")
    ])

    report = response.content
    print(f"  📝 报告生成完成，{len(report)} 字符")

    return {
        "report": report,
        "messages": [AIMessage(content=f"报告已完成！\n\n{report}")]
    }


# ━━━ 路由逻辑 ━━━

def review_decision(state: ResearchState) -> Literal["generate_outline", "write_report"]:
    """审批后的路由：通过 → 写报告，拒绝 → 修改大纲"""
    last_message = state["messages"][-1]

    if isinstance(last_message, HumanMessage):
        answer = last_message.content.strip().lower()
        if answer in ("yes", "y", "通过", "可以", "ok"):
            print("  ✅ 大纲通过审批 → 生成报告")
            return "write_report"
        else:
            print(f"  🔄 需要修改大纲（用户意见: {last_message.content[:50]}...）")
            return "generate_outline"

    return "write_report"


# ━━━ 组装图 ━━━

graph = StateGraph(ResearchState)

# 添加节点
graph.add_node("understand", understand_topic)
graph.add_node("search", search_info)
graph.add_node("outline", generate_outline)
graph.add_node("review", human_review)
graph.add_node("write", write_report)

# 添加边
graph.add_edge(START, "understand")             # 起点 → 理解问题
graph.add_edge("understand", "search")          # 理解 → 搜索
graph.add_edge("search", "outline")             # 搜索 → 生成大纲
graph.add_edge("outline", "review")             # 大纲 → 人工审批
graph.add_conditional_edges("review", review_decision)  # 审批 → 通过/拒绝
graph.add_edge("write", END)                    # 写报告 → 结束

# 编译（带 checkpointer 以支持 interrupt）
research_agent = graph.compile(checkpointer=MemorySaver())

# 打印图结构
print("📊 研究助手图结构（Mermaid）:")
print(research_agent.get_graph().draw_mermaid())
print()


# ══════════════════════════════════════
# 运行演示
# ══════════════════════════════════════

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "research-001"}}

    print("=" * 60)
    print("🎯 启动研究助手")
    print("=" * 60)

    # --- Step 1：提交研究问题 ---
    print("\n[Step 1] 提交研究问题...")
    print("  用户: 帮我调研一下 LangGraph 框架")
    print()

    result = research_agent.invoke(
        {"messages": [HumanMessage(
            content="帮我调研一下 LangGraph 框架，包括它的核心特性、竞争对手和适用场景"
        )]},
        config=config,
    )

    # Agent 在 review 节点的 interrupt 处暂停了
    state = research_agent.get_state(config)
    print(f"\n  ⏸️  Agent 已暂停，等待审批")
    outline = state.values.get("outline", "")
    if outline:
        print(f"\n  当前大纲（前 300 字）:\n{outline[:300]}...")

    # --- Step 2：审批大纲 ---
    print("\n" + "=" * 60)
    print("[Step 2] 用户审批大纲: yes（通过）")
    print("=" * 60)

    result = research_agent.invoke(
        Command(resume="yes"),
        config=config,
    )

    # --- 输出最终报告 ---
    print("\n" + "=" * 60)
    print("📝 最终报告:")
    print("=" * 60)

    final_report = state.values.get("report", "")
    if not final_report:
        # 报告在最后一条消息中
        final_report = result["messages"][-1].content
    print(final_report[:800])
    if len(final_report) > 800:
        print(f"\n... (共 {len(final_report)} 字符)")

    print("""
┌─────────────────────────────────────────────────────────────┐
│ 🎓 这个项目综合运用了 LangGraph 的全部核心技能             │
│                                                             │
│ ┌──────────────────┬──────────────────────────────────┐     │
│ │ 技能             │ 在项目中的体现                    │     │
│ ├──────────────────┼──────────────────────────────────┤     │
│ │ State 设计       │ ResearchState 含 6 个字段         │     │
│ │ 多节点图         │ 5 个节点各司其职                  │     │
│ │ 条件路由         │ review_decision 分支              │     │
│ │ HITL             │ interrupt() 在大纲审批处暂停      │     │
│ │ Checkpoint       │ MemorySaver 支持暂停/恢复         │     │
│ │ 循环图           │ 审批不通过 → 修改 → 再审批        │     │
│ └──────────────────┴──────────────────────────────────┘     │
│                                                             │
│ 🎉 恭喜！你已经掌握了 LangGraph 的核心能力！               │
│                                                             │
│ 下一步建议：                                                │
│ - 把模拟的 web_search 换成真实 API（如 Tavily）            │
│ - 把 MemorySaver 换成 SqliteSaver（持久化到磁盘）          │
│ - 加一个"写作者"子图，拆分报告生成的多个步骤               │
│ - 接入 LangSmith 看完整的执行追踪                           │
└─────────────────────────────────────────────────────────────┘
""")

    print("✅ 全部 8 个脚本完成！LangChain & LangGraph 入门到实战学习路径结束。")
