"""
Iter 3: 上下文工程 — 让 Agent 有记忆和感知（~220 行核心代码）
============================================================
目标：Agent 不再"失忆"。每次对话都能利用之前保存的知识。
新增：ContextBuilder（动态组装上下文）+ Memory（持久化记忆）+ Token 预算感知
学到：上下文窗口管理、System Prompt 动态构建、持久化存储。

Claude Code 对照：
  - context.ts: 动态组装 system prompt（项目信息 + 用户偏好 + 工具描述）
  - CLAUDE.md: 用户级持久化知识（项目约定、偏好等）
  - bootstrap/state.ts: 全局状态管理
  - 核心洞察："记忆不是记住所有，而是在有限窗口内放最有用的信息"

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter3_context_engine.py
"""

import os
import json
import time
from pathlib import Path
from config import client, MODEL


# ━━━ 工具注册表（复用 Iter 2 的模式，精简版） ━━━
class ToolRegistry:
    def __init__(self):
        self._tools, self._schemas = {}, []

    def tool(self, name, description, parameters):
        def decorator(fn):
            self._tools[name] = fn
            self._schemas.append({"type": "function", "function": {
                "name": name, "description": description, "parameters": parameters}})
            return fn
        return decorator

    def call(self, name, args):
        if name not in self._tools:
            return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        try:
            r = self._tools[name](**args)
            return r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @property
    def schemas(self): return self._schemas
    def list_tools(self): return list(self._tools.keys())


registry = ToolRegistry()


# ━━━ 持久化记忆（文件级 key-value 存储） ━━━
class Memory:
    """
    最简单的持久化记忆：JSON 文件。
    Claude Code 用 CLAUDE.md 做类似的事——把用户偏好和项目知识写入文件，
    下次启动时读取，注入 System Prompt。
    """
    def __init__(self, path: str = "agent_memory.json"):
        self.path = Path(path)
        self._data: dict = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, key: str, value: str):
        self._data[key] = {"value": value, "saved_at": time.strftime("%Y-%m-%d %H:%M")}
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> str | None:
        entry = self._data.get(key)
        return entry["value"] if entry else None

    def list_all(self) -> dict:
        return {k: v["value"] for k, v in self._data.items()}

    def clear(self):
        self._data = {}
        if self.path.exists():
            self.path.unlink()


memory = Memory()


# ━━━ 注册工具（含记忆工具） ━━━
@registry.tool("calculator", "计算数学表达式", {
    "type": "object",
    "properties": {"expression": {"type": "string", "description": "数学表达式"}},
    "required": ["expression"],
})
def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})


@registry.tool("save_memory", "保存一条重要信息到长期记忆（跨对话持久化）", {
    "type": "object",
    "properties": {
        "key": {"type": "string", "description": "记忆标识键，如 'user_project'"},
        "value": {"type": "string", "description": "要记住的内容"},
    },
    "required": ["key", "value"],
})
def save_memory(key: str, value: str) -> str:
    memory.save(key, value)
    return json.dumps({"status": "已保存", "key": key}, ensure_ascii=False)


@registry.tool("recall_memory", "回忆之前保存的信息", {
    "type": "object",
    "properties": {"key": {"type": "string", "description": "记忆键，留空则列出全部"}},
    "required": [],
})
def recall_memory(key: str = "") -> str:
    if key:
        val = memory.get(key)
        return json.dumps({"key": key, "value": val or "未找到"}, ensure_ascii=False)
    return json.dumps({"all_memories": memory.list_all()}, ensure_ascii=False)


# ━━━ 上下文构建器（动态组装 System Prompt） ━━━
class ContextBuilder:
    """
    Claude Code 的 context.ts 干的就是这件事：
    把多个来源的信息拼装成一份 System Prompt。
     来源包括：基础指令 + 环境信息 + 持久化记忆 + 工具描述。
    """
    def __init__(self, base_instructions: str, memory: Memory):
        self.base = base_instructions
        self.memory = memory

    def build(self) -> str:
        parts = [self.base]

        # 注入环境感知
        parts.append(f"\n## 当前环境\n- 目录: {os.getcwd()}\n- 时间: {time.strftime('%Y-%m-%d %H:%M')}")

        # 注入持久化记忆
        memories = self.memory.list_all()
        if memories:
            mem_lines = "\n".join(f"- {k}: {v}" for k, v in memories.items())
            parts.append(f"\n## 你记住的信息（来自之前的对话）\n{mem_lines}")

        # 注入工具概览
        parts.append(f"\n## 可用工具\n{', '.join(registry.list_tools())}")

        return "\n".join(parts)


# ━━━ Token 粗略估算 ━━━
def estimate_tokens(text: str) -> int:
    """中文约 1.5 token/字，英文约 0.4 token/字符"""
    cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return int(cn * 1.5 + (len(text) - cn) * 0.4)


def estimate_messages_tokens(messages: list[dict]) -> int:
    total = 0
    for m in messages:
        # messages 中可能混有字典和 API 返回的对象，统一处理
        if isinstance(m, dict):
            content = m.get("content") or ""
        else:
            content = getattr(m, "content", "") or ""
        if isinstance(content, str):
            total += estimate_tokens(content) + 4
    return total


# ━━━ Agent 循环（上下文增强版） ━━━
def agent_loop(user_message: str, max_turns: int = 10, token_budget: int = 6000) -> str:
    ctx = ContextBuilder("你是一个有记忆能力的AI助手。你可以保存和回忆重要信息，也可以做计算。", memory)
    system_prompt = ctx.build()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        tokens = estimate_messages_tokens(messages)
        print(f"  📊 ~{tokens} tokens（预算 {token_budget}）")

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
            result = registry.call(fn_name, fn_args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "达到最大轮次限制"


if __name__ == "__main__":
    memory.clear()  # 测试前清空
    print("=" * 60)
    print("Iter 3: 上下文工程 — 记忆与感知")
    print("=" * 60)

    # 测试 1: 保存记忆
    print("\n📝 测试 1: 保存记忆")
    r = agent_loop("请帮我记住两件事：1) 我的项目用 Python 3.11 + FastAPI  2) API 预算每月 500 元")
    print(f"\n🤖 {r}")

    # 测试 2: 回忆（模拟新对话，但记忆在文件中持久化了）
    print("\n" + "-" * 60)
    print("📝 测试 2: 回忆记忆")
    r = agent_loop("我之前告诉过你什么？请回忆一下。并把本次对话进行记忆")
    print(f"\n🤖 {r}")

    # 测试 3: 记忆 + 计算
    print("\n" + "-" * 60)
    print("📝 测试 3: 结合记忆做计算")
    r = agent_loop("根据我的预算信息，如果每次 API 调用 0.003 元，每天 5000 次，一个月能撑住吗？并把本次对话记忆")
    print(f"\n🤖 {r}")

    # memory.clear()  # 测试后清理
