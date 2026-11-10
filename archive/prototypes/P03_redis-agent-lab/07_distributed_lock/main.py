"""
07 · Distributed Lock & Leader Election

不依赖 LLM。fakeredis 完全支持 Lua 脚本，可在内嵌环境验证。

演示：
  1) 互斥锁：5 个并发抓同一 URL，只有 1 个真抓
  2) 锁误释放防护：B 不能释放 A 持有的锁
  3) Leader Election：3 个候选者只有 1 个当选；leader 崩了 follower 自动接任

跑法：
    python 07_distributed_lock/main.py
"""
from __future__ import annotations

import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import redis_text_client

r = redis_text_client()


# ---------- 分布式锁 ----------

# 释放锁用 Lua 脚本，保证"检查 token + 删除"原子
RELEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""

# 续期 Lua 脚本（看门狗用）
RENEW_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('PEXPIRE', KEYS[1], ARGV[2])
else
    return 0
end
"""


class RedisLock:
    """SET NX PX + Lua 安全释放"""

    def __init__(self, name: str, ttl_ms: int = 30000, token: str | None = None):
        self.key = f"lock:{name}"
        self.ttl_ms = ttl_ms
        self.token = token or uuid.uuid4().hex

    def acquire(self, timeout: float = 5.0, poll_interval: float = 0.05) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if r.set(self.key, self.token, nx=True, px=self.ttl_ms):
                return True
            time.sleep(poll_interval)
        return False

    def release(self) -> bool:
        return bool(r.eval(RELEASE_LUA, 1, self.key, self.token))

    def renew(self) -> bool:
        return bool(r.eval(RENEW_LUA, 1, self.key, self.token, self.ttl_ms))

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"无法获取锁: {self.key}")
        return self

    def __exit__(self, *args):
        self.release()


# ---------- 场景 1：互斥锁 ----------

def demo_mutex():
    print("=" * 70)
    print("场景 1：互斥锁 —— 5 个并发抓同一 URL，只有 1 个真抓")
    print("=" * 70)

    crawl_count = {"value": 0}
    lock_lock = threading.Lock()

    def crawler(name: str, url: str):
        lock = RedisLock(f"crawl:{url}", ttl_ms=5000)
        if lock.acquire(timeout=0.1):
            try:
                with lock_lock:
                    crawl_count["value"] += 1
                print(f"  [{name}] 🚀 抢到锁，开始抓 {url}")
                time.sleep(0.5)  # 模拟抓取
                print(f"  [{name}] ✅ 完成")
            finally:
                lock.release()
        else:
            print(f"  [{name}] 🚫 锁被占，跳过")

    threads = [threading.Thread(target=crawler, args=(f"W{i}", "https://example.com")) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"\n  📊 真正抓取的次数: {crawl_count['value']} (应该 = 1)")


# ---------- 场景 2：误释放防护 ----------

def demo_safe_release():
    print("\n" + "=" * 70)
    print("场景 2：误释放防护 —— B 不能释放 A 的锁")
    print("=" * 70)

    lock_a = RedisLock("shared_resource", ttl_ms=10000, token="alice")
    lock_b = RedisLock("shared_resource", ttl_ms=10000, token="bob")

    assert lock_a.acquire(), "Alice 应该拿到锁"
    print("  Alice 拿到锁")

    # Bob 用同样的 key 但不同 token 尝试释放
    bob_release_ok = lock_b.release()
    print(f"  Bob 尝试释放 Alice 的锁 -> 成功? {bob_release_ok}")
    assert not bob_release_ok, "Bob 不应能释放 Alice 的锁"

    # Alice 释放自己的锁
    alice_release_ok = lock_a.release()
    print(f"  Alice 释放自己的锁 -> 成功? {alice_release_ok}")
    assert alice_release_ok

    print("  ✅ Lua 脚本保证了 token 检查+删除 的原子性")


# ---------- 场景 3：Leader Election ----------

class LeaderElection:
    def __init__(self, name: str, instance_id: str, ttl_ms: int = 1500):
        self.lock = RedisLock(f"leader:{name}", ttl_ms=ttl_ms, token=instance_id)
        self.instance_id = instance_id
        self.is_leader = False
        self._stop = threading.Event()
        self.events: list[tuple[float, str, str]] = []  # (ts, instance, event)

    def _log(self, event: str):
        self.events.append((time.time(), self.instance_id, event))

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        renew_interval = self.lock.ttl_ms / 1000 / 3  # 1/3 TTL 续期一次
        while not self._stop.is_set():
            if not self.is_leader:
                if self.lock.acquire(timeout=0.1, poll_interval=0.05):
                    self.is_leader = True
                    self._log("BECAME_LEADER")
            else:
                if not self.lock.renew():
                    # 失去 leader 身份（被强制删除或锁过期）
                    self.is_leader = False
                    self._log("LOST_LEADER")
            time.sleep(renew_interval)

    def stop(self):
        self._stop.set()
        if self.is_leader:
            self.lock.release()


def demo_leader_election():
    print("\n" + "=" * 70)
    print("场景 3：Leader Election —— 3 个候选者，崩 1 个 follower 接任")
    print("=" * 70)

    # 清干净
    r.delete("lock:leader:scheduler")

    elections = [LeaderElection("scheduler", f"node-{i}", ttl_ms=1500) for i in range(3)]
    for e in elections:
        e.start()

    time.sleep(0.5)
    leaders_round1 = [e.instance_id for e in elections if e.is_leader]
    print(f"  T+0.5s 当前 leader: {leaders_round1} (应只有 1 个)")
    assert len(leaders_round1) == 1, f"应该只有 1 个 leader，实际 {leaders_round1}"

    # 模拟当前 leader 崩溃：强行 stop
    current_leader = next(e for e in elections if e.is_leader)
    print(f"  💀 模拟 {current_leader.instance_id} 崩溃")
    current_leader.stop()
    # 不主动释放锁，等 TTL 自然过期，模拟真崩溃

    # 等 TTL 过期 + 其他人抢锁
    time.sleep(2.5)
    new_leaders = [e.instance_id for e in elections if e.is_leader and e.instance_id != current_leader.instance_id]
    print(f"  T+3.0s 新 leader: {new_leaders} (follower 应已接任)")

    for e in elections:
        e.stop()

    print("\n  📊 事件时序:")
    all_events = sorted([ev for e in elections for ev in e.events], key=lambda x: x[0])
    t0 = all_events[0][0]
    for ts, who, what in all_events:
        print(f"    T+{ts-t0:.2f}s  [{who}]  {what}")


def main():
    demo_mutex()
    demo_safe_release()
    demo_leader_election()

    print("\n" + "=" * 70)
    print("✅ 分布式锁与 Leader Election 全部演示完成")
    print("\n💡 关键收获：")
    print("   - SET NX PX 一步原子设置，防死锁")
    print("   - token + Lua 释放，防误删")
    print("   - Leader Election 本质是带续期的分布式锁")
    print("   - 强一致需求请用 etcd/ZooKeeper，不是 Redis（详见 README Redlock 争议）")


if __name__ == "__main__":
    main()
