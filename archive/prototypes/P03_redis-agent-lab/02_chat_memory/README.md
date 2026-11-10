> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 02 · Chat Memory — 对话记忆（短期 + 长期）

> **状态**：⚡ 骨架 + README

## Why 这一章

Agent 的记忆系统通常分两层：

| 层 | 性质 | 数据结构 | TTL |
|----|------|---------|-----|
| **短期记忆** | 最近 N 轮对话 | List | 几小时 |
| **长期记忆** | 用户画像、关键事实 | Hash + Vector | 永久 |

短期保证连贯性（"你刚才说的那个..."），长期保证个性化（"我是你昨天问过 Python 的那个用户"）。

## 跑法

```powershell
python 02_chat_memory/main.py
```

## 核心代码骨架

```python
from _common.llm import chat, redis_text_client
import json, time

r = redis_text_client()

class ChatMemory:
    def __init__(self, user_id: str, max_short: int = 10):
        self.uid = user_id
        self.short_key = f"mem:short:{user_id}"      # List
        self.long_key = f"mem:long:{user_id}"        # Hash
        self.max_short = max_short

    def add_turn(self, role: str, content: str):
        # 短期：LPUSH + LTRIM 保持 max_short 条
        r.lpush(self.short_key, json.dumps({"role": role, "content": content, "ts": int(time.time())}))
        r.ltrim(self.short_key, 0, self.max_short - 1)
        r.expire(self.short_key, 3600 * 24)  # 24h TTL

    def get_recent(self, n: int = None) -> list:
        n = n or self.max_short
        raw = r.lrange(self.short_key, 0, n - 1)
        return [json.loads(x) for x in reversed(raw)]  # 旧→新

    def remember_fact(self, key: str, value: str):
        # 长期：Hash 字段
        r.hset(self.long_key, key, value)

    def recall_facts(self) -> dict:
        return r.hgetall(self.long_key)


def respond(user_id: str, user_msg: str) -> str:
    mem = ChatMemory(user_id)
    facts = mem.recall_facts()
    history = mem.get_recent()

    system = "你是私人助理。已知用户事实：" + json.dumps(facts, ensure_ascii=False)
    messages = [{"role": "system", "content": system}]
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_msg})

    answer = chat(messages)

    mem.add_turn("user", user_msg)
    mem.add_turn("assistant", answer)
    return answer


if __name__ == "__main__":
    # 演示
    uid = "demo_user_42"
    print(respond(uid, "我叫张三，是 Python 开发者"))
    print(respond(uid, "推荐一本进阶书"))  # 应该会用上"Python 开发者"信息
```

## 进阶：用 LLM 自动提炼"事实"到长期记忆

```python
def extract_facts(conversation: list) -> dict:
    """让 LLM 从对话里提炼 key-value 事实"""
    prompt = f"""从以下对话提炼用户的事实信息（姓名、职业、偏好等），输出 JSON：
{json.dumps(conversation, ensure_ascii=False)}
"""
    return json.loads(chat([{"role": "user", "content": prompt}]))
```

## 与 Mem0 的对比

| 维度 | 自实现（本 demo） | [Mem0](https://github.com/mem0ai/mem0) |
|------|-----------------|----------------------------------------|
| 复杂度 | < 50 行 | 需学习 Mem0 API |
| 长期记忆智能化 | 手动 hset | 自动提炼/更新/合并 |
| 适合场景 | 学习、简单 Agent | 生产级、多模态记忆 |

主报告 §三 已对 Mem0 详细评估，简单场景自己写更可控。

## TODO

- [ ] 实现"记忆衰减"：旧的事实降权
- [ ] 实现"记忆冲突解决"：用户说"我现在改名李四了"，旧的"张三"怎么办
- [ ] 集成 LLM 自动提炼事实

## 关联

- 主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §2.2
