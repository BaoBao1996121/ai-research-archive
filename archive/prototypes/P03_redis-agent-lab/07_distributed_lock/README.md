> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 07 · Distributed Lock & Leader Election — 分布式锁与主选举 🆕

> **新增量章节**。主报告未覆盖的工业级模式。多 Agent 系统在生产环境必备。

## Why 这一章

多 Agent 系统中两个关键问题：

1. **互斥（Distributed Lock）**：同一份数据只能让一个 Agent 写
   - 例：5 个爬虫 Agent 都想抓同一个网页 → 浪费
   - 例：2 个清理 Agent 都想清同一份过期数据 → 数据库 race condition
2. **主选举（Leader Election）**：N 个相同的 Agent 实例，要选一个当"主"
   - 例：3 个 Scheduler Agent 实例，只能 1 个真正派任务（其他做 hot standby）

Redis 提供两种成熟方案：
- **简单分布式锁**：`SET NX PX`（适合单 Redis 节点）
- **Redlock**：跨多 Redis 节点的强一致锁（适合 Redis Cluster/Sentinel）

## 跑法

```powershell
python 07_distributed_lock/main.py
```

## 核心代码骨架：简单锁

```python
import time, uuid
from _common.llm import redis_text_client

r = redis_text_client()


class RedisLock:
    """最小可用分布式锁

    核心：SET key value NX PX 30000
      NX = Not eXists（只在不存在时设置，原子）
      PX = expire in milliseconds（防死锁，持锁者崩了自动释放）
    """

    def __init__(self, name: str, ttl_ms: int = 30000):
        self.key = f"lock:{name}"
        self.ttl_ms = ttl_ms
        self.token = str(uuid.uuid4())  # 防止误释放别人的锁

    def acquire(self, timeout: float = 5.0) -> bool:
        """阻塞获取锁，超时返回 False"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if r.set(self.key, self.token, nx=True, px=self.ttl_ms):
                return True
            time.sleep(0.05)
        return False

    def release(self) -> bool:
        """释放锁。用 Lua 脚本保证'检查 token + 删除'的原子性"""
        lua = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end
        """
        return bool(r.eval(lua, 1, self.key, self.token))

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"无法获取锁: {self.key}")
        return self

    def __exit__(self, *args):
        self.release()


# 使用
def crawl_page(url: str):
    with RedisLock(f"crawl:{url}", ttl_ms=10000):
        print(f"  开始抓取 {url}")
        time.sleep(2)
        print(f"  完成抓取 {url}")
```

## 核心代码骨架：Leader Election

```python
import threading

class LeaderElection:
    """基于 Redis 的简易主选举

    思路：所有候选者周期性 SET NX 同一个 key，
         拿到的是 leader，没拿到的是 follower。
         leader 周期性续期；崩了 TTL 一过自然让位。
    """

    def __init__(self, name: str, instance_id: str, ttl_ms: int = 5000):
        self.lock = RedisLock(f"leader:{name}", ttl_ms=ttl_ms)
        self.lock.token = instance_id  # 固定 ID 方便观察
        self.is_leader = False
        self._stop = threading.Event()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while not self._stop.is_set():
            if not self.is_leader:
                if self.lock.acquire(timeout=0.5):
                    self.is_leader = True
                    print(f"[{self.lock.token}] 我是 LEADER")
            else:
                # 续期
                ok = r.pexpire(self.lock.key, self.lock.ttl_ms)
                if not ok:
                    self.is_leader = False
                    print(f"[{self.lock.token}] 失去 leader 身份")
            time.sleep(self.lock.ttl_ms / 3000)  # 1/3 TTL 续期一次

    def stop(self):
        self._stop.set()
        if self.is_leader:
            self.lock.release()
```

## Redlock：跨多节点的强一致锁

简单锁的弱点：单 Redis 节点挂了 = 所有锁丢失。

Redlock 算法（antirez 提出）：
1. 客户端去 N 个独立 Redis 实例上挨个 `SET NX PX`
2. 在大多数（≥ N/2 + 1）节点拿到锁，且总耗时 < TTL → 视为持锁成功
3. 任何节点失败也要去其他节点 `DEL` 释放

```python
from redis.lock import Lock as RedisLockImpl  # redis-py 自带的简单 lock
# Redlock 用 redlock-py 库:
# pip install redlock-py
from redlock import Redlock

dlm = Redlock([
    {"host": "redis-node-1", "port": 6379},
    {"host": "redis-node-2", "port": 6379},
    {"host": "redis-node-3", "port": 6379},
])

my_lock = dlm.lock("resource_name", 1000)  # ttl 1 秒
if my_lock:
    # do work
    dlm.unlock(my_lock)
```

⚠️ **争议**：Martin Kleppmann 在 [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) 中质疑 Redlock 的安全性（GC pause 场景下可能两个 client 同时持锁）。生产强一致需求请用 etcd / ZooKeeper。

## 关键避坑

| 坑 | 解法 |
|----|------|
| 没设 TTL → 持锁者崩了，锁永久死锁 | 必须 `PX` 设 TTL |
| 用 `SETNX` + `EXPIRE` 两步设置 | 不原子，崩在中间锁就漏 TTL。用 `SET key val NX PX ttl` 一步搞定 |
| 释放时直接 `DEL`，可能误删别人的锁 | 释放前先 `GET` 检查 token，用 Lua 保证原子 |
| 锁续期不及时，业务超过 TTL 还没结束 | "看门狗"机制，业务跑过半就续期 |

## Agent 场景下的具体应用

| 场景 | 用什么 |
|------|-------|
| 防止重复爬取同一 URL | 简单分布式锁，TTL 30 秒 |
| 多个 Scheduler Agent 选主 | Leader Election，TTL 5 秒 + 心跳续期 |
| 限制某个 LLM 工具的并发数 | 信号量（Semaphore），用 Sorted Set 实现 |
| 跨数据中心的关键资源协调 | etcd / ZooKeeper，不是 Redis |

## TODO

- [ ] 实现完整的 RedisLock + LeaderElection demo（多线程模拟多实例）
- [ ] 实现 Sorted Set 信号量（限并发数 N）
- [ ] 加入"看门狗"自动续期演示

## 关联

- 主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)（本章是新增量，主报告未覆盖）
- [长效Agent-Harness工程化研究报告](../../../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) 中讨论的多 Agent 协作范式
- antirez 原文 Redlock：https://redis.io/docs/latest/develop/use/patterns/distributed-locks/
