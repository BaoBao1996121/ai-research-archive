> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# 05 · Tool Cache — 工具结果缓存（7 级优先级链）

> **状态**：⚡ 骨架 + README

## Why 这一章

Agent 调用工具的成本：
- 调外部 API（搜索/数据库/天气）：数十毫秒到秒级
- 调付费服务（OpenAI/Google）：花钱
- 调慢工具（爬虫/分析）：可能数分钟

**很多调用其实是重复的**——同一用户问"北京天气"问 5 次，外部 API 不该被调 5 次。

## 7 级缓存优先级链（从快到慢）

```
请求 ─→ L1 进程内 LRU (μs) ─→ L2 Redis 精确缓存 (ms) ─→ L3 Redis 语义缓存 (10ms)
                                                            │
                                                            ↓ 都 miss
                                          L4 工具调用 ─→ 写回 L1+L2+L3
```

实际工业级 Agent 系统常见 7 级（含 CDN/Edge/数据库行缓存等），本章聚焦最核心的 L1+L2+L3。

## 跑法

```powershell
python 05_tool_cache/main.py
```

## 核心代码骨架

```python
import hashlib, json, time
from functools import lru_cache
from _common.llm import redis_text_client

r = redis_text_client()


def cache_key(tool_name: str, args: dict) -> str:
    """幂等 key 设计：tool_name + 排序后的 args 的 SHA256"""
    serialized = json.dumps(args, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(serialized.encode()).hexdigest()[:16]
    return f"tool:{tool_name}:{h}"


def cached_tool(tool_name: str, ttl: int = 300):
    """装饰器：自动缓存工具结果"""
    def decorator(fn):
        # L1: 进程内 LRU（最快，但跨进程不共享）
        fn = lru_cache(maxsize=128)(fn)

        def wrapper(**kwargs):
            key = cache_key(tool_name, kwargs)

            # L2: Redis 精确缓存
            cached = r.get(key)
            if cached:
                return json.loads(cached)

            # L4: 真正调工具
            result = fn(**kwargs)
            r.setex(key, ttl, json.dumps(result, ensure_ascii=False))
            return result
        return wrapper
    return decorator


@cached_tool("weather", ttl=600)  # 天气 10 分钟缓存
def get_weather(city: str) -> dict:
    print(f"  ⚠️ 真的调用 API for {city}")
    time.sleep(0.5)  # 模拟外部 API 延迟
    return {"city": city, "temp": 20, "condition": "sunny"}


if __name__ == "__main__":
    # 第一次调用：MISS，调 API
    print(get_weather(city="Beijing"))
    # 第二次相同参数：HIT，秒回
    print(get_weather(city="Beijing"))
    # 不同参数：MISS
    print(get_weather(city="Shanghai"))
```

## 关键设计：幂等 Key

**陷阱**：直接用 `f"{tool}:{args}"` 当 key——dict 的字符串表示不稳定，`{a:1, b:2}` 和 `{b:2, a:1}` 是不同 key。

**正解**：`json.dumps(args, sort_keys=True)` + hash。

## 工具结果该不该缓存？决策表

| 工具类型 | 缓存吗 | TTL | 原因 |
|---------|-------|-----|------|
| 天气、汇率 | ✅ | 5-15 min | 短期不变 |
| 数据库读 | ✅ | 1-5 min | 减压 |
| 数据库写 | ❌ | - | 写本身就要立即生效 |
| LLM 调用 | ✅ 语义缓存 | 1-24h | 见 03 章 |
| 用户隐私接口 | ⚠️ | 极短 | 慎重，避免越权 |
| 时间敏感（"现在几点"） | ❌ | - | 缓存失去意义 |
| 副作用工具（"发送邮件"） | ❌ | - | 缓存会跳过副作用 |

## 进阶：缓存击穿/雪崩防护

```python
# 击穿：热点 key 过期瞬间所有请求打到下游
# 解法：互斥锁，第一个请求负责回填，其他请求等
import redis as rlib

lock = r.set(f"{key}:lock", 1, nx=True, ex=10)
if lock:
    # 我负责回填
    result = fn(**kwargs)
    r.setex(key, ttl, ...)
    r.delete(f"{key}:lock")
else:
    # 等回填
    time.sleep(0.05)
    return cached_tool(...)
```

## TODO

- [ ] 实现完整 L1 + L2 + L3 三级缓存（L3 用 03 章的语义缓存）
- [ ] 加击穿/雪崩防护
- [ ] 测量真实场景的命中率和延迟分布

## 关联

- 主报告 §2.5
