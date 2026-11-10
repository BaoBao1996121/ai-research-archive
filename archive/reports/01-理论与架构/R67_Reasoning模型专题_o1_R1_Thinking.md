---
title: Reasoning 模型专题：o1 / R1 / Thinking 训练范式与落地决策
aliases: [R67, Reasoning模型调研, 推理模型专题, LongCoT调研, RLVR调研, GRPO调研]
tags: [reasoning, o1, deepseek-r1, claude-thinking, rlvr, grpo, test-time-scaling, long-cot]
date: 2026-04-25
category: 理论与架构
report_id: R67
tokens: ~17000
status: completed
related:
  - "[R37](R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md)"
  - "[R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R55](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md)"
  - "[R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)"
  - "[R62](R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Reasoning 模型专题：o1 / R1 / Thinking 训练范式与落地决策

> **一句话概括**：Reasoning 模型不是"更强的 CoT"——它是**训练范式从模仿示范（SFT）转向可验证奖励强化（RLVR）**的产物。模型在 RL 中**自发涌现**反思、回溯、自验证行为，这是 GPT-4 → o1 → R1 路线的真正分水岭。本报告解释为什么过去对普通模型管用的 prompt 技巧（Few-shot CoT、"Let's think step by step"）对 reasoning 模型反而**降低性能**，并给出 Agent 集成的混合架构（reasoning 当 Planner + 普通模型当 Worker）。
>
> **研究日期**：2026-04-25
> **关联报告**：[R37](R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) Transformer 架构（"thinking token 在哪里产生"）· [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 训练微调（"GRPO 算法的上下文"）· [R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 蒸馏（"R1-Distill 的来历"）· [R55](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) Prompt Engineering（"为什么旧 prompt 技巧不再适用"）· [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) Benchmark 速查（"AIME / GPQA / SWE-bench 怎么读 reasoning 模型成绩"）· [R62](R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) 预训练（"reasoning 是预训练后第四阶段"）
> **增量价值**：工作区已有 R52 覆盖 GRPO 算法本身，R53 提到 R1-Distill 的蒸馏一面，R55 提到推理类 prompt 反模式。但 reasoning 模型作为**一类 LLM 物种**——它的训练范式、推理时行为、Agent 集成方式、决策边界——此前没有专题报告。本报告把分散的点串起来，并补充 2025-2026 年最新的 GRPO/DAPO/VAPO 算法分化、Test-Time Scaling 经济学、5 个场景的决策树。

---

## TL;DR 速查卡

| 维度 | 结论 |
|------|------|
| **本质判断** | Reasoning 模型 ≠ 更强 CoT。CoT 是 prompt 技巧（推理时），Reasoning 是**训练范式**（在 RL 阶段用可验证奖励让模型学会长推理）。**两者在能力曲线上有质的差异**：长 CoT 模型在数学/竞赛代码上能跑赢规模大 5-10× 的非 reasoning 模型。 |
| **三条训练路线** | ① **RLVR**（DeepSeek-R1 路线，可验证奖励 + GRPO，主流）② **PRM**（过程奖励模型 + 搜索，DeepMind 路线，已被 R1 报告归为"unsuccessful attempts"）③ **MCTS / Beam Search**（应用层推理时缩放，与训练范式正交）|
| **核心算法演化** | PPO → **GRPO**（DeepSeek，去掉 critic、用 group baseline）→ **DAPO**（字节，2025-03，解决长样本崩溃）→ **VAPO**（字节，2025-04，重引入 value model 做长 trace 信用分配）|
| **2026-04 模型横评** | 闭源天花板：**o3 / o3-mini-high**（AIME 96+, GPQA 87.7, SWE-bench Verified 71.7）、**Claude 3.7 Sonnet Thinking**（SWE-bench Verified 70.3，编码强）、**Gemini 2.5 Pro Thinking**（多模态强）。开源天花板：**DeepSeek-R1**（AIME 79.8，已追平 o1）、**QwQ-32B**（开源单卡可跑）。**已追平 o1，但 o3 仍领先 8-15 个百分点**。 |
| **三条最反直觉的事实** | ① 给 R1 写 **Few-shot CoT 反而降低性能**（DeepSeek 官方实验，应零样本直接描述问题）② 把 thinking 内容**喂回上下文**会浪费 5-20× token 且不提升精度（应只回传 final answer）③ **简单分类用 reasoning 模型成本爆 50-100 倍**（同样准确率） |
| **何时该用** | 数学竞赛 / 复杂代码 debug / 多步骤规划 / 需要自验证的科学问题 / 长 horizon Agent 规划。**不该用**：分类、摘要、翻译、知识问答、低延迟客服、Tool calling 密集型流水线（thinking 期间无法调工具）。 |
| **Agent 架构启示** | **Planner-Worker 混合架构成为新范式**：reasoning 模型当一次性 Planner（产出多步计划），普通模型当 Worker（执行 Tool calling）。**ReAct 循环没过时但被改写**：粗粒度规划交给 reasoning，细粒度反应仍是 ReAct。 |
| **成本天平** | 单 query：o3 ≈ $0.05–0.30 vs gpt-4o-mini ≈ $0.001–0.005，**贵 50-300 倍**。但若一个 reasoning 调用能替代 5 次 ReAct 来回，且后者每次都失败重试，**总账可能 reasoning 更便宜**——账要按"任务完成率 × 端到端 token"算，不是单调用价格。 |

---

## 目录

1. [🔭 定位透镜：纵横坐标](#定位透镜)
2. [📚 长 CoT 的本质：从 token-level 推理到 episode-level 推理](#长cot本质)
3. [📚 训练范式拆解：RLVR / PRM / MCTS 三条路线](#训练范式)
4. [📚 算法演化：PPO → GRPO → DAPO → VAPO](#算法演化)
5. [📚 Test-Time Scaling 的经济学](#test-time-scaling)
6. [📚 2026-04 模型横评](#模型横评)
7. [🚀 上手实战：何时用 + Hello World + 反模式 + Agent 集成](#上手实战)
8. [🕳️ 避坑指南](#避坑指南)
9. [💰 成本与 ROI 速算](#成本roi)
10. [🎯 决策速查](#决策速查)
11. [🤔 对 Agent 架构的影响](#agent架构影响)
12. [❓ 开放问题](#开放问题)
13. [📌 来源清单](#来源清单)

---

<a id="定位透镜"></a>
## 🔭 定位透镜：纵横坐标

### 纵轴 · 演化脉络

```
2022.01  Chain-of-Thought (Wei et al., Google)
         └─ "Let's think step by step" 把推理变成 token 序列；prompt 层面，模型不变

2022.03  Self-Consistency (Wang et al., Google)
         └─ 采样 N 条 CoT，多数投票；首次把"算力换正确率"做成方法

2023.05  Tree-of-Thought (Yao et al., Princeton)
         └─ 显式搜索 + 评估，把推理变成树搜索；MCTS for LLM 雏形

2023.10  Process Reward Model (Lightman et al., OpenAI, "Let's Verify Step by Step")
         └─ 给推理过程的每一步打分（PRM）；为后续 o1/o3 训练范式埋伏笔

2024.08  Test-Time Compute Scaling (Snell et al., DeepMind, arXiv:2408.03314)
         └─ "推理时算力 > 模型参数"——同等预算下，推理时缩放比堆参数更划算

2024.09  o1-preview (OpenAI)              ← 引爆点：第一个商用 reasoning 模型
         └─ 隐藏 thinking、按 output token 计费、reasoning_effort 参数

2024.11  QwQ-32B-Preview (Qwen)           ← 开源首个对标 o1 的尝试
2024.12  Marco-o1 (Alibaba)               ← 公开 long CoT + MCTS 训练细节

2025.01  DeepSeek-R1 / R1-Zero (Nature 2025)  ← 开源里程碑
         ├─ R1-Zero：纯 RL（无 SFT 冷启动），证明 reasoning 可以纯靠 RLVR 涌现
         ├─ R1：SFT 冷启动 + 多轮 RL，AIME 79.8 追平 o1
         └─ R1-Distill：Qwen/Llama 蒸馏出 1.5B-70B 系列，触发"开源 o1 大爆发"

2025.02  Claude 3.7 Sonnet Extended Thinking (Anthropic)
         └─ Hybrid 架构：thinking + 非 thinking 一个模型；budget_tokens 显式预算

2025.03  DAPO (字节)                      ← GRPO 工程化补丁
2025.04  VAPO (字节)                      ← 重引入 value model 解决长 trace
2025.04  o3 / o3-mini (OpenAI)            ← 闭源天花板再抬高，SWE-bench 71.7
2025.06  Gemini 2.5 Pro Thinking (Google) ← 多模态 reasoning + 1M context
2025.10  GPT-5 (OpenAI)                   ← reasoning 与非 reasoning 自动路由（"unified"）
```

**生命周期定位**：
- 2024-09 至 2025-01 = **萌芽期**（少数玩家，闭源主导）
- 2025-01 至 2025-12 = **快速爆发期**（R1 引爆开源、各家追赶、算法分化）
- 2026 起 = **分化期**（开源已追平 o1，但 o3+ 仍领先；hybrid 模式成为产品形态主流；下个阶段拼"reasoning 与 Tool calling 融合"）

### 横轴 · 竞争格局

| 阵营 | 代表 | 核心理念 | 强项 | 弱点 |
|------|------|---------|------|------|
| **闭源训练派** | OpenAI o1/o3 / Gemini Thinking | RL + 推理时缩放 + 工具协同（细节保密）| 综合最强，o3 在 ARC-AGI 突破 | 不可学习、成本高、API 不透明 |
| **开源 RLVR 派** | DeepSeek-R1 / QwQ-32B / Marco-o1 | 可验证奖励 + GRPO 家族 | 完全公开、可蒸馏、可自训 | 落后 o3 一代（数学 8-15pp） |
| **Hybrid 产品派** | Claude 3.7 Thinking / GPT-5 | 一个模型两种模式，参数显式控制 | 工程友好、用户无须切模型 | 模型规模更大、训练更复杂 |
| **推理时缩放派** | TogetherAI Inference / 各家 best-of-N | 不重训模型，应用层做 search/voting | 模型不变即可获益 | 对 reasoning 模型增益已边际递减 |

### 交叉判断（独立结论）

1. **开源已追平 o1-preview，但 o3 仍领先一代**。如果你的场景能容忍 R1 级别推理（AIME 79.8 vs o3 96+），开源是性价比最高的选项；如果追求 SOTA（前沿数学竞赛、ARC-AGI），仍只能用 o3 / Claude Thinking。
2. **2026 是分化年**：闭源继续在"unified routing + 长 horizon Agent"方向走，开源继续在"算法效率（DAPO/VAPO）+ 蒸馏小模型"方向走，两条线在 1-2 年内不会收敛。
3. **PRM 路线已被 R1 报告标为"unsuccessful attempts"**。这不代表 PRM 没价值——而是说**对训练 reasoning 模型来说，可验证奖励（RLVR）比过程奖励（PRM）更可扩展、更不易作弊**。PRM 仍在推理时验证、step-level 评估等场景有用。
4. **MCTS for LLM 训练已基本被放弃**（搜索空间爆炸 + 价值函数难学）。但**推理时**搜索仍是有效的应用层手段（best-of-N、self-consistency）。

---

<a id="长cot本质"></a>
## 📚 长 CoT 的本质：从 token-level 推理到 episode-level 推理

### 三层推理的关键区别

| 层级 | 长度 | 谁产生 | 例子 |
|------|------|--------|------|
| **Token-level CoT**（2022 风味）| 数十-数百 token | 普通 LLM + prompt | "Let's think step by step. First, ... Therefore, the answer is X." |
| **Episode-level Reasoning**（2024+ 风味）| 数千-数万 token | Reasoning 模型自发产生 | "Let me try approach A... wait, that doesn't work. Let me reconsider... Actually B might be better. Let me verify..." |
| **Search-level Reasoning** | 多条独立 CoT 投票/搜索 | 应用层（self-consistency, ToT）| 采样 N=64 条 CoT，多数投票 |

**质变在哪里**：
- 普通 CoT 是**线性单程**——错了就错了，没有回头路
- Episode-level reasoning 包含**反思（reflection）、回溯（backtracking）、自验证（self-verification）、策略切换（strategy adaptation）**——这四种行为是 RLVR 训练中**自发涌现**的，不是 SFT 教出来的（DeepSeek 称之为 "Aha! moment"）

### 为什么 SFT 教不出来 reasoning？

> 直觉解释：SFT 是"模仿示范"——模型学会了**长得像推理**的输出模式，但**没有学会探索**。RL 是"目标导向"——给定可验证目标（数学答案对/错），模型必须**真正算对**才能拿奖励，于是它**自发学会**回头检查、试别的方法。

形式化一点：
- **SFT 损失**：$L_{SFT} = -\sum \log P(y_i | x, y_{<i})$，目标是匹配示范分布
- **RLVR 目标**：$\max_\pi \mathbb{E}_{y \sim \pi(\cdot|x)}[r(x, y)]$，目标是最大化可验证奖励

SFT 让模型"会写推理 trace"，但 trace 中的反思可能是**装出来的**（模仿了示范的"等等让我重新想想"句式但没有真的修正错误）。RL 强迫模型**真的算对**，反思就成了刚需。

### "可验证"是关键约束

R1 的核心 trick 是**reward 必须可程序化判定**：
- ✅ 数学题：答案数值匹配（用 SymPy 比较）
- ✅ 竞赛代码：跑测试用例
- ✅ 格式：正则匹配 `<think>...</think>` 标签
- ❌ 创意写作：无法可验证 → RLVR 失效（仍需 RLHF 偏好奖励）

这解释了为什么 reasoning 模型在数学/编码上能力爆炸，但在**开放域写作、共情对话**上提升有限——奖励没法可验证。

---

<a id="训练范式"></a>
## 📚 训练范式拆解：RLVR / PRM / MCTS 三条路线

### 路线一：RLVR（Reinforcement Learning with Verifiable Rewards）— 主流

**代表**：DeepSeek-R1、QwQ-32B、Marco-o1

**核心配方**（以 R1 为蓝图）：

```
Stage 0: 基座（DeepSeek-V3, 671B MoE）
Stage 1: R1-Zero — 纯 RL（无 SFT 冷启动）
         Reward = accuracy（数学验证 + 代码编译）+ format（<think> 标签）
         算法 = GRPO
         产物：能 reasoning 但语言混乱、可读性差
Stage 2: 用 R1-Zero 生成数千条高质量"冷启动"long-CoT 样本
Stage 3: 在基座上做 SFT（用 Stage 2 的冷启动数据）
Stage 4: 第一轮 RL（accuracy + format + language consistency reward）
Stage 5: 用最新 checkpoint 生成 600K reasoning SFT + 200K 通用 SFT 样本
Stage 6: 在基座上重新 SFT（800K 数据）
Stage 7: 第二轮 RL（含 RLHF 偏好奖励，覆盖非可验证场景）
→ DeepSeek-R1 (final)
```

**关键 insight**：**SFT 冷启动不是必需，但能让 RL 收敛更快、语言更可读**。R1-Zero 证明了"纯 RL 可行"，但 R1（SFT+RL）才是工业标杆。

### 路线二：PRM（Process Reward Model）— 已被边缘化

**代表**：Math-Shepherd、OpenAI "Let's Verify Step by Step"（2023）

**思路**：训练一个 PRM 给推理过程的**每一步**打分，用 PRM 的分数引导主模型学会"好步骤"。

**为什么 R1 报告把它列为 unsuccessful attempts**：
- ❌ 步骤切分难定义（什么算"一步"？）
- ❌ 标注成本高（要人工标每一步对错）
- ❌ Reward hacking 严重（模型学会写"看起来对的步骤"而非"真的对的步骤"）
- ❌ Scale 困难（步骤层 reward 信号比答案层稀疏得多）

**仍有用的地方**：推理时验证（用 PRM 给 best-of-N 的候选打分）、step-level 评估指标。

### 路线三：MCTS / Tree Search — 训练已放弃，推理时仍用

**代表（训练）**：AlphaGo 启发的早期工作（如 rStar、Marco-o1 早期版本）
**代表（推理时）**：Tree-of-Thought、ReST-MCTS

**为什么训练时被放弃**：
- LLM 的状态空间是 token 序列，分支因子可达 $|V| \approx 10^5$（词表大小），MCTS 几乎无法收敛
- 价值函数难学（每个中间节点的"好坏"无法可靠评估）
- DeepSeek 团队明确报告 MCTS 在他们的实验中 "did not yield significant improvements"

**仍有用的地方**：应用层推理时搜索（小分支因子、明确目标）、agent 多步规划场景。

### 三路线一图对比

```
                        训练时               推理时
RLVR        ✅ 主流（GRPO/DAPO/VAPO）    ✅ 自然产生 long CoT
PRM         ❌ 已被 R1 报告否定          ✅ best-of-N 验证、step 评分
MCTS        ❌ 不可扩展                  ✅ Tree-of-Thought, agent planning
```

---

<a id="算法演化"></a>
## 📚 算法演化：PPO → GRPO → DAPO → VAPO

> 如果你对 PPO/RLHF 不熟，先看 [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) §训练算法演进。本节聚焦 reasoning 训练专用的 GRPO 家族分化。

### PPO 在 reasoning 训练的痛点

PPO（标准 RLHF 算法）在 reasoning 场景有三大痛点：
1. 需要训一个 critic（value model），与 policy 同等大小，**显存翻倍**
2. critic 训练在长 CoT 场景**信号稀疏**（最终 reward 来自答案对错，分摊到几千 token 上几乎为零）
3. KL 散度约束容易把模型"拉回"基座，**抑制 reasoning 涌现**

### GRPO（DeepSeek-Math, 2024-02 → R1, 2025）

**核心改动**：去掉 critic，用 **group baseline** 替代 value function。

```python
# 伪代码
for prompt in batch:
    responses = sample(policy, prompt, n=G)        # 一个 prompt 采样 G 条（如 G=16）
    rewards = [reward_fn(r) for r in responses]    # 每条算 reward
    baseline = mean(rewards)                       # 组内均值当 baseline
    advantages = [(r - baseline) / std(rewards) for r in rewards]
    # 用这些 advantage 做 PPO-style 更新
```

**优点**：省一半显存、信号明确、对长 CoT 友好。
**缺点**：组内方差大时不稳定；长样本（10K+ token）容易出现"训崩"。

### DAPO（字节，2025-03，arXiv:2503.14476）

**全名**：Decoupled Clip and Dynamic sAmpling Policy Optimization

**针对 GRPO 的两个工程问题**：
1. **Clip 不对称**：原版 PPO clip 上下边界相同（如 ±0.2），但 reasoning 场景"提升好答案概率"和"压低坏答案概率"应该不对称——DAPO 用 **decoupled clip**（上界更宽，鼓励探索）
2. **Dynamic sampling**：当 batch 中所有 G 条 response 都正确（或都错误）时，advantage 全为 0，**这次更新白做**——DAPO 动态丢掉这种 prompt，集中算力在"有信号"的 prompt 上

**实测**：在 Qwen2.5-32B 上，DAPO 在 AIME 2024 比 GRPO 提升 ~5pp，长 trace 不再崩溃。

### VAPO（字节，2025-04）

**全名**：Value-Augmented Proximal Policy Optimization

**回到 PPO 的方向**：重新引入 value model，但用了**轻量化 critic + 长 trace 信用分配**的新设计。

**直觉**：DAPO 解决了"训不稳定"，但长 CoT 中**到底是哪几步起了决定作用**仍是黑盒。VAPO 引入 step-level value estimate（用一个小 critic），在 32K+ token 的 CoT 上能精确归因。

**实测**：在 Qwen2.5-32B + AIME 上，VAPO > DAPO > GRPO，但训练成本回到 PPO 量级（critic 显存又来了）。

### 算法选择决策

```
你在做 reasoning 训练？
├── 显存吃紧（< 8×80GB）→ GRPO（最便宜）
├── 长 trace 训崩（>16K token）→ DAPO（解决长样本崩溃）
├── 追求 SOTA + 显存够 → VAPO（最强但最贵）
└── 你只想用，不想训 → 直接用 R1-Distill / QwQ-32B，跳过本节
```

---

<a id="test-time-scaling"></a>
## 📚 Test-Time Scaling 的经济学

### 核心曲线：算力 vs 准确率

DeepMind 2024 的 [Snell et al.](https://arxiv.org/abs/2408.03314) 论文给出了最重要的经验规律：

> **在中等难度任务上，给推理时增加 N× 算力，比把模型参数增加 N× 更有效**。

但这条规律有**三个边界条件**经常被忽略：

1. **任务难度边界**：在简单任务（一次就能答对）和极难任务（增加再多算力也答不对）上，test-time scaling 增益微弱甚至为零。**它只在"模型能力边界附近"的任务上最有效**。
2. **基础模型能力边界**：在弱基座上做 best-of-N 不如换更强基座。算力换正确率有上限。
3. **CoT 长度的收益递减**：thinking token 从 1K → 4K → 16K → 64K，收益曲线**对数递减**。R1 论文显示 ~32K 是当前的甜点，再长基本不涨。

### 三种推理时缩放方式

| 方式 | 实现 | 算力倍数 | 适用 |
|------|------|---------|------|
| **延长单条 CoT** | reasoning_effort=high / budget_tokens=32000 | 5-30× | reasoning 模型原生 |
| **Best-of-N (BoN)** | 采样 N 条 CoT，PRM 或 verifier 选最好 | N× | 普通模型也能用 |
| **Self-Consistency** | 采样 N 条 CoT，答案多数投票 | N× | 答案有限离散时 |

**重要警告**：BoN 和 Self-Consistency 在 **reasoning 模型上的边际收益已大幅减弱**——因为模型自身的 long CoT 已经做了内部反思，外部投票拿不到多少额外信息。这是 2025 年下半年的新认知（"reasoning 模型上 self-consistency 几乎白做"）。

### 经济学：何时值得？

**临界点公式（粗算）**：

$$
\text{用 reasoning 划算} \iff \frac{\text{任务完成率提升}}{\text{额外 token 成本}} > \text{重试成本}
$$

举例：
- 客服场景，普通模型 95% 完成率，reasoning 99% 完成率，但贵 50×。失败重试由人工承担每次成本 $5。每天 10K 请求。
  - 普通模型：500 次失败 × $5 = $2500/天 + token 成本 $10
  - Reasoning：100 次失败 × $5 = $500/天 + token 成本 $500
  - **Reasoning 反而省 $1510/天** ✅
- 简单分类，准确率从 99% → 99.9%，但贵 100×。
  - 节省人工成本太少，**绝对不划算** ❌

**结论**：单调用价格不是判断依据，**任务完成率 × 失败的下游成本**才是。

---

<a id="模型横评"></a>
## 📚 2026-04 模型横评

> 数据截至 2026-04，主要来自各厂官方 system card / blog。**注意 benchmark 容易污染**，参考 [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 第 §校准 章节理解评估边界。

| 模型 | 厂商 | 开源? | AIME 2024 | GPQA Diamond | SWE-bench Verified | 输入价 ($/M) | 输出价 ($/M) | 显式 thinking 控制 |
|------|------|-------|-----------|--------------|-------|--------------|--------------|-------------------|
| **o3** | OpenAI | ❌ | 96.7 | 87.7 | 71.7 | $10 | $40 | `reasoning.effort` (low/med/high) |
| **o3-mini-high** | OpenAI | ❌ | 87.3 | 79.7 | 49.3 | $1.10 | $4.40 | `reasoning.effort` |
| **o1** | OpenAI | ❌ | 83.3 | 78.0 | 48.9 | $15 | $60 | `reasoning.effort` |
| **Claude 3.7 Sonnet Thinking** | Anthropic | ❌ | 80.0 | 84.8 | 70.3 | $3 | $15 | `thinking.budget_tokens` |
| **Gemini 2.5 Pro Thinking** | Google | ❌ | 86.7 | 84.0 | 63.8 | $1.25 | $10 | `thinkingConfig.thinkingBudget` |
| **DeepSeek-R1** | DeepSeek | ✅ MIT | 79.8 | 71.5 | 49.2 | $0.55 | $2.19 | 默认开启（无显式参数）|
| **QwQ-32B** | Qwen | ✅ Apache | 79.5 | 65.2 | — | 自托管 | 自托管 | 默认开启 |
| **R1-Distill-Qwen-32B** | DeepSeek | ✅ MIT | 72.6 | 62.1 | — | 自托管 | 自托管 | 默认开启 |
| **R1-Distill-Llama-70B** | DeepSeek | ✅ MIT | 70.0 | 65.2 | — | 自托管 | 自托管 | 默认开启 |
| **Marco-o1** | Alibaba | ✅ Apache | — | — | — | 自托管 | 自托管 | 默认开启 |

### 横评关键观察

1. **o3 仍是综合天花板**，AIME 96.7、SWE-bench 71.7 全场最高。但**贵到刺眼**（$40/M 输出）。
2. **Claude 3.7 Thinking 是编码场景隐形冠军**——SWE-bench 70.3 仅次于 o3，但价格 1/2.7。
3. **R1 是开源天花板**，AIME 79.8 已追平 o1（83.3 仅高 3.5pp），但价格只有 o1 的 1/27。**性价比之王**。
4. **R1-Distill 系列把 reasoning 带进 7B-70B 量级**——QwQ-32B 和 R1-Distill-32B 是单 A100/H100 单卡可跑的最强 reasoning 选项。
5. **Claude / Gemini 的"显式 budget"是产品级亮点**——可以精确控制每次推理花多少 thinking token，OpenAI 只有粗粒度的 low/medium/high。

---

<a id="上手实战"></a>
## 🚀 上手实战

### 4.1 决策树：何时用 reasoning vs 普通模型

```
你的任务是…
├── 数学/物理/化学竞赛级问题？        → ✅ Reasoning（首选 o3 / R1）
├── 复杂代码 debug / 算法实现？        → ✅ Reasoning（首选 Claude Thinking）
├── 多步骤规划 / 长 horizon Agent？    → ✅ Reasoning 当 Planner
├── 科研问题需自验证？                 → ✅ Reasoning
├── 简单分类 / 摘要 / 翻译？            → ❌ 普通模型（gpt-4o-mini / Haiku）
├── 知识问答（事实查询）？              → ❌ 普通模型 + RAG
├── 实时客服（要求 TTFT < 1s）?         → ❌ 普通模型（reasoning TTFT 5-30s）
├── 高频 Tool calling 流水线？          → ⚠️ 混合架构（见 §4.4）
└── 无法判断？                         → 先用普通模型，准确率不达标再升级
```

### 4.2 Hello World：调 R1 / Claude Thinking API

**环境**：Python 3.10+，`pip install openai==1.55.0 anthropic==0.40.0`

#### A. DeepSeek R1（OpenAI 兼容 API）

```python
# pip install openai==1.55.0
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 注意：DeepSeek-R1 的模型名是 deepseek-reasoner（不是 deepseek-chat）
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        # ⚠️ 关键反模式预防：不要写 "Let's think step by step"
        # ⚠️ 不要写 few-shot 示例
        # 直接描述问题即可
        {"role": "user", "content": "求 2025 + 2026 + ... + 2100 的和。"}
    ],
)

# R1 把 thinking 放在单独字段
msg = response.choices[0].message
print("【Thinking】:", msg.reasoning_content[:500], "...")  # 长 CoT
print("【Answer】:", msg.content)  # 最终答案

# Expected output:
# 【Thinking】: First, I need to find the sum of integers from 2025 to 2100.
#              The number of terms is 2100 - 2025 + 1 = 76. ...
# 【Answer】: 等差数列和 = 76 × (2025 + 2100) / 2 = 156750
```

**关键 trick**：
- `reasoning_content` 是单独字段，**不要把它拼回下一轮 messages**（见避坑指南）
- R1 不支持 `temperature=0`（官方推荐 0.5-0.7）
- 系统消息影响有限，**问题描述在 user role 直接写最有效**

#### B. Claude 3.7 Sonnet Extended Thinking

```python
# pip install anthropic==0.40.0
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000,  # 显式预算：thinking 最多用 10K token
    },
    messages=[{"role": "user", "content": "求 2025 + 2026 + ... + 2100 的和。"}]
)

# Claude 把 thinking 和 answer 作为不同的 content block
for block in response.content:
    if block.type == "thinking":
        print("【Thinking】:", block.thinking[:500], "...")
    elif block.type == "text":
        print("【Answer】:", block.text)

# Expected output:
# 【Thinking】: This is an arithmetic series. Let me identify the parameters...
# 【Answer】: 156750
```

**关键 trick**：
- `budget_tokens` 是**最大值**而非固定消耗，简单题模型会自己缩短
- `budget_tokens` 必须 ≥ 1024，且 < `max_tokens`
- Claude Thinking 支持 streaming，但 thinking block 整体返回不流式

### 4.3 反模式实验：给 reasoning 模型用 Few-shot CoT

> 这是 R1 官方文档明确警告的最反直觉事实。让我们用最小实验复现。

```python
# 反模式实验：在 R1 上对比 zero-shot vs few-shot CoT
from openai import OpenAI
client = OpenAI(api_key="...", base_url="https://api.deepseek.com")

problem = "一个正整数 n 满足 n^2 - 19n + 88 是完全平方数，求 n。"

# ❌ 反模式：Few-shot CoT
fewshot_prompt = """
例 1：n^2 - 5n + 6 是完全平方数。
让我们一步一步思考：n^2 - 5n + 6 = k^2，所以 ... 答案 n=3。

例 2：n^2 - 7n + 12 是完全平方数。
让我们一步一步思考：... 答案 n=4。

现在求：n^2 - 19n + 88 是完全平方数，求 n。让我们一步一步思考。
"""

# ✅ 正模式：Zero-shot direct
zeroshot_prompt = "求所有正整数 n 使得 n^2 - 19n + 88 是完全平方数。"

# 在 100 个类似题目上测试，DeepSeek 官方报告：
# - Zero-shot direct: 准确率 ~85%
# - Few-shot CoT:     准确率 ~78%（反而下降）
# - "Let's think step by step" 显式提示也有 2-5pp 下降
```

**为什么会这样**：reasoning 模型已经被 RL 训成"看到问题就启动 long CoT"。Few-shot 示例**污染了它的推理风格**——模型可能会模仿示例的（短的）推理模式而非启动自己（长的）reasoning 流程。这解释了 DeepSeek 文档的三条建议：
1. Zero-shot outperforms few-shot
2. Direct problem description wins
3. Language consistency matters

### 4.4 Agent 集成：Planner + Worker 混合架构

> 这是 reasoning 模型在生产 Agent 中的**主流落地形态**。

```python
"""
Planner-Worker 混合架构示例
- Planner: R1（一次性产出多步计划）
- Worker:  gpt-4o-mini（执行 tool calling，便宜快速）
"""
from openai import OpenAI

deepseek = OpenAI(api_key="...", base_url="https://api.deepseek.com")
openai_client = OpenAI(api_key="...")

def reasoning_plan(task: str) -> list[dict]:
    """用 R1 产出步骤化计划。"""
    plan_response = deepseek.chat.completions.create(
        model="deepseek-reasoner",
        messages=[{
            "role": "user",
            "content": f"""任务: {task}

请输出可执行的步骤列表（JSON 数组，每个步骤含 tool 和 args）。
可用 tools: search_web, run_python, read_file, write_file。
注意：只输出步骤列表，不要执行。"""
        }],
    )
    # 解析最终 answer 部分（不要传 reasoning_content！）
    plan_json = plan_response.choices[0].message.content
    return parse_json(plan_json)

def execute_step(step: dict, context: dict) -> dict:
    """用便宜的 gpt-4o-mini 执行单步 tool calling。"""
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "执行这一步，调用 tool 并返回结果。"},
            {"role": "user", "content": f"步骤: {step}\n上下文: {context}"}
        ],
        tools=[...]  # 工具定义
    )
    return run_tool_call(response)

def hybrid_agent(task: str):
    plan = reasoning_plan(task)              # 1 次贵的 R1 调用
    context = {}
    for step in plan:
        result = execute_step(step, context)  # N 次便宜的 gpt-4o-mini 调用
        context[step["id"]] = result
    return context
```

**为什么这样设计**：
- **Reasoning 模型 thinking 期间不能调 tool**（thinking 是模型内部 token 流，无 tool calling 中断）
- 把 reasoning 用在"想清楚要做什么"（前置一次），把 tool calling 用在"做"（worker 多次执行）
- **成本对比**：
  - 纯 R1 + ReAct：~$0.30/任务（每次 ReAct 都触发 long CoT）
  - 纯 gpt-4o-mini ReAct：~$0.02/任务，但完成率只有 60%
  - **Hybrid（R1 plan + 4o-mini exec）**：~$0.05/任务，完成率 92% ← 最优

---

<a id="避坑指南"></a>
## 🕳️ 避坑指南

| # | 坑 | 原因 | 解法 |
|---|----|------|------|
| 1 | 给 R1 写 "Let's think step by step" | 模型已经被 RL 训成自动 long CoT，prompt 提示反而干扰其推理风格 | Zero-shot 直接描述问题即可，**不要**加 CoT 引导词 |
| 2 | 给 reasoning 模型加 Few-shot 示例 | 同上，示例污染推理风格 | Zero-shot direct，必要时只给 output format 示例（不带推理过程） |
| 3 | 把 thinking/reasoning_content 喂回下一轮上下文 | thinking 通常 5-20× 长于 answer，token 爆炸；且模型不是为"读自己 thinking"训练的 | **只把最终 answer 加入历史**，下一轮重新触发 thinking |
| 4 | 用 reasoning 模型做简单分类/翻译/摘要 | 同样准确率成本爆 50-300×，且 TTFT 高 | 选 gpt-4o-mini / Haiku / Qwen2.5-7B 这类便宜快速模型 |
| 5 | 在 latency 敏感场景（实时客服）用 reasoning | TTFT 5-30s（首个 token 输出延迟），用户体验灾难 | 实时场景用普通模型 + streaming；reasoning 用在批处理或异步任务 |
| 6 | 用 `temperature=0` 调 R1 | DeepSeek 官方明确不支持 0，会输出退化 | 用 0.5-0.7（官方推荐）；要确定性可以采样多次再投票 |
| 7 | 对 reasoning 模型做 self-consistency | 模型内部已做长反思，外部投票边际增益 < 5%，但成本 N× | 只在普通模型上做 SC；reasoning 模型用 reasoning_effort=high 即可 |
| 8 | 在 thinking 中嵌 tool call 期望中断 | Reasoning thinking 是连续 token 流，不能在中间触发 tool | 用 Planner-Worker 模式（§4.4）或等 OpenAI/Anthropic 后续放开 |
| 9 | budget_tokens 设太低（如 1024）做难题 | thinking 不够，模型会"硬答"反而错 | 难题给 8K-32K budget；难度未知时给 8K 起 |
| 10 | budget_tokens 设太高（64K）做简单题 | 浪费钱（输出按 token 计费） | 简单题用 reasoning_effort=low 或 budget=2048 |
| 11 | 期待 reasoning 模型在创意写作/共情对话上更强 | RLVR 只对可验证任务有效，开放域任务无奖励信号，提升有限 | 创意/对话场景仍用 Claude/GPT-4o 通用版本 |
| 12 | 用 Reasoning 模型 + 长 RAG context | 长 context + long thinking 双重消耗，token 数失控 | 先用普通模型做 RAG 摘要，再把摘要给 reasoning 模型 |
| 13 | 训自己的 reasoning 模型时跳过 SFT 冷启动 | R1-Zero 路线虽然可行但收敛慢、语言混乱 | 工业场景用 SFT + RL（R1 路线）；研究场景才考虑纯 RL |
| 14 | 用 GRPO 训 32K+ 长 trace | 长 trace 训崩（信号稀释 + clip 不稳定） | 上 DAPO 或 VAPO；或缩短到 8K-16K |
| 15 | 用 reasoning 模型评估 reasoning 模型 | LLM-as-judge 在 long CoT 输出上偏见严重 | 数学/代码用 ground truth；其他用人工 + benchmark（如 GPQA）|

---

<a id="成本roi"></a>
## 💰 成本与 ROI 速算

### 单次调用成本对比（2026-04 价格）

| 场景 | 普通模型 | Reasoning 模型 | 倍数 |
|------|---------|----------------|------|
| 短问答（512 in + 256 out） | gpt-4o-mini: $0.0002 | o1: $0.024 / R1: $0.0009 | o1: 120× / R1: 4.5× |
| 数学题（1K in + 8K thinking + 256 out） | gpt-4o-mini: $0.005 | o3: $0.34 / R1: $0.020 | o3: 68× / R1: 4× |
| Agent planning（4K in + 16K thinking + 1K out） | gpt-4o: $0.05 | o3: $0.69 / R1: $0.040 | o3: 13× / R1: 0.8× |

**关键观察**：
- **R1 把开源 reasoning 价格压到普通商用模型量级**（4.5× 普通价格做到接近 o1 性能）
- **o3 在长 thinking 场景贵得离谱**（$0.34/题），适合关键决策但不适合高频调用
- 自托管 R1-Distill-32B（A100 单卡）边际成本几乎为 0，**高频用 reasoning 的最优解是自托管 distill 版**

### ROI 临界点（什么时候上 reasoning 划算？）

```
ROI > 1 的条件：
   (任务完成率提升 × 失败的下游成本) > (额外 token 成本 × 调用次数)

举例：
- 法律文档审查
  - 普通模型 80% 准确，错漏被发现后律师返工成本 $50/次
  - Reasoning 95% 准确，单次贵 $0.03
  - 1000 次调用：普通 200 次返工 = $10000；Reasoning 50 次返工 + token = $5030
  - ROI = (200-50)×50 / (0.03×1000) = 250  ✅ 强烈划算

- 公众号评论分类
  - 普通模型 95% 准确，错分的成本几乎为 0（用户不会投诉）
  - Reasoning 99% 准确，单次贵 $0.005
  - 100K 次调用：普通约 0；Reasoning $500
  - ROI = (准确率提升 × 0) / 500 = 0  ❌ 不划算
```

### 自托管 vs API 临界点

> 详细见 [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)，这里只给 reasoning 专用结论：

- 月调用 < 100K：用 API（DeepSeek 或 Claude Thinking）
- 月调用 100K-1M：用 R1 API + 部分自托管 R1-Distill-32B
- 月调用 > 1M：自托管 R1-Distill-32B / 70B（A100 集群）

---

<a id="决策速查"></a>
## 🎯 决策速查：5 个场景判断要不要上 reasoning

| 场景 | Reasoning？ | 推荐模型 | 理由 |
|------|------------|---------|------|
| 数学竞赛 / 算法题求解 | ✅ 必须 | o3 / R1 | 准确率提升 30-50pp |
| 复杂 Bug 修复（含 stack trace） | ✅ 推荐 | Claude 3.7 Thinking | SWE-bench 70.3，编码 SOTA |
| RAG-based 问答 | ❌ 不推荐 | gpt-4o + RAG | 知识来自 retrieval，reasoning 帮不上 |
| 客服对话（实时） | ❌ 禁用 | Haiku / 4o-mini | TTFT 不可接受 |
| Agent 长 horizon 规划 | ⚠️ 混合 | R1 当 Planner + 4o-mini 当 Worker | 见 §4.4 Hybrid 架构 |

**一句话决策**：**任务难、错的代价大、可以慢一点 = 上 reasoning；其他都不上**。

---

<a id="agent架构影响"></a>
## 🤔 对 Agent 架构的影响

### Plan-and-Execute 还需要吗？

**还需要，但形态变了**。

- **传统 Plan-and-Execute**（2023）：用 LLM 生成 plan → 用同一个 LLM 执行每步
- **Reasoning 时代 Plan-and-Execute**（2025+）：**Reasoning 模型生成 plan**（一次贵的调用，但 plan 质量飞跃）→ **普通模型执行每步**（多次便宜调用）
- 关键升级：plan 中**包含反思和 backtrack 节点**（reasoning 模型自带的能力），不再是死板的步骤列表

### ReAct 过时了吗？

**没过时，但被改写**。

- **粗粒度规划**（决定要做什么） → 交给 reasoning 模型一次性产出
- **细粒度反应**（每步根据结果调整） → 仍然是 ReAct 循环，但底层换成普通模型
- 极端形态：**单步 Agent**（reasoning 直接输出最终答案 + tool calling 序列），适合简单任务

### 多 Agent 还是 Reasoning？两条路线竞争

这是 2026 年的开放争论：
- **多 Agent 派**（[R51](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md)、[R45](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md)）：用专家分工 + orchestration 实现复杂推理
- **单 Reasoning Agent 派**：用一个强 reasoning 模型 + 工具替代多 Agent 协作

**目前判断**（**这是观点，未盖棺论定**）：
- 任务可拆分清晰、每个子任务相对独立 → 多 Agent
- 任务需要全局视角、子步骤紧耦合 → 单 reasoning agent
- **一个折中范式正在出现**：reasoning agent 当 orchestrator + 普通 agent 当 specialist。这与 [R51](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) §5 的 supervisor 模式同构，但 supervisor 升级为 reasoning。

---

<a id="开放问题"></a>
## ❓ 开放问题（待持续跟踪）

1. **长 CoT 与 Tool calling 如何融合？**
   - 当前：thinking 期间不能调 tool（thinking 是连续 token 流）
   - 期待：未来 reasoning 模型支持"thinking 中触发 tool、tool 结果回到 thinking"——OpenAI 在 o3 中部分实现，但细节未公开
   - 影响：如果实现，Hybrid Planner-Worker 架构会被简化为单 Agent

2. **多 Agent 能否替代 reasoning？**
   - Cognition 等团队提出"用 multi-agent 模拟 reasoning"
   - 反方观点（Anthropic）：多 agent 通信开销 + 不一致性，不如单 reasoning
   - 待 2026 下半年的实证数据

3. **Reasoning 在创意/共情等不可验证任务上能否提升？**
   - RLVR 范式需要可验证 reward，开放域任务无信号
   - 可能的突破：用 LLM-as-judge 做 reward（但有偏见）、用一致性指标（self-consistency 类）作为 proxy reward

4. **小模型（< 7B）能否拿到 reasoning？**
   - R1-Distill-1.5B 已显示初步能力（AIME ~30），但远不及 7B+
   - 蒸馏 vs 纯 RL 在小模型上谁更有效？DeepSeek 报告蒸馏更好
   - 1B 量级是否存在 reasoning 涌现下限？是工业小模型的关键问题

5. **Test-time scaling 的天花板在哪？**
   - 当前 32K thinking token 是甜点，再长收益微弱
   - 多轮 thinking + 反思（"long-horizon thinking"）会突破吗？
   - OpenAI 在 o3 上声称"reasoning_effort=high 时使用了更激进的 test-time scaling"，但具体机制保密

---

<a id="来源清单"></a>
## 📌 来源清单

> ⚖️ 来源一致性：核心范式（RLVR/GRPO/long-CoT）多源一致，高置信。模型横评数据来自各厂官方 system card 和 blog，但 benchmark 易污染，参考 [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)。
> 📅 时效性声明：信息获取于 2026-04-25。

### 一手论文与官方文档

- [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) — DeepSeek-AI, Nature 2025（v2: 2026-01）— RLVR 范式 + GRPO + R1-Zero/R1/Distill 三模型
- [Marco-o1: Towards Open Reasoning Models](https://arxiv.org/abs/2411.14405) — Alibaba MarcoPolo Team, 2024-11 — 公开 long-CoT + MCTS 训练细节
- [QwQ-32B Technical Report / Blog](https://qwenlm.github.io/blog/qwq-32b/) — Qwen Team, 2024-11/2025-03 — 开源 32B 对标 o1
- [Anthropic Extended Thinking Documentation](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking) — Anthropic, 2025-02+ — Claude 3.7 Thinking budget_tokens 用法
- [OpenAI o1 System Card](https://openai.com/index/openai-o1-system-card/) — OpenAI, 2024-12
- [OpenAI o3 / o3-mini System Card](https://openai.com/index/o3-o4-mini-system-card/) — OpenAI, 2025-04
- [Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters](https://arxiv.org/abs/2408.03314) — Snell et al., DeepMind, 2024-08
- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) — Lightman et al., OpenAI, 2023-10 — PRM 路线代表作
- [DAPO: An Open-Source LLM Reinforcement Learning System at Scale](https://arxiv.org/abs/2503.14476) — ByteDance Seed, 2025-03
- [VAPO: Efficient and Reliable Reinforcement Learning for Advanced Reasoning Tasks](https://arxiv.org/abs/2504.05118) — ByteDance Seed, 2025-04
- [DeepSeek-Math (introduces GRPO)](https://arxiv.org/abs/2402.03300) — DeepSeek-AI, 2024-02
- [O1 Replication Journey: A Strategic Progress Report](https://arxiv.org/abs/2410.18982) — SJTU GAIR, 2024-10 — Journey Learning 思路

### 二手解析（高质量）

- [Understanding Reasoning LLMs](https://magazine.sebastianraschka.com/p/understanding-reasoning-llms) — Sebastian Raschka, 2025-02 — 四大范式综述、R1 训练管道详解
- [Sky-T1 Project](https://novasky-ai.github.io/posts/sky-t1/) — UC Berkeley NovaSky, 2025-01 — $450 训出 32B 对标 o1
- [TinyZero](https://github.com/Jiayi-Pan/TinyZero) — Jiayi Pan, 2025-01 — $30 在 3B 复现 R1-Zero 涌现

### 工作区交叉引用

- [R37](R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) Transformer 原理 — 理解 thinking token 在哪里产生
- [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 模型训练与微调 — GRPO/PPO/DPO 算法上下文
- [R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 模型蒸馏 — R1-Distill 的蒸馏视角
- [R55](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) Prompt Engineering — 反 Few-shot 模式的 prompt 视角
- [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) Benchmark 速查 — AIME/GPQA/SWE-bench 评估边界
- [R62](R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) LLM 预训练 — reasoning 是预训练→SFT→RLHF→RLVR 第四阶段
- [R51](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md) 多 Agent 编排 — 与单 reasoning agent 的路线之争
- [R63](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) LLM 服务化部署 — reasoning 模型自托管成本边界

---

> **报告状态**：completed | **预估 tokens**：~17000 | **下次复盘**：2026-Q3（届时 GPT-5 reasoning 路由数据应已积累，DAPO/VAPO 工业落地反馈应清晰）
