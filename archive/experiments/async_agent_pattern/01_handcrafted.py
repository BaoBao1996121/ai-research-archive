"""
01_handcrafted.py — 手搓 Agent 异步监控回调模式

核心模式：
  Agent 启动一个长时间/需要外部交互的任务 → 不阻塞 → 继续做其他工作 → 任务完成后自动回调

运行方式：
  python 01_handcrafted.py  （无需任何 API key）

这个例子模拟了 VS Code Copilot 的异步终端监控机制：
  1. Agent 启动一个"需要用户授权"的模拟任务（类似 lark-cli auth login）
  2. Agent 不等待，继续做其他工作
  3. 后台任务完成后，通过回调通知 Agent
  4. Agent 在下一个"轮次"处理通知
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine


# ============================================================
# 第一层：任务状态管理（对应 VS Code 的 Terminal Manager）
# ============================================================

class TaskStatus(Enum):
    PENDING = "pending"         # 已创建，未启动
    RUNNING = "running"         # 执行中
    WAITING_INPUT = "waiting"   # 等待外部输入（如用户授权）
    COMPLETED = "completed"     # 完成
    FAILED = "failed"           # 失败


@dataclass
class AsyncTask:
    """一个异步任务的完整状态"""
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None


class TaskManager:
    """
    任务管理器 — 对应 Copilot 的 Terminal Manager 层

    职责：
    1. 注册和追踪异步任务
    2. 在后台运行任务
    3. 收集完成通知，供 Agent 在下一轮次读取
    """

    def __init__(self):
        self._tasks: dict[str, AsyncTask] = {}
        self._notifications: list[dict] = []  # 待处理的通知队列
        self._background_tasks: set[asyncio.Task] = set()

    def create_task(self, name: str) -> str:
        """创建一个新任务，返回 UUID"""
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = AsyncTask(id=task_id, name=name)
        return task_id

    async def run_async(
        self,
        task_id: str,
        coro: Coroutine,
    ) -> None:
        """在后台启动一个协程，完成后自动发通知"""
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING

        async def _wrapper():
            try:
                result = await coro
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = time.time()
                # 关键：完成后把通知压入队列
                self._notifications.append({
                    "type": "task_completed",
                    "task_id": task_id,
                    "task_name": task.name,
                    "result": result,
                    "duration": task.completed_at - task.created_at,
                })
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                self._notifications.append({
                    "type": "task_failed",
                    "task_id": task_id,
                    "task_name": task.name,
                    "error": str(e),
                })

        bg_task = asyncio.create_task(_wrapper())
        self._background_tasks.add(bg_task)
        bg_task.add_done_callback(self._background_tasks.discard)

    def drain_notifications(self) -> list[dict]:
        """
        取出所有待处理的通知（轮次间注入）

        这就是 VS Code Copilot 的 Layer 3 — 轮次间事件注入：
        Agent 每次"醒来"时，先把所有积压的通知读完。
        """
        notifications = self._notifications.copy()
        self._notifications.clear()
        return notifications

    def get_task(self, task_id: str) -> AsyncTask | None:
        return self._tasks.get(task_id)


# ============================================================
# 第二层：模拟外部任务（对应真实场景中的终端进程）
# ============================================================

async def simulate_oauth_login(delay: float = 3.0) -> dict:
    """
    模拟 OAuth 登录流程（类似 lark-cli auth login）

    真实场景：
    - 启动 device-code 流程
    - 等用户在浏览器中扫码
    - 用户完成后返回 access_token
    """
    print("  [OAuth] 请在浏览器中完成授权...")
    print(f"  [OAuth] 授权链接: https://example.com/auth?code=XXXX")
    await asyncio.sleep(delay)  # 模拟用户操作耗时
    print("  [OAuth] 用户已完成授权!")
    return {
        "access_token": "fake-token-12345",
        "user": "示例用户",
        "expires_in": 86400,
    }


async def simulate_long_build(delay: float = 4.0) -> dict:
    """模拟长时间构建任务（如 npm install / docker build）"""
    print("  [Build] 开始安装依赖...")
    await asyncio.sleep(delay * 0.3)
    print("  [Build] 正在编译...")
    await asyncio.sleep(delay * 0.5)
    print("  [Build] 运行测试...")
    await asyncio.sleep(delay * 0.2)
    print("  [Build] 构建完成!")
    return {"status": "success", "artifacts": ["dist/app.js", "dist/app.css"]}


async def simulate_file_download(delay: float = 2.0) -> dict:
    """模拟大文件下载"""
    print("  [Download] 开始下载 model-weights.bin (2.3GB)...")
    await asyncio.sleep(delay)
    print("  [Download] 下载完成!")
    return {"file": "model-weights.bin", "size_mb": 2300}


# ============================================================
# 第三层：Agent 主循环（对应 Copilot 的 Agent Turn）
# ============================================================

class SimpleAgent:
    """
    最简手搓 Agent — 演示轮次驱动的异步监控模式

    核心思想：
    - Agent 的每次 act() 调用是一个"轮次"
    - 每个轮次开始时，先读取所有通知（drain_notifications）
    - 然后执行当前轮次的工作
    - 可以在任何轮次启动新的异步任务
    """

    def __init__(self):
        self.task_manager = TaskManager()
        self.turn_count = 0
        self.completed_tasks: list[dict] = []

    async def act(self, user_input: str | None = None) -> str:
        """执行一个 Agent 轮次"""
        self.turn_count += 1
        print(f"\n{'='*60}")
        print(f"  Agent Turn #{self.turn_count}")
        print(f"{'='*60}")

        # Step 1: 读取所有积压的通知（轮次间事件注入）
        notifications = self.task_manager.drain_notifications()
        if notifications:
            print(f"\n  📬 收到 {len(notifications)} 条异步通知:")
            for n in notifications:
                if n["type"] == "task_completed":
                    print(f"    ✅ [{n['task_name']}] 完成 "
                          f"(耗时 {n['duration']:.1f}s)")
                    print(f"       结果: {n['result']}")
                    self.completed_tasks.append(n)
                elif n["type"] == "task_failed":
                    print(f"    ❌ [{n['task_name']}] 失败: {n['error']}")
        else:
            print(f"\n  📭 无新通知")

        # Step 2: 处理用户输入
        if user_input:
            print(f"\n  👤 用户请求: {user_input}")
            response = await self._handle_request(user_input)
            return response

        return "等待用户输入..."

    async def _handle_request(self, request: str) -> str:
        """处理用户请求，可能启动异步任务"""

        if "登录" in request or "auth" in request.lower():
            # 启动 OAuth 登录（异步）
            task_id = self.task_manager.create_task("OAuth登录")
            await self.task_manager.run_async(
                task_id,
                simulate_oauth_login(delay=3.0),
            )
            print(f"\n  🚀 已启动异步任务 [{task_id}]: OAuth登录")
            print(f"  💡 Agent 不阻塞，继续做其他工作...")

            # Agent 可以同时做其他事情！
            print(f"\n  📝 Agent: 同时帮你检查一下配置文件...")
            await asyncio.sleep(0.5)  # 模拟"检查配置"
            print(f"  📝 Agent: 配置文件检查完毕，一切正常。")

            return (
                f"OAuth 登录已在后台启动 (task_id={task_id})。\n"
                f"同时帮你检查了配置文件——没有问题。\n"
                f"等授权完成后我会在下一轮通知你。"
            )

        elif "构建" in request or "build" in request.lower():
            # 同时启动构建和下载（并行异步）
            build_id = self.task_manager.create_task("项目构建")
            download_id = self.task_manager.create_task("模型下载")

            await self.task_manager.run_async(
                build_id, simulate_long_build(delay=4.0)
            )
            await self.task_manager.run_async(
                download_id, simulate_file_download(delay=2.0)
            )

            print(f"\n  🚀 已启动 2 个并行异步任务:")
            print(f"     - [{build_id}]: 项目构建")
            print(f"     - [{download_id}]: 模型下载")
            print(f"  💡 两个任务并行执行，Agent 可以继续做别的")

            return (
                f"已启动并行任务: 构建({build_id}) + 下载({download_id})。\n"
                f"完成后会自动通知你。"
            )

        elif "状态" in request or "status" in request.lower():
            # 查看所有任务状态
            tasks = self.task_manager._tasks
            if not tasks:
                return "当前没有任何任务。"

            lines = ["当前任务状态:"]
            for tid, task in tasks.items():
                status_emoji = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.RUNNING: "🔄",
                    TaskStatus.WAITING_INPUT: "⏸️",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌",
                }
                lines.append(
                    f"  {status_emoji.get(task.status, '?')} "
                    f"[{tid}] {task.name}: {task.status.value}"
                )
            return "\n".join(lines)

        else:
            return f"收到请求: {request}（普通处理，不涉及异步任务）"


# ============================================================
# 主程序：模拟完整的异步回调流程
# ============================================================

async def main():
    print("=" * 60)
    print("  手搓 Agent 异步监控回调模式演示")
    print("  （模拟 VS Code Copilot 的终端监控机制）")
    print("=" * 60)

    agent = SimpleAgent()

    # Turn 1: 用户请求登录（Agent 启动异步任务，不阻塞）
    response = await agent.act("帮我登录飞书")
    print(f"\n  📤 Agent 回复: {response}")

    # Turn 2: 等一会再来（模拟用户发新消息，触发新 turn）
    # 此时 OAuth 可能还在进行中
    await asyncio.sleep(1.0)
    response = await agent.act("查看任务状态")
    print(f"\n  📤 Agent 回复: {response}")

    # Turn 3: 再等一会（OAuth 应该完成了）
    await asyncio.sleep(3.0)
    response = await agent.act("有什么新消息吗？")
    print(f"\n  📤 Agent 回复: {response}")

    # Turn 4: 启动并行任务
    response = await agent.act("帮我构建项目")
    print(f"\n  📤 Agent 回复: {response}")

    # Turn 5: 等并行任务完成
    await asyncio.sleep(5.0)
    response = await agent.act("查看任务状态")
    print(f"\n  📤 Agent 回复: {response}")

    print(f"\n{'='*60}")
    print(f"  演示结束。共完成 {len(agent.completed_tasks)} 个异步任务。")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
