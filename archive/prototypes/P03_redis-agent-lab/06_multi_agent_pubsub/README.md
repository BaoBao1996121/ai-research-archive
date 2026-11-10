> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 06 · Multi-Agent 通信 — Pub/Sub & Streams + Redis vs Kafka 取舍 🆕

> **新增量章节**。主报告 §2.6 提到 Pub/Sub 和 Streams 但没深入对比，本章给出可对照运行的代码 + **主报告未覆盖的"Redis 消息层 vs Kafka/RabbitMQ"决策框架**。

## Why 这一章

多 Agent 系统的灵魂是**通信范式**。用错了 Pub/Sub，关键任务消息会丢；用错了 Streams，简单广播也变得笨重；什么都用 Redis，规模到一定程度 Kafka 才是答案。

本章用一个对照实验讲清楚 Pub/Sub 和 Streams 的根本差异——**消息持久性**——然后回答更难的问题：**什么时候 Redis 不够用，要上 Kafka？**

## 跑法

```powershell
python 06_multi_agent_pubsub/main.py
# 选 3 跑两个对照
```

## 预期输出（节选）

```
模式 1：Pub/Sub —— fire-and-forget，晚到的订阅者会丢消息
======================================================================
  [Producer] 发布 task-00（1 个订阅者收到）   ← 只有 WorkerA
  [WorkerA] 收到: task-00
  [Producer] 发布 task-01（1 个订阅者收到）
  [WorkerA] 收到: task-01
  [Producer] 发布 task-02（1 个订阅者收到）
  [WorkerA] 收到: task-02
  [WorkerB] 晚启动 (1.5s 后), 订阅 tasks:pubsub
  [Producer] 发布 task-03（2 个订阅者收到）   ← B 上线了
  [WorkerA] 收到: task-03
  [WorkerB] 收到: task-03      ← B 错过了前 3 条
  ...
💡 观察：WorkerB 因为晚启动，丢了 task-00/01/02。Pub/Sub 不保留历史。

模式 2：Streams —— 持久化 + 消费组
======================================================================
  [Producer] 先发 5 条任务到 Stream（此时还没 worker）...
  [WorkerA] 收到 1714000000000-0: {'task': 'task-00', ...}    ← 5 条都拿到
  [WorkerA] 收到 1714000000001-0: {'task': 'task-01', ...}
  ...
  [WorkerB] 晚启动 (1.5s 后), 加入消费组 workers
  [WorkerB] 收到 1714000000005-0: {'task': 'task-05', ...}    ← 加入后分到新消息
💡 观察：8 条消息全部被消费，消费组负载均衡。Pending = 0。
```

## Pub/Sub vs Streams 对比

| 维度 | Pub/Sub | Streams |
|------|---------|---------|
| 持久化 | ❌ 不持久，订阅者不在线就丢 | ✅ 持久化到 RDB/AOF |
| 历史回放 | ❌ 不能 | ✅ XREAD 任意 ID 起点 |
| 消费确认 | ❌ 无 ACK 机制 | ✅ XACK + Pending List |
| 消费组负载均衡 | ❌（所有订阅者收全集） | ✅ 一条消息只分给组内一个 consumer |
| 故障重试 | ❌（丢了就丢了） | ✅ XCLAIM 把超时消息重新分配 |
| 延迟 | ~1ms | ~2ms |
| 内存开销 | 极低（不存消息） | 高（存全部历史，需 MAXLEN 裁剪） |

**选型口诀**：
- 不能丢 → Streams
- 实时广播 + 丢一两条无所谓 → Pub/Sub
- 不确定 → 默认 Streams（贵不到哪去，安全得多）

## 🆕 Redis 消息层 vs Kafka/RabbitMQ 取舍框架（主报告未覆盖）

这是**生产级 Agent 系统选型时绕不开的问题**。

### 决策树

```
你的 Agent 间通信场景：
  ├── 总吞吐 < 100K 消息/秒？
  │   └── 都用 Redis（Streams 足矣）
  │
  ├── 100K ~ 1M 消息/秒？
  │   ├── 跨机房/跨数据中心？
  │   │   └── Kafka（多副本 + ISR + 跨集群同步成熟）
  │   └── 单机房？
  │       └── Redis Cluster + Streams 仍可（但要做好分片）
  │
  └── > 1M 消息/秒 或 必须保留消息数月？
      └── Kafka 或 Pulsar（Redis 内存成本爆炸）
```

### 多维度对比

| 维度 | Redis Streams | Kafka | RabbitMQ |
|------|--------------|-------|----------|
| **吞吐上限** | ~100K msg/s（单节点） | 数百万 msg/s | ~50K msg/s |
| **存储模型** | 全内存（受 RAM 限制） | 磁盘 + Page Cache（无限） | 内存优先 + 磁盘溢出 |
| **延迟** | < 5ms | 5-50ms（取决于 batch） | < 5ms |
| **消息保留** | 受内存约束（用 MAXLEN） | 按时间/容量保留（默认 7 天） | 默认消费即删 |
| **消费模型** | 消费组 + Pending | 分区 + Offset（极其灵活） | Queue + Exchange（路由强） |
| **运维复杂度** | ⭐ 简单（同一个 Redis 顺手用） | ⭐⭐⭐⭐ 重（Zookeeper / KRaft + 调优） | ⭐⭐ 中等 |
| **生态/工具链** | 一般（主要在 Redis 体系内） | 极强（Connect/Streams/KSQL/Flink 集成） | 强（管理界面 + 协议丰富） |
| **学习曲线** | 1 天 | 1-2 周 | 3-5 天 |

### 关键直觉

1. **Redis 的强项是"低延迟 + 同进程已有"**——你 Agent 已经在用 Redis 做缓存/状态了，加 Streams 几乎零成本
2. **Kafka 的强项是"超大吞吐 + 持久回放 + 流处理生态"**——不需要这三样的话上 Kafka 是过度工程
3. **RabbitMQ 的强项是"复杂路由 + 协议兼容（AMQP/MQTT/STOMP）"**——传统企业集成场景

### Agent 场景下的具体建议

| Agent 子场景 | 推荐 |
|-------------|------|
| Agent 状态变更广播（"我开始 thinking"） | Redis Pub/Sub |
| Agent 任务分发（不能丢） | Redis Streams |
| Agent 工具调用结果回传 | Redis Streams（带 ACK） |
| Agent 间长链条工作流（Saga） | Redis Streams 起步，超 100K msg/s 切 Kafka |
| Agent 行为审计日志（合规要 6 个月+） | Kafka（Redis 内存撑不住） |
| Agent 与外部系统集成（MQTT 设备） | RabbitMQ |
| 多模态事件流处理 + 实时聚合 | Kafka + Flink |

## 停下来想一想 🤔

1. 如果 Agent A 给 Agent B 发任务，B 处理时崩了没 ACK，Streams 怎么把这条任务重新交给 Agent C？
   - 答：用 `XPENDING` 查超时未 ACK 的消息 + `XCLAIM` 改主
2. Pub/Sub 在什么场景下"丢消息"反而是优点？
   - 答：实时只关心"现在状态"的场景，比如"Agent 心跳"（错过的心跳没用，下次还会再来）
3. 为什么不能用 Redis List + LPUSH/BRPOP 做任务队列？
   - 答：可以，但缺消费组、缺 ACK、缺历史回放。简单场景行，复杂的还是 Streams

## 关联

- 主报告 [Redis在Agent中的应用与替代方案综合对比](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) §2.6（已有但未深入 Kafka 对比）
- 报告 [现代智能体编排框架深度调研报告](../../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) 中讨论的多 Agent 编排范式
- 主报告 §三 七方案对比表中**没有**Kafka/RabbitMQ —— 这正是本章补足的盲区
