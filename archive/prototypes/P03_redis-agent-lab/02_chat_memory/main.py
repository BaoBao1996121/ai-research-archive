"""
02 · Chat Memory — 对话记忆（短期 List + 长期 Hash）

不依赖 LLM 也能跑：用 fake_chat 模拟 LLM 响应。
配了 OPENAI_API_KEY 后会自动切到真 LLM。

跑法：
    python 02_chat_memory/main.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import chat as real_chat, redis_text_client


# ---------- 记忆类 ----------

class ChatMemory:
    """两层记忆系统

    短期：List 存最近 N 轮，FIFO 自动淘汰旧的
    长期：Hash 存提炼后的事实，永久保留（除非显式删除）
    """

    def __init__(self, user_id: str, max_short: int = 10, ttl_short: int = 86400):
        self.r = redis_text_client()
        self.uid = user_id
        self.short_key = f"mem:short:{user_id}"
        self.long_key = f"mem:long:{user_id}"
        self.max_short = max_short
        self.ttl_short = ttl_short

    # --- 短期 ---
    def add_turn(self, role: str, content: str) -> None:
        entry = json.dumps({"role": role, "content": content, "ts": int(time.time())}, ensure_ascii=False)
        # LPUSH 头插 + LTRIM 保留前 max_short 条
        self.r.lpush(self.short_key, entry)
        self.r.ltrim(self.short_key, 0, self.max_short - 1)
        self.r.expire(self.short_key, self.ttl_short)

    def get_recent(self, n: int | None = None) -> List[dict]:
        n = n or self.max_short
        raw = self.r.lrange(self.short_key, 0, n - 1)
        # LPUSH 是头插，所以列表是 新→旧，需 reverse 还原成 旧→新
        return [json.loads(x) for x in reversed(raw)]

    # --- 长期 ---
    def remember_fact(self, key: str, value: str) -> None:
        self.r.hset(self.long_key, key, value)

    def forget_fact(self, key: str) -> None:
        self.r.hdel(self.long_key, key)

    def recall_facts(self) -> dict:
        return self.r.hgetall(self.long_key) or {}

    # --- 维护 ---
    def clear(self) -> None:
        self.r.delete(self.short_key, self.long_key)

    def stats(self) -> dict:
        return {
            "short_len": self.r.llen(self.short_key),
            "long_facts": len(self.recall_facts()),
            "short_ttl": self.r.ttl(self.short_key),
        }


# ---------- LLM 接入（带 fallback） ----------

def fake_chat(messages: list) -> str:
    """LLM 不可用时的模拟回复，用于演示流程"""
    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
    facts_used = "（用上记忆）" if "facts" in sys_msg.lower() or "事实" in sys_msg else ""
    return f"[mock-reply{facts_used}] 收到「{last_user[:30]}」"


def maybe_chat(messages: list) -> str:
    """有 key 用真 LLM，没 key 用 mock"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("EXAMPLE_API_KEY"):
        try:
            return real_chat(messages, temperature=0.5)
        except Exception as e:
            print(f"  ⚠️ LLM 调用失败 fallback to mock: {e}")
    return fake_chat(messages)


def respond(user_id: str, user_msg: str) -> str:
    mem = ChatMemory(user_id)
    facts = mem.recall_facts()
    history = mem.get_recent()

    sys_content = "你是私人助理。"
    if facts:
        sys_content += f"已知事实：{json.dumps(facts, ensure_ascii=False)}"

    messages = [{"role": "system", "content": sys_content}]
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_msg})

    answer = maybe_chat(messages)

    mem.add_turn("user", user_msg)
    mem.add_turn("assistant", answer)
    return answer


# ---------- 主流程 ----------

def main():
    uid = "demo_user_42"
    mem = ChatMemory(uid)
    mem.clear()  # 干净起点

    print("=" * 70)
    print("场景 1：短期记忆 —— 多轮对话连贯性")
    print("=" * 70)

    turns = ["你好，我叫张三", "请记住我喜欢 Python", "我刚才说我叫什么？"]
    for q in turns:
        print(f"\n用户: {q}")
        print(f"助理: {respond(uid, q)}")

    print(f"\n短期记忆当前条数: {mem.stats()['short_len']} (max={mem.max_short})")
    print(f"短期记忆 TTL: {mem.stats()['short_ttl']}s")

    print("\n" + "=" * 70)
    print("场景 2：长期记忆 —— 关键事实持久化")
    print("=" * 70)

    print("\n手动写入 3 个长期事实...")
    mem.remember_fact("name", "张三")
    mem.remember_fact("language", "Python")
    mem.remember_fact("level", "进阶")
    print(f"  HGETALL mem:long:{uid} -> {mem.recall_facts()}")

    print("\n用户: 推荐一本进阶书（注意系统消息里会带上长期事实）")
    print(f"助理: {respond(uid, '推荐一本进阶书')}")

    print("\n" + "=" * 70)
    print("场景 3：短期淘汰 —— LTRIM 自动保留最近 N 条")
    print("=" * 70)

    print(f"\n再发 {mem.max_short} 条消息撑爆短期窗口...")
    for i in range(mem.max_short):
        mem.add_turn("user", f"flood-{i}")

    recent = mem.get_recent()
    print(f"短期记忆条数: {len(recent)} (始终 ≤ {mem.max_short})")
    print(f"最旧的条目: {recent[0]['content']}")
    print(f"最新的条目: {recent[-1]['content']}")
    print("✅ 旧消息自动被淘汰，长期记忆不受影响")

    print("\n" + "=" * 70)
    print(f"📊 最终统计: {mem.stats()}")
    print("\n💡 关键观察：")
    print("   - 短期 List 用 LPUSH+LTRIM 实现固定窗口（O(1)）")
    print("   - 长期 Hash 字段独立，可单独增删改")
    print("   - 短期带 TTL（24h），长期无 TTL（除非显式 expire）")


if __name__ == "__main__":
    main()
