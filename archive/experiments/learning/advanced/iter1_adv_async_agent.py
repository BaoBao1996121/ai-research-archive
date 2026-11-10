"""
Iter 1 进阶: 异步 Agent — async/await 并发（~140 行核心代码）
=============================================================
基础版差距：所有 API 调用和工具执行都是同步串行的。
进阶补全：async/await 异步循环 + 工具并行执行 + 性能对比。

Claude Code 对照：
  - 所有 API 调用都是 async：await querySingleTurn(), await stream()
  - toolOrchestration.ts: 独立工具并行执行，同文件操作串行
  - 并发不只是性能优化——它让 Agent 能"同时做多件事"

依赖：pip install openai（AsyncOpenAI 已内置）
运行：python iter1_adv_async_agent.py
"""

import asyncio
import json
import time
from openai import AsyncOpenAI
from config import API_KEY, BASE_URL, MODEL

# ━━━ 异步客户端（注意：和同步版是不同的类） ━━━
async_client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)


# ━━━ 工具定义 ━━━
TOOLS = [
    {"type": "function", "function": {
        "name": "slow_search", "description": "搜索技术资料（耗时操作）",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "搜索关键词"}
        }, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "slow_analyze", "description": "数据分析（耗时操作）",
        "parameters": {"type": "object", "properties": {
            "data": {"type": "string", "description": "要分析的数据"}
        }, "required": ["data"]}}},
    {"type": "function", "function": {
        "name": "calculator", "description": "计算数学表达式",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]}}},
]


# ━━━ 工具实现（异步版：用 await asyncio.sleep 模拟耗时 I/O） ━━━
async def slow_search(query: str) -> str:
    await asyncio.sleep(2)  # 模拟 2s 网络延迟
    return json.dumps({
        "results": [f"'{query}'相关结果 1", f"'{query}'相关结果 2"],
        "took_ms": 2000
    }, ensure_ascii=False)


async def slow_analyze(data: str) -> str:
    await asyncio.sleep(2)  # 模拟 2s 计算耗时
    return json.dumps({
        "analysis": f"对'{data}'的分析完成", "confidence": 0.85
    }, ensure_ascii=False)


async def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})


TOOL_MAP = {
    "slow_search": slow_search,
    "slow_analyze": slow_analyze,
    "calculator": calculator,
}


# ╔══════════════════════════════════════════════════════════════╗
# ║  核心：异步 Agent 循环 + 工具并行执行                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def async_agent_loop(user_message: str, max_turns: int = 5) -> str:
    """
    异步版 ReAct 循环，关键改进：
    1. API 调用用 await（非阻塞）
    2. 多个工具调用用 asyncio.gather 并行执行
    3. 总耗时 = max(单个工具耗时)，而非 sum(所有工具耗时)

    Claude Code 的 toolOrchestration.ts 做了更精细的调度：
    - 独立工具（search + analyze）→ 并行
    - 同文件操作（read → write 同一文件）→ 串行（避免竞争条件）
    """
    messages = [
        {"role": "system", "content": "你是一个AI助手。可以并行使用多个工具完成任务。"},
        {"role": "user", "content": user_message},
    ]

    for turn in range(max_turns):
        print(f"  ⚡ 第 {turn + 1} 轮推理...")

        # 异步 API 调用（不阻塞事件循环）
        response = await async_client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            print(f"  ✅ 完成（共 {turn + 1} 轮）")
            return msg.content or ""

        # ⭐ 关键改进：并行执行所有工具调用
        print(f"  🔧 并行执行 {len(msg.tool_calls)} 个工具...")
        t0 = time.time()

        async def execute_one(tc):
            """执行单个工具调用"""
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            print(f"    → {fn_name}({json.dumps(fn_args, ensure_ascii=False)[:60]})")
            if fn_name in TOOL_MAP:
                result = await TOOL_MAP[fn_name](**fn_args)
            else:
                result = json.dumps({"error": f"未知工具: {fn_name}"})
            return tc.id, result

        # asyncio.gather = 所有工具同时开始
        results = await asyncio.gather(*(execute_one(tc) for tc in msg.tool_calls))

        elapsed = time.time() - t0
        serial_estimate = sum(2 for _ in msg.tool_calls)  # 每个工具约 2s
        print(f"  ⏱️ {len(results)} 个工具并行完成: {elapsed:.1f}s（串行约需 {serial_estimate}s）")

        for tool_call_id, result in results:
            messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result})

    return "⚠️ 达到最大轮次"


# ╔══════════════════════════════════════════════════════════════╗
# ║  对照组：同步串行版本                                        ║
# ╚══════════════════════════════════════════════════════════════╝

def sync_agent_loop(user_message: str, max_turns: int = 5) -> str:
    """同步串行版——和基础版一样，一个接一个执行"""
    from config import client

    messages = [
        {"role": "system", "content": "你是一个AI助手。可以使用多个工具。"},
        {"role": "user", "content": user_message},
    ]
    for turn in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content or ""

        t0 = time.time()
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            time.sleep(2)  # 同步版：串行等待
            result = json.dumps({"result": f"[同步] {fn_name} 完成"}, ensure_ascii=False)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        print(f"  ⏱️ 同步串行: {time.time()-t0:.1f}s")

    return "⚠️ 达到最大轮次"


# ╔══════════════════════════════════════════════════════════════╗
# ║  进阶：智能调度（区分可并行 vs 需串行的工具）                  ║
# ╚══════════════════════════════════════════════════════════════╝

# Claude Code 的 toolOrchestration.ts 核心逻辑：
# 操作同一资源的工具必须串行，其余可以并行
RESOURCE_MAP = {
    "slow_search": None,      # 无共享资源 → 可并行
    "slow_analyze": None,     # 无共享资源 → 可并行
    "calculator": None,       # 无共享资源 → 可并行
    # 如果有 read_file/write_file，操作同一文件的需要串行
}


async def smart_dispatch(tool_calls: list, tool_map: dict) -> list[tuple[str, str]]:
    """
    智能调度：按资源分组，组内串行，组间并行。

    例：read_file(a.txt) + write_file(a.txt) + search("AI")
    → 组1: [read(a.txt), write(a.txt)] 串行
    → 组2: [search("AI")] 并行
    → 两组之间并行执行
    """
    # 按资源分组
    groups: dict[str, list] = {}  # resource → [tool_calls]
    for tc in tool_calls:
        resource = RESOURCE_MAP.get(tc.function.name)
        key = resource or f"_independent_{id(tc)}"
        groups.setdefault(key, []).append(tc)

    async def run_group(tcs):
        """组内串行执行"""
        results = []
        for tc in tcs:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            if fn_name in tool_map:
                r = await tool_map[fn_name](**fn_args)
            else:
                r = json.dumps({"error": f"未知: {fn_name}"})
            results.append((tc.id, r))
        return results

    # 组间并行
    all_results = await asyncio.gather(*(run_group(tcs) for tcs in groups.values()))
    return [item for sublist in all_results for item in sublist]


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 1 进阶: 异步 Agent — async/await 并发")
    print("=" * 60)

    print("\n📝 异步版: 多工具并行执行")
    result = asyncio.run(async_agent_loop(
        "帮我做三件事：\n"
        "1) 搜索 'AI Agent 框架'\n"
        "2) 分析 '2024年 Agent 发展趋势'\n"
        "3) 计算 365 * 24"
    ))
    print(f"\n🤖 最终回答:\n{result}")

    print(f"\n{'='*60}")
    print("📊 性能对比:")
    print("  同步串行: N 个工具 × 2s/个 = 2N 秒")
    print("  异步并行: N 个工具同时执行 = 2 秒")
    print("  提速 Nx（工具越多，差距越大）")
    print()
    print("  Claude Code 的精细调度:")
    print("  - 独立工具 → asyncio.gather 并行")
    print("  - 操作同一文件 → 串行（避免竞争条件）")
    print("  - 这就是 toolOrchestration.ts 的核心逻辑")
