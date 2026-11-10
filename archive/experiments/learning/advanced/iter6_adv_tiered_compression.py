"""
Iter 6 进阶: 四级分层压缩 — Claude Code 的压缩策略（~280 行核心代码）
=====================================================================
基础版差距：只有一种压缩策略（全量摘要），粒度太粗。
进阶补全：四级压缩策略（snip → micro → auto → reactive），像 Claude Code 一样。

Claude Code 对照（services/compact/）：
  Level 1 - Snip:     截断过长的单条消息（工具输出超过阈值就截断）
  Level 2 - Micro:    用廉价模型对单条消息做微摘要
  Level 3 - Auto:     自动全量压缩（合并多条旧消息为一段摘要）
  Level 4 - Reactive: Token 即将耗尽时的紧急压缩（激进丢弃）

核心思想：压缩是有代价的（信息损失），所以从轻到重逐级升级。
能截断就不摘要，能微摘要就不全量压缩，尽量保留信息。

依赖：pip install openai
运行：python iter6_adv_tiered_compression.py
"""

import json
import time
from config import client, MODEL

CHEAP_MODEL = "qwen-turbo"


# ━━━ Token 估算 ━━━
def estimate_tokens(text: str) -> int:
    cn = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return int(cn * 1.5 + (len(text) - cn) * 0.4)


def msg_content(m) -> str:
    if isinstance(m, dict):
        return m.get("content") or ""
    return getattr(m, "content", "") or ""


def msg_tokens(m) -> int:
    return estimate_tokens(msg_content(m)) + 4


# ╔══════════════════════════════════════════════════════════════╗
# ║  Level 1: Snip — 截断过长的单条消息                           ║
# ╚══════════════════════════════════════════════════════════════╝

def snip_message(content: str, max_chars: int = 2000) -> tuple[str, bool]:
    """
    如果单条消息太长（常见于工具输出），直接截断尾部。

    Claude Code 的做法：
    - 工具输出超过阈值 → 保留开头 + 结尾，中间用 [SNIPPED] 替代
    - 代码文件 → 保留前 N 行 + 后 M 行
    """
    if len(content) <= max_chars:
        return content, False

    # 保留开头 70% + 结尾 20%（模拟 Claude Code 的 head+tail 策略）
    head_size = int(max_chars * 0.7)
    tail_size = int(max_chars * 0.2)
    snipped = (content[:head_size]
               + f"\n\n[... 已截断 {len(content) - head_size - tail_size} 字符 ...]\n\n"
               + content[-tail_size:])
    return snipped, True


# ╔══════════════════════════════════════════════════════════════╗
# ║  Level 2: Micro — 对单条消息做微摘要                          ║
# ╚══════════════════════════════════════════════════════════════╝

def micro_summarize(content: str, max_tokens: int = 100) -> str:
    """
    用廉价模型对单条消息生成微摘要（1-3 句话）。

    比 snip 更智能（保留语义），但比全量压缩更便宜（只处理一条消息）。
    适用于：工具返回了大段结果，但后续对话只需要其中的关键数字/结论。
    """
    try:
        resp = client.chat.completions.create(
            model=CHEAP_MODEL,
            messages=[{"role": "user", "content":
                f"用 1-3 句话摘要以下内容，保留关键数字和结论：\n\n{content[:3000]}"}],
            max_tokens=max_tokens,
        )
        return f"[微摘要] {resp.choices[0].message.content}"
    except Exception:
        # 摘要失败，降级为 snip
        snipped, _ = snip_message(content, 500)
        return snipped


# ╔══════════════════════════════════════════════════════════════╗
# ║  Level 3: Auto — 自动全量压缩（多条消息合并摘要）              ║
# ╚══════════════════════════════════════════════════════════════╝

def auto_compress(messages: list[dict], keep_system: bool = True) -> str:
    """
    将多条旧消息压缩为一段综合摘要。

    这是基础版就有的策略，但在四级体系中它排第三——
    只有当 snip 和 micro 都不够时才动用全量压缩。
    """
    parts = []
    for m in messages:
        role = m.get("role", "?") if isinstance(m, dict) else getattr(m, "role", "?")
        content = msg_content(m)[:300]
        if content:
            parts.append(f"[{role}]: {content}")

    text = "\n".join(parts)
    try:
        resp = client.chat.completions.create(
            model=CHEAP_MODEL,
            messages=[{"role": "user", "content":
                f"请将以下对话历史压缩为 3-5 个要点，保留关键信息（数字、决策、结论）：\n\n{text}"}],
            max_tokens=300,
        )
        return resp.choices[0].message.content
    except Exception:
        # 压缩失败，硬截断
        return f"[压缩失败-硬截断] {text[:500]}"


# ╔══════════════════════════════════════════════════════════════╗
# ║  Level 4: Reactive — 紧急压缩（激进丢弃）                     ║
# ╚══════════════════════════════════════════════════════════════╝

def reactive_compress(messages: list[dict], target_tokens: int) -> list[dict]:
    """
    Token 即将耗尽时的紧急压缩——激进丢弃低优先级消息。

    优先级规则（从高到低）：
    1. System prompt（永远保留）
    2. 最近 2 条用户消息 + 对应的 assistant 回复
    3. 工具调用结果（只保留最新的）
    4. 旧的对话轮次（全部丢弃，用一句话概括）
    """
    if not messages:
        return messages

    system = [m for m in messages if (m.get("role") if isinstance(m, dict) else getattr(m, "role", "")) == "system"]
    non_system = [m for m in messages if (m.get("role") if isinstance(m, dict) else getattr(m, "role", "")) != "system"]

    # 保留最近 4 条
    if len(non_system) <= 4:
        return messages

    recent = non_system[-4:]
    old = non_system[:-4]

    # 旧消息用一句话概括
    old_summary = "[紧急压缩] 之前讨论了: " + ", ".join(
        msg_content(m)[:30] for m in old if msg_content(m)
    )[:200]

    result = system + [{"role": "system", "content": old_summary}] + recent

    total = sum(msg_tokens(m) for m in result)
    print(f"  🚨 紧急压缩: {len(messages)} → {len(result)} 条, ~{total} tokens")
    return result


# ╔══════════════════════════════════════════════════════════════╗
# ║  四级压缩管理器                                               ║
# ╚══════════════════════════════════════════════════════════════╝

class TieredCompressor:
    """
    四级压缩管理器：根据 token 使用情况，逐级升级压缩策略。

    阈值设计（假设 token 预算 = 4000）：
    - < 60% (2400): 不压缩
    - 60-75% (2400-3000): Level 1 Snip（截断长消息）
    - 75-90% (3000-3600): Level 2 Micro + Level 3 Auto
    - > 90% (3600+): Level 4 Reactive（紧急压缩）
    """
    def __init__(self, token_budget: int = 4000, keep_recent: int = 4):
        self.budget = token_budget
        self.keep_recent = keep_recent
        self.stats = {"snip": 0, "micro": 0, "auto": 0, "reactive": 0}

    def process(self, messages: list[dict]) -> list[dict]:
        """评估当前 token 用量，决定是否压缩以及使用哪一级"""
        total = sum(msg_tokens(m) for m in messages)
        ratio = total / self.budget

        if ratio < 0.6:
            return messages  # 不需要压缩

        print(f"\n  📊 Token 用量: {total}/{self.budget} ({ratio:.0%})")

        # Level 1: Snip — 截断过长的单条消息
        if ratio < 0.75:
            print("  🗜️ Level 1: Snip（截断长消息）")
            return self._apply_snip(messages)

        # Level 2+3: Micro + Auto
        if ratio < 0.90:
            print("  🗜️ Level 2+3: Micro + Auto（微摘要 + 全量压缩）")
            messages = self._apply_snip(messages)
            messages = self._apply_micro(messages)
            return self._apply_auto(messages)

        # Level 4: Reactive — 紧急压缩
        print("  🚨 Level 4: Reactive（紧急压缩）")
        return reactive_compress(messages, self.budget)

    def _apply_snip(self, messages: list[dict]) -> list[dict]:
        """对所有超长消息应用 snip"""
        result = []
        for m in messages:
            content = msg_content(m)
            snipped, was_snipped = snip_message(content, max_chars=1500)
            if was_snipped:
                self.stats["snip"] += 1
                if isinstance(m, dict):
                    m = {**m, "content": snipped}
                # 如果是 API 返回的对象，我们包装为 dict
            result.append(m)
        return result

    def _apply_micro(self, messages: list[dict]) -> list[dict]:
        """对工具返回的长结果应用微摘要"""
        result = []
        for m in messages:
            role = m.get("role", "") if isinstance(m, dict) else getattr(m, "role", "")
            content = msg_content(m)
            if role == "tool" and len(content) > 800:
                self.stats["micro"] += 1
                new_content = micro_summarize(content)
                m = {**m, "content": new_content} if isinstance(m, dict) else m
            result.append(m)
        return result

    def _apply_auto(self, messages: list[dict]) -> list[dict]:
        """对旧消息应用全量压缩"""
        if len(messages) <= self.keep_recent + 2:
            return messages

        system = messages[0]
        old = messages[1:-self.keep_recent]
        recent = messages[-self.keep_recent:]

        if not old:
            return messages

        self.stats["auto"] += 1
        summary = auto_compress(old)
        return [system, {"role": "system", "content": f"[对话历史摘要]\n{summary}"}] + recent

    def print_stats(self):
        print(f"\n  📊 压缩统计: snip={self.stats['snip']} micro={self.stats['micro']} "
              f"auto={self.stats['auto']} reactive={self.stats['reactive']}")


# ╔══════════════════════════════════════════════════════════════╗
# ║  Agent 循环（四级压缩版）                                     ║
# ╚══════════════════════════════════════════════════════════════╝

TOOLS = [{"type": "function", "function": {
    "name": "calculator", "description": "计算数学表达式",
    "parameters": {"type": "object", "properties": {
        "expression": {"type": "string", "description": "数学表达式"}
    }, "required": ["expression"]}}}]

def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return json.dumps({"error": "不允许的字符"})
    return json.dumps({"result": eval(expression)})

TOOL_MAP = {"calculator": calculator}


def auto_test():
    """自动化测试：发送大量消息触发各级压缩"""
    compressor = TieredCompressor(token_budget=2000, keep_recent=4)

    messages = [{"role": "system", "content": "你是一个数学助手，帮用户计算和记住信息。"}]

    questions = [
        "你好，我叫小明",
        "帮我算 123 * 456",
        "我正在做一个电商项目，技术栈是 Python + FastAPI + PostgreSQL",
        "帮我算 2 的 20 次方",
        "我的项目预算是每月 5000 元，团队 3 人",
        "帮我算如果每次 API 调用 0.01 元，一天 5000 次，一个月多少钱",
        "再算一下人力成本：3 人 × 每月 2 万 = 多少",
        "综合前面的信息，帮我做一个月度成本汇总",
    ]

    for i, q in enumerate(questions):
        print(f"\n{'='*50}")
        print(f"  第 {i+1}/{len(questions)} 轮: {q}")

        messages.append({"role": "user", "content": q})

        # 压缩（如果需要）
        messages = compressor.process(messages)

        total = sum(msg_tokens(m) for m in messages)
        print(f"  📊 当前: {len(messages)} 条消息, ~{total} tokens")

        # 调用 LLM
        for _ in range(3):
            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS,
            )
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                content = msg.content or ""
                print(f"  🤖 {content[:150]}")
                break

            for tc in msg.tool_calls:
                fn_args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                print(f"  🔧 calculator({fn_args})")
                result = TOOL_MAP[tc.function.name](**fn_args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    compressor.print_stats()

    print(f"\n{'='*50}")
    print("最终消息列表:")
    for i, m in enumerate(messages):
        role = m.get("role", "?") if isinstance(m, dict) else getattr(m, "role", "?")
        content = msg_content(m)[:60]
        print(f"  [{i}] {role}: {content}...")


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 6 进阶: 四级分层压缩")
    print("=" * 60)

    auto_test()

    print(f"\n{'='*60}")
    print("📚 四级压缩策略总结:")
    print("  Level 1 Snip     — 截断长消息（最轻，信息损失最小）")
    print("  Level 2 Micro    — 单条微摘要（保留语义，成本低）")
    print("  Level 3 Auto     — 全量压缩（多条合并，成本中等）")
    print("  Level 4 Reactive — 紧急压缩（激进丢弃，最后手段）")
    print()
    print("  Claude Code 的压缩触发逻辑:")
    print("  - snip: 工具输出超过 50K 字符")
    print("  - auto: 对话超过上下文窗口 75%")
    print("  - reactive: 剩余 token < 10%，紧急丢弃")
    print("  - 压缩用 CHEAP_MODEL，节省成本")
