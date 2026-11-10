"""
06 · Multi-Agent Pub/Sub & Streams — 多 Agent 通信（含 Redis vs Kafka 取舍 🆕）

本 demo 同一份代码演示 Redis 两种 Agent 间通信原语：
  - Pub/Sub：fire-and-forget，订阅者不在线就丢
  - Streams：持久化 + 消费组，断电不丢，可重放

场景：3 个 Agent 协作
  - Producer Agent：模拟"任务生成器"，向频道/Stream 推任务
  - Worker Agent A/B：消费任务，做模拟处理

跑法：
    python 06_multi_agent_pubsub/main.py

按提示输入 1 或 2 选模式：
    1) Pub/Sub 模式（注意观察：Worker B 启动慢，会丢前几条消息）
    2) Streams 模式（同一场景，Worker B 启动慢也不丢，因为消费组从头分配）
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import redis_text_client


# ---------- 模式 1：Pub/Sub ----------

def pubsub_worker(name: str, channel: str, stop_event: threading.Event, started_after: float = 0):
    """订阅频道，处理消息。started_after 模拟"晚启动"场景"""
    if started_after > 0:
        time.sleep(started_after)
        print(f"  [{name}] 晚启动 ({started_after}s 后), 订阅 {channel}")

    r = redis_text_client()
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    pubsub.get_message(timeout=1)  # 跳过 subscribe 确认

    while not stop_event.is_set():
        msg = pubsub.get_message(timeout=0.5)
        if msg and msg["type"] == "message":
            print(f"  [{name}] 收到: {msg['data']}")
    pubsub.close()


def demo_pubsub():
    print("\n" + "=" * 70)
    print("模式 1：Pub/Sub —— fire-and-forget，晚到的订阅者会丢消息")
    print("=" * 70)

    r = redis_text_client()
    channel = "tasks:pubsub"
    stop = threading.Event()

    # Worker A 立即启动；Worker B 1.5 秒后启动（模拟它"启动慢"或"刚崩溃恢复"）
    workers = [
        threading.Thread(target=pubsub_worker, args=("WorkerA", channel, stop, 0)),
        threading.Thread(target=pubsub_worker, args=("WorkerB", channel, stop, 1.5)),
    ]
    for w in workers:
        w.start()

    time.sleep(0.3)  # 让 Worker A 完成订阅

    print("  [Producer] 开始发布 5 条任务...")
    for i in range(5):
        msg = f"task-{i:02d}"
        n = r.publish(channel, msg)  # n = 当前订阅者数
        print(f"  [Producer] 发布 {msg}（{n} 个订阅者收到）")
        time.sleep(0.5)

    time.sleep(1)
    stop.set()
    for w in workers:
        w.join(timeout=2)
    print("\n💡 观察：WorkerB 因为晚启动，丢了 task-00/01/02。Pub/Sub 不保留历史。")


# ---------- 模式 2：Streams ----------

def stream_worker(name: str, stream: str, group: str, stop_event: threading.Event, started_after: float = 0):
    """从消费组读取，处理后 ACK。已读但未 ACK 的消息可重新分配"""
    if started_after > 0:
        time.sleep(started_after)
        print(f"  [{name}] 晚启动 ({started_after}s 后), 加入消费组 {group}")

    r = redis_text_client()
    while not stop_event.is_set():
        # XREADGROUP：从消费组读取，'>' 表示只读还没分给本 consumer 的新消息
        resp = r.xreadgroup(
            groupname=group,
            consumername=name,
            streams={stream: ">"},
            count=5,
            block=500,  # 阻塞 500ms
        )
        if not resp:
            continue
        for stream_name, messages in resp:
            for msg_id, fields in messages:
                print(f"  [{name}] 收到 {msg_id}: {fields}")
                # 模拟处理
                time.sleep(0.1)
                # ACK：告诉 Redis 这条消息处理完了，从 pending 列表移除
                r.xack(stream, group, msg_id)


def demo_streams():
    print("\n" + "=" * 70)
    print("模式 2：Streams —— 持久化 + 消费组，晚到的订阅者也能拿到积压消息")
    print("=" * 70)

    r = redis_text_client()
    stream = "tasks:stream"
    group = "workers"

    # 清理上次的状态
    try:
        r.delete(stream)
    except Exception:
        pass

    # Producer 先发 5 条到 Stream（消费组还没建）
    print("  [Producer] 先发 5 条任务到 Stream（此时还没 worker）...")
    for i in range(5):
        msg_id = r.xadd(stream, {"task": f"task-{i:02d}", "ts": int(time.time())})
        print(f"  [Producer] XADD {msg_id} task-{i:02d}")

    # 创建消费组（mkstream=True 防止 stream 不存在报错；id='0' 表示从最早的消息开始消费）
    try:
        r.xgroup_create(stream, group, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" in str(e):
            r.xgroup_destroy(stream, group)
            r.xgroup_create(stream, group, id="0", mkstream=True)
        else:
            raise

    stop = threading.Event()
    workers = [
        threading.Thread(target=stream_worker, args=("WorkerA", stream, group, stop, 0)),
        threading.Thread(target=stream_worker, args=("WorkerB", stream, group, stop, 1.5)),
    ]
    for w in workers:
        w.start()

    # Producer 再发 3 条新任务
    time.sleep(0.5)
    print("\n  [Producer] 再追加 3 条新任务...")
    for i in range(5, 8):
        r.xadd(stream, {"task": f"task-{i:02d}", "ts": int(time.time())})
        time.sleep(0.4)

    time.sleep(2)
    stop.set()
    for w in workers:
        w.join(timeout=3)

    pending = r.xpending(stream, group)
    print(f"\n💡 观察：")
    print(f"   - 8 条消息全部被消费（含 worker 启动前发的 5 条）")
    print(f"   - 消费组负载均衡：A 和 B 各自分到不同消息")
    print(f"   - Pending 队列剩余: {pending['pending']} 条（已 ACK 的不计）")


# ---------- 主入口 ----------

def main():
    print("06 · Multi-Agent 通信演示")
    print()
    print("选模式：")
    print("  1) Pub/Sub  —— 实时但会丢")
    print("  2) Streams  —— 持久不丢")
    print("  3) 两个都跑（推荐对比）")
    choice = input("输入 1/2/3 [默认 3]: ").strip() or "3"

    if choice in ("1", "3"):
        demo_pubsub()
    if choice in ("2", "3"):
        demo_streams()

    print("\n" + "=" * 70)
    print("📊 选型决策（详见 README.md）：")
    print("   实时事件、不在乎丢 → Pub/Sub（Agent 'thinking...' 状态广播）")
    print("   任务队列、必须送达  → Streams（Agent 工作分发、审计日志）")
    print("   超大规模、跨机房   → Kafka/RabbitMQ（见 README 取舍表）")


if __name__ == "__main__":
    main()
