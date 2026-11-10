"""
Iter 5: 安全与权限 — 信任边界（~200 行核心代码）
================================================
目标：Agent 不是所有操作都可以无条件执行。危险操作需要人类确认。
新增：Permission 枚举 + 工具权限注解 + 用户确认机制 + 审计日志
学到：最小权限原则、人在环路（HITL）、信任边界设计。

Claude Code 对照：
  - permissions.ts: 5 级权限模型（Bash/Write 是 DANGER → 需要用户 approve）
  - 用户可以设置 --allowedTools 白名单 和 --disallowedTools 黑名单
  - 权限评估 5 层流水线: Hooks → Deny Rules → Permission Mode → Allow Rules → canUseTool

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter5_safety.py
"""

import os
import json
import time
from enum import Enum
from pathlib import Path
from config import client, MODEL


# ━━━ 权限模型 ━━━
class Permission(Enum):
    SAFE = "safe"          # 直接执行，无需确认
    CONFIRM = "confirm"    # 执行前需要用户确认
    DENY = "deny"          # 拒绝执行


# ━━━ 增强版工具注册表（带权限） ━━━
class SafeToolRegistry:
    def __init__(self):
        self._tools = {}
        self._schemas = []
        self._permissions = {}
        self._audit_log = []

    def tool(self, name: str, description: str, parameters: dict,
             permission: Permission = Permission.SAFE):
        def decorator(fn):
            self._tools[name] = fn
            self._permissions[name] = permission
            self._schemas.append({"type": "function", "function": {
                "name": name, "description": description, "parameters": parameters}})
            return fn
        return decorator

    def call(self, name: str, args: dict) -> str:
        """执行工具前检查权限"""
        perm = self._permissions.get(name, Permission.DENY)

        # 权限检查
        if perm == Permission.DENY:
            msg = f"🚫 工具 '{name}' 被禁止执行"
            self._log(name, args, "DENIED", msg)
            return json.dumps({"error": msg}, ensure_ascii=False)

        if perm == Permission.CONFIRM:
            print(f"\n  ⚠️  Agent 想执行需要确认的操作:")
            print(f"     工具: {name}")
            print(f"     参数: {json.dumps(args, ensure_ascii=False)[:200]}")
            answer = input("     是否允许？(y/n): ").strip().lower()
            if answer != "y":
                msg = f"用户拒绝了 '{name}' 的执行"
                self._log(name, args, "USER_REJECTED", msg)
                return json.dumps({"error": msg}, ensure_ascii=False)
            self._log(name, args, "USER_APPROVED")

        # 执行
        try:
            result = self._tools[name](**args)
            r = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            self._log(name, args, "EXECUTED", r[:200])
            return r
        except Exception as e:
            err = json.dumps({"error": str(e)}, ensure_ascii=False)
            self._log(name, args, "ERROR", str(e))
            return err

    def _log(self, tool: str, args: dict, action: str, detail: str = ""):
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "tool": tool,
            "permission": self._permissions.get(tool, Permission.DENY).value,
            "action": action,
            "detail": detail[:100],
        }
        self._audit_log.append(entry)

    def print_audit_log(self):
        print("\n📋 审计日志:")
        for e in self._audit_log:
            icon = {"EXECUTED": "✅", "DENIED": "🚫", "USER_APPROVED": "👤", "USER_REJECTED": "❌", "ERROR": "💥"}.get(e["action"], "❓")
            print(f"  {e['time']} {icon} [{e['permission']}] {e['tool']} → {e['action']}")

    @property
    def schemas(self): return self._schemas
    def list_tools(self): return list(self._tools.keys())


registry = SafeToolRegistry()


# ━━━ 注册工具（带权限等级） ━━━

@registry.tool("calculator", "计算数学表达式", {
    "type": "object",
    "properties": {"expression": {"type": "string", "description": "数学表达式"}},
    "required": ["expression"],
}, permission=Permission.SAFE)
def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})


@registry.tool("read_file", "读取文件内容", {
    "type": "object",
    "properties": {"path": {"type": "string", "description": "文件路径"}},
    "required": ["path"],
}, permission=Permission.SAFE)
def read_file(path: str) -> str:
    try:
        content = Path(path).read_text(encoding="utf-8")[:3000]
        return json.dumps({"content": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@registry.tool("write_file", "写入文件内容（会覆盖已有文件！）", {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "内容"},
    },
    "required": ["path", "content"],
}, permission=Permission.CONFIRM)  # ⚠️ 写文件需要确认
def write_file(path: str, content: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")
    return json.dumps({"status": "ok", "path": path})


@registry.tool("execute_shell", "执行系统命令", {
    "type": "object",
    "properties": {"command": {"type": "string", "description": "Shell 命令"}},
    "required": ["command"],
}, permission=Permission.DENY)  # 🚫 禁止执行 Shell（除非升级权限）
def execute_shell(command: str) -> str:
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
    return json.dumps({"stdout": result.stdout[:1000], "stderr": result.stderr[:500]})


# ━━━ Agent 循环（带权限检查） ━━━
def agent_loop(user_message: str, max_turns: int = 10) -> str:
    messages = [
        {"role": "system", "content": "你是一个AI助手。可用工具: " + ", ".join(registry.list_tools()) + "。某些工具需要用户确认才能执行，某些被禁止使用。"},
        {"role": "user", "content": user_message},
    ]
    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=registry.schemas,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            print(f"  🔧 {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:60]})")
            result = registry.call(fn_name, fn_args)  # 权限检查在这里发生
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "达到最大轮次限制"


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 5: 安全与权限 — 信任边界")
    print("=" * 60)

    # 测试 1: SAFE 工具直接执行
    print("\n📝 测试 1: 安全工具（calculator）")
    r = agent_loop("计算 100 * 99 / 2")
    print(f"\n🤖 {r}")

    # 测试 2: CONFIRM 工具需要确认
    print("\n" + "-" * 60)
    print("📝 测试 2: 需确认工具（write_file）")
    r = agent_loop("请创建一个文件 /tmp/test_agent.txt，内容写 'Hello from Agent'")
    print(f"\n🤖 {r}")

    # 测试 3: DENY 工具被拒绝
    print("\n" + "-" * 60)
    print("📝 测试 3: 被禁止的工具（execute_shell）")
    r = agent_loop("帮我执行 ls -la 看看当前目录")
    print(f"\n🤖 {r}")

    # 打印审计日志
    registry.print_audit_log()
