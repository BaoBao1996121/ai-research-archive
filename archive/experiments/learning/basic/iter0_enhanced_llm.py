"""
Iter 0: 增强型 LLM — 单次调用（~50 行核心代码）
================================================
目标：用 Qwen API 完成 LLM 调用，理解"增强型 LLM"的含义。
学到：API 调用基础、System Prompt 的作用、消息格式、多轮对话。

Claude Code 对照：
  - query.ts 中的 querySingleTurn() — 单次 LLM 调用的最简形式
  - System Prompt 是 Agent 的"性格说明书"

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter0_enhanced_llm.py
"""

import os
from config import client, MODEL

# ━━━ System Prompt：Agent 的"性格说明书" ━━━
SYSTEM_PROMPT = """你是一个专业的技术分析助手。你的回答风格：
1. 先给出一句话结论
2. 然后用 3-5 个要点展开
3. 最后给出一个实际可操作的建议
请用中文回答。"""


def chat(user_message: str, system_prompt: str = SYSTEM_PROMPT, n: int = 1) -> str:
    """最基础的 LLM 调用：System Prompt + 用户消息 → 回复
    n>1 时会调用多次 API，返回多个候选回答（Qwen 不支持单次 n>1）"""
    results = []
    for i in range(n):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        if n == 1:
            return response.choices[0].message.content
        results.append(f"--- 候选 {i+1} ---\n{response.choices[0].message.content}")
    return "\n\n".join(results)


def multi_turn_chat():
    """多轮对话：手动维护消息历史"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("💬 多轮对话模式（输入 quit 退出）\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break

        messages.append({"role": "user", "content": user_input})
        response = client.chat.completions.create(model=MODEL, messages=messages)
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"\nAI: {reply}\n")


if __name__ == "__main__":
    # 示例 1：单次调用
    print("=" * 60)
    print("示例 1: 单次 LLM 调用")
    print("=" * 60)
    answer = chat("什么是 AI Agent？它和普通的 LLM 调用有什么区别？", n=5)
    print(answer)

    # # 示例 2：多轮对话
    # print("\n" + "=" * 60)
    # print("示例 2: 多轮对话")
    # print("=" * 60)
    # multi_turn_chat()
