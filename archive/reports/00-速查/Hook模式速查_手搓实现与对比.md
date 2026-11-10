> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Hook 模式速查：手搓实现与对比

> 一句话概括：Hook 本质是观察者模式的薄封装（字典+遍历+短路），20行代码即可实现，核心智力含量不在实现而在选对切入点。
> 研究日期：2026-05-10
> 关联报告：R82_Agent异步监控回调模式_从Copilot机制到三种实现

---

## 一、最小实现（20行）

```python
from typing import Callable

class HookEngine:
    def __init__(self):
        self._hooks: dict[str, list[Callable]] = {}
    
    def register(self, event_name: str, callback: Callable):
        """往字典里塞一个回调。key不存在就先建空列表"""
        self._hooks.setdefault(event_name, []).append(callback)
    
    async def fire(self, event_name: str, payload: dict) -> dict:
        """遍历该事件下所有回调，任何一个返回deny则短路"""
        for cb in self._hooks.get(event_name, []):
            result = await cb(payload)
            if result and result.get("deny"):
                return result  # 短路，后续回调不执行
        return {}
```

**内存结构**：
```python
{
    "pre_tool_use":  [block_dangerous, rate_limit],   # 工具执行前
    "post_tool_use": [audit_hook, metrics_hook],      # 工具执行后
}
```

---

## 二、工具执行器集成

```python
class ToolExecutor:
    async def execute(self, tool_name, tool_input):
        # 切入点1: 执行前 — 可拦截
        pre = await self.hooks.fire("pre_tool_use", {"tool": tool_name, "input": tool_input})
        if pre.get("deny"):
            return f"[BLOCKED] {pre['reason']}"
        
        # 实际执行
        result = await self._run(tool_name, tool_input)
        
        # 切入点2: 执行后 — 审计/计时
        await self.hooks.fire("post_tool_use", {"tool": tool_name, "result": result})
        return result
```

---

## 三、注册使用

```python
engine = HookEngine()

# 拦截钩子：危险工具直接拒绝
async def block_dangerous(payload):
    if payload["tool"] in ["rm_rf", "drop_table"]:
        return {"deny": True, "reason": "危险操作"}
    # 返回None = 放行

# 审计钩子：记录所有工具调用
async def audit_hook(payload):
    print(f"[AUDIT] {payload['tool']} → {payload['result'][:50]}")

engine.register("pre_tool_use", block_dangerous)
engine.register("post_tool_use", audit_hook)
```

---

## 四、执行流图示

**被拦截的情况**（工具名=`rm_rf`）：
```
Agent决定调用 "rm_rf"
  → ToolExecutor.execute("rm_rf", {...})
    → hooks.fire("pre_tool_use") 
      → block_dangerous({"tool": "rm_rf"}) → {"deny": True}
    → 短路！工具不执行
  → 返回 "[BLOCKED] 危险操作"
```

**放行的情况**（工具名=`read_file`）：
```
Agent决定调用 "read_file"
  → ToolExecutor.execute("read_file", {...})
    → hooks.fire("pre_tool_use")
      → block_dangerous({"tool": "read_file"}) → None → 放行
    → self._run("read_file", ...) → 实际读文件
    → hooks.fire("post_tool_use")
      → audit_hook(...) → 打印日志
  → 返回文件内容
```

---

## 五、Hook vs 手搓Agent 核心区别

| 维度 | 手搓版 | Hook版 |
|------|--------|--------|
| 控制流 | 过程式 — Agent Loop直接调度一切 | 事件驱动 — 执行器触发事件，注册方响应 |
| 扩展方式 | 改代码 — 加功能就改主循环 | 挂钩子 — 加功能只注册新回调 |
| 耦合度 | 高 — 所有逻辑嵌在一个turn()里 | 低 — Hook链与业务逻辑分离 |
| 拦截能力 | 无内置 — 要拦截工具得写if/else | 内置 — PreToolUse返回deny即可 |
| 异步监控 | asyncio.create_task + drain队列 | 同样是create_task + drain队列 |

**关键洞察**：在"异步监控回调"这个具体功能上，两者运行时行为几乎一样（都是轮次开头drain队列）。Hook真正多出的价值在于**工具调用拦截链**。

**类比**：
- 手搓 = 一个人既当厨师又当服务员又当收银员
- Hook = 把岗位拆开，各管各的，通过"喊号"协调

---

## 六、同族技术

| 领域 | 名字 | 共同抽象 |
|------|------|---------|
| OS | Windows Hook / eBPF | 在执行点注册回调 |
| Web框架 | Middleware | 请求经过一层层中间件 |
| Java/Spring | AOP（面向切面） | 切入点+通知 |
| Git | pre-commit / post-push | 事件前后自动触发 |
| React | Hooks | 命名灵感一脉相承 |
| Claude SDK | PreToolUse / PostToolUse | 工具调用拦截链 |

---

## 七、什么时候该用Hook

| 场景 | 结论 |
|------|------|
| 只做异步监控回调 | 两者等价，手搓更简单 |
| 异步监控 + 工具审计/拦截 | Hook更合适 |
| 理解原理/教学 | 手搓更直观 |
| 频繁加新"切面"功能 | Hook，否则主循环变意大利面 |
| 只有1-2个功能 | 手搓，Hook反而过度设计 |

**判断阈值**：当你发现主循环里的 if/else 超过 5 个分支、且它们之间互不相关时，就该重构为 Hook 了。
