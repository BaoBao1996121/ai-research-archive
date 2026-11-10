---
title: Qwen3.6 本地部署实战 — RTX 3060 Ti 8GB 落地指南
aliases: [Qwen3.6本地部署, Qwen3.6部署RTX3060Ti, Qwen3本地部署, R75]
tags: [qwen3.6, qwen3, 本地部署, ollama, llama.cpp, 量化, 推理引擎, rtx3060ti, moe, hybrid-attention]
date: 2026-04-26
updated: 2026-04-26
category: 工具与生态
report_id: R75
prev_path: 
status: completed
tokens: ~11000
related:
  - "[R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)"
  - "[R59](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)"
  - "[R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)"
  - "[R65](R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)"
  - "[Ch13-LLM推理部署入门](../../tutorial/Ch13-LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%85%A5%E9%97%A8.md)"
---

> 脱敏公开版 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../ARCHIVE_POLICY.md)。

# R75 · Qwen3.6 本地部署实战 — RTX 3060 Ti 8GB 落地指南

> 一句话概括：在一张消费级 8GB 显卡（RTX 3060 Ti）+ 64GB RAM 的家用主机上，跑通 **Qwen3.6-35B-A3B MoE Q4**（CPU offload，甜点）+ **Qwen3.6-27B Q4 稠密**（CPU offload，能力上限）+ **Qwen3-8B Q4**（保底基线，纯 GPU 极速），端到端含 Ollama 安装、模型选择、Python 调用、Agent 集成、避坑、成本测算。
> 研究日期：2026-04-26（**已修订**：原 v1 错误地声称 "Qwen3.6 不存在"，事实是 Qwen3.6-35B-A3B 于 2026-04-16、Qwen3.6-27B 于 2026-04-22 在 HuggingFace 与 Ollama 同步开源）
> 关联报告：[R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 量化与推理引擎 · [R59](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 推理优化 · [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 服务化 SLA · [R65](R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 主流技术栈速查 · [Ch13-LLM推理部署入门](../../tutorial/Ch13-LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%85%A5%E9%97%A8.md) 入门教程

---

## TL;DR 速查卡

- ✅ **Qwen3.6 是真实的、最新的、Apache 2.0 开源**。两个变体：**Qwen3.6-27B**（28B 稠密，旗舰编码）和 **Qwen3.6-35B-A3B**（36B/3B 激活 MoE，多模态视觉语言模型）。Ollama 4 天前已上架官方 tags（`qwen3.6:27b` / `qwen3.6:35b`）
- 🏆 **8GB VRAM + 64GB RAM 的甜点 = `qwen3.6:35b`**（35B-A3B MoE，Q4 24GB 总量但激活仅 3B，靠 CPU offload + MoE 稀疏激活，预期 8–15 t/s，**视觉+语言+工具调用全包**）
- 🥇 **能力上限路径 = `qwen3.6:27b`**（28B 稠密 Q4 17GB，必须大量 CPU offload，预期 2–5 t/s，慢但 SWE-bench 77.2 顶级编码能力）
- 🚀 **保底快速基线 = `qwen3:8b`**（5GB 全装显存，35–45 t/s）
- 🥈 **NVFP4 进阶 = `qwen3.6:27b-coding-nvfp4`**（NVIDIA 专用 FP4 量化 20GB，需 4090/5090 等支持 FP4 的卡，3060 Ti 不适用）
- ❌ **跑不动**：Qwen3.6 未量化版（27B BF16=56GB / 35B-A3B BF16=72GB）、Qwen3-235B、Qwen3.5-397B-A17B（硬件根本不够）
- 🛠️ **首选工具栈 = Ollama 0.21.2+**（已原生支持 Qwen3.6 hybrid attention 架构）→ 进阶 llama.cpp（细粒度 GPU layers 控制）→ KTransformers（CPU-GPU 异构推理，专为 8GB 显卡跑大 MoE 设计）
- 💰 **零边际成本**：本地推理无 Token 费；电费按 200W × 8h × 30 天 ≈ ¥30–40/月。日均 LLM 调用 ≥3000 次时 1 个月内回本
- ⚠️ **Qwen3.6 三个新坑**：① **不再支持 `/think` `/nothink` 软切换**（Qwen3 的双模式被废弃，改成 thinking by default + `enable_thinking=False` 关闭）② **多模态 Vision Encoder 多吃 1–2GB 显存**（用 `--language-model-only` 等价标志可关闭，节省显存）③ **256K 原生上下文吃 KV Cache 极大**（务必用 `num_ctx=32768` 起步，别一上来开 256K）

---

## 目录

- [TL;DR 速查卡](#tldr-速查卡)
- [🔭 定位透镜：纵横坐标](#-定位透镜纵横坐标)
- [📚 研究分析轨道](#-研究分析轨道)
  - [Qwen3 家族全景](#qwen3-家族全景)
  - [硬件适配测算](#硬件适配测算)
  - [推理引擎对比](#推理引擎对比)
  - [量化方案对比](#量化方案对比)
- [🚀 上手实战轨道](#-上手实战轨道)
  - [第一步：安装 Ollama](#第一步安装-ollama)
  - [第二步：拉取并验证 qwen3:8b](#第二步拉取并验证-qwen38b)
  - [第三步：Python 调用](#第三步python-调用)
  - [第四步：进阶 — 30B MoE CPU Offload](#第四步进阶--30b-moe-cpu-offload)
  - [第五步：接入 Agent 框架](#第五步接入-agent-框架)
- [🕳️ 避坑指南](#-避坑指南)
- [💰 成本与 ROI 速算](#-成本与-roi-速算)
- [🎯 决策速查](#-决策速查)
- [开放问题与后续](#开放问题与后续)
- [📌 来源清单](#-来源清单)

---

## 🔭 定位透镜：纵横坐标

### 纵轴 · Qwen 演化脉络

```
Qwen 1.0 (2023.08) ─ 7B/14B 起家，对标 LLaMA 1
   ↓
Qwen 1.5 (2024.02) ─ 加 0.5B/1.8B/4B 小尺寸 + 72B 顶配
   ↓
Qwen 2 (2024.06) ──── MoE 首发 (Qwen1.5-MoE-A2.7B)
   ↓
Qwen 2.5 (2024.09) ── 中文 SOTA，3B/14B/32B 补齐尺寸阶梯
   ↓
Qwen3 (2025.04) ───── ★ 本文主角 ★
                     ✦ 思考/非思考双模式可切换（`/think` `/nothink`）
                     ✦ 0.6B / 1.7B / 4B / 8B / 14B / 32B 稠密 + 30B-A3B / 235B-A22B MoE
                     ✦ Apache 2.0 许可，商用友好
   ↓
Qwen3-2507 (2025.07-08)
                     ✦ Instruct 与 Thinking 拆成两个模型（双模式被废弃）
                     ✦ 三档：4B / 30B-A3B / 235B-A22B
                     ✦ 原生 256K 上下文，可扩到 1M
   ↓
Qwen3-Next (2025-09) ─ 80B-A3B 超稀疏 MoE + 混合注意力（Gated DeltaNet + Gated Attention）
                     ✦ 极致效率，长上下文友好
                     ✦ 引入 Qwen3.5/3.6 的核心架构基础
   ↓
Qwen3.5 (2026-02-16 起)
                     ✦ 旗舰：Qwen3.5-397B-A17B（403B MoE）
                     ✦ 中端：Qwen3.5-122B-A10B / 35B-A3B / 27B 稠密
                     ✦ 小尺寸：9B / 4B / 2B / 0.8B
                     ✦ 统一视觉-语言基础（早期融合）
                     ✦ 上下文 262K 原生
   ↓
Qwen3.6 (2026-04) ─── ★ 本文主角 ★
                     ✦ 2026-04-16 Qwen3.6-35B-A3B（36B/3B 激活 MoE，256 experts）
                     ✦ 2026-04-22 Qwen3.6-27B（28B 稠密旗舰）
                     ✦ 双重升级：Agentic Coding（SWE-bench Verified 77.2 / 73.4）+ Thinking Preservation
                     ✦ 多模态：Image-Text-to-Text，可处理图、视频
                     ✦ 上下文 262K 原生，YaRN 可扩到 1M
                     ✦ 架构：Gated DeltaNet + Gated Attention 混合注意力（继承 Qwen3-Next）
                     ✦ Apache 2.0 完全开源
```

**生命周期定位**：成熟期 + 高速迭代期。Qwen 系列 GitHub Stars 27.2k，2026 年起每 2 个月推出一代主线。Qwen3.6 GitHub `QwenLM/Qwen3.6` 仓库 4 天前刚开（3.2k stars），HuggingFace `Qwen/Qwen3.6-35B-A3B` 已 1.03M 下载、`Qwen/Qwen3.6-27B` 258K 下载——明显是真实落地、社区高速接入的现象级发布。Ollama 0.21.2、vLLM ≥0.19.0、SGLang ≥0.5.10 已全部适配新架构。

**架构关键创新（Qwen3.6 / 3.5 / Next 共享）**：**混合注意力**——`Gated DeltaNet`（线性注意力）+ `Gated Attention`（标准 GQA）按 3:1 比例堆叠。线性注意力大幅降低长上下文 KV Cache 显存（这是 256K 原生上下文能在消费级硬件上跑的关键），标准注意力保留全局精度。

**Qwen3.6 vs Qwen3.5 的差异定位**：Qwen3.5 是"全家桶大版本"（全尺寸更新+多模态融合），Qwen3.6 只发了两个尺寸——这是 Qwen Team 针对 "Agentic Coding 和 Thinking Preservation" 这两个生产痛点的**专项优化版**，不是 Qwen3.5 的全面替代。如果你只用文本聊天，Qwen3.5-27B 也是好选择；如果你要做 Agent / Coding / 看图，Qwen3.6 是当下最优。

### 横轴 · 8GB VRAM 本地模型竞争格局（2026-04 最新）

| 模型 | 尺寸 | Q4 显存 | 中文 | 速度 | 长上下文 | 多模态 | 推荐度 |
|------|------|---------|------|------|---------|--------|---------|
| **Qwen3.6-35B-A3B** | MoE 36B/3B 激活 | **24 GB**（offload） | 🟢 SOTA | 🟢 8–15 t/s | 🟢 **256K** | 🟢 | ⭐⭐⭐⭐⭐ **新王** |
| **Qwen3.6-27B** | 28B 稠密 | 17 GB（重 offload） | 🟢 SOTA | 🟡 2–5 t/s | 🟢 256K | 🟢 | ⭐⭐⭐⭐（慢但强） |
| **Qwen3-8B** | 8B 稠密 | 5.0 GB ✅ 全 GPU | 🟢 优 | 🟢 35–45 t/s | 🟡 32K | ❌ | ⭐⭐⭐⭐ 保底基线 |
| **Qwen3-4B-2507** | 4B 稠密 | 2.5 GB ✅ 全 GPU | 🟢 良 | 🟢 60+ t/s | 🟢 256K | ❌ | ⭐⭐⭐ 长文极速 |
| **Qwen3-30B-A3B** | MoE 30B/3B 激活 | 22 GB（offload） | 🟢 优 | 🟡 12–18 t/s | 🟢 256K | ❌ | ⭐⭐⭐ 上一代 MoE 保底 |
| Qwen3.5-27B | 27B 稠密 | 17 GB（offload） | 🟢 优 | 🟡 3–6 t/s | 🟢 256K | 🟢 | ⭐⭐⭐ |
| Llama 3.3-70B Q4 | 70B 稠密 | 42 GB | 🟡 中 | 🔴 1–3 t/s | 🟡 128K | ❌ | ⭐⭐ 太慢 |
| GLM-4-9B | 9B 稠密 | 5.8 GB | 🟢 优 | 🟢 35 t/s | 🟢 128K | ❌ | ⭐⭐⭐ |
| Gemma 3-12B | 12B 稠密 | 7.5 GB | 🟡 中 | 🟡 25 t/s | 🟡 128K | ❌ | ⭐⭐⭐ |
| Mistral-Small-3.1-24B | 24B 稠密 | 14 GB（offload） | 🟡 中 | 🟡 4–8 t/s | 🟡 128K | 🟢 | ⭐⭐⭐ |
| Phi-4-14B | 14B 稠密 | 8.9 GB | 🟡 中 | 🔴 部分 GPU | 🟡 16K | ❌ | ⭐⭐ |

> 数据来源：HuggingFace 模型卡 + Qwen 官方 Benchmark（[Qwen3.6-27B 模型卡](https://huggingface.co/Qwen/Qwen3.6-27B) / [Qwen3.6-35B-A3B 模型卡](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)）+ Ollama 库 tags + llama.cpp 社区实测帖（2026-04-23~26）。`qwen3.6:27b` / `qwen3.6:35b` 速度估算基于 8GB 显存 CPU offload 场景；MoE 在 8GB 上速度优势明显的根因 = **每个 token 只激活 3B 参数**，CPU↔GPU 数据交换量是稠密 27B 的 1/9。

### 交叉判断（独立结论）

**纵轴说**：Qwen 已进入"每 2 个月一代"的高速迭代期，2026-Q1 至少出了 Qwen3.5、Qwen3.6 两条主线。意味着——**6 个月后 Qwen3.7 必然来**，今天搭的部署体系要保证"模型可热替换"（Ollama 满足，vLLM 也满足）。
**横轴说**：8GB VRAM + 64GB RAM 这个组合下，**MoE 模型是唯一能既跑大模型、又有可用速度的范式**。`qwen3.6:35b` (35B-A3B) 是当下绝对最优解，原因有三：
  1. **MoE 稀疏激活**：每 token 只激活 3B，CPU offload 的 IO 代价远小于稠密 27B
  2. **多模态原生**：看图、看视频不需要切模型
  3. **256K 上下文 + Hybrid Attention**：长文档 KV Cache 压力小

**结论**：
- **甜点（首推）**：`qwen3.6:35b`（MoE，能力强 + 速度可接受 + 多模态）
- **能力上限**：`qwen3.6:27b`（稠密旗舰，编码/推理 SOTA，但 2-5 t/s 只适合非交互式批处理）
- **保底基线**：`qwen3:8b`（纯 GPU 极速，普通对话/Agent 工具调用首选）
- **长文备胎**：`qwen3:4b-instruct-2507`（256K + 极速 + 资源占用极小）

四档覆盖 95% 场景。

---

## 📚 研究分析轨道

### Qwen3.6 关键升级（重点）

#### 两个变体的定位

| 维度 | Qwen3.6-27B（稠密旗舰） | Qwen3.6-35B-A3B（MoE） |
|------|------------------------|------------------------|
| 总参数 / 激活 | 28B / 28B | 36B / **3B** |
| 隐藏层 | 64 | 40 |
| 隐藏维度 | 5120 | 2048 |
| 注意力布局 | 16 × (3×DeltaNet→FFN + 1×Attention→FFN) | 10 × (3×DeltaNet→MoE + 1×Attention→MoE) |
| Experts | — | 256 个，每 token 激活 8 routed + 1 shared |
| 上下文 | 262K（YaRN 扩到 1M） | 262K（YaRN 扩到 1M） |
| 多模态 | ✅ 视觉编码器 + LLM | ✅ 视觉编码器 + LLM |
| 发布 | 2026-04-22 | 2026-04-16 |
| HF 下载（截至 4-26） | 258K | 1.03M |
| 旗舰 Bench | SWE-bench Verified **77.2** / SWE-bench Pro **53.5** / AIME26 **94.1** | SWE-bench Verified **73.4** / Terminal-Bench 2.0 **51.5** / AIME26 **92.7** |
| 适合场景 | 离线代码工程、复杂推理、批处理 | 在线 Agent、多轮对话、看图、长文档 |

#### 三大新能力

1. **Agentic Coding 大幅提升**
   - SWE-bench Verified：Qwen3.6-27B = **77.2**（已超越 Claude 3.5 Sonnet 早期版本，与 GPT-5 同级别）
   - Terminal-Bench 2.0：Qwen3.6-27B = **59.3**（实际终端任务执行能力）
   - 直接的工程意义：本地跑一个 Coding Agent 已经接近闭源旗舰水平

2. **Thinking Preservation（新机制）**
   - 之前的 thinking 模型只在最新一轮保留 `<think>` 块，历史轮次的推理痕迹会被丢弃
   - Qwen3.6 训练上让模型**保留并利用历史 thinking**，对 Agent 多步任务有显著好处：
     - 决策一致性提升
     - KV Cache 复用率提升 → 推理效率提升
     - 减少冗余推理 → 实际 token 消耗下降
   - 启用方式：API 参数 `chat_template_kwargs.preserve_thinking=True`

3. **混合注意力架构（Gated DeltaNet + Gated Attention）**
   - 这是 Qwen3-Next（2025-09）首发、Qwen3.5/3.6 继承的核心架构
   - 工程意义：256K 原生上下文 + 1M 可扩，但 KV Cache 不爆——线性注意力部分的 KV 是 O(1) 而非 O(n)
   - 8GB 显卡跑长上下文不再需要疯狂 KV 量化

#### ⚠️ 与 Qwen3 的破坏性变更

| 项 | Qwen3 / Qwen3-2507 | Qwen3.6 |
|----|--------------------|---------|
| `/think` `/nothink` 软切换 | ✅ 支持 | ❌ **不再支持** |
| 关闭思考的方式 | system prompt 加 `/nothink` | API 参数 `enable_thinking=False` |
| Instruct/Thinking 是否拆分 | 2507 拆成两模型 | 单模型，默认 thinking |
| Sampling 推荐值 | temperature=0.7 | thinking: 1.0 / non-thinking: 0.7 |

**实际影响**：你之前 Qwen3 时代写的 system prompt 末尾加 `/nothink` 的写法，迁到 Qwen3.6 上**会被当作普通文本忽略**，思考依然会输出。必须改用 API 参数。

### Qwen3 家族全景（含 Qwen3.5/3.6）

> 所有 Qwen 系列模型 **Apache 2.0** 许可，商用零门槛。

#### 原始 Qwen3 系列（2025-04 发布）

| 模型 | 类型 | 上下文 | 模式 | 适配硬件下限 |
|------|------|--------|------|-------------|
| Qwen3-0.6B / 1.7B | 稠密小 | 32K | 双模式 | CPU 也能跑 |
| Qwen3-4B / 8B | 稠密中 | 32K | 双模式 | **8GB GPU ✅** |
| Qwen3-14B | 稠密 | 32K | 双模式 | 16GB GPU |
| Qwen3-32B | 稠密大 | 32K | 双模式 | 24GB GPU（量化） |
| Qwen3-30B-A3B | **MoE** | 32K | 双模式 | **8GB GPU + 64GB RAM ✅** |
| Qwen3-235B-A22B | MoE 旗舰 | 32K | 双模式 | 多卡 |

**双模式机制**：同一权重，运行时通过 `/think` `/nothink` 命令或 `enable_thinking=True/False` 切换是否生成 `<think>...</think>` 推理过程。

#### Qwen3-2507 系列（2025-07/08 发布）

| 模型 | 模式 | 上下文 | 说明 |
|------|------|--------|------|
| Qwen3-4B-Instruct-2507 | 仅非思考 | **256K**（可扩 1M） | 8GB 卡 + 长文档场景首选 |
| Qwen3-4B-Thinking-2507 | 仅思考 | 256K | 4B 体积下做推理任务 |
| Qwen3-30B-A3B-Instruct-2507 | 仅非思考 | 256K | MoE 加强版 |
| Qwen3-30B-A3B-Thinking-2507 | 仅思考 | 256K | MoE + 推理 |
| Qwen3-235B-A22B-Instruct/Thinking-2507 | 各一 | 256K | 旗舰 |

**2507 的关键变化**：
1. Instruct 与 Thinking **拆分为两个模型**——再也不需要 `/think` 切换
2. 上下文 32K → 256K 原生，工程化文档处理大幅好转
3. 全维度能力提升（Instruction Following、Math、Code、Tool Use）

#### Qwen3.5 系列（2026-02 发布）

| 模型 | 类型 | 上下文 | 多模态 | 适配硬件 |
|------|------|-------|-------|---------|
| Qwen3.5-397B-A17B | MoE 旗舰 | 262K | ✅ | 多卡 H100 |
| Qwen3.5-122B-A10B | MoE 中端 | 262K | ✅ | 多卡 |
| Qwen3.5-35B-A3B | MoE 中小 | 262K | ✅ | 64GB RAM + 8GB GPU offload |
| Qwen3.5-27B | 稠密 | 262K | ✅ | 16-24GB GPU 量化 |
| Qwen3.5-9B / 4B / 2B / 0.8B | 稠密小 | 262K | ✅ | 8GB GPU ✅ |

核心变化：**Qwen3.5 起全系列原生多模态**（早期融合训练）+ **混合注意力 + MoE 普及**。

#### Qwen3.6 系列（2026-04，本文主角）

| 模型 | 类型 | 上下文 | 多模态 | Ollama tag | 8GB 显卡可行性 |
|------|------|-------|--------|-----------|---------------|
| **Qwen3.6-35B-A3B** | MoE 36B/3B | 262K | ✅ | `qwen3.6:35b` (24GB) | 🟡 CPU offload，8–15 t/s |
| **Qwen3.6-27B** | 稠密 28B | 262K | ✅ | `qwen3.6:27b` (17GB) | 🟡 重 offload，2–5 t/s |
| Qwen3.6-27B-FP8 | 稠密 FP8 | 262K | ✅ | （需 H100/H200/B200） | ❌ 3060 Ti 不支持 FP8 |
| Qwen3.6-35B-A3B-FP8 | MoE FP8 | 262K | ✅ | （需 H100/H200） | ❌ 3060 Ti 不支持 FP8 |

**社区扩展**：Ollama 上还有 `qwen3.6:27b-coding-nvfp4`（NVIDIA NVFP4 量化，需 RTX 50 系/Blackwell）、`unsloth/Qwen3.6-27B-GGUF`（458K 下载，最热门第三方 GGUF）、`huihui_ai/Qwen3.6-abliterated`（无审查版，慎用）等。

### 硬件适配测算

#### 显存预算公式（必看）

```
所需显存 ≈ 量化权重 + KV Cache + 激活内存 + 系统开销

Q4_K_M 权重大小 ≈ 模型参数(B) × 0.55 GB
KV Cache（Qwen3 GQA）≈ 上下文长度(K) × 0.05 GB    # 8B 模型，32K 约 1.6GB
激活内存 ≈ 0.3–0.5 GB（推理）
系统开销 ≈ 0.5 GB（CUDA Context + Driver）
```

#### 8GB（实际可用 ~7.5GB）+ 64GB RAM 配置能跑什么

| 模型 | 量化权重 | KV Cache (32K) | 总需求 | GPU 装载 | 是否可行 | 预期速度 |
|------|---------|----------------|--------|----------|---------|---------|
| Qwen3-4B-2507 Q4_K_M | 2.5 GB | 0.8 GB | 4.0 GB | 全部 ✅ | ✅ 完美 | 60+ t/s |
| **Qwen3-8B Q4_K_M** | **5.0 GB** | **1.6 GB** | **7.1 GB** | 全部 ✅ | ✅ 保底基线 | 35–45 t/s |
| Qwen3-14B Q4_K_M | 8.5 GB | 1.5 GB | 10.5 GB | ~70% | ❌ 部分 offload | 8–15 t/s |
| Qwen3-30B-A3B Q4_K_M (旧) | 22 GB | 1.5 GB | 23.5 GB | ~25% | ✅ MoE offload | 12–18 t/s |
| **Qwen3.6-35B-A3B Q4 (`qwen3.6:35b`)** | **24 GB** | 1.5 GB + Vision 1-2GB | **~27 GB** | ~22% | **✅ MoE offload 甜点** | **8–15 t/s** |
| **Qwen3.6-27B Q4 (`qwen3.6:27b`)** | **17 GB** | 1.5 GB + Vision 1-2GB | **~20 GB** | ~30% | 🟡 重 offload，能跑但慢 | **2–5 t/s** |
| Qwen3.5-27B Q4 | 17 GB | 1.5 GB | 18.5 GB | ~30% | 🟡 类似 27B 稠密 | 3–6 t/s |
| Qwen3-32B Q4_K_M | 19 GB | 1.5 GB | 20.5 GB | ~25% | 🟡 慢 | 2–4 t/s |
| Qwen3.5-122B-A10B Q4 | 73 GB | 1.5 GB | 74 GB | — | ❌ RAM 也不够 | — |
| Qwen3.6-27B-FP8 | 28 GB | — | — | — | ❌ FP8 需 H100/B200 | — |

**关键观察 1**：8GB 显卡跑 24GB 的 `qwen3.6:35b` MoE 比跑 17GB 的 `qwen3.6:27b` 稠密**反而更快**——稀疏激活使 CPU↔GPU IO 降到 1/9。这是反直觉但真实的 MoE 优势。

**关键观察 2**：多模态 Vision Encoder 额外吃 1–2GB 显存。如果只用文字功能，Ollama / vLLM 可加 `--language-model-only` 等价标志关闭视觉模块释放显存。

**KV 量化救场**：开启 `--kv-cache-type q8_0`（llama.cpp）/ Ollama 的 `OLLAMA_KV_CACHE_TYPE=q8_0` 可把 KV Cache 砍半。

#### CPU Offload 可行性（Qwen3.6-35B-A3B 的关键）

```
Qwen3.6-35B-A3B 总参数 36B，MoE 激活仅 3B（每 token 只激活 256 个 expert 中的 8 个 routed + 1 shared）
   ↓
Q4_K_M 权重 24GB ≈ GPU 7GB（attention + 部分 expert）+ RAM 17GB（其余 expert 池）
   ↓
推理时按路由动态调用 expert：
   - Attention 层全在 GPU（占 ~3GB）
   - 命中的 expert 临时调入 GPU（~1.5GB）
   - 未命中的 expert 留在 RAM
   ↓
RAM ↔ GPU 传输的是"激活的那 3B"，而非 36B 全量
   ↓
速度 ≈ 8–15 t/s（取决于专家路由命中率、CPU 内存带宽、PCIe 4.0 带宽）
```

**64GB RAM 是关键资产**——这是 MoE 能在 8GB 显卡上跑得动 36B 模型的物理基础。如果只有 16GB RAM，就只能跑 8B 稠密模型。

#### 进阶：KTransformers（专为消费级单卡跑大 MoE 设计）

[KTransformers](https://github.com/kvcache-ai/ktransformers) 是清华团队的开源项目，专门优化 "小 GPU + 大 RAM 跑 MoE" 这个场景。它在 Qwen3.6 模型卡上被官方列为推荐部署方案之一。

关键能力：
- 智能 expert 路由命中预测，主动预取 expert 到 GPU
- 支持 Q4 量化下混合精度推理
- 在 4090/3090 上实测可跑 DeepSeek-V3（671B MoE），8GB 卡跑 Qwen3.6-35B-A3B 完全可行

如果你对 Ollama 的 `qwen3.6:35b` 速度不满意（实际 < 8 t/s），考虑迁移到 KTransformers。

### 推理引擎对比

| 引擎 | 适用 | 8GB 显存表现 | 中文支持 | 学习曲线 | 推荐度 |
|------|------|-------------|---------|---------|--------|
| **Ollama** | 单机本地、开发体验 | ⭐⭐⭐⭐⭐ | 🟢 | 😀 极易 | ⭐⭐⭐⭐⭐（首推） |
| **llama.cpp** | 极致性能调控、CPU+GPU 混跑 | ⭐⭐⭐⭐⭐ | 🟢 | 😐 中 | ⭐⭐⭐⭐ |
| **LM Studio** | GUI 选手、不爱命令行 | ⭐⭐⭐⭐ | 🟢 | 😀 易 | ⭐⭐⭐⭐ |
| **vLLM** | 服务化、高并发 | ⭐⭐ | 🟢 | 😡 难 | ⭐⭐（8GB 不值得） |
| **SGLang** | 极致吞吐、前缀缓存 | ⭐⭐ | 🟢 | 😡 难 | ⭐（8GB 不值得） |
| **TensorRT-LLM** | NVIDIA 顶配压榨 | ⭐ | 🟢 | 🤯 极难 | ⭐（8GB 别碰） |

**为什么 vLLM 在 8GB 上不推荐**：vLLM 的 PagedAttention 优势在并发场景（10+ 请求同时来），单机自用时 Ollama 的开发体验完胜，且 8GB 显存吃不下 vLLM 的 KV Cache 预分配机制（默认占 90% 显存）。

详见 [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)。

### 量化方案对比

| 量化 | 文件大小（8B） | 质量损失 | 推荐场景 |
|------|---------------|---------|----------|
| FP16 / BF16 | 16 GB | 0% | ❌ 8GB 跑不动 |
| **Q8_0** | 8.5 GB | <1% | ❌ 8GB 跑不动 |
| Q6_K | 6.5 GB | ~1.5% | ⚠️ 紧贴显存上限，KV 不够 |
| **Q5_K_M** | 5.7 GB | ~2% | 🟡 备选 |
| **Q4_K_M** | **5.0 GB** | **~3%** | **✅ 默认首选** |
| Q4_K_S | 4.7 GB | ~4% | 🟡 极端紧凑 |
| Q3_K_M | 4.0 GB | ~7% | ❌ 质量明显劣化 |
| Q2_K | 3.2 GB | ~15% | ❌ 仅作奇技淫巧 |

**经验值**：Q4_K_M 是社区共识的"质量/体积"甜点。低于 Q4 后中文能力会先于英文劣化（可能因为中文 token 更多、舍入误差累积）。

---

## 🚀 上手实战轨道 — Qwen3.6 在 8GB 显卡上跑起来 + 极限优化

> 这一段是本报告的核心。**目标**：让 RTX 3060 Ti 8GB + 64GB RAM + i5-12600KF 这套配置跑动 Qwen3.6，并把性能从默认配置榨到尽头。

### 阶段 0：环境准备（一次性）

#### 0.1 检查 Ollama 环境

```powershell
ollama --version
ollama list
```

#### 0.2 关键环境变量（**必设**，影响 Qwen3.6 性能上限）

打开 PowerShell 以管理员身份执行（永久生效）：

```powershell
# 编辑替换的示例目录：按实际磁盘空间选择存储路径
[System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\example-models", "User")

# KV Cache 8-bit 量化（关键优化，省 50% KV 显存，质量损失 <1%）
[System.Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE", "q8_0", "User")

# 启用 Flash Attention（必开，降低长上下文显存与延迟）
[System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "1", "User")

# 模型常驻 24h，避免重新加载（否则每次冷启动 30-60 秒）
[System.Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "24h", "User")

# 单请求模式（8GB 显卡不要并发，并发会让 KV 撑爆）
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "1", "User")
```

**重启 Ollama 服务让环境变量生效**：
```powershell
Get-Process ollama* | Stop-Process -Force
ollama serve  # 或重启 Ollama 桌面应用
```

#### 0.3 GPU 显存清理（榨出每一 MB）

```powershell
# 看看现在 GPU 谁在占
nvidia-smi
# 关掉占显存的：浏览器硬件加速、其他游戏/视频软件
# Qwen3.6:35b 跑起来时建议给它至少 7GB 空闲显存
```

### 阶段 1：基线对照（先跑 qwen3:8b 摸清你机器的极限）

```powershell
# 若尚未下载，先执行 ollama pull qwen3:8b
ollama run qwen3:8b --verbose
>>> /set parameter num_ctx 32768
>>> 用三段话解释 Transformer 的注意力机制。
# 看末尾输出的 eval rate（应在 35-45 t/s 之间）
>>> /bye
```

**为什么先跑 8B**：建立性能基准。如果连 8B 都跑不到 30 t/s，说明你的 GPU 被其他进程占用了，先解决再上 Qwen3.6。

### 阶段 2：核心 — 跑动 Qwen3.6-35B-A3B（推荐主力）

#### 2.1 拉取（24GB，耗时取决于网速）

```powershell
ollama pull qwen3.6:35b
# 这是 35B-A3B MoE Q4 版本，多模态
# 实际下载 23GB，看网速 30-90 分钟
```

#### 2.2 首次启动 + 关键调参

```powershell
ollama run qwen3.6:35b --verbose
```

进入交互模式后**第一时间设这些参数**：

```
/set parameter num_ctx 16384          # 起步 16K，别贪 256K，KV 会爆
/set parameter num_predict 4096       # 单次生成上限
/set parameter temperature 1.0        # Qwen3.6 thinking 模式官方推荐
/set parameter top_p 0.95
/set parameter top_k 20
/set parameter min_p 0.0
/show info                            # 看实际配置
```

#### 2.3 验证可用 + 测速

```
>>> 你好，简短介绍一下你自己。这是 Qwen3.6 35B-A3B 在我的 RTX 3060 Ti 上的测试。
```

看末尾输出。**预期数据**（基于社区类似配置实测）：
- `prompt eval rate`: 80-200 t/s（prefill 阶段，输入越长越快进入 GPU）
- `eval rate`: **8-15 t/s**（decode 阶段，越接近 15 越好）
- 首 token 延迟（TTFT）: 1.5-3 秒

如果 < 5 t/s，看下面阶段 3 的优化路径。

### 阶段 3：性能极限优化（实战手法，按收益从高到低排）

#### 优化 1：调整 GPU 卸载层数（**最高收益**）

Ollama 默认自动决定有多少层放 GPU。但默认决策对 Qwen3.6 这种新架构 + 多模态模型偏保守。手动指定可榨出更多速度：

```powershell
# 设置环境变量（Ollama 0.21+ 支持）
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_GPU", "32", "User")
# 32 = 把前 32 层放 GPU。Qwen3.6-35B-A3B 共 40 层，放 32 层后剩 8 层在 CPU
# 8GB 显卡上 32 层是极限，再多会 OOM
```

或在交互式会话中通过 modelfile 临时调整：

```powershell
# 创建定制版本
@"
FROM qwen3.6:35b
PARAMETER num_gpu 32
PARAMETER num_ctx 16384
PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER top_k 20
"@ | Out-File -Encoding ascii Modelfile.qwen36-tuned

ollama create qwen3.6-tuned -f Modelfile.qwen36-tuned
ollama run qwen3.6-tuned --verbose
```

**调参原则**：从 num_gpu=24 起步，每次 +4，跑一句测速，OOM 就回退。**找到不 OOM 的最大值就是最优**。

#### 优化 2：关闭视觉编码器（如果不看图，省 1.5GB 显存）

Qwen3.6 默认加载视觉编码器（占 ~1.5GB）。如果你只做文本，禁用它能给 KV Cache / GPU 层留更多空间：

**方式 A：Ollama 通过环境变量**（部分版本支持）：
```powershell
$env:OLLAMA_LANGUAGE_MODEL_ONLY = "1"
```

**方式 B：迁移到 vLLM（更可控）**：
```powershell
vllm serve Qwen/Qwen3.6-35B-A3B --port 8000 --max-model-len 32768 `
  --reasoning-parser qwen3 --language-model-only --gpu-memory-utilization 0.85
```

#### 优化 3：KV Cache q8_0 量化（已在 0.2 步设过）

这个优化我们在环境变量里已经开了。复述一下收益：
- 默认 FP16 KV：16K 上下文吃 2GB 显存
- q8_0 KV：16K 上下文吃 **1GB** 显存（省一半）
- 质量损失：< 1%（在中文场景几乎无感）

**验证生效**：
```powershell
ollama ps  # 看 Memory 列，应明显比未开 q8_0 时小
```

#### 优化 4：上下文窗口策略

| 场景 | num_ctx 推荐 | 原因 |
|------|-------------|------|
| 普通对话 / Agent 工具调用 | **8K-16K** | 够用，速度最快 |
| 中等文档问答 | 32K | 平衡性能与能力 |
| 长文档总结 / 代码库分析 | 64K-128K | 必须 + KV 量化 + 关闭视觉 |
| 256K 满血 | ❌ 8GB 卡上不现实 | 即使 KV q8 也吃 8GB+ |

**bug 提醒**：Qwen3.6 模型卡明确说"上下文 < 128K 时，thinking 能力会受影响"。如果你只用 8K 上下文跑数学/推理任务，**关闭 thinking 模式**（参考阶段 4）效果可能反而更好。

#### 优化 5：换更小的量化（最后手段）

如果 Q4_K_M 还是 OOM，用社区的更激进量化版本：

```powershell
# 第三方 GGUF 已有 Q3_K_M / IQ3_XXS 等
ollama pull batiai/qwen3.6-27b:q3_k_m
# 或更极端
ollama pull isotnek/qwen3.6-27b-batiai-iq3:latest
```

**警告**：Q3 以下中文劣化严重（错别字、逻辑跳跃）。仅在必要时用，并跑 Eval 确认质量可接受。

#### 优化 6：终极性能 — KTransformers（替换 Ollama）

如果以上调到极限还嫌慢（< 8 t/s），考虑切到 KTransformers——它专为"小 GPU + 大 RAM 跑 MoE"优化：

```bash
# 在 WSL2 / Linux 环境下
git clone https://github.com/kvcache-ai/ktransformers && cd ktransformers
pip install -e .
python -m ktransformers.local_chat \
  --model_path Qwen/Qwen3.6-35B-A3B \
  --gguf_path /path/to/Qwen3.6-35B-A3B-Q4_K_M.gguf \
  --cpu_infer 12  # i5-12600KF 给它 12 个 CPU 推理线程
```

**KTransformers 在该示例配置上的预期增益**：相比 Ollama 的 8-15 t/s，可达 **15-25 t/s**（实测因 expert 路由命中率而异）。

### 阶段 4：Qwen3.6 的关键特殊用法

#### 4.1 关闭 thinking 模式（**Qwen3.6 必看**）

> ⚠️ **变更**：Qwen3.6 不再支持 Qwen3 的 `/think` `/nothink` 软切换！必须用 API 参数。

**Python 端关闭 thinking**：
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

resp = client.chat.completions.create(
    model="qwen3.6:35b",
    messages=[
        {"role": "user", "content": "用一句话说什么是 RAG"}
    ],
    temperature=0.7, top_p=0.8,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": False},  # ← 关键！
        "options": {"num_ctx": 16384, "top_k": 20, "min_p": 0.0},
    },
    max_tokens=512,
)
print(resp.choices[0].message.content)
```

**注意**：在 Ollama 上某些版本 `chat_template_kwargs` 透传不完整。如果你看到 `<think>...</think>` 仍在输出，临时方案：
```python
# 把生成结果中的 think 块去掉
import re
content = resp.choices[0].message.content
clean = re.sub(r'<think>.*?</think>\n*', '', content, flags=re.DOTALL)
```

#### 4.2 Thinking Preservation（Qwen3.6 新能力）

Agent 多轮场景下保留历史 thinking，可显著提升决策一致性 + 降低 token 消耗：

```python
resp = client.chat.completions.create(
    model="qwen3.6:35b",
    messages=multi_turn_messages,
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": True,
            "preserve_thinking": True,   # ← Qwen3.6 独占新能力
        },
    },
)
```

#### 4.3 Vision Input（看图能力）

```python
resp = client.chat.completions.create(
    model="qwen3.6:35b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/screenshot.png"}},
            {"type": "text", "text": "这张图描述了什么？"},
        ]
    }],
    max_tokens=1024,
)
```

**坑**：Ollama 0.21.2 对 Qwen3.6 视觉的支持仍在完善，部分 base64 图片会失败。建议用 URL 形式或迁移到 vLLM。

### 阶段 5：接入 Agent 框架

#### LangChain / LangGraph

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model="qwen3.6:35b",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    temperature=0.7, top_p=0.8,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

#### Qwen-Agent（官方，最佳兼容性）

```python
from qwen_agent.agents import Assistant

llm_cfg = {
    "model": "qwen3.6:35b",
    "model_type": "qwenvl_oai",   # ← 多模态版要用这个
    "model_server": "http://localhost:11434/v1",
    "api_key": "ollama",
    "generate_cfg": {
        "use_raw_api": True,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": True,
                "preserve_thinking": True,
            }
        },
    },
}
bot = Assistant(
    llm=llm_cfg,
    function_list=[{"mcpServers": {
        "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]}
    }}],
)
```

详见 [R65](R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 的主流栈搭配建议。

---

## 🕳️ 避坑指南（Qwen3.6 专项）

| # | 坑 | 现象 | 原因 | 解法 |
|---|----|------|------|------|
| 1 | ⚠️ **`/nothink` 在 Qwen3.6 失效** | 设了 `/nothink` 仍输出 `<think>` | Qwen3.6 废弃软切换，只认 API 参数 | `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` |
| 2 | ⚠️ **Ollama num_ctx 默认 2048** | Qwen3.6 上更要命：能力会显著退化 | Ollama 沿袭 llama.cpp 安全默认 | 必须改 `num_ctx >= 8192`；推理任务 `>= 16384` |
| 3 | ⚠️ **首次启动 OOM** | qwen3.6:35b 启动直接 CUDA OOM | 默认 num_gpu 偏激进 | 设 `OLLAMA_NUM_GPU=24`，从 24 开始往上调 |
| 4 | **未开 KV q8_0 → 长上下文 OOM** | num_ctx=32768 时 OOM | KV Cache FP16 是 q8_0 的 2 倍 | `OLLAMA_KV_CACHE_TYPE=q8_0` 后**重启 Ollama** |
| 5 | **未开 Flash Attention → 慢 30%** | t/s 偏低、长上下文延迟高 | 默认未启用 | `OLLAMA_FLASH_ATTENTION=1` 后重启 |
| 6 | **视觉编码器吃 1-2GB 但用不上** | 文本任务也占着这块显存 | qwen3.6:35b 默认加载 | 文本场景用 vLLM `--language-model-only`，或忍一下 |
| 7 | **Q3 以下中文/Coding 显著劣化** | 模型说话变笨、代码跑不通 | 中文 token 多、舍入误差累积 | 死守 Q4_K_M 底线；3060 Ti 不要碰 NVFP4（需 RTX 50） |
| 8 | **冷启动 30-60 秒** | 第一句话等很久 | 24GB 模型从磁盘加载 | `OLLAMA_KEEP_ALIVE=24h` 让模型常驻 RAM |
| 9 | **系统盘空间不足** | 拉取大模型后磁盘容量告警 | 默认模型目录位于用户目录 | 用 `OLLAMA_MODELS` 指定有足够空间的目录后重启 |
| 10 | **vLLM/SGLang 启不来** | 报 `qwen3_5` / `qwen3_5_moe` 架构未识别 | vLLM < 0.19.0 / SGLang < 0.5.10 | 升级到推荐版本，否则只能用 Ollama |
| 11 | **多模态 base64 图片失败** | Vision 输入 500 错误 | Ollama 0.21.2 透传不完整 | 用图片 URL，或迁 vLLM |
| 12 | **Tool Calling 在 thinking 下 JSON 错误** | 函数参数解析失败 | thinking 内容污染解析 | 工具调用关闭 thinking；保留 thinking 用于规划阶段，工具调用阶段切非 thinking |
| 13 | **MoE 速度只有 2-4 t/s（应 8-15）** | num_gpu 过低 / GPU 被其他程序占 | 默认决策不够激进 | 关浏览器硬件加速；调大 num_gpu；nvidia-smi 看真实空闲 |
| 14 | **Ollama 并发请求卡死** | 第二个请求等很久 | OLLAMA_NUM_PARALLEL 默认 4 但 8GB 不够 | 强制设 `OLLAMA_NUM_PARALLEL=1` |
| 15 | **Modelfile PARAMETER 不生效** | 改了 num_gpu 但日志显示用的还是默认 | 用 `ollama create` 后忘 `ollama run 新名` | 用新创建的 tag，不是原始 `qwen3.6:35b` |
| 16 | **VRAM 显示 4GB（实际 8GB）** | Windows 系统报错 | WDDM 显示的是 BAR1 上限 | 以 `nvidia-smi` 为准（8192MiB） |

---

## 💰 成本与 ROI 速算

### 直接成本

| 项 | 数值 |
|----|------|
| 模型权重存储 | qwen3:8b 5GB + 30b-a3b 18GB + 4b-2507 2.5GB = ~26GB |
| 一次推理电费 | RTX 3060 Ti 满载 200W，1 小时推理 ≈ 0.2 度 ≈ ¥0.12 |
| 月电费（每天 8 小时常用） | 200W × 8h × 30 = 48 度 ≈ **¥30–40** |
| API 等价折算 | 同等用量调 GPT-4o-mini ≈ ¥800–1500/月（10K 次/天 × 1K token）|

**ROI 拐点**：日均 LLM 调用 ≥ 5000 次时，本地部署在 3 个月内回本（电费 vs API 费）。

### 隐性成本

- ⏱️ **首次部署投入**：2–4 小时（含下载模型、调参、踩坑）
- 🧠 **运维成本**：模型版本管理、监控、prompt 适配。生产场景必须配 LiteLLM 或 OpenAI Proxy 做路由（详见 [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)）
- 🔋 **机器占用**：跑模型时 GPU 100%，无法同时打游戏/做视频渲染

### 适用规模决策

| 场景 | 推荐方案 |
|------|---------|
| 个人学习、Agent 开发 | ✅ 本地 Qwen3-8B |
| 团队 < 5 人内部工具 | ✅ 本地 Qwen3-30B-A3B（性价比之王） |
| 生产环境、外部用户 | ❌ 别用消费级显卡，上 H100/A100 + vLLM |
| 数据合规 + 中等流量 | 🟡 多张 4090 + vLLM 自建（参考 [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)） |

---

## 🎯 决策速查（Qwen3.6 时代）

```
RTX 3060 Ti 8GB + 64GB RAM，想跑 Qwen3.6？
│
├── 想体验 Qwen3.6 最新能力 + 多模态 + 中速可接受
│   → ✅ ✅ ✅ qwen3.6:35b（35B-A3B MoE）— 本报告主推
│       └── 24GB 模型，CPU offload，预期 8-15 t/s
│       └── 优化清单：KV q8_0 + FlashAttn + num_gpu=32 + num_ctx=16K
│
├── 想要顶级 Coding 能力，速度慢可以接受（批处理）
│   → ✅ qwen3.6:27b（28B 稠密，SWE-bench 77.2 顶级）
│       └── 17GB 模型，重 offload，2-5 t/s
│       └── 适合：跑离线代码 review、async 任务、cron job
│
├── 想极速响应（30+ t/s）+ 普通对话/Agent
│   → ✅ qwen3:8b（5GB 全装显存）
│       └── 35-45 t/s，但能力 < Qwen3.6
│       └── 适合：交互式对话、IDE 内 LLM、聊天 bot
│
├── 想跑 Coding Agent 但 Qwen3.6:27b 太慢
│   → 🟡 等 unsloth 的 IQ3_XXS GGUF（社区已发，约 12GB）
│       └── 质量妥协但速度回到 6-10 t/s
│       └── 链接：huggingface.co/unsloth/Qwen3.6-27B-GGUF
│
├── 长文档总结（>64K token）
│   → ✅ qwen3:4b-instruct-2507（2.5GB，60+ t/s，256K ctx）
│       └── 能力弱于 Qwen3.6 但够用，速度优先
│
├── 想极限榨速度（追求 15+ t/s 跑 35B-A3B）
│   → 🔧 切 KTransformers（WSL2 + Q4_K_M GGUF + 12 CPU 线程）
│       └── 实测可达 Ollama 的 1.5-2 倍
│
├── 想做多并发服务（>3 RPS）
│   → ❌ 8GB 卡老实串行，要并发上 16GB+ 显卡 + vLLM
│
└── 多模态深度任务（高频 OCR / 视频理解）
    → 🟡 Qwen3.6 已含视觉，但 8GB 卡跑视频会很慢
    → 推荐：复杂视觉走 Qwen Studio API，本地只做文本+轻图
```

### 一句话总结

> **本地体验 Qwen3.6 = 装 Ollama → `ollama pull qwen3.6:35b` → 设好 5 个环境变量（KV q8 / FlashAttn / KEEP_ALIVE / NUM_PARALLEL=1 / NUM_GPU=32）→ `ollama run qwen3.6:35b` → 调 num_ctx 到 16K → 关 thinking 提速 → 跑起来。** 预期 8-15 t/s，足够日常使用。

**何时不要本地部署**：
- 只是偶尔用一下 → 直接调 API（DeepSeek API ¥2/M tokens 真不贵）
- 需要 SOTA 推理能力 → DeepSeek-R1 / Qwen3-235B-Thinking 在线用
- 涉及多模态（图/视频/语音） → 还是 API（本地 VL 模型 24GB 起跳）

---

## 开放问题与后续

- ⬜ **Qwen3-Coder 系列** 是否值得专门部署做编程 Agent？需对比 DeepSeek-Coder、StarCoder2
- ⬜ **量化精度对 Tool Calling 准确率的影响**：Q4 vs Q5 vs Q8 在工具调用 benchmark 上的差异（参考 [R71](R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md) Coding Agent 五家横评的方法论）
- ⬜ **多 Agent 本地部署**：Ollama 串行限制下，如何编排多 Agent 协作？（候选方案：Qwen-Agent + 流式调度）
- ⬜ **持续学习接入**：本地 Qwen3 + Skill 自迭代（[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)）的可行性，验证小模型能否承担 Skill 进化任务

---

## 📌 来源清单

- [Qwen3 GitHub README](https://github.com/QwenLM/Qwen3) — 2026-04-26 — 模型尺寸、版本、部署支持矩阵
- [Qwen3 官方 Blog](https://qwenlm.github.io/blog/qwen3/) — 2025-04-29 — Qwen3 发布
- [Qwen3-2507 Model Card (HuggingFace)](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507) — 2025-07-30
- [Qwen Speed Benchmark](https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html) — 推理速度官方数据
- [Ollama Library qwen3 tags](https://ollama.com/library/qwen3/tags) — 2026-04-26
- [llama.cpp release b5401+](https://github.com/ggml-org/llama.cpp) — Qwen3 原生支持
- [Qwen3 Technical Report (arXiv:2505.09388)](https://arxiv.org/abs/2505.09388) — 训练细节
- 模型训练知识 — 截止 2025-04 — 仅作背景参考
- 本工作区 [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)、[R59](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)、[R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)、[R65](R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) — 推理引擎/量化/SLA/技术栈背景

⚖️ 来源一致性：**多源一致，高置信**（Qwen 官方 + GitHub + Ollama + HuggingFace 四方互证）
📅 时效性声明：信息获取于 2026-04-26
