"""
05 · Tool Cache — 工具结果缓存（L1 进程内 + L2 Redis 精确）

不依赖 LLM。演示：
- 幂等 key 设计（args 排序 + sha256）
- 装饰器自动包装工具函数
- 命中率与延迟测量
- 缓存击穿防护（Lua 互斥锁）

跑法：
    python 05_tool_cache/main.py
"""
from __future__ import annotations

import functools
import hashlib
import json
import sys
import threading
import time
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _common.llm import redis_text_client

r = redis_text_client()


# ---------- L1：进程内 LRU ----------
# 直接用 functools.lru_cache，最快但跨进程不共享


# ---------- L2：Redis 精确缓存 ----------

def cache_key(tool_name: str, args: dict) -> str:
    """幂等 key 设计：tool + 排序后 args 的 sha256
    
    陷阱：dict 的 str() 顺序不稳定，必须 json.dumps(sort_keys=True)
    """
    serialized = json.dumps(args, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(serialized.encode()).hexdigest()[:16]
    return f"tool:{tool_name}:{h}"


# 击穿防护用 Lua 脚本：原子地"读 → 设锁"
ACQUIRE_LOCK_LUA = """
if redis.call('GET', KEYS[1]) then
    return 0
end
return redis.call('SET', KEYS[1], ARGV[1], 'NX', 'PX', ARGV[2])
"""


def cached_tool(tool_name: str, ttl: int = 300, breakdown_protection: bool = True):
    """装饰器：L1 LRU + L2 Redis 缓存"""

    def decorator(fn: Callable):
        # L1
        l1_cached = functools.lru_cache(maxsize=128)(lambda kwargs_tuple: fn(**dict(kwargs_tuple)))

        @functools.wraps(fn)
        def wrapper(**kwargs):
            key = cache_key(tool_name, kwargs)
            wrapper.calls = getattr(wrapper, "calls", 0) + 1

            # L2: Redis 查
            cached = r.get(key)
            if cached is not None:
                wrapper.l2_hits = getattr(wrapper, "l2_hits", 0) + 1
                return json.loads(cached)

            # 击穿防护：用 Lua 抢锁
            lock_key = f"{key}:lock"
            if breakdown_protection:
                got_lock = r.eval(ACQUIRE_LOCK_LUA, 1, lock_key, "1", "10000")
                if not got_lock:
                    # 没抢到锁，等一下让别人回填
                    for _ in range(20):  # 最多等 1 秒
                        time.sleep(0.05)
                        cached = r.get(key)
                        if cached is not None:
                            wrapper.l2_hits_after_wait = getattr(wrapper, "l2_hits_after_wait", 0) + 1
                            return json.loads(cached)
                    # 等超时，自己也调一下兜底
                    wrapper.lock_timeout = getattr(wrapper, "lock_timeout", 0) + 1

            # 真正调用
            wrapper.misses = getattr(wrapper, "misses", 0) + 1
            try:
                result = fn(**kwargs)
                r.setex(key, ttl, json.dumps(result, ensure_ascii=False))
                return result
            finally:
                if breakdown_protection:
                    r.delete(lock_key)

        wrapper.cache_key = lambda **kw: cache_key(tool_name, kw)
        wrapper.invalidate = lambda **kw: r.delete(cache_key(tool_name, kw))
        return wrapper

    return decorator


# ---------- 模拟工具 ----------

@cached_tool("weather", ttl=600)
def get_weather(city: str) -> dict:
    print(f"    🌐 调用真 API for {city} (耗时 0.3s)")
    time.sleep(0.3)
    return {"city": city, "temp": 20, "condition": "sunny"}


@cached_tool("expensive_calc", ttl=60, breakdown_protection=True)
def expensive_calc(n: int) -> int:
    print(f"    🔥 真的算 fib({n}) (耗时 0.4s)")
    time.sleep(0.4)
    return sum(range(n))


# ---------- 主流程 ----------

def demo_basic():
    print("=" * 70)
    print("场景 1：基础缓存 —— 同参数直接命中")
    print("=" * 70)

    # 清干净
    for city in ["Beijing", "Shanghai"]:
        get_weather.invalidate(city=city)

    for label, kw in [("第一次 Beijing", {"city": "Beijing"}),
                      ("第二次 Beijing（应命中）", {"city": "Beijing"}),
                      ("第一次 Shanghai", {"city": "Shanghai"}),
                      ("第三次 Beijing（应命中）", {"city": "Beijing"})]:
        t0 = time.time()
        res = get_weather(**kw)
        elapsed = (time.time() - t0) * 1000
        print(f"  {label}: {res}  耗时 {elapsed:6.1f}ms")

    print(f"\n  📊 调用统计: calls={get_weather.calls}, "
          f"l2_hits={getattr(get_weather, 'l2_hits', 0)}, "
          f"misses={getattr(get_weather, 'misses', 0)}")


def demo_idempotent_key():
    print("\n" + "=" * 70)
    print("场景 2：幂等 key —— args 顺序无关")
    print("=" * 70)

    k1 = cache_key("foo", {"a": 1, "b": 2, "c": 3})
    k2 = cache_key("foo", {"c": 3, "b": 2, "a": 1})
    k3 = cache_key("foo", {"a": 1, "b": 2})
    print(f"  key({{a,b,c}})    = {k1}")
    print(f"  key({{c,b,a}})    = {k2}")
    print(f"  key({{a,b}})      = {k3}")
    print(f"  ✅ 顺序无关: {k1 == k2}")
    print(f"  ✅ 内容敏感: {k1 != k3}")


def demo_breakdown_protection():
    print("\n" + "=" * 70)
    print("场景 3：缓存击穿防护 —— 5 个并发请求只有 1 个真调下游")
    print("=" * 70)

    expensive_calc.invalidate(n=100)
    # 重置计数
    expensive_calc.calls = 0
    expensive_calc.misses = 0
    expensive_calc.l2_hits = 0
    expensive_calc.l2_hits_after_wait = 0

    results = {}

    def worker(idx: int):
        t0 = time.time()
        res = expensive_calc(n=100)
        results[idx] = (res, (time.time() - t0) * 1000)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total = (time.time() - t0) * 1000

    print(f"  5 个并发请求总耗时: {total:.1f}ms (vs 串行 5×400=2000ms)")
    print(f"  各 worker 结果一致: {len(set(r[0] for r in results.values())) == 1}")
    print(f"  📊 calls={expensive_calc.calls}, "
          f"misses={expensive_calc.misses} (真调下游次数), "
          f"hits_after_wait={getattr(expensive_calc, 'l2_hits_after_wait', 0)}")
    print(f"  💡 misses 应该 = 1（只有抢到锁的 1 个真调），其他 4 个等回填后命中")


def main():
    demo_basic()
    demo_idempotent_key()
    demo_breakdown_protection()

    print("\n" + "=" * 70)
    print("✅ 工具缓存全部演示完成")
    print("\n💡 生产建议：")
    print("   - 写工具/有副作用的别缓存（发邮件、扣款）")
    print("   - 时间敏感的工具加短 TTL（天气 5 分钟，FAQ 24 小时）")
    print("   - 高 QPS 工具必须开击穿防护，避免雪崩")


if __name__ == "__main__":
    main()
