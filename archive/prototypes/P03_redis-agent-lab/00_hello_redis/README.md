> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# 00 · Hello Redis — 五大数据结构速通

> **目的**：不碰 LLM，先把 Redis 五大基础数据结构和 TTL 机制走一遍。这是后续所有章节的地基。

## Why 这一章

后面所有章节都假设你知道 Redis 的 String/Hash/List/Stream/Pub-Sub 长什么样、各擅长什么。如果你已经熟，跳过即可。

## 5 大结构与 Agent 场景的对应

| 结构 | Agent 中干啥用 | 对比常见错误用法 |
|------|---------------|----------------|
| String | 缓存 LLM 响应、简单计数器、分布式锁 token | 别用来存 JSON 字符串（会反复 parse），用 Hash |
| Hash | 用户画像、Agent 状态字段、配置项 | 字段超过 100 个建议拆 key |
| List | 对话历史、任务队列、消息缓冲 | 别当持久消息队列用（Pub/Sub 也不行），不丢消息要用 Stream |
| Stream | 事件溯源、Agent 间持久消息、Audit Log | 比 Pub/Sub 重，但保证不丢；适合关键消息 |
| Pub/Sub | 实时广播、Agent 间事件通知 | 订阅者不在线就丢消息，不能丢的别用 |

## 跑法

```powershell
# 前置：docker compose up -d 已起好 Redis
python 00_hello_redis/main.py
```

## 预期输出

```
✅ Redis 连接成功
============================================================

[String] —— Agent 中典型用途：缓存 LLM 响应、简单计数器
  set greet=hello agent (ex=10s)
  get greet -> 'hello agent', ttl -> 10s
  incr hits 3 次 -> 3

[Hash] —— Agent 中典型用途：用户画像、Agent 状态字段
  HGETALL user:1001 -> {'name': 'Alice', 'role': 'researcher', 'credits': '100'}
  HINCRBY credits -10 -> 现在 credits = 90

[List] —— Agent 中典型用途：对话历史、任务队列、消息缓冲
  LRANGE 全部 -> ['task1', 'task2', 'task3']
  LPOP 出队顺序（FIFO）： task1 task2 task3

[Stream] —— Agent 中典型用途：事件溯源、Agent 间持久消息
  XADD 写入 3 条
  XRANGE 读出 3 条:
    1714000000000-0 -> {'agent': 'researcher', 'action': 'search', 'round': '0'}
    ...

[Pub/Sub] —— Agent 中典型用途：实时广播
  发布: 'hello channel'
  订阅者收到: 'hello channel'

[TTL] —— Agent 中典型用途：会话/缓存自动过期
  存入 ephemeral, ttl=2s
  等 2.5 秒...
  get ephemeral -> None（已自动消失）

============================================================
✅ 五大数据结构演示完成
```

## 停下来想一想 🤔

1. 一个 Agent 的"短期对话历史"（最近 10 轮）你用哪个结构？为什么不用 Stream？
2. 多个 Agent 互相广播"我完成了任务"，用 Pub/Sub 还是 Stream？什么情况下选哪个？
3. 缓存 LLM 响应的 key 该怎么设计才能避免冲突？

> 答案在主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §一/§二 里。
