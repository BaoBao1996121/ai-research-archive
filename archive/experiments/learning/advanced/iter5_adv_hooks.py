"""
Iter 5 进阶: Hooks 可编程拦截 — 五层权限流水线（~250 行核心代码）
=================================================================
基础版差距：权限只有三级（SAFE/CONFIRM/DENY），无法自定义拦截逻辑。
进阶补全：Hook 系统 + 五层权限流水线 + 可组合的拦截器。

Claude Code 对照：
  - Hooks 系统: 用户可注册 before/after 钩子拦截工具调用
  - 五层权限评估流水线:
    Layer 1: Hooks（外部脚本拦截）
    Layer 2: Deny Rules（黑名单）
    Layer 3: Permission Mode（模式：auto/confirm/deny）
    Layer 4: Allow Rules（白名单）
    Layer 5: canUseTool（工具自身的权限检查）
  - 每一层都可以 ALLOW / DENY / PASS（交给下一层）

依赖：pip install openai
运行：python iter5_adv_hooks.py
"""

import json
import time
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional
from config import client, MODEL


# ╔══════════════════════════════════════════════════════════════╗
# ║  Hook 协议定义                                               ║
# ╚══════════════════════════════════════════════════════════════╝

class Decision(Enum):
    ALLOW = "allow"   # 明确允许（跳过后续层）
    DENY = "deny"     # 明确拒绝（跳过后续层）
    PASS = "pass"     # 不做决定，交给下一层


@dataclass
class HookContext:
    """传递给 Hook 的上下文信息"""
    tool_name: str
    arguments: dict
    user_message: str = ""
    turn: int = 0
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class HookResult:
    """Hook 的返回结果"""
    decision: Decision
    reason: str = ""
    modified_args: Optional[dict] = None  # Hook 可以修改参数


# Hook 函数签名：接收 HookContext，返回 HookResult
HookFn = Callable[[HookContext], HookResult]


# ╔══════════════════════════════════════════════════════════════╗
# ║  Hook 注册表                                                 ║
# ╚══════════════════════════════════════════════════════════════╝

class HookRegistry:
    """
    Hook 注册和执行引擎。

    支持两类 Hook：
    - before_tool: 工具执行前拦截（可阻止执行或修改参数）
    - after_tool: 工具执行后拦截（可修改结果或记录审计）
    """
    def __init__(self):
        self._before_hooks: list[tuple[str, HookFn]] = []  # [(name, fn)]
        self._after_hooks: list[tuple[str, HookFn]] = []

    def before_tool(self, name: str):
        """注册 before_tool Hook 的装饰器"""
        def decorator(fn: HookFn):
            self._before_hooks.append((name, fn))
            return fn
        return decorator

    def after_tool(self, name: str):
        """注册 after_tool Hook 的装饰器"""
        def decorator(fn: HookFn):
            self._after_hooks.append((name, fn))
            return fn
        return decorator

    def run_before(self, ctx: HookContext) -> HookResult:
        """按顺序执行所有 before hooks，任何一个 ALLOW/DENY 都立即返回"""
        for hook_name, fn in self._before_hooks:
            result = fn(ctx)
            if result.decision != Decision.PASS:
                print(f"    [Hook:{hook_name}] → {result.decision.value}: {result.reason}")
                return result
        return HookResult(Decision.PASS, "所有 hooks 都 PASS")

    def run_after(self, ctx: HookContext, tool_result: str) -> str:
        """执行所有 after hooks（可修改结果）"""
        for hook_name, fn in self._after_hooks:
            ctx.metadata["tool_result"] = tool_result
            result = fn(ctx)
            if result.modified_args and "tool_result" in result.modified_args:
                tool_result = result.modified_args["tool_result"]
        return tool_result


hooks = HookRegistry()


# ╔══════════════════════════════════════════════════════════════╗
# ║  内置 Hooks（演示各种拦截场景）                                ║
# ╚══════════════════════════════════════════════════════════════╝

@hooks.before_tool("rate_limiter")
def rate_limiter_hook(ctx: HookContext) -> HookResult:
    """Hook 1: 速率限制——防止工具被频繁调用"""
    # 简单实现：用 metadata 记录调用时间
    key = f"last_call_{ctx.tool_name}"
    last_call = rate_limiter_hook.__dict__.get(key, 0)
    now = time.time()
    if now - last_call < 1.0:  # 同一工具 1 秒内只能调一次
        return HookResult(Decision.DENY, f"速率限制：{ctx.tool_name} 调用过快")
    rate_limiter_hook.__dict__[key] = now
    return HookResult(Decision.PASS)


@hooks.before_tool("path_guard")
def path_guard_hook(ctx: HookContext) -> HookResult:
    """Hook 2: 路径守卫——阻止访问敏感目录"""
    dangerous_patterns = [r"/etc/", r"C:\\Windows", r"\.env", r"password", r"secret"]
    args_str = json.dumps(ctx.arguments)
    for pattern in dangerous_patterns:
        if re.search(pattern, args_str, re.IGNORECASE):
            return HookResult(Decision.DENY, f"安全拦截：参数匹配敏感模式 '{pattern}'")
    return HookResult(Decision.PASS)


@hooks.before_tool("arg_sanitizer")
def arg_sanitizer_hook(ctx: HookContext) -> HookResult:
    """Hook 3: 参数清洗——修改危险参数"""
    if ctx.tool_name == "execute_shell":
        cmd = ctx.arguments.get("command", "")
        # 去除危险命令
        for danger in ["rm -rf", "sudo", "mkfs", "dd if="]:
            if danger in cmd:
                return HookResult(Decision.DENY, f"危险命令被拦截: {danger}")
    return HookResult(Decision.PASS)


@hooks.after_tool("audit_logger")
def audit_logger_hook(ctx: HookContext) -> HookResult:
    """Hook 4: 审计日志——记录所有工具调用"""
    result = ctx.metadata.get("tool_result", "")
    print(f"    [审计] {time.strftime('%H:%M:%S')} | {ctx.tool_name} | "
          f"args={json.dumps(ctx.arguments, ensure_ascii=False)[:50]} | "
          f"result={result[:50]}")
    return HookResult(Decision.PASS)


@hooks.after_tool("output_filter")
def output_filter_hook(ctx: HookContext) -> HookResult:
    """Hook 5: 输出过滤——脱敏敏感信息"""
    result = ctx.metadata.get("tool_result", "")
    # 简单示例：隐藏邮箱和手机号
    filtered = re.sub(r'[\w.-]+@[\w.-]+', '[EMAIL_REDACTED]', result)
    filtered = re.sub(r'1[3-9]\d{9}', '[PHONE_REDACTED]', filtered)
    if filtered != result:
        return HookResult(Decision.PASS, "已脱敏", {"tool_result": filtered})
    return HookResult(Decision.PASS)


# ╔══════════════════════════════════════════════════════════════╗
# ║  五层权限流水线                                               ║
# ╚══════════════════════════════════════════════════════════════╝

class PermissionPipeline:
    """
    五层权限评估流水线（仿 Claude Code 的权限模型）。

    Layer 1: Hooks（用户自定义拦截）
    Layer 2: Deny Rules（全局黑名单）
    Layer 3: Permission Mode（当前模式：auto/confirm/strict）
    Layer 4: Allow Rules（全局白名单）
    Layer 5: Tool.canUse（工具自身的权限检查）

    每一层返回 ALLOW/DENY/PASS，ALLOW/DENY 立即短路，PASS 继续下一层。
    """
    def __init__(self, hook_registry: HookRegistry):
        self.hooks = hook_registry
        self.deny_rules: list[str] = []     # 黑名单工具名
        self.allow_rules: list[str] = []    # 白名单工具名
        self.mode = "confirm"               # auto / confirm / strict
        self.tool_permissions: dict[str, Callable] = {}  # 工具自身权限检查

    def evaluate(self, ctx: HookContext) -> HookResult:
        """五层流水线评估"""
        # Layer 1: Hooks
        result = self.hooks.run_before(ctx)
        if result.decision != Decision.PASS:
            return HookResult(result.decision, f"[Layer1:Hook] {result.reason}")

        # Layer 2: Deny Rules
        if ctx.tool_name in self.deny_rules:
            return HookResult(Decision.DENY, f"[Layer2:DenyRule] '{ctx.tool_name}' 在黑名单中")

        # Layer 3: Permission Mode
        if self.mode == "auto":
            pass  # auto 模式不拦截，交给下一层
        elif self.mode == "strict":
            if ctx.tool_name not in self.allow_rules:
                return HookResult(Decision.DENY, f"[Layer3:Strict] 严格模式下 '{ctx.tool_name}' 未在白名单")
        elif self.mode == "confirm":
            pass  # confirm 模式在 Layer4 之后处理

        # Layer 4: Allow Rules
        if ctx.tool_name in self.allow_rules:
            return HookResult(Decision.ALLOW, f"[Layer4:AllowRule] '{ctx.tool_name}' 在白名单中")

        # Layer 5: Tool's own permission check
        if ctx.tool_name in self.tool_permissions:
            can_use = self.tool_permissions[ctx.tool_name](ctx)
            if not can_use:
                return HookResult(Decision.DENY, f"[Layer5:CanUse] 工具自身拒绝执行")

        # 默认：confirm 模式需要确认，auto 模式允许
        if self.mode == "confirm":
            return HookResult(Decision.ALLOW, "[Default:Confirm] 需要用户确认")
        return HookResult(Decision.ALLOW, "[Default] 允许执行")


# ╔══════════════════════════════════════════════════════════════╗
# ║  组装：带 Hook 的 Agent                                      ║
# ╚══════════════════════════════════════════════════════════════╝

TOOLS = [
    {"type": "function", "function": {
        "name": "calculator", "description": "计算数学表达式",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "read_file", "description": "读取文件内容",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "文件路径"}
        }, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "execute_shell", "description": "执行系统命令",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "命令"}
        }, "required": ["command"]}}},
]


def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})

def read_file(path: str) -> str:
    return json.dumps({"content": f"[模拟] 文件 {path} 的内容..."}, ensure_ascii=False)

def execute_shell(command: str) -> str:
    return json.dumps({"stdout": f"[模拟] 执行: {command}"}, ensure_ascii=False)


TOOL_MAP = {"calculator": calculator, "read_file": read_file, "execute_shell": execute_shell}


def hooked_agent(user_message: str, pipeline: PermissionPipeline, max_turns: int = 5) -> str:
    """带完整 Hook 和权限流水线的 Agent"""
    messages = [
        {"role": "system", "content": "你是一个AI助手。可用工具: calculator, read_file, execute_shell"},
        {"role": "user", "content": user_message},
    ]
    for turn in range(max_turns):
        print(f"\n  ⚡ 第 {turn+1} 轮...")
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            ctx = HookContext(tool_name=fn_name, arguments=fn_args,
                            user_message=user_message, turn=turn)

            # 五层权限评估
            print(f"  🔧 {fn_name} → 权限评估...")
            perm = pipeline.evaluate(ctx)

            if perm.decision == Decision.DENY:
                result = json.dumps({"error": f"权限拒绝: {perm.reason}"}, ensure_ascii=False)
                print(f"  🚫 拒绝: {perm.reason}")
            else:
                # 执行工具
                actual_args = perm.modified_args if perm.modified_args else fn_args
                result = TOOL_MAP[fn_name](**actual_args)
                # after hooks
                result = hooks.run_after(ctx, result)
                print(f"  ✅ 执行完成")

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "⚠️ 达到最大轮次"


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 5 进阶: Hooks 可编程拦截 — 五层权限流水线")
    print("=" * 60)

    # 配置权限流水线
    pipeline = PermissionPipeline(hooks)
    pipeline.deny_rules = ["execute_shell"]  # 禁止 Shell
    pipeline.allow_rules = ["calculator"]     # 白名单
    pipeline.mode = "confirm"

    # 测试 1: 白名单工具（直接允许）
    print("\n📝 测试 1: 白名单工具 (calculator)")
    r = hooked_agent("计算 99 * 88", pipeline)
    print(f"\n🤖 {r}")

    # 测试 2: 黑名单工具（被拦截）
    print(f"\n{'='*60}")
    print("📝 测试 2: 黑名单工具 (execute_shell)")
    r = hooked_agent("执行 ls -la 查看目录", pipeline)
    print(f"\n🤖 {r}")

    # 测试 3: 敏感路径拦截
    print(f"\n{'='*60}")
    print("📝 测试 3: 路径守卫（拦截 .env 文件）")
    r = hooked_agent("帮我读取 .env 文件的内容", pipeline)
    print(f"\n🤖 {r}")

    print(f"\n{'='*60}")
    print("📚 Hook 系统总结:")
    print("  五层流水线: Hooks → Deny → Mode → Allow → canUse")
    print("  每层可 ALLOW/DENY/PASS，短路返回")
    print()
    print("  内置 Hooks 演示:")
    print("  - rate_limiter  — 速率限制")
    print("  - path_guard    — 敏感路径拦截")
    print("  - arg_sanitizer — 参数清洗")
    print("  - audit_logger  — 审计日志")
    print("  - output_filter — 输出脱敏")
    print()
    print("  Claude Code 的 Hooks 支持外部脚本 (.claude/hooks/)：")
    print("  用户写 Shell/Python 脚本，在工具执行前后自动调用")
