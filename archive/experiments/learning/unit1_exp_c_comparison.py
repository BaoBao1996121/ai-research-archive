"""
实验 C: 三种 LLM 调用方式对比
参考: S5-01 第二章「三种 LLM 调用模式」

学习目标:
  1. 用三种方式完成同一任务，直观感受差异
  2. 对比代码量、启动开销、灵活性
  3. 形成自己的选型判断力

任务: 给一段文本做摘要

运行方式:
  pip install httpx langchain-openai python-dotenv
  python unit1_exp_c_comparison.py
"""

import httpx
import asyncio
import time
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "")

TEXT = """
FastAPI 是一个现代、快速（高性能）的 Web 框架，用于构建 API，
基于 Python 类型提示。它的主要特点包括：自动生成交互式 API 文档（Swagger UI）、
内建数据验证（通过 Pydantic v2）、支持异步请求处理（async/await）、
以及与 OpenAPI 标准的完全兼容。FastAPI 的性能接近 Node.js 和 Go，
同时保持了 Python 的易用性。它被广泛用于构建 AI/ML 后端服务、
微服务架构和实时数据处理管道。
"""

SYSTEM_PROMPT = "你是摘要助手。用一句话（不超过50字）总结用户给的文本。只输出摘要，不要其他内容。"


# ================================================================
# 方式一：httpx 直调（最轻量）
# ================================================================
async def summarize_httpx(text: str) -> dict:
    start = time.time()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0,
            },
        )
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"]
    elapsed = time.time() - start
    return {"method": "httpx 直调", "result": result, "time": elapsed, "lines": 12}


# ================================================================
# 方式二：LangChain ChatOpenAI（框架化）
# ================================================================
def summarize_langchain(text: str) -> dict:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    start = time.time()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=API_KEY,
        base_url=API_BASE,
    )
    result = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ])
    elapsed = time.time() - start
    return {"method": "LangChain", "result": result.content, "time": elapsed, "lines": 10}


# ================================================================
# 对比运行
# ================================================================
async def main():
    if not API_KEY or API_KEY == "YOUR_KEY_HERE":
        print("❌ 请先在 .env 中填入 OPENAI_API_KEY")
        return

    print("=" * 60)
    print("实验 C: 三种 LLM 调用方式对比")
    print("=" * 60)
    print(f"\n任务: 摘要以下文本 ({len(TEXT.strip())} 字)")
    print(f"文本: {TEXT.strip()[:80]}...")
    print()

    results = []

    # httpx
    print("⏳ 测试 httpx 直调...")
    r1 = await summarize_httpx(TEXT)
    results.append(r1)
    print(f"   ✅ {r1['time']:.2f}s")

    # LangChain
    print("⏳ 测试 LangChain...")
    r2 = summarize_langchain(TEXT)
    results.append(r2)
    print(f"   ✅ {r2['time']:.2f}s")

    # 结果对比
    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)
    print(f"{'方式':<15} {'耗时':>6} {'核心代码行':>10}  摘要内容")
    print("-" * 60)
    for r in results:
        print(f"{r['method']:<15} {r['time']:>5.2f}s {r['lines']:>8}行  {r['result']}")

    print("\n" + "=" * 60)
    print("选型决策树（来自 S5-01）：")
    print("""
    你的场景需要 tool calling / Agent 编排吗？
    ├── 是 → 需要多 Agent 协作吗？
    │   ├── 是 → LangGraph + ChatOpenAI
    │   └── 否 → LangChain ReAct Agent 或 Claude SDK
    └── 否 → httpx 直调 OpenAI API
    """)

    print("对比总结：")
    print("┌──────────────┬─────────────┬──────────────┬──────────────┐")
    print("│ 维度         │ httpx 直调  │ LangChain    │ Claude SDK   │")
    print("├──────────────┼─────────────┼──────────────┼──────────────┤")
    print("│ 依赖         │ 仅 httpx    │ langchain-*  │ anthropic    │")
    print("│ 代码量       │ 最少        │ 中等         │ 中等         │")
    print("│ Tool Calling │ 需手动处理  │ 内建支持     │ 内建支持     │")
    print("│ 流式输出     │ 手动解析SSE │ 内建callback │ 内建支持     │")
    print("│ Agent 编排   │ 不支持      │ LangGraph    │ 原生         │")
    print("│ 适用场景     │ 简单问答    │ 复杂编排     │ 一次性任务   │")
    print("└──────────────┴─────────────┴──────────────┴──────────────┘")
    print()
    print("✅ 实验完成！")
    print()
    print("下一步：")
    print("  1. 在 httpx 版本中加入主备 fallback")
    print("  2. 在 LangChain 版本中加入 Tool Calling（参考实验 B）")
    print("  3. 尝试流式输出（参考实验 A 的 chat_stream）")


if __name__ == "__main__":
    asyncio.run(main())
