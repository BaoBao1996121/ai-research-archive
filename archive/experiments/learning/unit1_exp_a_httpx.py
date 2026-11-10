"""
实验 A: httpx 直调 OpenAI 兼容 API
公开编辑说明：已删除内部代码位置引用；本文件仅作为 API 调用教学示例，本次未运行。

学习目标:
  1. 理解 OpenAI 兼容 API 的请求/响应 JSON 结构
  2. 掌握 httpx.AsyncClient 的异步用法
  3. 体会"最轻量、无框架依赖"的 LLM 调用方式

运行方式:
  1. 复制 .env.example 为 .env，填入真实 API Key
  2. python unit1_exp_a_httpx.py
"""

import httpx
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv(Path(__file__).parent / ".env")

API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "")


async def chat(prompt: str, model: str = "gpt-4o-mini") -> str:
    """最简 LLM 调用：httpx 直接 POST /chat/completions"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        # === 学习点：打印完整响应结构 ===
        print("=== 完整响应结构 ===")
        print(f"id:      {data['id']}")
        print(f"model:   {data['model']}")
        print(f"usage:   {data['usage']}")
        print(f"choices: {len(data['choices'])} 条")
        print()

        return data["choices"][0]["message"]["content"]


async def chat_stream(prompt: str, model: str = "gpt-4o-mini"):
    """流式调用：逐 token 输出（SSE）"""
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "stream": True,  # 关键差异
            },
        ) as resp:
            resp.raise_for_status()
            print("=== 流式输出（逐 chunk）===")
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        print(content, end="", flush=True)
            print("\n")


async def main():
    if not API_KEY or API_KEY == "YOUR_KEY_HERE":
        print("❌ 请先在 .env 中填入 OPENAI_API_KEY")
        return

    print("=" * 50)
    print("实验 A: httpx 直调 OpenAI 兼容 API")
    print("=" * 50)

    # 测试 1: 非流式调用
    print("\n--- 非流式调用 ---")
    result = await chat("用一句话解释什么是 RAG（检索增强生成）")
    print(f"回答: {result}")

    # 测试 2: 流式调用
    print("\n--- 流式调用 ---")
    await chat_stream("用三句话解释 FastAPI 的核心优势")

    print("=" * 50)
    print("✅ 实验完成！")
    print()
    print("思考题：")
    print("1. 非流式 vs 流式，请求 JSON 有什么区别？")
    print("2. 流式响应的格式是什么？（提示：SSE）")
    print("3. 如果 API 返回错误，httpx 会怎么处理？")


if __name__ == "__main__":
    asyncio.run(main())
