"""
00 · Hello Redis — 五大数据结构速通

不依赖 LLM，只验证：
1) Redis 连接通
2) String / Hash / List / Stream / Pub-Sub 五大基础结构怎么用
3) TTL 自动过期机制

跑法：
    python 00_hello_redis/main.py

预期输出（节选）：
    [String]   key=greet, value=hello agent, ttl=10s
    [Hash]     user:1001 -> {name: Alice, role: researcher}
    [List]     queue:tasks 出队顺序: ['task1', 'task2', 'task3']
    [Stream]   events 写入了 3 条，读出 3 条
    [Pub/Sub]  订阅者收到消息: hello channel
    [TTL]      key 在 2 秒后自动消失：True
    ✅ 全部通过
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# 让脚本能从任何目录直接跑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import redis_text_client


def demo_string(r):
    print("\n[String] —— Agent 中典型用途：缓存 LLM 响应、简单计数器")
    r.set("greet", "hello agent", ex=10)  # 10 秒后自动过期
    val = r.get("greet")
    ttl = r.ttl("greet")
    print(f"  set greet=hello agent (ex=10s)")
    print(f"  get greet -> {val!r}, ttl -> {ttl}s")

    # 计数器（原子操作）
    r.delete("hits")
    for _ in range(3):
        r.incr("hits")
    print(f"  incr hits 3 次 -> {r.get('hits')}")


def demo_hash(r):
    print("\n[Hash] —— Agent 中典型用途：用户画像、Agent 状态字段")
    r.delete("user:1001")
    r.hset("user:1001", mapping={"name": "Alice", "role": "researcher", "credits": 100})
    print(f"  HGETALL user:1001 -> {r.hgetall('user:1001')}")
    r.hincrby("user:1001", "credits", -10)
    print(f"  HINCRBY credits -10 -> 现在 credits = {r.hget('user:1001', 'credits')}")


def demo_list(r):
    print("\n[List] —— Agent 中典型用途：对话历史、任务队列、消息缓冲")
    r.delete("queue:tasks")
    for t in ["task1", "task2", "task3"]:
        r.rpush("queue:tasks", t)
    print(f"  LRANGE 全部 -> {r.lrange('queue:tasks', 0, -1)}")

    print(f"  LPOP 出队顺序（FIFO）：", end=" ")
    while True:
        v = r.lpop("queue:tasks")
        if v is None:
            break
        print(v, end=" ")
    print()


def demo_stream(r):
    print("\n[Stream] —— Agent 中典型用途：事件溯源、Agent 间持久消息（vs Pub/Sub 不丢消息）")
    r.delete("events")
    for i in range(3):
        r.xadd("events", {"agent": "researcher", "action": "search", "round": i})

    msgs = r.xrange("events", min="-", max="+")
    print(f"  XADD 写入 3 条")
    print(f"  XRANGE 读出 {len(msgs)} 条:")
    for msg_id, fields in msgs:
        print(f"    {msg_id} -> {fields}")

    print(f"  💡 Stream 的 ID 是时间戳-序号，自带顺序，且消息持久化（断电不丢）")


def demo_pubsub(r):
    print("\n[Pub/Sub] —— Agent 中典型用途：实时广播（注意：订阅者不在线就丢）")

    pubsub = r.pubsub()
    pubsub.subscribe("agent:broadcast")
    # 消费第一条 subscribe 确认消息
    pubsub.get_message(timeout=1)

    r.publish("agent:broadcast", "hello channel")
    msg = pubsub.get_message(timeout=2)
    if msg and msg["type"] == "message":
        print(f"  发布: 'hello channel'")
        print(f"  订阅者收到: {msg['data']!r}")
    else:
        print(f"  ⚠️ 未收到消息，msg={msg}")

    pubsub.close()


def demo_ttl(r):
    print("\n[TTL] —— Agent 中典型用途：会话/缓存自动过期，省得手动清理")
    r.set("ephemeral", "我只活 2 秒", ex=2)
    print(f"  存入 ephemeral, ttl={r.ttl('ephemeral')}s")
    print(f"  等 2.5 秒...")
    time.sleep(2.5)
    val = r.get("ephemeral")
    print(f"  get ephemeral -> {val!r}（已自动消失）")


def main():
    r = redis_text_client()

    # 健康检查
    try:
        r.ping()
    except Exception as e:
        print(f"❌ 连不上 Redis: {e}")
        print("   请先跑 docker compose up -d")
        sys.exit(1)

    print("✅ Redis 连接成功")
    print("=" * 60)

    demo_string(r)
    demo_hash(r)
    demo_list(r)
    demo_stream(r)
    demo_pubsub(r)
    demo_ttl(r)

    print("\n" + "=" * 60)
    print("✅ 五大数据结构演示完成")
    print("\n下一步：")
    print("  - 跑 03_semantic_cache 看最有 AI 特色的语义缓存")
    print("  - 跑 06_multi_agent_pubsub 看多 Agent 通信模式")


if __name__ == "__main__":
    main()
