---
title: LLM 预训练全景：从数据到 Scaling Law
aliases: [R62, LLM预训练调研, 预训练全景, Scaling Law 调研, Pretraining Panorama]
tags: [pretraining, scaling-law, chinchilla, data-engineering, llama3, deepseek-v3, fineweb]
date: 2026-04-24
category: 理论与架构
report_id: R62
tokens: ~15000
status: completed
related:
  - "[R37](R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md)"
  - "[R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R56](R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)"
  - "[R54](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R54_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E6%80%BB%E8%A7%88.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# LLM 预训练全景：从数据到 Scaling Law

> **一句话概括**：应用工程师虽然不会亲手训 GPT-4，但读懂**预训练数据构成 + Scaling Law + 预训练 vs 后训练边界**，能解释你遇到的 80% 模型"为什么这样"——小模型胡说、知识截止、中文能力差、微调不动某些能力，全都回到这里。本报告不做 Hello World（训一次 GPT-4 约 $78M，成本太高），改以「10 篇必读论文路线图」收尾。
>
> **研究日期**：2026-04-24
> **关联报告**：[R37](R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) Transformer 底层（"模型长什么样"） · [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 后训练（SFT/DPO/GRPO，"训完怎么对齐"） · [R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 蒸馏（"训完怎么瘦身"） · [R56](R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) Tokenization（"文本怎么变 Token"）
> **增量价值**：工作区此前 58 篇报告均未系统覆盖预训练。R52 明确从 SFT 起点开始，R37 讲 Attention 但未触及"如何用 15 万亿 Token 把模型从随机初始化推到能写代码"。本报告填补 LLM 底层三部曲（架构 / 预训练 / 后训练）中缺失的第二块。

---

## TL;DR 速查卡

| 维度 | 结论 |
|------|------|
| **预训练的本质** | 在海量（现在 ≥10T tokens）无标注文本上，用 next-token prediction 让模型"读完整个互联网"，学会语言模式 + 世界知识 + 推理雏形。SFT/RLHF 不教模型新知识，只是**唤醒**预训练学到的。 |
| **Scaling Law 的两次校正** | Kaplan (2020, OpenAI)："参数越大越好，数据够就行" → Chinchilla (2022, DeepMind)："**参数:数据 ≈ 1:20** 才最优" → Llama 3 (2024, Meta)："推理时代应故意**过训练 100×+**，因为推理成本远大于训练成本" |
| **现代预训练数据配方（2025 基线）** | Common Crawl 清洗（≈55%）+ 代码（10-20%，GitHub/StackExchange）+ 学术/书籍（≈10%）+ 多语言（≈10%）+ 合成/高质量筛选（≈10-15%，逐年上升）。**数据质量 ＞ 数据数量**，这是 2024 后共识。 |
| **训一次要多少钱** | GPT-3 (175B, 300B tok) ≈ $4.6M (2020) · Llama 3 405B (15.6T tok) ≈ $60-80M · **DeepSeek-V3 (671B MoE, 14.8T tok) ≈ $5.6M**（FP8 + MoE 降本的里程碑） |
| **数据墙时间表** | Villalobos et al. (2024) 估计：**英文高质量文本将在 2028±2 年耗尽**。救命方案：合成数据、多模态数据、持续数据采集 |
| **应用工程师必记三条** | ① 预训练决定知识上限，SFT 只能调风格 ② 知识截止日期≈模型能解释时事的天花板 ③ **小模型不是大模型的"低配"，是完全不同的知识压缩产物**——别指望 1.5B 能像 70B 那样推理 |
| **最危险的误解** | "Scaling Law 已经到头" —— 数据墙是真命题，但合成数据 + 多模态 + MoE 让有效 Scaling 还能跑 2-3 年；**过度乐观和过度悲观都错** |

---

## 目录

1. [🔭 定位透镜：纵横坐标](#定位透镜)
2. [📚 预训练 vs SFT vs RLHF：术语澄清](#术语澄清)
3. [📚 数据工程：从 Common Crawl 到 FineWeb](#数据工程)
4. [📚 Scaling Laws：Kaplan / Chinchilla / Llama 3 三次校正](#scaling-laws)
5. [📚 训练基础设施：3D 并行与成本账本](#训练基础设施)
6. [📚 Tokenizer 训练：被低估的地基](#tokenizer-训练)
7. [📚 预训练数据配方的三大趋势](#数据配方趋势)
8. [📚 CPT vs SFT 的边界](#cpt-vs-sft)
9. [📚 五家厂商预训练策略横评](#厂商横评)
10. [🕳️ 避坑指南](#避坑指南)
11. [💰 成本与 ROI 速算](#成本roi)
12. [📖 10 篇必读论文路线图](#论文路线图)
13. [🎯 决策速查](#决策速查)
14. [📌 来源清单](#来源清单)

---

<a id="定位透镜"></a>
## 🔭 定位透镜：纵横坐标

### 纵轴 · 演化脉络

```
2020.05  GPT-3 (OpenAI)          175B 参数  300B tokens        ~$4.6M    ← 算力缩放范式确立
         └─ Kaplan Scaling Law：参数为王，数据是配角

2022.03  Chinchilla (DeepMind)    70B 参数  1.4T tokens         ~$5M+    ← 第一次校正
         └─ "当前 LLM 严重欠训练"；参数:数据 ≈ 1:20 才最优

2023.02  Llama 1 (Meta)           7-65B     1-1.4T tokens       ~$2-5M   ← 开源起点
         └─ 首个"完全按 Chinchilla 打"的开源模型

2023.07  Llama 2                  7-70B     2T tokens           ~$20M    ← 引入 RLHF 标准范式
         └─ 数据仍略低于 Chinchilla 最优点

2024.04  Llama 3                  8-70B     15T tokens          ~$20-40M ← 第二次校正
         └─ "过训练"时代：8B 也喂 15T，远超 Chinchilla 最优的 160B
         └─ 推理总成本 >> 训练成本，所以训练阶段多花一点很划算

2024.12  DeepSeek-V3             671B MoE  14.8T tokens         ~$5.6M  ← 效率革命
         └─ FP8 混合精度 + MoE 激活 37B + 多 Token 预测 = 以 1/10 预算达 GPT-4o 水平
         └─ 公开披露最彻底的前沿模型（技术报告 >50 页）

2025+    数据墙焦虑 + 合成数据崛起 + 多模态数据 + 1T 参数 MoE 成为常态
```

### 横轴 · 竞争格局（五家预训练策略差异）

| 厂商 | 代表模型 | 公开度 | 核心特征 | 预训练哲学 |
|------|---------|--------|---------|-----------|
| **OpenAI** | GPT-4 / o1 / GPT-5 | **闭源**（只讲能力不讲细节） | 算力堆料 + 极强后训练 | "Secret sauce 绝不公开" |
| **Anthropic** | Claude 3.7 / 4 | **闭源**（只发 Model Card） | Constitutional AI + 长上下文优先 | 安全压倒透明度 |
| **Meta** | Llama 3 / 4 | **半公开**（权重 + 简化报告） | 工业级对标 + 生态战略 | "给开源社区一个能打的基座" |
| **DeepSeek** | V2/V3/R1 | **近乎全公开**（详细技术报告 + 权重） | MoE + FP8 + 效率极致 | "用工程创新抵消算力差距" |
| **Qwen (阿里)** | Qwen2.5 / Qwen3 | **半公开**（权重 + 中等详细报告） | 中文 tokenizer 优化 + 多尺寸齐全 | "覆盖从 0.5B 到 72B 全尺寸生态" |
| **Mistral** | Mistral 7B / Mixtral | **半公开**（早期权重 + 简报告，近期转向闭源） | 欧洲视角 + MoE 早期探索 | "小而精，不跟巨头比参数" |

### 交叉判断

- **纵轴结论**：Scaling Law 不是"撞墙即死"，而是"拐弯进化"——从 Kaplan 的"堆算力"，到 Chinchilla 的"均衡"，到 Llama 3 的"为推理过训练"，每次都是更精细的工程选择，而不是范式终结。
- **横轴结论**：如果想**搞懂前沿模型是怎么造的**，读 **DeepSeek-V3 + Llama 3 技术报告**足够——这两家是 2025 年公开度最高的参考系。OpenAI/Anthropic 的细节永远猜不到，不值得在这上面浪费时间。
- **给应用工程师的独立判断**：预训练是 LLM 基础设施层，和你的关系像"操作系统内核"——不用自己写，但**必须懂原理**。否则你会在 Prompt Engineering 上花时间试错那些预训练阶段就锁死的能力边界（例如 7B 模型永远不会有 70B 那种推理链深度）。

---

<a id="术语澄清"></a>
## 📚 预训练 vs SFT vs RLHF：术语澄清

> **坑**：本工作区历史报告里偶尔有把"训练""微调""对齐"混用的情况，这是行业通病。先把术语钉死。

### 完整训练链路全景

```
          阶段                      数据                 目标              典型成本       谁做
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ① Pretraining (预训练)    │ 15T+ tokens         │ next-token        │ $10-100M   │ 基座厂商  │
│   next-token prediction   │ 网页+代码+书籍       │ prediction        │            │ (OpenAI/  │
│   用自监督学会             │ 无标注               │ 学会语言+世界知识  │            │ Meta等)   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ② Continued Pretraining   │ 领域语料            │ 同 ①              │ $10K-1M   │ 有领域数据 │
│   (CPT, 持续预训练)       │ (如医疗/法律/代码)   │ 注入领域知识       │            │ 的中型玩家 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ③ SFT (监督微调)          │ 10K-1M             │ 模仿人类示范       │ $100-10K  │ 几乎所有   │
│                           │ 指令-回答对          │ 学会"说人话"      │            │ 应用团队   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ④ 偏好对齐 (DPO/RLHF)     │ 10K-100K           │ 人类偏好对比       │ $1K-100K  │ 中大型团队 │
│                           │ (好答案, 坏答案)     │ 学会"说好话"      │            │            │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ⑤ RL 推理强化 (GRPO/PPO) │ 任务+可验证奖励     │ 奖励最大化         │ $10K-10M  │ 前沿实验室 │
│                           │ (数学/代码)          │ 学会"想清楚"       │            │            │
└─────────────────────────────────────────────────────────────────────────────────┘
                             ①②                         ③④⑤
                        ─── 预训练层 ───          ──── 后训练层（见 R52）────
```

### 一图看清**哪一步教了什么**

| 能力 | 主要获得阶段 | 后续阶段能改动吗？ |
|------|------------|----------------|
| 语法、常识、世界知识 | ① 预训练 | SFT 几乎**改不动**，只能微调表达 |
| 通用推理能力雏形 | ① 预训练 | RL 能**放大**，但不能从零建立 |
| 指令遵循（听话） | ③ SFT | 预训练模型几乎不会听话 |
| 风格/语气/人格 | ③ SFT + ④ DPO | 这是对齐阶段的主要产物 |
| 拒绝有害请求 | ④ DPO/RLHF | 对齐阶段注入 |
| 深度推理链（思考） | ⑤ RL (GRPO) | DeepSeek-R1 证明可由 RL 涌现 |

> **关键结论**：如果你发现 LLM "不会 X"，99% 是预训练阶段没学过 X，后面各种微调都救不回来。这就是为什么应用工程师**选对基座**比"反复调 Prompt"重要 10 倍。

---

<a id="数据工程"></a>
## 📚 数据工程：从 Common Crawl 到 FineWeb

> **行业内部玩笑**："LLM 预训练的 70% 工程师时间在洗数据，剩下 30% 在吐槽数据。" 这不夸张。

### 数据的工业流水线（6 道工序）

```
Common Crawl (原始)
   │  ~900 TB/月、压缩 ~80 TB、文本 ~400B tokens/月
   ▼
1. 语言识别 → 按语言分桶 (fastText, CLD3)
   │  只保留目标语言（英文通常占 45%）
   ▼
2. 质量过滤 → 去广告、菜单、导航、垃圾页
   │  规则 + 分类器（如 DCLM fastText classifier）
   │  关键指标：平均句长、标点比例、重复 n-gram 率
   ▼
3. 去重 → MinHash LSH / SimHash / Bloom Filter
   │  近重复 & 精确重复，通常砍掉 60-80% 文本
   ▼
4. 去污染 → 排查测试集泄露
   │  常用测试集（MMLU/HumanEval 等）做 n-gram 匹配剔除
   ▼
5. 有害内容过滤 → PII / NSFW / 暴力
   │  分类器 + 关键词列表
   ▼
6. 质量重排 → 给每个文档打分
   │  高分文档多采样几次（upsampling）
   ▼
干净预训练数据（~10-15% of 原始）
```

### 主流公开数据集速查

| 数据集 | 发布 | 规模 | 来源 | 一句话特点 |
|--------|------|------|------|----------|
| **C4** | 2019 Google | ~156B tok | CC 清洗 | T5 原始数据，过滤偏激进 |
| **The Pile** | 2020 EleutherAI | 825 GB | 22 个源 | 第一个"多源混合"开源数据集 |
| **RedPajama** | 2023 Together | 1.2T tok | 复现 Llama 1 | 证明"开源可以复现 Meta 的配方" |
| **RefinedWeb** | 2023 Falcon | 5T tok | 纯 CC | 只用 CC 也能打，颠覆"必须多源"迷信 |
| **Dolma** | 2024 AI2 | 3T tok | 多源 | 伴随 OLMo 全开源，可追溯每条数据来源 |
| **FineWeb** | 2024 HuggingFace | **15T tok** | 96 期 CC | 目前**最干净的开源英文 CC 清洗数据** |
| **FineWeb-Edu** | 2024 HuggingFace | 1.3T tok | FineWeb 高分子集 | "只留教育内容"，训小模型效果反超 15T 原版 |
| **Matrix / WuDao** | 2021- 智源 | 多 T | 中文为主 | 国产早期重要中文预训练数据 |
| **Chinese-LLaMA** 系列 | 2023- | - | 中文社区 | 为中文 LLM 微调的开源配方 |

### FineWeb 的里程碑意义（2024 重点）

HuggingFace 2024 发布的 FineWeb **证明了两件事**：

1. **清洗流水线的威力**：同规模 tokens 下，FineWeb 训出的模型 MMLU 比 C4 训的高 **3-5 个点**——"只换数据不换模型"就能涨。
2. **质量 > 数量**：**FineWeb-Edu 只用 1.3T** tokens 但针对教育主题筛选，小模型（1-3B 规模）下游表现反而胜过 15T 的 FineWeb 全集。这是 2024 年数据配方设计的重大方向修正。

这条结论支撑了下面 Llama 3 的"过训练"策略——既然数据质量可以继续榨，训练 token 数就不再是天花板。

---

<a id="scaling-laws"></a>
## 📚 Scaling Laws：Kaplan / Chinchilla / Llama 3 三次校正

### 第一代 · Kaplan 2020（OpenAI）

**核心发现**：Loss L 与参数量 N、数据量 D、算力 C 呈幂律关系。在固定算力预算下：

$$ L(N, D) \approx \left(\frac{N_c}{N}\right)^{\alpha_N} + \left(\frac{D_c}{D}\right)^{\alpha_D} $$

**当时结论**："参数越大越好，数据量到 `~2 tokens/param` 就够"——GPT-3 的 175B × 300B ≈ **1.7 tokens/param** 就是这么来的。

**隐含假设**：数据量不是瓶颈，算力才是。

### 第二代 · Chinchilla 2022（DeepMind，Hoffmann et al.）

> "We find current large language models are **significantly undertrained**."

DeepMind 训了 400 多个不同规模模型做网格扫描，发现 Kaplan 的估计**低估了数据的重要性**。校正后的结论：

> **参数与数据应按 1:20 的比例同时放大**。固定算力下，训一个更小但喂更多数据的模型，效果碾压更大但欠喂的模型。

**验证实验**：70B Chinchilla 用和 280B Gopher 相同算力（但 4× 数据），在几乎所有基准上碾压 Gopher、GPT-3、Megatron-Turing NLG。

**行业影响**：2022-2023 年所有新模型（Llama 1, Llama 2, PaLM 2, Falcon）都按 Chinchilla 配方造——"**~20 tokens/param**"一度成为金科玉律。

### 第三代 · Llama 3 2024（Meta）的"过训练"

Meta 做了一个在 Chinchilla 时代看似"不经济"的事：**Llama 3 8B 喂 15T tokens = 1875 tokens/param，是 Chinchilla 最优的近 100 倍。**

**为什么这么做？** 因为 Chinchilla 只算了**训练算力**，但应用场景下：

```
总算力 = 训练算力 + (用户数 × 平均推理次数) × 单次推理算力
```

对 Meta 这种日活亿级的平台，推理算力 >> 训练算力。于是：

- **训练时多花 5-10×** → 模型能力提升 → **推理端每次调用便宜 5×**（同等能力下用更小模型）
- 只要推理总次数 > 某阈值，**过训练的投资回报率极高**

Llama 3 技术报告明确指出：按 Chinchilla 8B 最优应是 ~160B tokens，他们训到 15T 后 loss 还在缓慢下降——**"没有看到饱和"**。

### 第四代伏笔 · 数据墙（2024+）

Villalobos et al. 的两次测算（2022、2024）给出数据墙时间表：

| 数据类型 | 总量估算 | 预计耗尽年份 |
|----------|---------|------------|
| 英文高质量文本 | ~300T tokens | **2026-2028** |
| 全部互联网文本 | ~3500T tokens | 2032-2060（取决于增长率） |
| 视频+图像+音频（Token 化后） | ~10^6 T | 短期不缺 |

**业界应对**：
1. **合成数据**（Phi 系列、Llama 3 后期、DeepSeek-R1 的 reasoning trace）
2. **多模态数据**（视频转文本、图像-文本对）
3. **数据重复利用**（同一数据 train 多个 epoch，Muennighoff 2023 证明重复 4 epochs 几乎无损失）
4. **合成数据 + RL**（让模型自己生成-自我筛选-再训）

**关键判断**：数据墙是真的，但"Scaling Law 到头"**不是**真的——它在转向新的维度（推理时计算 test-time compute、合成数据、多模态）。

### Scaling Laws 一张图看懂三次校正

```
                    数据量 D (tokens)
                     │
              10T    │                    ★ Llama 3 8B (过训练时代)
                     │                   /
                     │                  /
              2T     │                ◉ Llama 2 / Chinchilla 时代
                     │              / (≈20 tokens/param)
                     │            /
                     │          /
            300B     │       ● GPT-3 (Kaplan 时代)
                     │    / (≈1.7 tokens/param)
                     │ /
                     └────────────────────────────── 参数量 N
                          10B        70B       175B
```

---

<a id="训练基础设施"></a>
## 📚 训练基础设施：3D 并行与成本账本

### 为什么需要并行？

训一个 70B 模型需要多少显存？

- **参数本身**：70B × 2 字节 (bf16) = 140 GB
- **梯度**：140 GB
- **优化器状态 (Adam)**：70B × 8 字节 = 560 GB
- **激活值**：与 batch size × seq len 成正比，通常 100-500 GB
- **合计**：**~1 TB 级**

一张 H100 才 80 GB，所以必须**切开**，这就是并行策略。

### 三大并行维度（"3D Parallelism"）

```
                    Data Parallel (DP)
                    ────────────────────
                    多张卡跑同一模型的副本
                    各处理不同 batch 的样本
                    每步同步梯度（AllReduce）

                    Tensor Parallel (TP, 张量并行)
                    ──────────────────────────────
                    把同一个层的权重矩阵切到多张卡
                    例：Linear(4096, 16384) → 切成 2 份 (4096, 8192) 放 2 张卡
                    前向/反向时需 AllGather / ReduceScatter
                    典型用在同一节点内（NVLink 带宽高）

                    Pipeline Parallel (PP, 流水线并行)
                    ──────────────────────────────
                    把模型的不同层放到不同卡
                    例：80 层 Transformer 切成 8 段，每段 10 层放一张卡
                    用微批次 (micro-batch) 流水线缓解气泡
                    跨节点通信，带宽要求相对低
```

实践中三者**叠加使用**，例如 Llama 3 405B 用了 TP=8, PP=16, DP=128（等效 16384 张 H100）。

### FSDP vs Megatron-LM（两大主流栈）

| 方案 | 出处 | 特点 | 适合场景 |
|------|------|------|---------|
| **DeepSpeed ZeRO** | Microsoft | ZeRO-1/2/3 分级切分优化器/梯度/参数 | 上手简单，中型模型（≤70B） |
| **Megatron-LM** | NVIDIA | 原生 TP+PP，与 Transformer Engine 深度集成 | 工业级前沿（Llama 3、GPT-4 均用） |
| **FSDP** | Meta (PyTorch) | ZeRO-3 的 PyTorch 原生实现 | 学术界和 Llama 家族主力 |
| **Megatron-DeepSpeed** | 融合 | 取两者之长 | BLOOM/OPT 等大项目 |

### 训一次要多少钱？（2025 基线）

> 数据来源：Chinchilla 论文、Llama 3 / DeepSeek-V3 官方技术报告、Epoch AI 估算。

| 模型 | 参数 × 数据 | GPU-小时 | 估算成本 |
|------|------------|---------|---------|
| GPT-3 (2020) | 175B × 300B tok | ~3.1M (V100) | ~$4.6M |
| Chinchilla (2022) | 70B × 1.4T tok | ~2.0M (TPUv4) | ~$5M |
| Llama 2 70B (2023) | 70B × 2T tok | ~1.7M (A100) | ~$3-5M |
| Llama 3 70B (2024) | 70B × 15T tok | ~6.4M (H100) | ~$15-25M |
| Llama 3 405B (2024) | 405B × 15.6T tok | ~30.8M (H100) | ~$60-80M |
| **DeepSeek-V3 (2024)** | **671B MoE (37B 激活) × 14.8T tok** | **2.79M (H800)** | **~$5.6M** ⭐ |
| GPT-4（估算，未公开） | ~1.8T MoE × ~13T tok | ~25M (A100) | ~$63-78M |

**DeepSeek-V3 为何便宜 10×？** 三个创新叠加：
1. **FP8 混合精度**训练（比 bf16 省 ~50% 显存和通信）
2. **MoE 结构**：671B 参数但每 token 只激活 37B（计算量只有 dense 的 5.5%）
3. **Multi-Token Prediction (MTP)** 预训练目标：一次预测多个 token，数据利用率更高

这是工程创新的力量——**算力差距可以被工程追回来**，Scaling Law 没那么绝对。

---

<a id="tokenizer-训练"></a>
## 📚 Tokenizer 训练：被低估的地基

> 详细 Tokenizer 机制见 [R56](R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)，本节只讲与**预训练**的交互。

### Tokenizer 是预训练的"尺子"

一个 LLM 的"上下文窗口 128K"是 **128K tokens**，不是 128K 字符。Tokenizer 决定了：

1. **每条数据切成几个 token** → 训练效率
2. **中文/代码/数学的压缩率** → 同预算下实际见过多少"内容"
3. **长尾符号的处理** → 会不会一见 emoji 就崩

### 预训练与 Tokenizer 的典型坑

1. **Tokenizer 训练数据不够多样**：如果只用英文网页训 tokenizer，模型一见代码就把 `def` 切成 `d|e|f` 三个 token，训练效率骤降。
   - **Llama 3 的教训**：Llama 2 的 32K 词表偏英文导向，Llama 3 扩到 128K 词表后**中文/代码压缩率提升 ~2×**，相当于免费涨了算力。
2. **国产模型中文 tokenizer 优化**：
   - GPT-3.5: "你好"占 6 tokens
   - Qwen/DeepSeek: "你好"占 1 token
   - 这意味着同 128K 上下文窗口，Qwen 能装下的**中文信息量是 GPT 的 6 倍**。
3. **Tokenizer 一旦定了，训练中不能改**。后训练阶段继续用同一 tokenizer，否则全部白练。这也是为什么 continued pretraining 常遇到词表不对齐的问题。

### Tokenizer 训练的实操流程（简述）

```
1. 收集代表性语料（~100GB，覆盖目标语言和领域）
2. 选算法：BPE / Unigram / SentencePiece
3. 设词表大小：小模型 32K，大模型 128K+
4. 训练 tokenizer（HuggingFace tokenizers 几小时搞定）
5. 验证关键指标：压缩比、OOV 率、典型样本切分合理性
6. 冻结，进入预训练
```

详细代码和进阶话题（chat template、特殊 token 家族）见 [R56](R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)。

---

<a id="数据配方趋势"></a>
## 📚 预训练数据配方的三大趋势

### 趋势 1：代码数据比例持续上升

| 时期 | 代表模型 | 代码占比 |
|------|---------|---------|
| 2020 | GPT-3 | ~0% |
| 2023 | Llama 2 | ~4% (根据推测) |
| 2024 | Llama 3 | ~17% (官方报告) |
| 2024 | DeepSeek-V3 | ~15-20% |

**原因**：实验发现代码数据**对非代码任务也有帮助**（提升推理能力、严谨性）。这是 2023 后的共识——代码是"逻辑的结构化示例"，让模型学会分步思考。

### 趋势 2：合成数据从禁忌变主流

2022 年：业界普遍认为"用合成数据会导致模型崩溃（model collapse）"。
2024 年：Phi 系列（微软）证明**精心设计的合成数据能让 3B 小模型打败 70B 通用模型**在特定任务上。

**典型合成数据路径**：
1. 用强模型（GPT-4、Claude）生成教科书式数据
2. 数学题 + 答案链（从已验证答案反推）
3. 代码 + 单元测试（可自动验证）
4. 多语言翻译（增加低资源语言数据）

**DeepSeek-R1 的一个关键洞察**：通过 RL 让模型**自己生成高质量 reasoning trace**（~800K 条），再用这些 trace 蒸馏到小模型。这是把合成数据推到极致的工程范例，详见 [R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) §LLM 蒸馏专章。

### 趋势 3：领域数据的"精准加强"

不再是"把能找到的都扔进去"，而是：

- **数学**：ProofNet、数学教科书、arXiv 数学论文
- **法律**：判例、法规
- **医疗**：PubMed、临床指南
- **多语言**：明确配比而非随机

**做法**：训练过程分两阶段——
1. **阶段 1（大数据量）**：通用配方，学语言和世界知识
2. **阶段 2（小数据量，质量高）**：领域加强，微调最后几步

Llama 3 技术报告明确提到这种"退火阶段 annealing"做法：最后 ~5% 训练步用高质量精选数据，对下游效果提升显著。

---

<a id="cpt-vs-sft"></a>
## 📚 CPT vs SFT 的边界

> **最常见的应用工程师问题**："我想把模型灌进我们的行业知识，该 SFT 还是 CPT？"

### 决策树

```
你想让模型...
│
├─ 学会新的【表达风格/回复格式】？
│    → SFT 就够了（10K 示例，LoRA 即可）
│
├─ 学会新的【领域知识】但知识点已在互联网上？
│    → SFT + RAG 够了（不用重新灌输）
│
├─ 学会新的【领域知识】但知识是公司私有的？
│    ├─ 私有知识 < 1GB → SFT (把知识做成 QA 对) 或 RAG
│    ├─ 私有知识 1-100GB → 考虑 CPT
│    └─ 私有知识 > 100GB 且长期使用 → CPT 是正确路径
│
├─ 学会新的【语言】（如小语种）？
│    → CPT 必须，SFT 救不回来（预训练没见过足够多样本）
│
└─ 学会新的【推理能力】？
     → 答案复杂：如果基座本身推理不行，CPT 也很难救
     → 优先换更好的基座，或用 RL (GRPO) 放大现有能力
```

### CPT 的真实成本

| 模型规模 | 数据量 | GPU 时数 | 估算成本 |
|---------|-------|---------|---------|
| 7B × 10B tok | 小规模领域 | ~500 (A100) | ~$500-1500 |
| 70B × 10B tok | 小规模领域 | ~4000 (A100) | ~$4K-12K |
| 7B × 100B tok | 深度领域强化 | ~5000 (A100) | ~$5K-15K |

**关键坑**：CPT 不小心会**遗忘原有能力**（catastrophic forgetting）。对策：
1. 混入原预训练数据（比例 ~20-30%，Replay Buffer）
2. 用较小学习率（通常是预训练学习率的 1/10）
3. 冷启动监控 MMLU / HellaSwag 等通用基准，发现退化立刻停

---

<a id="厂商横评"></a>
## 📚 五家厂商预训练策略横评

| 维度 | OpenAI | Meta | DeepSeek | Qwen | Mistral |
|------|--------|------|----------|------|---------|
| **预训练数据量（旗舰）** | GPT-4 约 13T (估) | Llama 3 15-15.6T | V3 14.8T | Qwen3 暂未披露 (>10T) | 保守估计 5-10T |
| **公开度** | ★☆☆☆☆ | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ |
| **MoE 策略** | GPT-4 是 MoE（估） | Llama 4 开始用 MoE | V2/V3 深度 MoE（细粒度） | Qwen3 部分 MoE | Mixtral 8x7B/8x22B |
| **精度/训练栈** | 未知 (传闻 bf16) | bf16 + Megatron | **FP8 + 自研** | bf16 + Megatron 变体 | bf16 |
| **Tokenizer 策略** | tiktoken 专属 | 128K 词表 | 128K 含中文优化 | **中文优化最激进** | SentencePiece |
| **核心差异化** | 数据+对齐 secret sauce | 规模 + 生态 + 开源 | **工程效率（1/10 成本）** | 多尺寸 + 中文 | 欧洲数据/合规 |
| **过训练程度** | 未知 | Llama 3 重度过训练 | MoE 等效算力过训练 | 重度过训练 | 中度 |
| **学习推荐度** | 没细节可学 | ⭐⭐⭐⭐⭐ 首选参考 | ⭐⭐⭐⭐⭐ 首选参考 | ⭐⭐⭐ 中文视角补充 | ⭐⭐ 早期探索有意思 |

### 给工程师的学习选择

- **想搞懂主流工业方法** → 读 Llama 3 技术报告（92 页，最系统）
- **想搞懂工程创新/榨干成本** → 读 DeepSeek-V3 报告（强烈推荐）
- **想理解中文适配** → 读 Qwen 系列报告
- **不要浪费时间在 OpenAI/Anthropic 上**——他们不公开细节，逆向猜测收益低

---

<a id="避坑指南"></a>
## 🕳️ 避坑指南

| 坑 | 原因 | 解法 |
|---|------|-----|
| 把"预训练""微调""对齐"混用 | 术语继承自不同时期 | 记住：预训练 = next-token，SFT = 模仿示范，RLHF = 偏好对齐。一个模型的总能力 = 预训练天花板 × 后训练开关 |
| 以为 Scaling Law 已到头 | 只看算力/参数维度 | 算力维度放缓是真的，但**推理时计算、合成数据、多模态**是新维度；有效 Scaling 还能跑 2-3 年 |
| 以为知识能靠 SFT 灌进去 | "微调"一词误导 | SFT 只改风格，不加实质知识。要灌知识要么 CPT，要么 RAG。这是最常见的应用工程师错误 |
| 低估 tokenizer 对 Scaling 的影响 | 以为 token 数 = 字符数 | 中文 tokenizer 差的模型 "15T tokens" 的**实际知识量**可能只等于好 tokenizer 的 3-5T；用 OpenAI tokenizer 估 Claude/Qwen 成本偏差可达 3 倍 |
| 低估数据清洗的工作量 | 以为"爬下来就能用" | Common Crawl 原始 400B tok/月，清洗后只剩 10-15%；FineWeb 比 C4 训出的模型 MMLU 高 3-5 分仅仅因为清洗改善 |
| CPT 把基座训废了 | 学习率沿用预训练值 | CPT 学习率应降到预训练的 1/10；并混入 20-30% 通用数据防遗忘 |
| 以为小模型是大模型的低配 | "只是参数少" | 小模型和大模型是**不同的知识压缩结果**；7B 从来不会"像 70B 那样推理"，换预期比调 prompt 有用 |
| 合成数据崩溃恐惧症 | 2022 年论文吓的 | 2024+ 实践证明：**精心筛选的**合成数据不崩，Phi 系列和 DeepSeek-R1 是证据 |
| 看 OpenAI/Anthropic 的模型卡找答案 | 他们不公开 | 要学工业细节就读 Llama 3 和 DeepSeek-V3 技术报告，其他都是猜测 |
| 按 Chinchilla 配方训小模型 | 守旧 | Llama 3 已证明推理密集场景下应过训练 50-100×。Chinchilla 仅在"训练 + 单次推理"场景下最优 |

---

<a id="成本roi"></a>
## 💰 成本与 ROI 速算

### 给应用工程师的"何时投预训练"决策

```
你面临的问题是...
│
├─ API 成本 < $10K/月 → 继续用 GPT/Claude API，别想自训
│
├─ API 成本 $10K-100K/月 → 考虑开源模型 + vLLM 自托管（见 [R58](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)）
│
├─ API 成本 $100K-1M/月 → 考虑 CPT + 微调（中等规模）
│
├─ API 成本 > $1M/月 且领域特殊 → 认真考虑 CPT
│
└─ 预算 > $1M 且有独特大规模数据 → 考虑从头预训练（依然建议先用开源基座 + CPT 验证价值）
```

### 训练 vs 推理的总拥有成本（TCO）示意

假设某模型训练成本 T，单次推理成本 I，日调用 N，运行 D 天。

```
TCO = T + N × D × I
```

- GPT-3 时代 (2020)：T=$5M, N 小，I 相对大 → T 占比 > 50%
- Llama 3 时代 (2024)：T=$50M，但日活亿级、I 被 vLLM 等压低 → 一年后 N×D×I >> T，**推理 TCO 占 80%+**
- 所以 Llama 3 "过训练" 策略合理：多花 5× 训练，换 5× 推理变便宜，1 个月就能回本

### 个人学习者的成本定位

- **读论文 + 复现小规模实验**：$0-500，强烈推荐
- **复现 GPT-2 级（124M）**：$50-200（在 Lambda/RunPod 租 A100 跑几小时）—— Karpathy `nanoGPT` 即是此级别
- **复现 GPT-2 Large (1.5B)**：$1K-3K
- **训个真有用的 7B**：$30K-100K（一般人别碰，用开源基座就好）

---

<a id="论文路线图"></a>
## 📖 10 篇必读论文路线图

> 按阅读顺序排列。不读就看 Karpathy 的解读视频也行——每一篇都有优秀的视频解读。

| # | 论文 | 年份 | 为什么读 | 难度 |
|---|------|------|---------|------|
| 1 | **Attention is All You Need** (Vaswani et al.) | 2017 | Transformer 架构起源，一切的根 | ★★☆ |
| 2 | **GPT-2 Paper** "Language Models are Unsupervised Multitask Learners" | 2019 | 预训练-微调范式确立；zero-shot 能力雏形 | ★☆☆ |
| 3 | **GPT-3 Paper** "Language Models are Few-Shot Learners" | 2020 | 175B 规模效应；ICL 现象首次系统讨论 | ★★☆ |
| 4 | **Scaling Laws for Neural Language Models** (Kaplan et al.) | 2020 | 第一代 Scaling Law | ★★★ |
| 5 | **Chinchilla Paper** "Training Compute-Optimal LLMs" (Hoffmann et al.) | 2022 | 第二代 Scaling Law，20:1 黄金比 | ★★★ |
| 6 | **InstructGPT / RLHF Paper** "Training LMs to follow instructions" | 2022 | 后训练对齐的起点（与 R52 衔接） | ★★☆ |
| 7 | **Llama 2 Paper** | 2023 | 工业级开源模型第一个完整报告 | ★★☆ |
| 8 | **Llama 3 Paper** "The Llama 3 Herd of Models" | 2024 | 当前最系统的工业预训练细节 92 页 | ★★★ |
| 9 | **DeepSeek-V3 Technical Report** | 2024 | FP8 + MoE + MTP 的工程创新大全 | ★★★★ |
| 10 | **FineWeb Paper / Blog** | 2024 | 数据清洗工艺的现代标杆 | ★★☆ |

### 进阶补充（5 篇可选）

- **Phi-3 Technical Report** (Microsoft, 2024)：合成数据证明之作
- **OLMo Paper** (AI2, 2024)：完全开源的预训练流水线参考
- **Data-Constrained Scaling Laws** (Muennighoff et al., 2023)：数据重复使用的 Scaling Law
- **Villalobos et al. "Will we run out of data?"** (2022/2024)：数据墙测算
- **DeepSeek-R1 Paper** (2025)：展示 RL 涌现推理 + 合成数据的威力

### 视频补充（不爱读论文的走这条）

- **Karpathy** "Let's build GPT" + "Let's build the GPT Tokenizer" (YouTube)
- **Stanford CS224N** 2024 版
- **Hugging Face** Scaling/Pretraining 系列博客

---

<a id="决策速查"></a>
## 🎯 决策速查

### 你应该花多少时间在预训练上？

| 你是 | 投入建议 |
|------|---------|
| Agent/应用工程师 | 读完本报告 + 3-5 篇论文（前 6 篇选读）即可，够支撑你做选型和边界判断 |
| LLM 微调工程师 | 本报告 + 全部 10 篇论文 + 复现 nanoGPT |
| 基础模型研究员 | 本报告只是起点，需要深入每个细节 + 追踪 arXiv |
| 只是好奇的读者 | TL;DR + 定位透镜 + 厂商横评即可 |

### 选基座模型的三个标准（直接影响你的应用天花板）

1. **预训练数据量和质量**：优先选 Llama 3.1+ / Qwen2.5+ / DeepSeek-V3+ 级别，老模型（Llama 2 以下）能力天花板明显低
2. **Tokenizer 适配度**：处理中文/代码优先看 Qwen / DeepSeek
3. **MoE vs Dense**：推理吞吐优先选 MoE（DeepSeek-V3、Llama 4 系列）；显存紧优先 Dense

### 不要做的三件事

- ❌ 自己从头预训练（除非你是字节/阿里级别，$1M+ 预算）
- ❌ 用 SFT 灌输新知识（99% 会失败，直接上 RAG 或 CPT）
- ❌ 相信"Scaling Law 已经到头"的流派（短期悲观长期错）

---

## 📚 本报告解决了什么开放问题？

对照 R54 路线图缺口清单 G5，本报告产出：

- ✅ 预训练 vs SFT vs RLHF 术语澄清（应用层最常混）
- ✅ Scaling Law 三次校正的完整梳理（Kaplan → Chinchilla → Llama 3）
- ✅ 数据工程流水线 + 主流数据集速查（FineWeb 为里程碑）
- ✅ 3D 并行与成本账本（DeepSeek-V3 的 $5.6M 里程碑）
- ✅ 五家厂商预训练策略横评（含公开度推荐优先级）
- ✅ CPT vs SFT 决策树
- ✅ 10 篇必读论文路线图（替代 Hello World）
- ✅ 与 [R37](R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) / [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) / [R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) / [R56](R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) 的完整交叉引用，三联变四联

---

## 🔮 开放问题与后续计划

1. **合成数据的质量边界**：Phi 系列已证明精选合成数据有效，但"完全合成"能走多远？2025-2026 会见分晓
2. **数据墙的真实时间表**：Villalobos 的 2028 估算是否过于乐观？等 2027 的重新测算
3. **Test-time Compute 能否替代更多预训练？** o1/R1 范式给出答案，但边界未清
4. **1T 参数 MoE 是否已是甜蜜点？** DeepSeek-V3 效果接近 GPT-4，但 Gemini 2/GPT-5 可能证明还能再大
5. **多模态预训练对纯文本能力的影响**：Llama 4 的多模态会不会反过来提升文本能力？悬而未决

---

<a id="来源清单"></a>
## 📌 来源清单

| 来源 | URL | 日期 | 关键摘要 |
|------|-----|------|---------|
| Kaplan et al. "Scaling Laws for Neural Language Models" | arXiv:2001.08361 | 2020-01 | 第一代 Scaling Law，参数为王 |
| Hoffmann et al. "Training Compute-Optimal LLMs" (Chinchilla) | arXiv:2203.15556 | 2022-03 | 20:1 黄金比，"current LLMs significantly undertrained" |
| Meta AI "The Llama 3 Herd of Models" | arXiv:2407.21783 / ai.meta.com/blog | 2024-07 | 405B × 15.6T tok，过训练策略首次工业级披露 |
| DeepSeek-AI "DeepSeek-V3 Technical Report" | arXiv:2412.19437 / github.com/deepseek-ai/DeepSeek-V3 | 2024-12 | 671B MoE + FP8 + MTP，$5.6M 训练 |
| HuggingFace "FineWeb: decanting the web for the finest text data at scale" | huggingface.co/spaces/HuggingFaceFW/blogpost-fineweb-v1 | 2024-05 | 15T 开源清洗数据，清洗工艺标杆 |
| Villalobos et al. "Will we run out of data?" | arXiv:2211.04325 / 2024 update | 2022/2024 | 数据墙测算 2026-2028 |
| Muennighoff et al. "Scaling Data-Constrained Language Models" | arXiv:2305.16264 | 2023-05 | 数据重复 4 epochs 几乎无损失 |
| Epoch AI 算力估算 | epochai.org | 2024 | GPU 时数与成本基准 |
| Karpathy "Let's build GPT" 系列 | YouTube @AndrejKarpathy | 2022-2024 | 教学性预训练复现 |
| 模型训练知识（补充） | — | 截止训练数据 | 仅作背景，具体数字均以上述公开源为准 |

⚖️ 来源一致性：**高度一致**（Scaling Law 三阶段演进、Llama 3/DeepSeek-V3 成本数据、FineWeb 数据工艺均由至少 2 个独立权威来源印证）
📅 时效性声明：本报告信息获取于 2026-04-24，关键数据以 2024 Q4 的 Llama 3 / DeepSeek-V3 公开技术报告为基准，2025 年新模型（Llama 4、DeepSeek-V4、GPT-5 等）若发布，相关数字和趋势判断可能需要更新。

---

> **给读者的一句话**：预训练不是你要做的事，但它是决定你做事边界的事。读懂它，你就从"LLM 使用者"变成了"LLM 合作者"。
