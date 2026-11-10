"""
02_langgraph.py — LangGraph 实现异步监控回调模式

核心机制：
  LangGraph 的 interrupt() + Checkpointer 天然支持"暂停等待 → 恢复执行"模式。
  这就是 VS Code Copilot 终端监控的框架级实现。

运行方式：
  pip install langgraph langchain-core
  python 02_langgraph.py  （无需 API key，使用模拟 LLM）

关键概念：
  1. interrupt() — 暂停图执行，等待外部事件
  2. Checkpointer — 序列化当前状态，支持暂停/恢复
  3. Command(resume=...) — 外部事件完成后，注入结果并恢复执行
"""
import asyncio
import time
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


# ============================================================
# 状态定义
# ============================================================

class AgentState(TypedDict):
    """Agent 的状态——图中每个节点共享的数据"""
    messages: Annotated[list, add_messages]  # 消息历史
    pending_tasks: list[dict]                # 待处理的异步任务
    completed_results: list[dict]            # 已完成的结果
    current_action: str                      # 当前动作


# ============================================================
# 模拟异步任务
# ============================================================

def simulate_oauth_check() -> dict:
    """模拟检查 OAuth 授权状态"""
    # 真实场景：调用 lark-cli auth status 检查
    return {
        "status": "authorized",
        "user": "示例用户",
        "token": "fake-token-12345",
    }


def simulate_build_result() -> dict:
    """模拟构建结果"""
    return {
        "status": "success",
        "duration": "45s",
        "artifacts": ["dist/app.js"],
    }


# ============================================================
# 图节点
# ============================================================

def parse_request(state: AgentState) -> dict:
    """解析用户请求，决定下一步"""
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""

    print(f"\n  [parse_request] 收到: {last_msg}")

    if "登录" in last_msg or "auth" in last_msg.lower():
        return {
            "current_action": "oauth_login",
            "messages": [{"role": "assistant", "content": "正在启动 OAuth 登录..."}],
        }
    elif "构建" in last_msg or "build" in last_msg.lower():
        return {
            "current_action": "build_project",
            "messages": [{"role": "assistant", "content": "正在启动项目构建..."}],
        }
    else:
        return {
            "current_action": "direct_reply",
            "messages": [{"role": "assistant", "content": f"已处理: {last_msg}"}],
        }


def start_async_task(state: AgentState) -> dict:
    """
    启动异步任务并暂停图执行

    这里用 interrupt() 实现"暂停等待外部事件"——
    相当于 Copilot 的 mode=async 终端命令。

    当 interrupt() 被调用时：
    1. 当前图状态被 Checkpointer 序列化保存
    2. 图执行暂停，控制权交回调用者
    3. 调用者（主程序）可以去做其他事情
    4. 外部事件完成后，用 Command(resume=result) 恢复
    """
    action = state.get("current_action", "")
    print(f"\n  [start_async_task] 动作: {action}")

    if action == "oauth_login":
        print("  [start_async_task] 暂停图执行，等待用户在浏览器完成 OAuth 授权...")
        print("  [start_async_task] 授权链接: https://example.com/auth?code=XXXX")

        # interrupt() — 暂停执行，等待外部事件
        # 返回值就是 Command(resume=xxx) 传入的 xxx
        auth_result = interrupt({
            "type": "oauth_login",
            "message": "请在浏览器中完成授权",
            "url": "https://example.com/auth?code=XXXX",
        })

        print(f"  [start_async_task] 授权完成! 结果: {auth_result}")
        return {
            "completed_results": [{"task": "oauth", "result": auth_result}],
            "messages": [{"role": "assistant", "content":
                f"OAuth 授权成功! 用户: {auth_result.get('user', 'unknown')}"}],
        }

    elif action == "build_project":
        print("  [start_async_task] 暂停图执行，等待构建完成...")

        build_result = interrupt({
            "type": "build_project",
            "message": "项目正在构建中...",
        })

        print(f"  [start_async_task] 构建完成! 结果: {build_result}")
        return {
            "completed_results": [{"task": "build", "result": build_result}],
            "messages": [{"role": "assistant", "content":
                f"构建完成! 状态: {build_result.get('status', 'unknown')}"}],
        }

    return {}


def direct_reply(state: AgentState) -> dict:
    """直接回复，不涉及异步任务"""
    return {
        "messages": [{"role": "assistant", "content": "已处理你的请求。"}],
    }


# ============================================================
# 路由
# ============================================================

def route_action(state: AgentState) -> str:
    """根据 current_action 路由到不同节点"""
    action = state.get("current_action", "direct_reply")
    if action in ("oauth_login", "build_project"):
        return "async_task"
    return "direct_reply"


# ============================================================
# 构建图
# ============================================================

def build_graph():
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("parse", parse_request)
    graph.add_node("async_task", start_async_task)
    graph.add_node("direct_reply", direct_reply)

    # 添加边
    graph.add_edge(START, "parse")
    graph.add_conditional_edges("parse", route_action, {
        "async_task": "async_task",
        "direct_reply": "direct_reply",
    })
    graph.add_edge("async_task", END)
    graph.add_edge("direct_reply", END)

    # 编译——必须有 checkpointer 才能用 interrupt
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ============================================================
# 主程序：演示完整的异步回调流程
# ============================================================

async def main():
    print("=" * 60)
    print("  LangGraph 异步监控回调模式演示")
    print("  （interrupt + Checkpointer 实现暂停/恢复）")
    print("=" * 60)

    agent = build_graph()
    config = {"configurable": {"thread_id": "demo-session-1"}}

    # ============================================================
    # 场景 1: OAuth 登录（暂停 → 等用户操作 → 恢复）
    # ============================================================
    print("\n" + "=" * 60)
    print("  场景 1: OAuth 登录")
    print("=" * 60)

    # Step 1: 发送请求，触发 interrupt
    print("\n  [主程序] Step 1: 发送登录请求...")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "帮我登录飞书"}]},
        config=config,
    )

    # 此时图已暂停在 interrupt 处
    # 主程序可以做其他事情！
    print("\n  [主程序] 图已暂停。模拟等待用户在浏览器完成授权...")
    print("  [主程序] 同时我可以做其他工作（检查文件、读取配置...）")
    await asyncio.sleep(2.0)  # 模拟用户操作耗时

    # Step 2: 外部事件完成，用 Command(resume=...) 恢复执行
    print("\n  [主程序] Step 2: 用户已完成授权，恢复图执行...")
    auth_result = simulate_oauth_check()
    result = agent.invoke(
        Command(resume=auth_result),
        config=config,
    )

    print(f"\n  [主程序] 最终结果:")
    for msg in result.get("messages", []):
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        print(f"    {content}")

    # ============================================================
    # 场景 2: 构建任务（新线程）
    # ============================================================
    print("\n" + "=" * 60)
    print("  场景 2: 项目构建")
    print("=" * 60)

    config2 = {"configurable": {"thread_id": "demo-session-2"}}

    # Step 1: 发送构建请求
    print("\n  [主程序] Step 1: 发送构建请求...")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "帮我构建项目"}]},
        config=config2,
    )

    # 图暂停在 interrupt
    print("\n  [主程序] 图已暂停。模拟构建过程...")
    await asyncio.sleep(2.0)

    # Step 2: 构建完成，恢复
    print("\n  [主程序] Step 2: 构建完成，恢复图执行...")
    build_result = simulate_build_result()
    result = agent.invoke(
        Command(resume=build_result),
        config=config2,
    )

    print(f"\n  [主程序] 最终结果:")
    for msg in result.get("messages", []):
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        print(f"    {content}")

    # ============================================================
    # 场景 3: 直接回复（无异步任务，对比）
    # ============================================================
    print("\n" + "=" * 60)
    print("  场景 3: 直接回复（对比，无需暂停）")
    print("=" * 60)

    config3 = {"configurable": {"thread_id": "demo-session-3"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "你好，今天天气怎么样？"}]},
        config=config3,
    )

    print(f"\n  [主程序] 最终结果:")
    for msg in result.get("messages", []):
        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
        print(f"    {content}")

    print(f"\n{'='*60}")
    print(f"  演示完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
