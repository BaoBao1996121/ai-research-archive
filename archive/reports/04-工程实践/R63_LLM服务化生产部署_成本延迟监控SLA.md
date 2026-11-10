---
title: LLM 服务化生产部署：成本 / 延迟 / 监控 / SLA
aliases:
  - LLM服务化生产部署_成本延迟监控SLA
  - R63
  - LLM 生产运维
  - LLM Serving Ops
  - LLM 可观测性与 SLA
tags:
  - 生产部署
  - 可观测性
  - Autoscaling
  - OpenTelemetry
  - Langfuse
  - TTFT
  - SLA
  - 工程实践
date: 2026-04-24
category: 工程实践
report_id: R63
tokens: 11000
status: completed
related:
  - "[R04](R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)"
  - "[R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md)"
  - "[R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)"
  - "[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)"
prev_path: ""
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# LLM 服务化生产部署：成本 / 延迟 / 监控 / SLA

> **一句话概括**：[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 回答了"引擎跑什么、怎么跑"，本报告回答"跑起来之后怎么运维得起、扛得住、省得下来"——聚焦生产级 LLM 服务的**四大延迟指标、弹性伸缩、多模型编排、可观测性、成本治理与 SLA 设计**。
> **研究日期**：2026-04-24
> **关联报告**：[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 量化与推理引擎（算力层） · [R04](R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) Agent 部署上线全景 · [R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) 长效 AgentHarness · [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) Redis 在 Agent 中的应用（语义缓存）
> **增量定位**：R58 聚焦单引擎内部的吞吐与量化选择；本报告站在**服务运维视角**，把若干引擎 + 多模型 + 多租户拼装成一个稳定、可观测、可算账的生产系统。
> **目标读者**：要把 LLM API 对外开放（内部或 SaaS）、要背 SLA、要对账单负责的平台 / SRE / AI Infra 工程师

---

## TL;DR 速查卡

- **延迟四件套**：TTFT（首 token 延迟）决定"感官响应"；ITL/TPOT（token 间延迟）决定"生成流畅度"；TPS（吞吐）决定"成本"；E2E p99 决定"SLA"。**只看平均值等于没看**，一律按 p50/p95/p99 分位数盯。
- **Autoscaling 铁律**：传统 CPU/QPS 伸缩对 LLM **全部失效**。正确做法 = 按 **GPU KV Cache 利用率 + 排队深度**伸缩，参考 vLLM Production Stack 的 `num_requests_waiting` / `gpu_cache_usage_perc` 指标。冷启动加载 70B 模型动辄 60-180s，预热副本（warm pool）几乎必选。
- **多模型编排三板斧**：Router（按能力 / 成本 / 长度路由）+ A/B（新老模型 10%/90% 分流）+ Canary（先内部灰度再放量）。推荐开源组合：**LiteLLM（路由）+ vLLM Production Stack（K8s 部署）+ Langfuse（观测）**。
- **可观测性 2026 新基座**：**OpenTelemetry GenAI Semantic Conventions**（v1.40.0，仍标注 Development 但已被 Langfuse/Phoenix/Arize/Traceloop 广泛采用）——统一 `gen_ai.*` span/metric 命名，**选工具前先对 OTel**。
- **成本三把刀**：① **Prompt Caching**（Anthropic/OpenAI/Gemini/DeepSeek 原生支持，命中可省 50-90%）② **语义缓存**（用 Redis + embedding 做召回，呼应 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)）③ **请求去重 + Token 预算**（单用户日配额 + prompt 长度上限）。三者叠加典型场景可降 30-70% 账单。
- **SLA 兜底四件套**：**重试策略**（指数退避 + 抖动）→ **降级路由**（主模型失败转到 fallback 模型）→ **限流**（token/s 而非 req/s，因为单请求差 1000×）→ **熔断**（连续失败自动断主路线）。
- **最大坑**：按 req/s 做限流、按 CPU% 做扩容、按 average latency 做告警——**这三件事在 LLM 场景全是错的**。

---

## 目录

- [🔭 定位透镜：纵横坐标](#-定位透镜纵横坐标)
- [📚 研究分析轨道](#-研究分析轨道)
  - [1. 延迟四大指标：定义与测量](#1-延迟四大指标定义与测量)
  - [2. Autoscaling 策略](#2-autoscaling-策略)
  - [3. 多模型编排](#3-多模型编排)
  - [4. 可观测性：OTel / Langfuse / Phoenix](#4-可观测性otel--langfuse--phoenix)
  - [5. 成本治理](#5-成本治理)
  - [6. SLA 设计](#6-sla-设计)
- [🚀 上手实战轨道](#-上手实战轨道)
  - [Hello World 1：vLLM 原生 metrics → Prometheus](#hello-world-1vllm-原生-metrics--prometheus)
  - [Hello World 2：LiteLLM 做模型路由 + fallback](#hello-world-2litellm-做模型路由--fallback)
  - [Hello World 3：Langfuse 一行接入 OpenAI 追踪](#hello-world-3langfuse-一行接入-openai-追踪)
  - [Hello World 4：语义缓存最小实现](#hello-world-4语义缓存最小实现)
  - [生产部署 Checklist](#生产部署-checklist)
- [🕳️ 避坑指南](#-避坑指南)
- [💰 成本与 ROI 速算](#-成本与-roi-速算)
- [🎯 决策速查](#-决策速查)
- [结论与最佳实践](#结论与最佳实践)
- [开放问题与后续计划](#开放问题与后续计划)
- [📌 来源清单](#-来源清单)

---

## 🔭 定位透镜：纵横坐标

### 纵轴 · 演化脉络

```
2022  ChatGPT 上线 → 大家第一次被 LLM API 的"慢"教育（10-30s 延迟）
2023  vLLM/PagedAttention → TTFT/ITL 成通用词汇，Prometheus + vLLM metrics 成事实标准
2024  OTel GenAI SemConv v0.x → 可观测性开始收敛；Langfuse 爆红、Phoenix (Arize) 开源
      OpenAI 推出 Prompt Caching（自动生效，无需改代码）
2025  Anthropic ephemeral cache_control、Gemini Context Caching、DeepSeek Hard-Cache
      vLLM Production Stack 1.0 → K8s 原生 LLM Serving 范式成型
      LiteLLM 成为 Python 应用层"LLM 路由事实标准"（~20k stars）
2026  OTel GenAI SemConv v1.40（仍 Development，但 SDK 广泛对接）；
      PD 分离（Prefill/Decode 分离部署）进入开源主流（SGLang、DistServe）
      语义缓存工具箱（GPTCache/Redis-LangCache/Portkey）生产化
```

**生命周期定位**：**成熟期初段**。引擎层（R58）已卷到瓶颈；**运维层正是当前增量最大、红利最高的层**——同样的硬件，不同的运维能把成本拉出 3-5 倍差距。

### 横轴 · 竞争格局

| 能力层 | 主流开源 | 商业 SaaS | 设计哲学差异 |
|--------|----------|----------|-------------|
| **引擎 metrics** | vLLM / SGLang / TGI（内置 Prometheus） | Bedrock/Azure OpenAI（平台自带） | OSS 更细粒度；SaaS 更抽象 |
| **网关 / 路由** | **LiteLLM**、Portkey（OSS 版）、Kong AI Gateway | Portkey SaaS、Cloudflare AI Gateway | LiteLLM=SDK 优先；Portkey=平台优先 |
| **K8s 编排** | **vLLM Production Stack**、Ray Serve、KServe | AWS SageMaker、GKE Inference | Production Stack=引擎原生；KServe=通用推理 |
| **可观测性** | **Langfuse**、Arize Phoenix、Traceloop OpenLLMetry、Helicone | LangSmith（LangChain）、Datadog LLM Obs | Langfuse=LLM-App 首选；Phoenix=Eval 强 |
| **语义缓存** | GPTCache、Redis LangCache、Portkey Cache | 同 SaaS | 呼应 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) |
| **负载测试** | **GenAI-Perf** (NVIDIA)、llmperf (Anyscale)、Vegeta+脚本 | Grafana k6 AI | GenAI-Perf 对 LLM 指标原生 |

### 交叉判断

1. **阶段判断**：OTel GenAI 2026 尚未 stable，**但已经是事实标准**——新项目直接对齐，不要自己定义 span 命名（两年后全部要返工）。
2. **开源 vs SaaS**：中小团队直接上 **Langfuse self-hosted + LiteLLM + vLLM Production Stack**，三个月内能跑到生产；大厂合规场景必须自建，否则把流量送给 Langfuse/Portkey 云即可。
3. **不该造的轮子**：路由、语义缓存、Prometheus Dashboard——全部都有开源成熟方案，自己写 100% 亏。
4. **该亲手做的事**：① 你自己业务的 SLA 定义与告警规则 ② 成本配额的业务层策略 ③ 降级逻辑（主模型挂了走哪条路）——这些是业务特异性的，工具只提供接口。

---

## 📚 研究分析轨道

### 1. 延迟四大指标：定义与测量

生产环境**只看平均延迟 = 自欺欺人**。LLM 的延迟分布是重尾的：95% 请求 2 秒、5% 请求 20 秒的场景很常见，平均 3 秒看着很漂亮，但客户流失在那 5%。

#### 四大指标定义

| 指标 | 全称 | 口径 | 决定什么 | 目标值（参考） |
|------|------|------|---------|---------------|
| **TTFT** | Time To First Token | 从发请求到**收到第一个 token**的墙钟时间 | 用户感官响应速度 | 交互式：< 500ms；批处理：不重要 |
| **ITL / TPOT** | Inter-Token Latency / Time Per Output Token | **相邻 output token 间**的延迟（通常取中位数或均值） | 生成流畅度（读秒感） | < 80ms（类比人类阅读速度 ~10 tokens/s） |
| **TPS** | Tokens Per Second（throughput） | 单实例或集群**每秒生成的 output tokens 总数** | 硬件利用率 / 成本 | 越高越好，依模型与硬件而定 |
| **E2E Latency** | End-to-end | 整个请求从发出到完成的墙钟时间 = TTFT + N × ITL | SLA 承诺 | 业务定义 |

**关系公式**：`E2E ≈ TTFT + (output_tokens - 1) × ITL`

**关键直觉**：
- **TTFT** 几乎只受 **prefill 阶段**影响——输入越长越慢（输入 4k tokens 的 TTFT 是 1k 的 4 倍左右）。**Prompt Caching 命中时 TTFT 可降 80%+**。
- **ITL** 几乎只受 **decode 阶段**影响——和输入长度基本无关，但和**当前 batch 里挤了多少并发请求**高度相关（连续批处理会拖慢单请求 ITL，换取总吞吐）。
- **高吞吐和低 ITL 天然矛盾**——引擎参数 `max_num_seqs` 加大 → 吞吐↑但 ITL↑。

#### 分位数的坑

**不要用平均值**。LLM 延迟分布极偏。标配做法：

```
监控四件套：p50 / p90 / p95 / p99
告警基线：p99 而不是 avg
SLA 承诺：也按 p99
```

**举例**：TTFT avg 600ms 看起来达标，但 p99 可能 8 秒——这 1% 的请求就是你 NPS 掉分的源头。

#### 测量工具

| 工具 | 用途 | 特点 |
|------|------|------|
| **GenAI-Perf** (NVIDIA) | LLM 专用压测 | 原生输出 TTFT/ITL/TPS p50/p90/p99，JSON + CSV |
| **llmperf** (Anyscale) | 并发压测 | 轻量，Python 脚本 |
| **vLLM metrics** (`/metrics`) | 运行时监控 | Prometheus 格式，含 KV 缓存命中率等引擎内指标 |
| **Langfuse / Phoenix** | 应用层追踪 | 按 trace 粒度看 per-request TTFT/总延迟，适合排查单个坏请求 |

> ⚠️ **不要用 Vegeta/JMeter 的 default 指标**——它们测的是 HTTP 请求延迟，对流式响应（SSE）的 TTFT/ITL 不敏感。必须用 LLM 专用压测工具。

---

### 2. Autoscaling 策略

> 核心结论：**传统 HPA（按 CPU/QPS）对 LLM 全部失效**。LLM 的瓶颈是 GPU 显存（KV Cache）和队列深度，不是 CPU。

#### 为什么传统 HPA 失效

- **CPU 利用率**：LLM Serving 的 CPU 通常 < 20%（GPU 是瓶颈），HPA 永远不会触发扩容。
- **QPS**：一个 req 可能是 50 tokens 的问候，也可能是 16k tokens 的文档摘要，**工作量差 300 倍**，QPS 没有意义。
- **Response time**：等 p95 飙升才扩容已经太晚——GPU 模型加载 + 预热要 1-3 分钟，用户此时在疯狂超时。

#### LLM 专属伸缩指标

参考 vLLM Production Stack 的经验指标（来自 Prometheus `/metrics` endpoint）：

| 指标 | 语义 | 触发扩容阈值（经验值） |
|------|------|----------------------|
| `vllm:num_requests_waiting` | 当前排队中的请求数 | > 5 持续 30s |
| `vllm:gpu_cache_usage_perc` | KV Cache 占用率 | > 80% 持续 1min |
| `vllm:time_to_first_token_seconds` (p95) | 首 token 延迟 p95 | > SLA 阈值持续 1min |
| `vllm:time_per_output_token_seconds` (p95) | token 间隔 p95 | > SLA 阈值持续 1min |

**K8s 做法**：用 **KEDA** + Prometheus Scaler（或 K8s HPA + custom metrics）。vLLM Production Stack 的 Roadmap 里的首要项就是"Autoscaling based on vLLM-specific metrics"——说明这个动作业内仍在持续收敛。

#### 冷启动优化

70B 模型从 S3/OSS 冷启动到可服务，典型耗时：

```
Pod 调度 + 镜像拉取           30-120s
模型权重下载 (~140GB INT8)    60-300s（网络带宽瓶颈）
模型加载到 GPU 显存            30-60s
Warm up + JIT 编译            10-30s
————————————————————————————————
总计                          2-8 分钟
```

**优化三板斧**：
1. **Warm Pool**：预留 1-2 个空跑副本，扩容时直接接流量（代价是这部分钱白烧，但 SLA 可控）。
2. **模型权重本地化**：从对象存储拉到节点 local NVMe / PV，K8s 用 `InitContainer` + Local PV；或用 **RunAI / JuiceFS**。
3. **镜像瘦身**：把模型权重**不要**打进镜像（那样每次 pull 都要重新拉），镜像只含代码；权重挂 PV。

#### 请求排队 vs GPU 扩容的选择

短期突发（秒-分钟级）→ **排队**（Continuous Batching 会自己吃掉）
中期增长（分钟-小时级）→ **扩容**（KEDA 按 KV 使用率伸缩）
日级规律（白天高、夜晚低）→ **定时伸缩**（CronHPA，白天 N 个、夜晚 N/3 个）

**不要**遇到任何队列都立刻扩容——GPU 扩容成本远高于让 Continuous Batching 吞掉突发。

---

### 3. 多模型编排

生产 LLM 服务几乎不可能只跑一个模型。典型编排需求：

1. **按任务能力路由**：简单问答 → 小模型（省钱）；代码生成 → 专业代码模型；多模态 → 有视觉的模型。
2. **按长度路由**：短输入 → 快模型；超长上下文（>32k） → 长上下文专用模型。
3. **A/B 测试**：新模型 10% 流量，老模型 90%；一周后比较指标。
4. **Canary 发布**：先内部员工 1% → 扩到 10% → 全量。
5. **失败降级**：主模型（比如 GPT-4）失败 → 自动转到 fallback（Claude / 本地 Qwen）。

#### 主流路由方案对比

| 方案 | 部署形态 | 路由能力 | 适用阶段 |
|------|---------|---------|---------|
| **LiteLLM Proxy** | Python / Docker | 按 model 名路由、fallback、retry、rate limit、token budget | 大多数团队的首选 |
| **Portkey** | SaaS / 自托管 | 同上 + 更强的可观测性 UI | 不想自己搭 UI 的团队 |
| **Kong AI Gateway** | Gateway 插件 | 需要已有 Kong 部署 | 企业已有 API Gateway |
| **Cloudflare AI Gateway** | 全托管 | 零运维 + 缓存 | 简单场景、快速上线 |
| **自研 Envoy + Wasm filter** | — | 极限灵活 | 超大厂 / 特殊需求 |

#### LiteLLM 为什么成了事实标准

- **统一接口**：所有模型（OpenAI / Anthropic / Gemini / vLLM / Ollama / Bedrock / Azure / DeepSeek / Qwen / 智谱）通过**同一个 OpenAI 兼容 API** 调用。
- **内置能力**：模型列表 + API key 轮换 + fallback + retry + rate limit + token budget + cost tracking。
- **无侵入**：应用代码改一行 base_url 即可。

缺点：Python + YAML 配置，不是**原生高性能网关**（单实例 1-3k QPS 天花板，对 LLM 完全够，但纯转发不适合）。

#### A/B 与 Canary 的数据面差异

- **A/B**：路由层按 `user_id % 100 < 10` 分流，**两个流量都是生产**，重在比较指标（质量 / 成本 / 延迟）。
- **Canary**：路由层按 version 灰度，**旧版本是主力、新版本是验证**，重在发现问题就立刻回滚。

两者都**必须同时记录 prompt / response 到 Langfuse**，否则做不了事后离线对比。

---

### 4. 可观测性：OTel / Langfuse / Phoenix

#### OpenTelemetry GenAI Semantic Conventions

> 状态：**Development**（v1.40.0，未 stable）。但 Langfuse / Traceloop OpenLLMetry / Arize Phoenix / Google Cloud Trace / Azure Monitor 都已对齐。**新项目一律对齐 OTel**。

核心命名约定（节选）：

```
// Span 名称
gen_ai.{system}.{operation}   // 例：gen_ai.openai.chat

// 核心 attributes
gen_ai.system            = "openai" | "anthropic" | "vllm" | ...
gen_ai.request.model     = "gpt-4o" | "claude-sonnet-4.5" | ...
gen_ai.operation.name    = "chat" | "text_completion" | "embeddings"
gen_ai.usage.input_tokens
gen_ai.usage.output_tokens
gen_ai.response.finish_reasons = ["stop"|"length"|"tool_calls"|...]

// 核心 metrics
gen_ai.client.token.usage        // Histogram，按 model/type 聚合
gen_ai.client.operation.duration // Histogram（E2E 延迟）
gen_ai.server.time_to_first_token
gen_ai.server.time_per_output_token
```

> 📌 **2026 迁移提示**：旧 SDK 在 v1.36.0 之前用的命名会保留兼容性，通过 `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` 环境变量启用新版。

#### 工具选型三选一

| 工具 | 核心价值 | 不适合 |
|------|---------|-------|
| **Langfuse** | LLM 应用全生命周期（trace + prompt mgmt + eval + dataset），OSS 社区最大 | 纯推理引擎层 metrics（用 Prometheus + Grafana） |
| **Arize Phoenix** | 评估能力最强（注释、RAG 评估、Drift 检测），开源免费 | Prompt 管理偏弱 |
| **Traceloop OpenLLMetry** | 纯 OTel SDK，最轻量，可对接任何后端 | 自己不做 UI，需要搭配 Grafana/Jaeger |

**推荐组合**：
- **引擎层**：Prometheus + Grafana（vLLM 原生 `/metrics`）
- **应用层**：Langfuse（trace / prompt / eval）或 Traceloop + Jaeger（如果公司已有 OTel 基建）
- **两层打通**：通过 `trace_id` 贯穿——网关入口生成 trace_id，引擎日志、应用 trace 都带上，Grafana/Langfuse 双向跳转。

#### 必监控的 15 个指标清单

```
延迟层（按 p50/p95/p99）
├─ gen_ai.server.time_to_first_token
├─ gen_ai.server.time_per_output_token
├─ gen_ai.client.operation.duration (E2E)
└─ queue_wait_time

吞吐层
├─ requests_per_second
├─ output_tokens_per_second (TPS)
└─ concurrent_running_requests

资源层
├─ gpu_utilization
├─ gpu_memory_used
├─ kv_cache_usage_perc
└─ num_requests_waiting

质量层
├─ error_rate (5xx / tool-call-fail / schema-invalid)
├─ token_budget_exceeded_rate
└─ prompt_cache_hit_rate

成本层
└─ cost_per_request / cost_per_user（按 tag 聚合）
```

---

### 5. 成本治理

> 核心命题：LLM 账单不是"用多少花多少"——**运维策略的差距可以让同样 QPS 的账单差 3-10 倍**。

#### 三把刀

**① Prompt Caching（原生，免费）**

2024-2025 各家陆续上线，**不改代码自动生效**（Anthropic 需要 `cache_control` 标记）。典型节省：

| 厂商 | 机制 | 命中折扣 | 触发条件 |
|------|------|---------|---------|
| OpenAI | 自动 KV 缓存 | 50% off input | ≥ 1024 tokens 相同前缀 |
| Anthropic | `cache_control: ephemeral` | 90% off input（读取时） | 手动标记、5 分钟 TTL |
| Gemini | Context Caching | ~75% off | 显式创建 cache 对象 |
| DeepSeek | Hard-Cache（磁盘级） | 90%+ off | 自动，无 TTL 限制 |

**工程落地要点**：
- **长 system prompt / few-shot 放前面**（缓存只命中**共同前缀**）
- **动态内容放后面**（用户问题、时间戳）
- 监控 `prompt_cache_hit_rate`——低于 50% 说明结构写错了

**② 语义缓存（需搭建，呼应 [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)）**

Prompt Caching 只命中**字面完全一致**的前缀。用户问"北京天气怎么样？"和"北京今天天气？"命中不了。语义缓存补这个空缺：

```
用户 query → embedding → ANN 检索缓存库 → 相似度 > 0.92 → 直接返回旧答案
                                        → 否则 → 调 LLM → 写入缓存
```

工具箱：
- **GPTCache**（开源，Python 最轻量）
- **Redis LangCache**（Redis 官方 module，生产级）
- **Portkey Cache**（SaaS，免运维）

**命中率典型**：客服 FAQ 类 30-60%；通用 Chat 5-15%；代码生成场景 < 5%（不建议用）。

> ⚠️ **一致性陷阱**：语义缓存会让"时效性问题"（如"今天股价"）回答永远是历史答案。必须在缓存键里纳入**业务上下文的时间切片**，或对实时类问题显式绕开缓存。

**③ 请求去重 + Token 预算**

- **前端去重**：防抖（debounce 500ms），用户点 5 次按钮只发 1 次。
- **网关去重**：相同 `(user_id, prompt_hash)` 5 秒内只放行一次（挡重放攻击和前端 bug）。
- **Token 预算**：
  - **单请求上限**：`max_tokens_input` / `max_tokens_output`
  - **单用户日限额**：`tokens_per_user_per_day`
  - **预算快达上限时降级**：自动路由到更便宜的模型
  - LiteLLM 内置 `max_budget` 每个 key / team / user 配额

**组合示例**：

```
场景：客服 SaaS，日均 100 万请求
→ Prompt Cache（system prompt 重复，命中 60%）: 省 40% input 费用
→ 语义缓存（FAQ 高频）: 再省 30% 总请求
→ 请求去重：再省 5%
综合：~50-60% 账单下降
```

---

### 6. SLA 设计

#### SLA 定义的三层

```
L1 · 可用性 (Availability)
  - 99.5% / 99.9% / 99.95%
  - 统计口径：5xx 错误率 / 健康探活

L2 · 延迟 (Latency)
  - TTFT p95 < 1s, E2E p99 < 30s
  - 按 endpoint 和 model 分别承诺

L3 · 质量 (Quality)
  - Schema 合规率（要求 JSON 输出的场景）
  - Tool call 成功率
  - 人工抽样 good-rate（呼应 [R15](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R15_Skill%E4%B8%8EAgent%E8%AF%84%E4%BC%B0%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) Eval 体系）
```

#### 兜底四件套

**① 重试**：指数退避 + 抖动

```python
max_retries = 3
backoff = [1, 3, 9]  # 秒
jitter = random.uniform(0, 1)
# 第 N 次重试间隔 = backoff[N] + jitter
```

⚠️ **LLM 重试的陷阱**：幂等性不保证（temperature > 0 每次不同），**流式响应已产生部分 token 再失败**时不要重试完整请求——要么从断点续流（要引擎支持），要么只在客户端报错。

**② 降级路由**：主模型失败 → fallback

```yaml
# LiteLLM 配置片段
model_list:
  - model_name: gpt-4-main
    litellm_params: { model: gpt-4o, api_key: ... }
  - model_name: gpt-4-fallback
    litellm_params: { model: claude-sonnet-4.5, api_key: ... }

router_settings:
  fallbacks:
    - gpt-4-main: [gpt-4-fallback]
```

**③ 限流**：按 token/s 而不是 req/s

传统 req/s 限流在 LLM 场景完全错配——一个用户发 1 个 req（16k tokens）可以把 GPU 打满；另一个发 100 个 req（每个 100 tokens）才吃掉 1% GPU。

正确做法：
- **按 input_tokens/s 限流**：保护 prefill GPU
- **按 output_tokens/s 限流**：保护 decode GPU
- **并发请求数限流**：保护 KV Cache 显存

所有主流网关（LiteLLM / Portkey / Kong AI）都原生支持。

**④ 熔断**：连续失败自动断主路线

```
窗口：30s
阈值：错误率 > 50% 或 连续失败 > 10
动作：主路线熔断 → 全部走 fallback 2 分钟 → 再试探恢复
```

推荐库：**Resilience4j**（JVM）/ **pybreaker**（Python）/ **Istio Envoy circuit-breaker**（平台级）。

#### 错误分类与处理

| 错误类型 | 典型场景 | 处理策略 |
|---------|---------|---------|
| **429 Rate Limited** | 上游模型限流 | 重试 + 切 fallback |
| **503 Service Unavailable** | 实例挂了 | 重试到其他实例 |
| **超时 (client/server)** | 长 prompt / 大模型慢 | 重试一次，仍超时则客户端报错 |
| **Context Length Exceeded** | 输入超限 | **不要重试**（重试也是错的），客户端应用层裁剪或拒绝 |
| **Content Filter / Safety** | 内容审核拦截 | **不要重试**，返回用户明确错误 |
| **Schema 不合规** | 结构化输出失败 | 自动重试 1-2 次（配合 Guardrails/Instructor 修正） |
| **Tool Call 失败** | 工具不存在 / 参数错 | 应用层处理，不是 Serving 层问题 |

---

## 🚀 上手实战轨道

### Hello World 1：vLLM 原生 metrics → Prometheus

vLLM 启动时自动暴露 `/metrics` endpoint（Prometheus 格式）。

```bash
# 启 vLLM（需已下载 Qwen2.5-7B-Instruct）
pip install "vllm==0.7.3"
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-7B-Instruct \
  --port 8000 \
  --gpu-memory-utilization 0.9

# 另一终端拉 metrics
curl http://localhost:8000/metrics | grep -E "vllm:(time_to_first|num_requests|gpu_cache)"
```

预期看到：

```
# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{le="0.1"} 5
vllm:time_to_first_token_seconds_bucket{le="0.5"} 23
# TYPE vllm:num_requests_waiting gauge
vllm:num_requests_waiting 0
# TYPE vllm:gpu_cache_usage_perc gauge
vllm:gpu_cache_usage_perc 0.15
```

Prometheus `scrape_config`：

```yaml
scrape_configs:
  - job_name: 'vllm'
    scrape_interval: 5s
    static_configs:
      - targets: ['vllm-svc:8000']
```

**下一步**：导入 [vLLM 官方 Grafana Dashboard](https://github.com/vllm-project/vllm/blob/main/examples/production_monitoring/grafana.json)（JSON 直接 import）。

---

### Hello World 2：LiteLLM 做模型路由 + fallback

```bash
pip install "litellm[proxy]==1.55.0"
```

`config.yaml`：

```yaml
model_list:
  - model_name: chat-main
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
  - model_name: chat-fallback
    litellm_params:
      model: anthropic/claude-3-5-haiku-latest
      api_key: os.environ/ANTHROPIC_API_KEY
  - model_name: local-qwen
    litellm_params:
      model: openai/Qwen/Qwen2.5-7B-Instruct
      api_base: http://vllm-svc:8000/v1
      api_key: dummy

router_settings:
  fallbacks:
    - chat-main: [chat-fallback, local-qwen]
  num_retries: 2
  timeout: 30

general_settings:
  max_budget: 100.0  # 全局月度预算 $100
```

启动 + 测试：

```bash
litellm --config config.yaml --port 4000

# 客户端代码跟调 OpenAI 完全一样
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chat-main",
    "messages": [{"role":"user","content":"Hello"}]
  }'
# 若 OpenAI 挂了，自动转 Claude；再挂走本地 Qwen
```

**验收**：故意把 `OPENAI_API_KEY` 改错 → 应用层无感切到 fallback。

---

### Hello World 3：Langfuse 一行接入 OpenAI 追踪

```bash
pip install "langfuse==2.60.0" openai
# 先在 Langfuse Cloud 或 self-host 拿到 3 个 key
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

```python
from langfuse.openai import openai  # <- 只改这一行 import

resp = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "讲个冷笑话"}],
    metadata={"user_id": "u_001", "feature": "joke"},  # 自定义 tag
)

# 打开 Langfuse UI，自动看到：
# - TTFT / E2E latency
# - input / output tokens
# - cost (自动按 model 算)
# - 完整 prompt/response 可点击查看
```

预期输出：UI 中出现一条 trace，latency / cost / tokens 全有。

**进阶**：添加用户反馈（👍/👎）、批量 dataset 回归测试、自定义 Eval。

---

### Hello World 4：语义缓存最小实现

```python
# pip install redis==5.0.8 openai sentence-transformers

import hashlib, json, numpy as np, redis
from openai import OpenAI
from sentence_transformers import SentenceTransformer

r = redis.Redis(decode_responses=False)
embedder = SentenceTransformer("BAAI/bge-small-zh-v1.5")
client = OpenAI()
THRESHOLD = 0.92

def semantic_cache_chat(query: str) -> str:
    q_vec = embedder.encode([query], normalize_embeddings=True)[0].astype(np.float32)

    # 简化版：全库扫描（生产用 Redis Search / pgvector / Milvus）
    for key in r.scan_iter(match="cache:*"):
        entry = json.loads(r.get(key))
        sim = float(np.dot(q_vec, np.array(entry["vec"], dtype=np.float32)))
        if sim >= THRESHOLD:
            print(f"[CACHE HIT sim={sim:.3f}]")
            return entry["answer"]

    # Miss → 调 LLM
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":query}]
    )
    answer = resp.choices[0].message.content

    key = "cache:" + hashlib.md5(query.encode()).hexdigest()
    r.set(key, json.dumps({"vec": q_vec.tolist(), "answer": answer}))
    return answer

print(semantic_cache_chat("北京天气怎么样？"))
print(semantic_cache_chat("北京今天天气如何？"))  # Expected: CACHE HIT
```

**生产建议**：
- 用 **Redis Search + HNSW 索引**做向量检索（`FT.SEARCH` 秒级百万级召回）
- 或直接用 **Redis LangCache module** / **GPTCache**
- 阈值 **≥ 0.92 起步**，低于此值误命中率快速上升

---

### 生产部署 Checklist

```
架构层
□ 引擎选型：对照 R58 决策树
□ 模型路由：LiteLLM or Portkey
□ K8s 编排：vLLM Production Stack or KServe
□ 存储：模型权重 PV / 对象存储 + 镜像瘦身

可观测层
□ vLLM /metrics → Prometheus → Grafana
□ 应用 trace → Langfuse / Phoenix
□ Trace_id 贯穿网关 / 引擎 / 应用三层
□ 15 大指标全开
□ OTel GenAI SemConv 对齐

伸缩层
□ KEDA + Prometheus Scaler（按 KV cache % 伸缩）
□ Warm Pool >= 1（冷启动防护）
□ CronHPA（白天晚上不同规模）

成本层
□ Prompt Caching 生效验证（hit_rate > 50%）
□ 语义缓存（如果适用场景）
□ 单用户 Token 配额
□ 预算告警（月度 / 日度两档）

SLA 层
□ 重试策略（指数退避 + 抖动）
□ 降级路由（主模型 → fallback）
□ 限流（按 token/s）
□ 熔断（错误率阈值）
□ 错误分类处理表

安全层（见 R57）
□ Prompt Injection 过滤（Llama Guard / Prompt Guard）
□ 工具权限白名单
□ 输出脱敏
□ API Key 轮换与审计
```

---

## 🕳️ 避坑指南

| 坑 | 原因 | 解法 |
|----|------|------|
| **按 req/s 限流** | 单请求 tokens 差 1000×，req/s 不反映真实负载 | 按 `input_tokens/s` + `output_tokens/s` + `concurrent_requests` 三维限流 |
| **按 CPU% 做 HPA** | GPU 是瓶颈，CPU 永远不会涨 | 用 KEDA + `vllm:gpu_cache_usage_perc` 或 `num_requests_waiting` |
| **告警用 average latency** | 重尾分布下均值无意义 | 全部用 p95 / p99 |
| **把模型权重打进镜像** | 每次 pull 都要重传几十 GB | 镜像只含代码，权重挂 PV / 对象存储 |
| **重试所有错误** | Context Length / 内容审核拦截重试也是错 | 分类：4xx 客户端错误**不重试**，5xx / 超时**重试** |
| **语义缓存阈值定太低** | 误命中（问"今天"返回"昨天"的答案） | 阈值 ≥ 0.92，且时效类问题显式绕开 |
| **Prompt Cache 命中率低** | 动态内容放前面了 | 长 system prompt / few-shot 放最前面，user query 放最后 |
| **没做 Warm Pool 大模型场景直接冷启动** | 70B 模型加载 2-8 分钟，用户全超时 | 至少保留 1 个 warm 副本 |
| **流式响应只计算 E2E latency** | 用户早在 TTFT 时就退出了 | TTFT 单独监控且按感官阈值告警（> 1s） |
| **只监控引擎层** | 应用层 prompt 构造错误看不到 | 两层都上（Prometheus + Langfuse），trace_id 贯穿 |
| **fallback 模型也挂怎么办没想** | 级联失败时没有最后保底 | 至少 3 级 fallback（主 → 备 → 本地小模型/静态文案） |
| **用旧 OTel 命名** | v1.36 前命名后来被废弃 | 新项目直接用 `gen_ai.*` v1.40 命名 |
| **Langfuse 没 self-host 把生产数据送到 SaaS** | 合规风险 | 敏感场景必须 self-host |

---

## 💰 成本与 ROI 速算

### 典型场景成本对照（月度）

**场景 A：内部研发助手（100 人团队，日均 2000 req/人）**

```
原始方案：裸调 GPT-4o
  200k req/day × $0.03 avg = $6000/day × 30 ≈ $180k/月 ❌ 破产

优化后：
  + Prompt Caching（system prompt 共享，命中 70%）    → -40% input cost
  + LiteLLM 按任务路由到 4o-mini                      → -60% 混合成本
  + 语义缓存（FAQ 命中 25%）                          → -25% 总请求
  + Token 预算（人均日 100k tokens 上限）             → 封顶控制
最终：~$30-40k/月，降本 78-83%
```

**场景 B：对外 SaaS（1 万 DAU，日均 5 req/人）**

```
5 万 req/day，混合场景（50% 问答、30% 代码、20% 长文档）
自建 vLLM（4×A100-80G）成本：
  硬件租赁 ~$3.5k/用户/月
  运维人力 0.5 FTE ≈ $5k/月
合计 ~$18-20k/月
相当于 $0.12 / req

对比直接调 OpenAI：
  50k × $0.02 avg = $1000/day × 30 = $30k/月
  $0.2 / req，贵 60%

结论：DAU > 8k 左右，自建开始划算；更小规模先用 API + 缓存
```

### 运维投入估算

| 规模阶段 | 工程投入 | 持续运维 |
|---------|---------|---------|
| **MVP（直接调 API）** | 1-2 人周（LiteLLM + Langfuse 接入） | 0.1 FTE |
| **中等（自建 + 混合）** | 1-2 人月（K8s + Prometheus + Langfuse） | 0.5 FTE |
| **大规模（多集群 + 全球化）** | 3-6 人月 | 2-3 FTE + 专职 SRE |

---

## 🎯 决策速查

```
你的场景 →

【DAU < 1000 或 POC 阶段】
  → 直接调 OpenAI/Anthropic/Gemini API
  + LiteLLM 路由 + fallback
  + Langfuse Cloud 免费版
  + Prompt Caching 自动生效
  不要自建、不要上 K8s

【DAU 1000-10000 或企业内部工具】
  → 混合：主力走 API + 本地跑小模型兜底/敏感数据
  + 自托管 Langfuse
  + 语义缓存（如果重复问题多）
  + KEDA autoscaling

【DAU > 10000 或合规要求高】
  → 自建 vLLM Production Stack on K8s
  + LiteLLM Proxy 做入口
  + Prometheus + Grafana + Langfuse 三件套
  + PD 分离（长文档场景）
  + 专职 SRE / LLMOps 团队

【对成本极度敏感】
  先接 Prompt Caching 和语义缓存，再谈自建
  （缓存给 40-60%，自建一次性省 10-30%，投入产出比不同）
```

---

## 结论与最佳实践

1. **别把 LLM 当普通微服务运维**——伸缩指标、延迟统计、限流单位、缓存策略**全部**要换思维。
2. **OTel GenAI + Langfuse/Phoenix + Prometheus 已形成事实标准栈**，新项目直接用，不要造观测轮子。
3. **成本 ≠ Token 单价**。运维策略差距可达 3-10 倍；在架构阶段就把 Prompt Caching / 语义缓存 / 限额设计进去。
4. **SLA 必须分 TTFT / E2E / 质量三层承诺**，并按 p95/p99 而非 avg 统计。
5. **四件兜底（重试 / 降级 / 限流 / 熔断）不是可选项**——生产 LLM 服务一定会失败，决定差距的是失败后的用户体验。
6. **开源三件套成熟度足够**：LiteLLM（路由）+ vLLM Production Stack（编排）+ Langfuse（观测）。中等以下规模团队完全不必自研。
7. **不自建引擎也要监控**：调 OpenAI/Claude API 的团队同样需要 Langfuse 层面的观测和 LiteLLM 层面的成本/限流治理。

---

## 开放问题与后续计划

- 🟡 **PD 分离（Prefill/Decode 分离部署）** 的运维模式（SGLang、DistServe、vLLM PD 版本）成本与延迟 tradeoff 真实数据，值得单独一篇实验验证报告
- 🟡 **多租户隔离**：K8s namespace vs 模型实例 vs 调度优先级的 tradeoff，企业私有云场景如何设计
- 🟡 **LLMOps 组织形态**：谁该负责 LLM 服务？SRE / ML Infra / 应用团队？职责边界在哪
- ⬜ **Agent 场景的特殊运维**：工具调用失败、多轮会话、长期记忆的监控体系（与 [R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) 结合的深度议题）
- ⬜ **跨区域部署与合规**：数据主权、同一个模型在不同 region 提供服务的路由策略

---

## 📌 来源清单

- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 2026-04-24 访问 — v1.40.0 Development，定义了 `gen_ai.*` 命名空间、GenAI metrics/spans/events/agent-spans
- [vLLM Production Stack](https://github.com/vllm-project/production-stack) — 2.3k stars，2026-04-24 访问 — K8s-native vLLM 集群部署参考，Helm / Prometheus / Grafana / Router / LMCache 全栈
- [vLLM Metrics 文档](https://docs.vllm.ai/en/latest/serving/metrics.html) — 引擎内部 Prometheus 指标规范（`vllm:time_to_first_token_seconds` 等）
- [Langfuse Docs](https://langfuse.com/docs) — 2026-04-24 访问 — OSS LLM 可观测性事实标准，原生 OpenTelemetry
- [LiteLLM Docs](https://docs.litellm.ai/) — 2026-04-24 访问 — Proxy + Router + Budget + Fallback
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — OSS LLM 观测 + Eval
- [Traceloop OpenLLMetry](https://github.com/traceloop/openllmetry) — OTel GenAI instrumentation 最早期实现
- [NVIDIA GenAI-Perf](https://github.com/triton-inference-server/perf_analyzer/tree/main/genai-perf) — 官方 LLM 压测工具
- [KEDA](https://keda.sh/) — K8s event-driven autoscaling，支持 Prometheus scaler
- Anthropic / OpenAI / Gemini / DeepSeek 官方文档 — Prompt Caching 各家机制与定价

**⚖️ 来源一致性**：OTel 命名、vLLM 指标名、Langfuse 能力三大块信息来自官方文档，多源交叉一致，高置信。
**📅 时效性声明**：信息获取于 **2026-04-24**；OTel GenAI SemConv 仍在演进（当前 Development 状态），半年后可能有命名收敛。
**📝 与模型训练语料差异**：本报告中 2025-2026 的工具版本号、`vllm-project/production-stack` 项目存在性、OTel v1.40 命名规范等以当次联网获取信息为准；早期训练语料中这些内容可能不存在或命名不同。

---

> **交付后续（Forge 审视）**：
> - 本报告涌现的新范式候选：**"LLM Serving Ops 三层心智模型"**（引擎层 / 路由层 / 应用层，每层独立监控但 trace_id 贯穿）——建议在 KNOWLEDGE_INDEX §三 核心范式中增添一行。
> - 候选产物：**"LLM 生产部署 Checklist"**（本报告"生产部署 Checklist"小节）未来若被跨 3 个以上项目复用，可固化为 `wiki/templates/` 下模板；当前先留在报告内，不强行固化。
> - 未产生需要独立登记的代码产出；Hello World 4 片段若演化为完整示例，可移到 `experiments/single/E{NN}_semantic_cache.py`。
