---
title: Agent 开发必备 Python 知识清单
aliases: [R02, Python清单, Python知识, Agent开发Python知识清单]
tags: [python, development, async, pydantic]
date: 2026-04-10
category: 理论与架构
report_id: R02
tokens: 6370
status: completed
related:
  - "[Agent架构深度研究报告](R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)"
prev_path: reports/Agent开发Python知识清单.md
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Agent 开发必备 Python 知识清单

> 从"能看懂"到"能写 Agent"，按优先级排列
>
> 每个知识点都配有 Agent 场景中的真实用法

---

## 📋 速览：知识点优先级矩阵

| 优先级 | 知识点 | 为什么 Agent 开发需要它 | 你需要的程度 |
|--------|--------|----------------------|-------------|
| 🔴 必须 | async/await | Agent 循环、并发工具执行、API调用全是异步的 | 熟练 |
| 🔴 必须 | 函数 & 装饰器 | 所有框架用装饰器定义工具 `@tool` | 熟练 |
| 🔴 必须 | dict/JSON 操作 | LLM 输入输出全是 JSON | 熟练 |
| 🔴 必须 | 类 & 继承 | Agent/Tool 都是类，框架要继承 | 掌握 |
| 🟡 重要 | Type Hints 类型标注 | Pydantic schema验证、工具参数定义 | 掌握 |
| 🟡 重要 | Generator 生成器 | 流式输出、Agent循环的状态机模式 | 掌握 |
| 🟡 重要 | 错误处理 | Agent必须优雅处理LLM/工具的各种错误 | 掌握 |
| 🟡 重要 | Pydantic | 几乎每个框架都用Pydantic做数据验证 | 掌握 |
| 🟢 加分 | 上下文管理器 | 资源清理、MCP连接管理 | 了解 |
| 🟢 加分 | ABC 抽象类 | 设计工具接口、Agent接口 | 了解 |
| 🟢 加分 | 回调 & 观察者模式 | 钩子系统、事件监听 | 了解 |
| 🟢 加分 | 多进程/多线程 | 多Agent并行、后台任务 | 了解 |

---

## 🔴 第一优先级：这些不会就写不了 Agent

### 1. async/await（异步编程）⭐⭐⭐⭐⭐

**为什么最重要**：Agent 开发中 90% 的代码都跟异步有关——调 LLM API 是异步的、执行工具是异步的、多工具并发是异步的。

```python
# ============================================
# 基础：同步 vs 异步
# ============================================

# ❌ 同步写法 — 调3个API要等3次，总耗时 = 1s + 1s + 1s = 3s
import requests

def call_llm_sync(prompt):
    response = requests.post("https://api.anthropic.com/...", json={"prompt": prompt})
    return response.json()

result1 = call_llm_sync("问题1")  # 等1秒
result2 = call_llm_sync("问题2")  # 又等1秒
result3 = call_llm_sync("问题3")  # 又等1秒


# ✅ 异步写法 — 3个API同时发出，总耗时 ≈ 1s
import asyncio
import httpx

async def call_llm_async(prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.anthropic.com/...", json={"prompt": prompt})
        return response.json()

# 并发执行3个调用
async def main():
    results = await asyncio.gather(
        call_llm_async("问题1"),
        call_llm_async("问题2"),
        call_llm_async("问题3"),
    )
    # results = [结果1, 结果2, 结果3]

asyncio.run(main())
```

**Agent 中的真实场景**：

```python
# 场景1: Agent 主循环（最核心的模式）
async def agent_loop(user_input: str):
    messages = [{"role": "user", "content": user_input}]

    while True:
        # await = "等LLM回复，但不阻塞其他任务"
        response = await call_llm(messages)

        if response.tool_calls:
            # 多个只读工具可以并发执行！
            tasks = [execute_tool(tc) for tc in response.tool_calls]
            results = await asyncio.gather(*tasks)  # 并发执行
            # ...把结果加入 messages
        else:
            return response.content  # 没有工具调用 → 结束

# 场景2: 流式接收LLM响应
async def stream_response():
    async with client.stream("POST", url, json=payload) as response:
        async for chunk in response.aiter_text():
            # 每收到一块就处理（不等全部完成）
            print(chunk, end="", flush=True)

# 场景3: 带超时的工具执行
async def execute_with_timeout(tool_fn, args, timeout=30):
    try:
        result = await asyncio.wait_for(tool_fn(args), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        return "工具执行超时"
```

**必须掌握的 async 知识清单**：

```python
# (1) async def — 定义异步函数
async def my_func():
    pass

# (2) await — 等待异步操作完成
result = await some_async_operation()

# (3) asyncio.gather — 并发执行多个异步任务（Agent并发工具执行的核心）
results = await asyncio.gather(task1(), task2(), task3())

# (4) asyncio.run — 启动异步程序的入口
asyncio.run(main())

# (5) async for — 异步迭代（流式响应）
async for chunk in stream:
    process(chunk)

# (6) async with — 异步上下文管理器（HTTP连接等）
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# (7) asyncio.wait_for — 带超时的等待
result = await asyncio.wait_for(coroutine, timeout=10.0)

# (8) asyncio.create_task — 创建后台任务
task = asyncio.create_task(background_work())
# 继续做其他事...
await task  # 需要时再等结果
```

---

### 2. 函数 & 装饰器（Decorator）⭐⭐⭐⭐⭐

**为什么重要**：**所有 Agent 框架都用装饰器来定义工具**，这是 Agent 开发中出现频率最高的语法。

```python
# ============================================
# 装饰器基础：它到底做了什么？
# ============================================

# 装饰器 = 一个"包装函数"的函数
# 它接收一个函数，返回一个"增强版"的函数

# 不用装饰器的写法（等价，但丑）：
def my_tool(query):
    return search(query)
my_tool = register_as_tool(my_tool)  # 手动包装

# 用装饰器的写法（语法糖，一样的效果）：
@register_as_tool      # ← 这就是装饰器
def my_tool(query):
    return search(query)

# ============================================
# Agent 框架中装饰器的真实用法
# ============================================

# --- OpenAI Agents SDK ---
from agents import function_tool

@function_tool               # ← 自动把函数注册为 Agent 可调用的工具
def search_web(query: str) -> str:
    """搜索网页获取最新信息"""    # ← docstring 会自动变成工具描述！
    return do_search(query)

# --- LangChain / LangGraph ---
from langchain.tools import tool

@tool                        # ← 同样的模式
def calculator(expression: str) -> str:
    """计算数学表达式"""
    return str(eval(expression))

# --- CrewAI ---
from crewai import tool

@tool("Search Tool")         # ← 带参数的装饰器
def search(query: str) -> str:
    """搜索信息"""
    return results
```

**理解装饰器原理**（面试和Debug都需要）：

```python
# 装饰器的真面目：一个返回函数的函数

# === 无参装饰器 ===
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"开始调用 {func.__name__}")  # 调用前做点事
        result = func(*args, **kwargs)       # 调用原函数
        print(f"调用完成")                   # 调用后做点事
        return result
    return wrapper

@my_decorator
def hello(name):
    print(f"Hello {name}!")

hello("World")
# 输出:
# 开始调用 hello
# Hello World!
# 调用完成


# === 带参数的装饰器（套了三层！）===
def timeout(seconds):               # 第1层：接收装饰器参数
    def decorator(func):             # 第2层：接收被装饰的函数
        async def wrapper(*args, **kwargs):  # 第3层：实际执行
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
        return wrapper
    return decorator

@timeout(30)   # 等价于：my_tool = timeout(30)(my_tool)
async def my_tool(query):
    return await slow_search(query)


# === Agent 开发中最常用的装饰器模式：注册模式 ===
# 把函数注册到一个工具列表中

TOOL_REGISTRY = {}

def register_tool(name: str):
    def decorator(func):
        TOOL_REGISTRY[name] = {
            "function": func,
            "description": func.__doc__,  # 从 docstring 提取描述
        }
        return func
    return decorator

@register_tool("web_search")
def search(query: str) -> str:
    """搜索网页"""
    return "搜索结果..."

@register_tool("calculator")
def calc(expression: str) -> str:
    """数学计算"""
    return str(eval(expression))

print(TOOL_REGISTRY)
# {'web_search': {'function': <func>, 'description': '搜索网页'},
#  'calculator': {'function': <func>, 'description': '数学计算'}}
```

---

### 3. dict 与 JSON 操作 ⭐⭐⭐⭐⭐

**为什么重要**：LLM API 的输入输出全是 JSON，工具定义是 JSON Schema，消息列表是 dict 数组。

```python
import json

# ============================================
# Agent 开发中的 JSON 操作高频场景
# ============================================

# 场景1: 构建消息列表（每个Agent都要做的事）
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "帮我搜索 Python 教程"},
]

# 追加消息
messages.append({
    "role": "assistant",
    "content": None,
    "tool_calls": [{
        "id": "call_123",
        "type": "function",
        "function": {"name": "search", "arguments": '{"query": "Python教程"}'}
    }]
})

# 场景2: 解析 LLM 返回的工具调用参数（经常需要）
tool_call = response.choices[0].message.tool_calls[0]
args = json.loads(tool_call.function.arguments)  # JSON字符串 → Python dict
print(args["query"])  # "Python教程"

# 场景3: 构建工具的 JSON Schema（告诉LLM工具怎么用）
tool_schema = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "搜索网页",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}

# 场景4: 安全地访问嵌套字典（LLM返回的JSON经常嵌套很深）
# ❌ 危险：任何一层是 None 都会崩
content = response["choices"][0]["message"]["content"]

# ✅ 安全：用 .get() 提供默认值
content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

# ✅ 更安全：try/except
try:
    content = response["choices"][0]["message"]["content"]
except (KeyError, IndexError, TypeError):
    content = ""

# 场景5: dict 合并（合并配置、合并上下文）
default_config = {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 4096}
user_config = {"temperature": 0.2}
final_config = {**default_config, **user_config}  # user_config 覆盖 default
# {'model': 'gpt-4o', 'temperature': 0.2, 'max_tokens': 4096}

# Python 3.9+ 也可以这样：
final_config = default_config | user_config
```

---

### 4. 类与继承 ⭐⭐⭐⭐

**为什么重要**：Agent、Tool、Memory 在框架中都是类。你需要定义自己的 Agent 类、继承框架的 BaseTool 等。

```python
# ============================================
# Agent 开发中类的典型用法
# ============================================

# 场景1: 定义工具基类 + 实现具体工具（几乎每个框架都这么干）
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """所有工具的基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（LLM会看到这个！）"""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具"""
        ...

    def to_schema(self) -> dict:
        """自动生成 JSON Schema（所有子类共享这个方法）"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
            }
        }


class WebSearchTool(BaseTool):
    """搜索工具 — 继承BaseTool，实现具体逻辑"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "搜索网页获取最新信息"

    async def execute(self, query: str, max_results: int = 5) -> str:
        # 实际搜索逻辑
        results = await do_search(query, max_results)
        return json.dumps(results)


# 场景2: Agent 类（管理状态 + 循环）
class Agent:
    def __init__(self, model: str, tools: list[BaseTool], system_prompt: str):
        self.model = model
        self.tools = {t.name: t for t in tools}  # 名字→工具的映射
        self.system_prompt = system_prompt
        self.messages: list[dict] = []            # 对话历史（状态）
        self.total_tokens = 0                     # Token 计数（状态）

    async def run(self, user_input: str) -> str:
        """Agent 主循环"""
        self.messages.append({"role": "user", "content": user_input})

        while True:
            response = await self._call_llm()
            self.total_tokens += response.usage.total_tokens

            if not response.tool_calls:
                return response.content

            for tc in response.tool_calls:
                tool = self.tools[tc.function.name]
                result = await tool.execute(**json.loads(tc.function.arguments))
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })

    async def _call_llm(self):
        """调用 LLM（私有方法，用 _ 前缀表示）"""
        return await client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=[t.to_schema() for t in self.tools.values()]
        )
```

**类相关的必备知识**：

```python
# (1) __init__ — 构造函数，初始化状态
# (2) self — 实例引用
# (3) 继承 — class Child(Parent)
# (4) @abstractmethod — 强制子类实现
# (5) @property — 把方法当属性用
# (6) @classmethod / @staticmethod — 类方法/静态方法
# (7) __str__ / __repr__ — 调试打印
# (8) dataclass — 简化数据类定义（见下面 Pydantic 部分）
```

---

## 🟡 第二优先级：不会也能跑，但很快会碰壁

### 5. Type Hints 类型标注 ⭐⭐⭐⭐

**为什么重要**：Agent 框架会**读取你的类型标注**来自动生成工具的参数 Schema。类型标注不对，工具就废了。

```python
# ============================================
# 类型标注如何变成工具 Schema
# ============================================

# 你写的 Python 函数：
@function_tool
def search(
    query: str,                           # ← 框架看到 str → JSON type: "string"
    max_results: int = 5,                 # ← int + 默认值 → type: "integer", default: 5
    include_images: bool = False,         # ← bool → type: "boolean"
) -> str:
    """搜索网页获取信息"""                   # ← docstring → description
    ...

# 框架自动生成的 JSON Schema（发给LLM）：
# {
#   "name": "search",
#   "description": "搜索网页获取信息",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "query": {"type": "string"},
#       "max_results": {"type": "integer", "default": 5},
#       "include_images": {"type": "boolean", "default": false}
#     },
#     "required": ["query"]     ← 没有默认值的参数 = required
#   }
# }


# ============================================
# Agent 开发常用的类型标注
# ============================================
from typing import Optional, Union, Any

# 基础类型
name: str = "agent"
count: int = 0
temperature: float = 0.7
enabled: bool = True

# 容器类型（Python 3.9+ 可以直接用小写）
messages: list[dict] = []                    # 消息列表
tools: dict[str, callable] = {}              # 工具注册表
config: dict[str, Any] = {}                  # 任意配置

# Optional — 可以是 None
result: Optional[str] = None                 # str 或 None
# Python 3.10+ 等价写法：
result: str | None = None

# Union — 多种类型
content: Union[str, list[dict]] = ""         # str 或 list[dict]
# Python 3.10+:
content: str | list[dict] = ""

# Literal — 限定取值（Agent框架中用于模式选择）
from typing import Literal
mode: Literal["plan", "execute", "review"] = "execute"
model: Literal["sonnet", "opus", "haiku"] = "sonnet"

# Callable — 函数类型（钩子、回调）
from typing import Callable
hook: Callable[[str, dict], bool]            # 接收 (str, dict)，返回 bool
async_hook: Callable[..., Awaitable[None]]   # 异步回调

# TypedDict — 给 dict 加类型约束
from typing import TypedDict

class ToolCall(TypedDict):
    id: str
    name: str
    arguments: dict[str, Any]

class Message(TypedDict):
    role: Literal["user", "assistant", "system", "tool"]
    content: str | None
    tool_calls: list[ToolCall] | None   # 注意: 不是 Optional
```

---

### 6. Generator 生成器 ⭐⭐⭐⭐

**为什么重要**：流式输出和 Agent 循环的高级模式都用 generator。Claude Code 的整个核心循环就是 async generator。

```python
# ============================================
# 生成器基础
# ============================================

# 普通函数：一次返回所有结果
def get_all_results():
    results = []
    for i in range(1000000):
        results.append(expensive_compute(i))
    return results  # 全部算完才返回，内存炸了

# 生成器：要一个给一个（懒计算）
def get_results_lazy():
    for i in range(1000000):
        yield expensive_compute(i)  # yield = "给你一个，我先暂停"

for result in get_results_lazy():
    print(result)  # 边算边用，内存友好


# ============================================
# Agent 中生成器的实际用法
# ============================================

# 场景1: 流式输出LLM响应（打字机效果）
async def stream_llm_response(prompt: str):
    """异步生成器 — Agent 中最常见的模式"""
    async with client.stream("POST", api_url, json={"prompt": prompt}) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                chunk = json.loads(line[6:])
                yield chunk["text"]  # 每收到一块就 yield 出去

# 使用：
async for text in stream_llm_response("你好"):
    print(text, end="", flush=True)  # 打字机效果


# 场景2: Agent 循环作为生成器（Claude Code 的核心模式！）
async def agent_loop(messages):
    """
    把 Agent 循环做成 async generator，
    调用者可以实时收到中间状态（工具调用、进度等）
    """
    while True:
        response = await call_llm(messages)

        # yield 中间产物（让调用者看到进度）
        yield {"type": "llm_response", "content": response}

        if response.tool_calls:
            for tc in response.tool_calls:
                yield {"type": "tool_start", "tool": tc.name}
                result = await execute_tool(tc)
                yield {"type": "tool_result", "result": result}
                messages.append(make_tool_result_message(tc, result))
        else:
            yield {"type": "final", "content": response.content}
            return  # 生成器结束

# 调用者可以实时处理每一步：
async for event in agent_loop(messages):
    if event["type"] == "tool_start":
        print(f"🔧 正在执行 {event['tool']}...")
    elif event["type"] == "final":
        print(f"✅ {event['content']}")


# 场景3: yield from — 委托给子生成器（子Agent结果传递）
async def orchestrator():
    # 把子Agent的所有事件透传出来
    async for event in sub_agent_loop():
        yield event  # "透传"
    yield {"type": "orchestrator_done"}
```

**必须记住的语法**：

```python
# yield     — 产出一个值，暂停
# yield from — 委托给另一个生成器（同步）
# async for — 消费异步生成器
# async def + yield = 异步生成器
# return 在生成器中 = StopIteration（结束）
```

---

### 7. 错误处理 ⭐⭐⭐⭐

**为什么重要**：Agent 调用外部 API 和工具，什么错都可能出——网络超时、API 限流、工具崩溃、LLM 拒绝回答。不处理就全崩。

```python
# ============================================
# Agent 开发中的错误处理模式
# ============================================

# 模式1: 工具执行 — 错误不崩溃，而是反馈给 LLM
async def safe_tool_execute(tool, args):
    """Agent 的黄金法则：工具出错 → 告诉 LLM，而不是程序崩溃"""
    try:
        result = await tool.execute(**args)
        return {"success": True, "result": result}
    except TimeoutError:
        return {"success": False, "error": "工具执行超时，请尝试其他方法"}
    except PermissionError:
        return {"success": False, "error": "没有权限执行此操作"}
    except Exception as e:
        return {"success": False, "error": f"工具执行失败: {type(e).__name__}: {str(e)}"}
    # → LLM 看到错误后会自己调整策略！


# 模式2: API 调用 — 重试 + 退避
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),           # 最多重试3次
    wait=wait_exponential(min=1, max=10), # 指数退避: 1s, 2s, 4s...
)
async def call_llm_with_retry(messages):
    try:
        return await client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
    except RateLimitError:
        raise  # 让 tenacity 来重试
    except AuthenticationError:
        raise  # 认证错误，不重试，直接崩（该崩的时候要崩）


# 模式3: 自定义异常（清晰的错误语义）
class AgentError(Exception):
    """Agent 基础异常"""
    pass

class ToolExecutionError(AgentError):
    """工具执行失败"""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")

class TokenBudgetExceeded(AgentError):
    """Token 预算耗尽"""
    pass

class MaxTurnsExceeded(AgentError):
    """超过最大循环次数"""
    pass


# 模式4: Agent 循环的完整错误处理
async def robust_agent_loop(messages, max_turns=20):
    for turn in range(max_turns):
        try:
            response = await call_llm_with_retry(messages)
        except AuthenticationError:
            raise  # 致命错误，向上抛
        except Exception as e:
            # 非致命 API 错误 → 告诉用户
            return f"抱歉，AI 服务暂时不可用: {e}"

        if not response.tool_calls:
            return response.content

        for tc in response.tool_calls:
            result = await safe_tool_execute(tools[tc.name], tc.args)
            messages.append(make_tool_message(tc.id, result))

    raise MaxTurnsExceeded(f"Agent exceeded {max_turns} turns")
```

---

### 8. Pydantic（数据验证框架）⭐⭐⭐⭐

**为什么重要**：LangChain、CrewAI、OpenAI SDK 等几乎所有框架都用 Pydantic 做数据验证和 Schema 生成。

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

# ============================================
# Pydantic 基础：带验证的数据类
# ============================================

# 普通 dict — 什么都能塞，运行时才发现错误
config = {"model": "gpt-4o", "temperature": "高"}  # "高"不是数字！但不会报错

# Pydantic model — 定义时就约束类型，错了立刻报错
class AgentConfig(BaseModel):
    model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0, le=2.0)  # 0-2.0之间
    max_tokens: int = Field(default=4096, gt=0)
    tools: list[str] = []

config = AgentConfig(temperature=0.5)  # ✅ 正常
config = AgentConfig(temperature="高")  # ❌ 立刻报错: value is not a valid float


# ============================================
# Agent 开发中的 Pydantic 用法
# ============================================

# 场景1: 定义工具的输入参数（自动生成 JSON Schema）
class SearchInput(BaseModel):
    """搜索工具的输入参数"""
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=5, description="最大结果数", ge=1, le=20)
    language: Literal["zh", "en"] = Field(default="zh", description="结果语言")

# 自动生成 JSON Schema（就是发给 LLM 的工具描述）
print(SearchInput.model_json_schema())
# {
#   "properties": {
#     "query": {"description": "搜索关键词", "type": "string"},
#     "max_results": {"default": 5, "description": "最大结果数", ...},
#     "language": {"default": "zh", "enum": ["zh", "en"], ...}
#   },
#   "required": ["query"],
#   ...
# }


# 场景2: 解析 LLM 输出为结构化数据
class TaskPlan(BaseModel):
    """让 LLM 输出结构化计划"""
    goal: str = Field(description="任务目标")
    steps: list[str] = Field(description="执行步骤列表")
    estimated_time: Optional[str] = Field(default=None, description="预计时间")

# LLM 返回 JSON → Pydantic 自动验证和解析
raw_json = '{"goal": "重构代码", "steps": ["分析", "设计", "实现"], "estimated_time": "2小时"}'
plan = TaskPlan.model_validate_json(raw_json)  # JSON字符串 → Python对象
print(plan.goal)    # "重构代码"
print(plan.steps)   # ["分析", "设计", "实现"]


# 场景3: 嵌套模型（复杂Agent配置）
class ToolConfig(BaseModel):
    name: str
    enabled: bool = True
    timeout: int = 30

class MemoryConfig(BaseModel):
    type: Literal["session", "persistent"] = "session"
    max_entries: int = 100

class FullAgentConfig(BaseModel):
    model: str = "gpt-4o"
    system_prompt: str
    tools: list[ToolConfig]
    memory: MemoryConfig = MemoryConfig()
```

---

## 🟢 第三优先级：进阶提升，写出更专业的 Agent

### 9. 上下文管理器（Context Manager）⭐⭐⭐

```python
# Agent 开发中的上下文管理器：确保资源正确清理

# 场景1: MCP 服务器连接管理
class MCPConnection:
    async def __aenter__(self):
        self.client = await connect_to_mcp_server()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()  # 无论是否出错，都关闭连接

async def main():
    async with MCPConnection() as mcp:
        tools = await mcp.list_tools()

# 场景2: 用 contextmanager 装饰器（更简洁）
from contextlib import asynccontextmanager

@asynccontextmanager
async def agent_session(config):
    agent = Agent(config)
    await agent.start()
    try:
        yield agent          # yield 之前 = __aenter__，之后 = __aexit__
    finally:
        await agent.cleanup()
        await agent.save_memory()
```

### 10. 回调与观察者模式 ⭐⭐⭐

```python
# 这就是"钩子系统"的 Python 实现原理

class EventEmitter:
    """简版事件系统 — 钩子的核心实现原理"""

    def __init__(self):
        self._hooks: dict[str, list[callable]] = {}

    def on(self, event: str, callback: callable):
        """注册钩子"""
        self._hooks.setdefault(event, []).append(callback)

    async def emit(self, event: str, data: dict):
        """触发钩子"""
        for callback in self._hooks.get(event, []):
            result = await callback(data)
            if result and result.get("block"):
                return {"blocked": True, "reason": result.get("reason")}
        return {"blocked": False}


# 使用：
agent = EventEmitter()

# 注册钩子：禁止删除操作
async def block_delete(data):
    if "rm -rf" in data.get("command", ""):
        return {"block": True, "reason": "危险操作！"}

agent.on("pre_tool_use", block_delete)

# Agent 执行工具前触发钩子：
result = await agent.emit("pre_tool_use", {"command": "rm -rf /"})
if result["blocked"]:
    print(f"被拦截: {result['reason']}")
```

### 11. 列表推导式 & 函数式操作 ⭐⭐⭐

```python
# Agent 开发中高频使用的简洁写法

# 过滤启用的工具
enabled_tools = [t for t in all_tools if t.is_enabled()]

# 提取所有工具名
tool_names = [t.name for t in tools]

# 构建工具名 → 工具的映射
tool_map = {t.name: t for t in tools}

# 过滤只读工具（并行执行用）
readonly_tools = [tc for tc in tool_calls if tools[tc.name].is_readonly()]
writable_tools = [tc for tc in tool_calls if not tools[tc.name].is_readonly()]

# 多条件过滤
safe_calls = [
    tc for tc in tool_calls
    if tc.name not in BLOCKED_TOOLS
    and not tc.args.get("dangerous", False)
]

# any / all — 快速判断
has_errors = any(r.get("is_error") for r in results)
all_done = all(t.status == "completed" for t in tasks)

# map + filter 函数式风格
schemas = list(map(lambda t: t.to_schema(), enabled_tools))
```

---

## 📋 速查表：Agent 开发 Python 备忘录

```python
# ===== 异步 =====
async def fn():                    # 定义异步函数
await coroutine                    # 等待异步结果
asyncio.gather(a(), b(), c())      # 并发执行
asyncio.run(main())                # 入口
async for item in gen:             # 异步迭代
async with ctx as x:               # 异步上下文

# ===== 装饰器 =====
@decorator                         # 无参装饰器
@decorator(arg)                    # 带参装饰器
functools.wraps(func)              # 保留原函数信息

# ===== 类型 =====
x: str                             # 字符串
x: int | None                      # 可选 (3.10+)
x: list[str]                       # 字符串列表
x: dict[str, Any]                  # 字典
x: Literal["a", "b"]              # 枚举值
x: Callable[[str], bool]           # 函数类型

# ===== Pydantic =====
class M(BaseModel):                # 定义模型
    x: str = Field(description="") # 带描述的字段
M.model_json_schema()              # 生成JSON Schema
M.model_validate_json(s)           # 从JSON解析
M.model_dump()                     # 转为dict

# ===== 生成器 =====
yield value                        # 产出值
yield from other_gen               # 委托
async def gen(): yield x           # 异步生成器

# ===== 错误处理 =====
try: ... except E as e: ...        # 捕获异常
raise CustomError("msg")           # 抛出异常
except (E1, E2): ...               # 多异常
finally: cleanup()                 # 必定执行

# ===== 常用操作 =====
json.loads(s) / json.dumps(obj)    # JSON 互转
d.get("key", default)              # 安全取值
{**d1, **d2}                       # 合并字典
[x for x in lst if cond]           # 列表推导
{k: v for k, v in items}           # 字典推导
any(...) / all(...)                # 存在/全部判断
```

---

## 🗓️ 建议学习路线

```
Week 1: async/await + JSON操作
├─ 写一个异步调用 LLM API 的脚本
├─ 用 asyncio.gather 并发调用3次 API
└─ 练习解析和构建 LLM 消息格式的 JSON

Week 2: 装饰器 + 类
├─ 写一个 @register_tool 装饰器
├─ 实现 BaseTool + 2个具体工具类
└─ 组装成一个简单 Agent（30行版本）

Week 3: Pydantic + Type Hints
├─ 用 Pydantic 定义工具输入 Schema
├─ 实现 LLM 输出 → Pydantic 模型的解析
└─ 给 30 行 Agent 加上类型标注

Week 4: Generator + 错误处理
├─ 把 Agent 循环改成 async generator
├─ 实现流式输出
├─ 加上完整的错误处理和重试逻辑
└─ 🎉 你已经具备 Agent 开发能力了！
```
