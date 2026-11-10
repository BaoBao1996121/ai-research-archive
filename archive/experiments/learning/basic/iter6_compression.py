"""
Iter 6: 对话压缩 — 无限对话的秘密（~220 行核心代码）
====================================================
目标：当对话历史超过 LLM 上下文窗口时，自动压缩旧消息保留核心信息。
新增：ConversationManager + 自动摘要压缩 + 滑动窗口策略
学到：Token 预算管理、对话摘要策略、信息密度优化。

Claude Code 对照：
  - services/compact/: 四级压缩策略（snip → micro → auto → reactive）
  - compactMessages(): 将旧消息摘要为一段话，保留关键信息
  - 使用 qwen-turbo（便宜快速模型）做压缩，主模型做推理——成本优化技巧

运行：
  pip install openai
  export DASHSCOPE_API_KEY="你的密钥"
  python iter6_compression.py
"""

import os
import json
from config import client, MODEL

CHEAP_MODEL = "qwen-turbo"  # 用便宜模型做压缩


# ━━━ Token 估算 ━━━
def estimate_tokens(text: str) -> int:
    cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return int(cn * 1.5 + (len(text) - cn) * 0.4)


# ━━━ 对话管理器（核心新增） ━━━
class ConversationManager:
    """
    管理对话历史，在接近 token 上限时自动压缩旧消息。

    策略：
    - 始终保留：system prompt + 最近 N 条消息
    - 超出预算时：将中间的旧消息用 LLM 摘要为一段话
    - 摘要注入为一条 system 消息，紧跟在原始 system prompt 后面

    Claude Code 用了更复杂的四级策略（从轻量到重度），
    但核心思路一样："用少量 token 保留尽可能多的信息"。
    """
    def __init__(self, system_prompt: str, max_tokens: int = 4000, keep_recent: int = 6):
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
        self.messages = [{"role": "system", "content": system_prompt}]
        self.summary = ""
        self.compress_count = 0

    def add(self, message: dict):
        self.messages.append(message)

    def get_messages(self) -> list[dict]:
        """返回当前消息列表，必要时先压缩"""
        if self._estimate_total() > self.max_tokens:
            self._compress()
        return self.messages

    def _estimate_total(self) -> int:
        total = 0
        for m in self.messages:
            if isinstance(m, dict):
                content = m.get("content") or ""
            else:
                content = getattr(m, "content", "") or ""
            if isinstance(content, str):
                total += estimate_tokens(content)
            total += 4
        return total

    def _compress(self):
        """将旧消息压缩为摘要"""
        # 保留: system(第1条) + 最近 N 条
        if len(self.messages) <= self.keep_recent + 2:
            return  # 太少了不值得压缩

        before_tokens = self._estimate_total()
        print(f"\n  🗜️ 压缩前: {len(self.messages)} 条消息, ~{before_tokens} tokens")

        system = self.messages[0]
        old_messages = self.messages[1:-self.keep_recent]
        recent = self.messages[-self.keep_recent:]

        if not old_messages:
            return

        # 用便宜模型生成摘要
        old_text = "\n".join(
            f"[{m.get('role', '?') if isinstance(m, dict) else getattr(m, 'role', '?')}]: "
            f"{(m.get('content') or '' if isinstance(m, dict) else getattr(m, 'content', '') or '')[:200]}"
            for m in old_messages
        )
        print(f"\n  🗜️ 压缩 {len(old_messages)} 条旧消息...")

        try:
            summary_resp = client.chat.completions.create(
                model=CHEAP_MODEL,
                messages=[{"role": "user", "content":
                    f"请将以下对话历史摘要为 3-5 个要点，保留关键信息（数字、决策、结论）：\n\n{old_text}"}],
                max_tokens=500,
            )
            new_summary = summary_resp.choices[0].message.content

            # 合并历史摘要
            if self.summary:
                self.summary = f"[更早的摘要] {self.summary}\n[近期摘要] {new_summary}"
            else:
                self.summary = new_summary

            # 重建消息列表
            self.messages = [system]
            if self.summary:
                self.messages.append({
                    "role": "system",
                    "content": f"[对话历史摘要]\n{self.summary}",
                })
            self.messages.extend(recent)

            self.compress_count += 1
            new_tokens = self._estimate_total()
            print(f"  🗜️ 压缩完成（第 {self.compress_count} 次），当前 ~{new_tokens} tokens")

        except Exception as e:
            print(f"  ⚠️ 压缩失败: {e}")


# ━━━ 工具 ━━━
TOOLS = [
    {"type": "function", "function": {
        "name": "calculator", "description": "计算数学表达式",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        }, "required": ["expression"]}}},
]

def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})

TOOL_MAP = {"calculator": calculator}


# ━━━ Agent 循环（带自动压缩） ━━━
def agent_with_compression(max_tokens: int = 3000, keep_recent: int = 4):
    """交互式对话，自动压缩长对话历史"""
    conv = ConversationManager(
        system_prompt="你是一个AI助手，可以做数学计算。请记住对话中提到的关键信息。",
        max_tokens=max_tokens,
        keep_recent=keep_recent,
    )
    print(f"💬 对话模式（token 预算: {max_tokens}，保留最近 {keep_recent} 条）")
    print(f"   输入 quit 退出，输入 status 查看状态\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if user_input.lower() == "status":
            print(f"  📊 消息数: {len(conv.messages)}, ~{conv._estimate_total()} tokens, 压缩次数: {conv.compress_count}")
            if conv.summary:
                print(f"  📝 当前摘要: {conv.summary[:200]}...")
            continue

        conv.add({"role": "user", "content": user_input})

        for _ in range(5):  # max tool rounds
            messages = conv.get_messages()
            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS,
            )
            msg = response.choices[0].message
            conv.add(msg)

            if not msg.tool_calls:
                print(f"\nAI: {msg.content}\n")
                break

            for tc in msg.tool_calls:
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                print(f"  🔧 calculator({fn_args})")
                result = TOOL_MAP[tc.function.name](**fn_args)
                conv.add({"role": "tool", "tool_call_id": tc.id, "content": result})


# ━━━ 自动化测试：模拟长对话触发压缩 ━━━
def auto_test():
    """自动发送多条消息，观察压缩行为"""
    conv = ConversationManager(
        system_prompt="你是一个数学助手。",
        max_tokens=2000,  # 故意设低，易触发压缩
        keep_recent=4,
    )
    questions = [
        "你好，我叫小明，是一个数据工程师",
        "帮我算 123 * 456",
        "我在做一个数据管线项目，用 Python + Airflow",
        "帮我算 2 的 20 次方",
        "我的项目预算是每月 1000 元",
        "帮我算如果每次调用 0.01 元，一天 3000 次，一个月多少钱",
        "根据前面的信息，我的预算够吗？",  # 这条测试压缩后是否还记得关键信息
    ]

    for i, q in enumerate(questions):
        print(f"\n{'='*50}")
        print(f"第 {i+1}/{len(questions)} 轮: {q}")
        conv.add({"role": "user", "content": q})

        # 最多跑 3 轮工具调用（和交互模式一样的完整流程）
        for _ in range(3):
            messages = conv.get_messages()
            print(f"  📊 消息数: {len(conv.messages)}, ~{conv._estimate_total()} tokens")

            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS,
            )
            msg = response.choices[0].message
            conv.add(msg)

            if not msg.tool_calls:
                # 没有工具调用，打印最终回复，进入下一轮用户提问
                if msg.content:
                    print(f"  🤖 {msg.content[:200]}")
                break

            # 有工具调用：执行工具，把结果加回对话
            for tc in msg.tool_calls:
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                print(f"  🔧 {tc.function.name}({fn_args})")
                result = TOOL_MAP[tc.function.name](**fn_args)
                conv.add({"role": "tool", "tool_call_id": tc.id, "content": result})

    print(f"\n{'='*50}")
    print(f"总结: 共 {len(questions)} 轮对话, 压缩 {conv.compress_count} 次")
    if conv.summary:
        print(f"当前摘要:\n{conv.summary}")


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 6: 对话压缩 — 无限对话")
    print("=" * 60)

    print("\n📝 自动化测试: 模拟长对话")
    auto_test()

    print("\n" + "=" * 60)
    print("📝 交互模式:")
    agent_with_compression(max_tokens=1000, keep_recent=4)
