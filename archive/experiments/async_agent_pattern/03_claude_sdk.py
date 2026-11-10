"""
03_claude_sdk.py — Claude Agent SDK 实现异步监控回调模式

核心机制：
  Claude Agent SDK 的 Hooks 系统（PreToolUse / PostToolUse / Notification）
  可以实现工具执行前后的拦截和异步监控。

  与 LangGraph 的 interrupt 不同，Claude SDK 的做法更接近"事件钩子"：
  - Agent 在执行工具时，Hooks 可以拦截、修改、记录
  - Notification hook 接收 Agent 的状态通知
  - 可以在 Hook 中做异步等待（如等外部授权完成）

运行方式：
  pip install anthropic
  set ANTHROPIC_API_KEY=sk-ant-xxx
  python 03_claude_sdk.py

注意：此脚本需要有效的 Anthropic API key。
      如果没有 key，请看 03b_claude_sdk_mock.py 的纯模拟版本。
"""
import asyncio
import time
from typing import Any


# ============================================================
# 方式 1: 基于 Anthropic Messages API 的手搓 Agent Loop + Hook
#
# Claude Agent SDK (claude_agent_sdk) 在 2026 年 5 月仍不是公开包，
# 所以这里展示用 anthropic 官方 SDK + 手搓 agent loop + hook 机制
# 来实现相同模式。这也更接近"手搓+SDK"的混合方案。
# ============================================================

# -- Hook 系统定义 --

class HookEvent:
    """Hook 事件基类"""
    pass


class PreToolUse(HookEvent):
    """工具调用前触发"""
    def __init__(self, tool_name: str, tool_input: dict, tool_use_id: str):
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.tool_use_id = tool_use_id


class PostToolUse(HookEvent):
    """工具执行后触发"""
    def __init__(self, tool_name: str, tool_input: dict, result: Any, duration: float):
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.result = result
        self.duration = duration


class AsyncTaskNotification(HookEvent):
    """异步任务状态变更通知"""
    def __init__(self, task_id: str, status: str, result: Any = None):
        self.task_id = task_id
        self.status = status
        self.result = result


class HookEngine:
    """
    Hook 引擎 — 实现 Claude Agent SDK 的 Hook 模式

    在工具执行前后插入自定义逻辑：
    - PreToolUse: 可以拦截（deny）、修改输入、记录日志
    - PostToolUse: 记录审计日志、触发后续操作
    - AsyncTaskNotification: 异步任务状态变更
    """

    def __init__(self):
        self._hooks: dict[str, list] = {
            "PreToolUse": [],
            "PostToolUse": [],
            "AsyncTaskNotification": [],
        }
        self._async_tasks: dict[str, dict] = {}

    def register(self, event_type: str, callback):
        """注册一个 hook 回调"""
        self._hooks.setdefault(event_type, []).append(callback)

    async def fire(self, event: HookEvent) -> dict:
        """触发事件，执行所有匹配的 hook"""
        event_type = type(event).__name__
        results = {}
        for callback in self._hooks.get(event_type, []):
            result = await callback(event)
            if result:
                results.update(result)
        return results

    def register_async_task(self, task_id: str, name: str):
        """注册一个异步任务"""
        self._async_tasks[task_id] = {
            "name": name,
            "status": "running",
            "created_at": time.time(),
        }

    async def complete_async_task(self, task_id: str, result: Any):
        """标记异步任务完成并触发通知"""
        if task_id in self._async_tasks:
            self._async_tasks[task_id]["status"] = "completed"
            self._async_tasks[task_id]["result"] = result
            await self.fire(AsyncTaskNotification(task_id, "completed", result))


# -- 工具定义 --

TOOLS = [
    {
        "name": "start_oauth_login",
        "description": "启动 OAuth 登录流程。返回授权 URL，需要用户在浏览器中完成授权。",
        "input_schema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "OAuth 提供商 (e.g., feishu, github)"},
            },
            "required": ["provider"],
        },
    },
    {
        "name": "check_auth_status",
        "description": "检查 OAuth 授权状态。",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "授权任务 ID"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "start_build",
        "description": "启动项目构建任务。",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "项目名称"},
            },
            "required": ["project"],
        },
    },
]


# -- 工具执行器 --

class ToolExecutor:
    """工具执行器——带 Hook 拦截"""

    def __init__(self, hook_engine: HookEngine):
        self.hooks = hook_engine
        self._auth_tasks: dict[str, asyncio.Task] = {}

    async def execute(self, tool_name: str, tool_input: dict, tool_use_id: str) -> str:
        """执行工具（经过 Hook 拦截链）"""

        # 1. 触发 PreToolUse hook
        pre_result = await self.hooks.fire(
            PreToolUse(tool_name, tool_input, tool_use_id)
        )

        # 检查是否被拦截
        if pre_result.get("deny"):
            return f"[BLOCKED] {pre_result.get('reason', 'Denied by hook')}"

        # 2. 执行工具
        start_time = time.time()
        result = await self._run_tool(tool_name, tool_input)
        duration = time.time() - start_time

        # 3. 触发 PostToolUse hook
        await self.hooks.fire(
            PostToolUse(tool_name, tool_input, result, duration)
        )

        return result

    async def _run_tool(self, name: str, input: dict) -> str:
        if name == "start_oauth_login":
            return await self._start_oauth(input)
        elif name == "check_auth_status":
            return await self._check_auth(input)
        elif name == "start_build":
            return await self._start_build(input)
        return f"Unknown tool: {name}"

    async def _start_oauth(self, input: dict) -> str:
        """启动 OAuth——异步启动后立即返回"""
        provider = input.get("provider", "feishu")
        task_id = f"auth-{int(time.time())}"

        # 注册异步任务
        self.hooks.register_async_task(task_id, f"OAuth-{provider}")

        # 在后台启动模拟授权流程
        async def _auth_flow():
            await asyncio.sleep(3.0)  # 模拟用户操作
            await self.hooks.complete_async_task(task_id, {
                "status": "authorized",
                "user": "示例用户",
                "provider": provider,
            })

        task = asyncio.create_task(_auth_flow())
        self._auth_tasks[task_id] = task

        return (
            f"OAuth 登录已启动 (task_id={task_id})。\n"
            f"授权链接: https://accounts.{provider}.cn/oauth/device\n"
            f"请在浏览器中完成授权。使用 check_auth_status 检查状态。"
        )

    async def _check_auth(self, input: dict) -> str:
        """检查授权状态"""
        task_id = input.get("task_id", "")
        task_info = self.hooks._async_tasks.get(task_id)
        if not task_info:
            return f"未找到任务: {task_id}"
        if task_info["status"] == "completed":
            return f"授权完成! 结果: {task_info.get('result', {})}"
        return f"任务 {task_id} 状态: {task_info['status']}（仍在等待用户操作）"

    async def _start_build(self, input: dict) -> str:
        """启动构建——异步"""
        project = input.get("project", "my-app")
        task_id = f"build-{int(time.time())}"
        self.hooks.register_async_task(task_id, f"Build-{project}")

        async def _build_flow():
            await asyncio.sleep(4.0)
            await self.hooks.complete_async_task(task_id, {
                "status": "success",
                "project": project,
                "artifacts": ["dist/app.js"],
            })

        asyncio.create_task(_build_flow())
        return f"构建已启动 (task_id={task_id})。后台执行中..."


# ============================================================
# Agent Loop（模拟 Claude Agent 循环，不调用真实 API）
# ============================================================

class MockAgentLoop:
    """
    模拟 Claude Agent 的工具调用循环

    真实版本会用 anthropic.Anthropic().messages.create()，
    这里用预设的脚本模拟 Agent 的决策序列，以便无需 API key 也能运行。
    """

    def __init__(self):
        self.hook_engine = HookEngine()
        self.tool_executor = ToolExecutor(self.hook_engine)
        self.notifications: list[str] = []

        # 注册 Hooks
        self._setup_hooks()

    def _setup_hooks(self):
        """注册所有 Hook 回调"""

        # Hook 1: 审计日志
        async def audit_logger(event: PreToolUse) -> dict:
            print(f"  [HOOK:audit] 工具调用: {event.tool_name}({event.tool_input})")
            return {}

        # Hook 2: 异步任务完成通知
        async def task_completion_handler(event: AsyncTaskNotification) -> dict:
            msg = f"异步任务 {event.task_id} 已完成: {event.result}"
            self.notifications.append(msg)
            print(f"  [HOOK:notification] {msg}")
            return {}

        # Hook 3: PostToolUse 计时
        async def timing_logger(event: PostToolUse) -> dict:
            print(f"  [HOOK:timing] {event.tool_name} 耗时 {event.duration:.2f}s")
            return {}

        self.hook_engine.register("PreToolUse", audit_logger)
        self.hook_engine.register("AsyncTaskNotification", task_completion_handler)
        self.hook_engine.register("PostToolUse", timing_logger)

    async def run(self, user_message: str):
        """模拟一轮 Agent 执行"""
        print(f"\n  👤 用户: {user_message}")

        # 检查是否有待处理的通知
        if self.notifications:
            print(f"\n  📬 有 {len(self.notifications)} 条异步通知:")
            for n in self.notifications:
                print(f"    → {n}")
            self.notifications.clear()

        # 模拟 Agent 的工具调用决策（真实版本由 Claude 生成）
        if "登录" in user_message or "auth" in user_message.lower():
            print(f"\n  🤖 Agent 决定调用: start_oauth_login")
            result = await self.tool_executor.execute(
                "start_oauth_login",
                {"provider": "feishu"},
                "call-001",
            )
            print(f"\n  📤 工具结果: {result}")
            print(f"\n  🤖 Agent: 已启动 OAuth 登录。请在浏览器中完成授权。"
                  f"授权完成后，你可以问我'检查状态'。")

        elif "检查状态" in user_message or "status" in user_message.lower():
            # 查找最近的 auth task
            auth_tasks = {k: v for k, v in self.hook_engine._async_tasks.items()
                         if k.startswith("auth-")}
            if auth_tasks:
                task_id = list(auth_tasks.keys())[-1]
                result = await self.tool_executor.execute(
                    "check_auth_status",
                    {"task_id": task_id},
                    "call-002",
                )
                print(f"\n  📤 工具结果: {result}")
            else:
                print(f"\n  🤖 Agent: 没有进行中的授权任务。")

        elif "构建" in user_message or "build" in user_message.lower():
            print(f"\n  🤖 Agent 决定调用: start_build")
            result = await self.tool_executor.execute(
                "start_build",
                {"project": "my-app"},
                "call-003",
            )
            print(f"\n  📤 工具结果: {result}")

        else:
            print(f"\n  🤖 Agent: {user_message} — 已处理。")


# ============================================================
# 主程序
# ============================================================

async def main():
    print("=" * 60)
    print("  Claude SDK Hook 模式异步监控演示")
    print("  （PreToolUse + PostToolUse + AsyncNotification）")
    print("=" * 60)

    agent = MockAgentLoop()

    # Turn 1: 启动 OAuth
    await agent.run("帮我登录飞书")

    # Turn 2: 立即检查（还没完成）
    await asyncio.sleep(1.0)
    await agent.run("检查状态")

    # Turn 3: 等一会再检查（已完成）
    await asyncio.sleep(3.0)
    await agent.run("检查状态")

    # Turn 4: 启动构建
    await agent.run("帮我构建项目")

    # Turn 5: 等构建完成
    await asyncio.sleep(5.0)
    await agent.run("构建完成了吗？")

    print(f"\n{'='*60}")
    print(f"  演示完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
