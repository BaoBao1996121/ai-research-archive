"""
Iter 2: 工具系统 — 注册、调度、执行（~170 行核心代码）
====================================================
目标：工具从硬编码变为可插拔。装饰器注册 → 自动生成 Schema → 统一分发。
新增：ToolRegistry 类 + @tool 装饰器 + 5 个工具演示
学到：注册表模式、工具自描述、统一工具接口。

Claude Code 对照：
  - tools/Tool.ts: abstract class Tool { name, description, inputSchema, execute() }
  - tools/index.ts: TOOL_REGISTRY —— 所有工具在此注册
  - 每个工具是独立文件（BashTool.ts, ReadFileTool.ts...），implements Tool

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter2_tool_system.py
"""

import os
import json
from pathlib import Path
from config import client, MODEL


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  核心：工具注册表
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ToolRegistry:
    """
    统一的工具注册、Schema 生成和分发中心。
    Claude Code 的 Tool.ts 做了同样的事——让每个工具自描述。
    """
    def __init__(self):
        self._tools: dict[str, callable] = {}
        self._schemas: list[dict] = []

    def tool(self, name: str, description: str, parameters: dict):
        """装饰器：把普通函数注册为 Agent 工具"""
        def decorator(fn):
            self._tools[name] = fn
            self._schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            })
            return fn
        return decorator

    def call(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        try:
            result = self._tools[name](**arguments)
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False)

    @property
    def schemas(self) -> list[dict]:
        return self._schemas

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


registry = ToolRegistry()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  注册具体工具（每个只需 @registry.tool + 一个函数）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@registry.tool("calculator", "计算数学表达式（加减乘除、括号、幂运算）", {
    "type": "object",
    "properties": {
        "expression": {"type": "string", "description": "数学表达式，如 '(1+2)*3**2'"}
    },
    "required": ["expression"],
})
def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "包含不允许的字符"}, ensure_ascii=False)
    return json.dumps({"result": eval(expression)})


@registry.tool("get_current_time", "获取当前日期和时间", {
    "type": "object", "properties": {},
})
def get_current_time() -> str:
    from datetime import datetime
    return json.dumps({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


@registry.tool("read_file", "读取本地文件的文本内容（前 5000 字符）", {
    "type": "object",
    "properties": {"path": {"type": "string", "description": "文件路径"}},
    "required": ["path"],
})
def read_file(path: str) -> str:
    try:
        content = Path(path).read_text(encoding="utf-8")[:5000]
        return json.dumps({"content": content, "chars": len(content)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@registry.tool("list_directory", "列出目录下的文件和子目录", {
    "type": "object",
    "properties": {"path": {"type": "string", "description": "目录路径", "default": "."}},
    "required": [],
})
def list_directory(path: str = ".") -> str:
    try:
        entries = sorted(os.listdir(path))[:50]
        dirs = [e + "/" for e in entries if os.path.isdir(os.path.join(path, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        return json.dumps({"directories": dirs, "files": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@registry.tool("write_file", "将内容写入文件（创建或覆盖）", {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "要写入的内容"},
    },
    "required": ["path", "content"],
})
def write_file(path: str, content: str) -> str:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return json.dumps({"status": "ok", "path": path, "bytes": len(content.encode())})
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Agent 循环
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def agent_loop(user_message: str, max_turns: int = 10) -> str:
    messages = [
        {"role": "system", "content": f"你是一个AI助手。可用工具: {', '.join(registry.list_tools())}。根据需要使用工具。"},
        {"role": "user", "content": user_message},
    ]
    for turn in range(max_turns):
        print(f"  ⚡ 第 {turn + 1} 轮...")
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
            print(f"  🔧 {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:80]})")
            result = registry.call(fn_name, fn_args)
            print(f"  📋 → {result[:100]}...")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "⚠️ 达到最大轮次限制"


if __name__ == "__main__":
    print("=" * 60)
    print(f"Iter 2: 工具系统 — 已注册 {len(registry.list_tools())} 个工具")
    print(f"工具列表: {registry.list_tools()}")
    print("=" * 60)

    print("\n📝 测试: 综合使用多种工具")
    result = agent_loop(
        "帮我做三件事：\n1) 看看当前目录有哪些文件\n2) 现在几点了\n3) 计算 2**10 + 3**7"
    )
    print(f"\n🤖 最终回答:\n{result}")
