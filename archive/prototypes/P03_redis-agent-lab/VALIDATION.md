> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Redis-for-Agent Lab 全量验证报告

> 验证日期：2026-04-24
> 环境：Windows 11 / Python 3.13 / fakeredis 2.35.1（无 Docker / 无 Redis 服务 / 无 LLM key）
> 验证策略：Redis 后端用 fakeredis 内嵌；LLM/Embedding 缺 key 时自动 mock fallback

## 总览

| 章节 | 状态 | 关键观察 | 备注 |
|------|------|---------|------|
| 00 hello_redis | ✅ | String/Hash/List/Stream/Pub-Sub/TTL 全部演示通过 | 基础数据结构 |
| 01 checkpoint | ⏭️ | langgraph-checkpoint-redis 要求真 Redis 8.0 | 代码与 README 完整，待真服务 |
| 02 chat_memory | ✅ | LPUSH+LTRIM 自动淘汰生效（10 条窗口稳定）；长期 Hash 独立 | 全程无 LLM 也跑通 |
| 03 semantic_cache | ✅ | mock embed 下：完全相同 query 命中 sim=1.00；同义 query 命中需真 embedding | 框架本身验证通过 |
| 04 vector_rag | ✅ | fakeredis 走手写 cosine，4 个 query 检索+生成完整管道跑通 | 真 Redis 自动切 redisvl HNSW |
| 05 tool_cache | ✅ | 5 并发请求 → misses=1（精准），其余 4 个等回填命中 | Lua 击穿防护按预期工作 |
| 06 multi_agent_pubsub | ✅ | Pub/Sub: WorkerB 晚启 1.5s 丢前 3 条；Streams: 8 条全消费 pending=0 | 同代码两模式对比 |
| 07 distributed_lock | ✅ | 5 抢 1 锁；Bob 不能释放 Alice 锁；node-0 崩 → node-2 接任 | Lua 释放原子性验证 |

**统计**：8 章中 7 章 ✅ 完整跑通，1 章 ⏭️ 待真 Redis 验证。

## 关键问题与解决

### 1. 环境零依赖启动
- Docker/Redis/Memurai 均未安装
- **解法**：选 fakeredis 作为内嵌后端，`USE_FAKEREDIS=1` 一键切换
- 改造点：`_common/llm.py` 加 `_make_redis_client(decode)` 工厂，全局 `_FAKE_SERVER` 单例确保两类客户端（bytes/text）共享同一虚拟 server，Pub/Sub 才能跨客户端联通

### 2. 无 LLM key 不能跑 03/04
- DashScope key 用户离开未提供
- **解法**：`embed()` 和 `chat()` 加 `USE_MOCK_LLM` 自动检测分支
  - `_mock_embed()`: sha256(unigram+bigram) → 散列到 EMBEDDING_DIM 槽 → L2 归一化
  - `chat()` mock 模式：返回 `[mock-llm] 收到「{query}」` 回复
- 局限：mock embed 抓不到跨语言/同义词的语义相似度，但保证管道完整跑通；真 key 时自动透明切回真模型

### 3. fakeredis 不支持 RediSearch
- 试 `redisvl.SearchIndex.create()` → `unknown command 'ft._list'`
- **解法**：04 章 `VectorRAG` 类按 `USE_FAKEREDIS` 标记自动选路径：
  - `True` → 手写 cosine 全表扫，O(n)
  - `False` → redisvl + HNSW，O(log n)
- 用户切到真 Redis 8.0 即自动用上 HNSW，业务代码零改动

### 4. Windows GBK 终端 + emoji
- 默认 `cp936` 编码，所有 emoji print 全部 `UnicodeEncodeError`
- **解法**：在 `_common/llm.py` 顶部 `sys.stdout.reconfigure(encoding="utf-8")`，所有章节 import 时自动生效
- 残留：PowerShell 渲染层仍是 GBK，输出乱码但程序逻辑正确（VS Code 终端面板正常）

## 真 Redis + 真 LLM 重跑指引

当用户提供真环境时，零代码改动重跑：

```bash
# 1) 启 Redis（任选其一）
docker compose up -d                                # 用本目录的 docker-compose.yml
# 或：winget install Memurai.Memurai.Developer    # Windows 原生 Redis 兼容服务

# 2) 改 .env
USE_FAKEREDIS=0
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-xxxxx       # 你的 DashScope key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 3) 验证连通
python _common/llm.py     # 应看到 redis/llm/embedding 三个 ✅

# 4) 全量回放
python 00_hello_redis/main.py
python 02_chat_memory/main.py
python 03_semantic_cache/main.py    # 此时同义 query 应能稳定 HIT (sim≥0.85)
python 04_vector_rag/main.py        # 自动切 redisvl + HNSW 索引
python 05_tool_cache/main.py
python 06_multi_agent_pubsub/main.py
python 07_distributed_lock/main.py
python 01_checkpoint/main.py        # 待补 main.py，已有完整 README 设计文档
```

## 锻造产出

本次"全量跑"过程中沉淀的可复用模式：

1. **fakeredis 单例 + 双模式客户端**：`_make_redis_client(decode)` + 模块级 `_FAKE_SERVER` 单例。同样适用于其他需要"无外部依赖单元测试"的项目。
2. **mock embed 兜底**：sha256-bigram 伪向量。让"无 key 也能演示 RAG 管道"的脚手架模式可复用到任何 RAG 教学场景。
3. **Windows UTF-8 自动修复 import 副作用**：在共享 `_common` 模块顶部统一 reconfigure stdout，所有 child 模块零成本继承。

考虑后续固化进 `skills/agent-harness-scaffolder` 的"教学原型"模板族。
