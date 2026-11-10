---
title: LLM 从业者学习路线总览（从 Transformer 到 Agent 的完整路由图）
aliases: [R54, LLM学习路线, AI-Native学习路线, LLM从业者路线图, Learning Roadmap]
tags: [meta, learning-path, roadmap, llm, 路由图]
date: 2026-04-25
category: 工程实践
report_id: R54
tokens: 15000
status: completed
related:
  - "KNOWLEDGE_INDEX（原稿交叉引用，本归档未解析）"
  - "[R23](R23_AIAgent%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E4%B8%8E%E9%A1%B9%E7%9B%AE%E6%95%B4%E5%90%88.md)"
  - "[R24](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R24_%E4%BB%8E%E9%9B%B6%E6%9E%84%E5%BB%BAAgent%E6%B8%90%E8%BF%9B%E5%BC%8F%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF.md)"
  - "[R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md)"
  - "[R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)"
  - "[R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)"
  - "[R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md)"
  - "[R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)"
  - "[R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md)"
  - "[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)"
  - "[R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)"
  - "[R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)"
  - "[R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)"
  - "[R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)"
  - "[R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)"
  - "[R64](R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md)"
  - "[R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)"
  - "[R66](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R66_%E5%A4%9A%E6%A8%A1%E6%80%81Agent%E4%B8%8EComputerUse%E8%B0%83%E7%A0%94.md)"
  - "[R67](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R67_Reasoning%E6%A8%A1%E5%9E%8B%E4%B8%93%E9%A2%98_o1_R1_Thinking.md)"
  - "[R68](R68_Agent%E4%BA%A7%E5%93%81%E6%A8%A1%E5%BC%8F%E4%B8%8EHITL%E8%AE%BE%E8%AE%A1.md)"
  - "[R69](R69_LLM_Agent%E7%BB%8F%E6%B5%8E%E5%AD%A6%E4%B8%8E%E5%95%86%E4%B8%9A%E5%86%B3%E7%AD%96.md)"
  - "[R70](R70_AI-Native%E5%9B%A2%E9%98%9F%E4%B8%8E%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86.md)"
  - "[R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md)"
  - "[R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# LLM 从业者学习路线总览

> **一句话概括**：把本知识库 **72 篇报告** + 12 章 tutorial + 50 个产出物，按"一个优秀 LLM 从业者应有的认知顺序"重组为 **7 阶段学习路由图 + 3 条路径**。从 Transformer 底层到 Agent 应用层层递进，每个节点都有深度报告兜底。
>
> **研究日期**：2026-04-25｜**版本**：v1.2（R64-R72 全量集成 + 新增路径 C 技术管理者）
> **与 R23 的关系**：[R23](R23_AIAgent%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E4%B8%8E%E9%A1%B9%E7%9B%AE%E6%95%B4%E5%90%88.md) 聚焦"Agent 应用层学习路线"（假设读者已懂 LLM）；本报告向下延伸到**模型底层/训练/推理部署**并向上拓展到**产品设计/经济学/团队管理**，形成完整的"从地壳到云端、从实现者到决策者"路线。
> **增量价值**：v1.2 首次把 R64-R72 九篇新报告接入路线图，**新增路径 C：技术管理者路径**（面向 Lead/Architect/PM，基于 R69+R70+R31）。

### 📌 v1.2 修订说明（2026-04-25）

**v1.1 不启动新缺口补充"的决策被现实推翻**——6 周内实际产出了 R64-R72 九篇报告，v1.2 全量集成：

| 报告 | 接入阶段 | 填补什么 |
|------|---------|---------|
| [R64](R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) Agent 网关三层拆解 | **L7.7 新增** | 以前 L7 没有“多模型路由/限流/隐藏密钥”该怎么做，R64 补齐 |
| [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) Agent 主流技术栈速查 | **L4.7 新增**（速查手册） | 新人入门时"入口页"——一页看清选 BGE-M3 / Milvus / vLLM / LangGraph |
| [R66](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R66_%E5%A4%9A%E6%A8%A1%E6%80%81Agent%E4%B8%8EComputerUse%E8%B0%83%E7%A0%94.md) 多模态 Agent 与 Computer Use | **L1.4 从"只扫边"升级为✅** | VLM 三大实现机制（Anthropic/OpenAI/开源派）|
| [R67](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R67_Reasoning%E6%A8%A1%E5%9E%8B%E4%B8%93%E9%A2%98_o1_R1_Thinking.md) Reasoning 模型专题 | **L1.6 新增** | reasoning 模型作为一类 LLM 物种、Planner-Worker 混合架构 |
| [R68](R68_Agent%E4%BA%A7%E5%93%81%E6%A8%A1%E5%BC%8F%E4%B8%8EHITL%E8%AE%BE%E8%AE%A1.md) Agent 产品模式与 HITL | **L5.10 新增** | Copilot/Workflow/Autopilot 三模式 + 10 种 HITL + 流式 UX 三层 |
| [R69](R69_LLM_Agent%E7%BB%8F%E6%B5%8E%E5%AD%A6%E4%B8%8E%E5%95%86%E4%B8%9A%E5%86%B3%E7%AD%96.md) LLM/Agent 经济学 | **L7.7 新增** + 路径 C 核心 | token 四维度、ROI 拐点、计费模型、开闭源决策 |
| [R70](R70_AI-Native%E5%9B%A2%E9%98%9F%E4%B8%8E%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86.md) AI-Native 团队与工程管理 | **L7.8 新增** + 路径 C 核心 | EDD、4 阶段引入、Agent KPI、双轨组织、6 月路线图 |
| [R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md) Coding Agent 五家横评 | **L5.11 新增** | Cursor/Cline/Aider/Claude Code/OpenCode，吃掉 G13 |
| [R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md) Agent 记忆系统横评 | **L4.7 增补** + L5 交叉 | 三层记忆模型（Working/Episodic/Semantic）、五家选型 |

**新增路径 C：技术管理者路径**——面向 Lead / Architect / PM，**不代码但必须会账**。基于 R69 经济学 + R70 工程管理 + R31 提效分析、R57 安全、R64 网关、R68 产品模式五篇核心报告。估计 6-9 个月。

### 📌 v1.1 修订说明（2026-04-24，保留）

v1.0 识别出 12 个学习路线缺口（G1-G12），v1.1 全部补齐。完整映射：

| 缺口 | 新报告 | 所属阶段 |
|------|-------|---------|
| G1+G2+G3（合篇） | [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) LLM 从业者数学与代码速查手册 | L0 |
| G4 | [R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) Tokenization 深度解析 | L1 |
| G5 | [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) LLM 预训练全景（Scaling Law） | L2 |
| G6+G7（合篇） | [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) LLM 推理部署工程指南（量化 + 引擎） | L3 |
| G8 | [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 推理优化技术（KV Cache / FlashAttention / 投机解码） | L3 |
| G9 | [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) LLM 服务化生产部署（成本 / 延迟 / SLA） | L3+L7 |
| G10 | [R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) Prompt Engineering 系统化调研 | L4 |
| G11 | [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) LLM Benchmark 速查手册 | L6 |
| G12 | [R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) Agent 安全与红队攻防体系 | L6 |

**🔴 红色缺口数量：v1.0 的 4 个 → v1.1 的 0 个**。L3（推理与部署）从"最大空白"变为"三篇报告（R58+R59+R63）覆盖最系统的阶段之一"。

---

## TL;DR 速查卡

- **骨架**：7 阶段 × 平均 3-5 个节点/阶段，从 Python 预备 → Transformer → 训练对齐 → 推理部署 → Prompt/RAG → Agent → 生产运维
- **三条路径（v1.2 新）**：**A 应用工程师**（~2 个月）/ **B LLM 深究**（~6 个月）/ **C 技术管理者**（~6-9 个月，面向 Lead/Architect/PM）
- **R64-R72 九篇新报告补齐三块空白**：产品设计（R68 HITL）、商业决策（R69 经济学）、团队管理（R70 EDD）——以前路线只走到 "东西能跑起来"，现在延伸到 "走入产品与企业"
- **走法**：路径 A 快上手、路径 B 启发式打底子、路径 C 是 "带团队走完 A 后多看三本"；v1.2 三路径如同一棵树的三个枝条，根部是 L0-L4 公用基础
- **最快的 24 小时体验**：R54 + Ch01 + R37 §Hello + R30 §2 + R71 §TL;DR + R69 §2（联调实践：Hello Agent + RAG + 选 Coding Agent + 估 Token 账）
- **总投入估算**：路径 A ~2 月、路径 B ~6 月、路径 C ~6-9 月（每天 2 小时）
- **现有覆盖**：**7 阶段全线路 ✅**（v1.1 起）——共 62 篇报告 + 12 章 tutorial 兜底
- **无系统性缺口**：v1.0 识别的 12 个缺口全部补齐（参见上方 v1.1 修订说明）
- **推荐起点**：不是从 L0 开始，而是从 L5 Ch1（[tutorial/Ch01-跑通第一个Agent](../../tutorial/Ch01-%E8%B7%91%E9%80%9A%E7%AC%AC%E4%B8%80%E4%B8%AAAgent.md)）先跑通，再回头补 L1/L2 底层——fast.ai "Whole Game" 教学法
- **总投入估算**：深究路径 ~6 个月、应用者路径 ~2 个月（每天 2 小时）

---

## 目录

- [一、路线设计哲学](#一路线设计哲学)
- [二、7 阶段学习路由图](#二7-阶段学习路由图)
- [三、每阶段详细编排](#三每阶段详细编排)
- [四、两种学习路径](#四两种学习路径)
- [五、已识别的内容缺口（待用户决策）](#五已识别的内容缺口待用户决策)
- [六、推荐的第一个月行动清单](#六推荐的第一个月行动清单)

---

## 一、路线设计哲学

### 1.1 为什么不从 Transformer 开始

你的直觉"Transformer → 训练 → ... → Agent"**方向正确但起点错了**。理由：

- **动机先于原理**：先让你体会"Agent 能干什么"、"为什么 LLM 会出错"，再回头看 Transformer，你会带着问题去读——每个设计选择都能对应到你遇到的现象
- **Whole Game 教学法**（fast.ai）：先跑完整游戏（Ch1 40 分钟跑通一个 Agent），再学每个位置的规则
- **知识库现状佐证**：本库 tutorial 12 章就是这样编排的——Ch1 直接上手 Agent，Ch2 讲本质，越往后越底层

### 1.2 从业者的两种画像决定两条路径

| 画像 | 典型职责 | 侧重 |
|------|---------|------|
| **LLM 应用工程师**（大多数） | 拿模型 API 做产品，调 Prompt/RAG/Agent | L4-L7 扎学，L1-L3 知道"是什么"即可 |
| **LLM 研究/训练工程师**（少数） | 微调模型、做对齐、研究推理优化 | L1-L3 深究，L4-L5 作为验证场景 |

本路线默认**应用工程师路径**，但每阶段标注"深究分支"指向训练向报告。

### 1.3 螺旋式而非线性

同一个概念（如"注意力机制"）会在 L1（数学原理）、L4（上下文工程中的注意力衰减）、L6（长期漂移检测）三个阶段以不同深度反复出现——这是 Bruner 螺旋式课程的体现，不是重复。

---

## 二、7 阶段学习路由图

```
                         ┌──────────────────────────────────────┐
                         │     LLM 从业者学习路由图（7 阶段）      │
                         └──────────────────────────────────────┘

 L0 预备         L1 模型底层       L2 训练与对齐     L3 推理与部署
 ┌─────────┐   ┌────────────┐   ┌────────────┐   ┌──────────────┐
 │Python   │──►│Transformer │──►│预训练SFT   │──►│量化/vLLM/   │
 │ML基础   │   │注意力机制  │   │RLHF/DPO   │   │服务化        │
 │数学基础 │   │Tokenization│   │蒸馏PEFT   │   │推理引擎      │
 └─────────┘   └────────────┘   └────────────┘   └──────────────┘
     │              │                  │                 │
     │         [R37已覆盖]         [R52/R53]        [部分缺失]
     │         [Ch02]              [已覆盖]
     ▼              ▼                  ▼                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │              L4 Prompt 与上下文工程层                        │
 │  Prompt Engineering → Context 工程 → RAG → Memory           │
 │  [部分缺失]          [Ch05]       [R30/R42]  [R19/R46]      │
 └─────────────────────────────────────────────────────────────┘
     │                    ▼
     ▼              ┌──────────────┐        ┌──────────────┐
 ┌─────────────────────────────────┐   ┌──────────────────────┐
 │  L5 Agent 工程层                │   │  L6 评估与可靠性      │
 │  单 Agent → Tool → Skill →     │◄─►│  Eval基准/指令漂移   │
 │  多 Agent → 自迭代             │   │  红队/安全/漂移      │
 │  [Ch01-04/R03/R26/R45/R51/R28] │   │  [R15/R17 + 空白]    │
 └─────────────────────────────────┘   └──────────────────────┘
                       │                         ▲
                       ▼                         │
 ┌─────────────────────────────────────────────────────────────┐
 │           L7 生产落地与运维                                   │
 │  部署/可观测性/成本优化/长效运行/持续学习                      │
 │  [R04/R11/R29/R32/R33/R46]                                  │
 └─────────────────────────────────────────────────────────────┘
```

### 阶段一览表（含覆盖度）

| 阶段 | 核心问题 | 已有报告覆盖度 | 建议投入（应用者） |
|------|---------|--------------|-----------------|
| **L0 预备** | 能不能读懂代码、理解概率 | � 已覆盖（[R02](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R02_Agent%E5%BC%80%E5%8F%91Python%E7%9F%A5%E8%AF%86%E6%B8%85%E5%8D%95.md)[R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)） | 1-2 周 |
| **L1 模型底层** | LLM 内部到底在做什么 | 🟢 已覆盖（[R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md)[R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)） | 1 周（薄学）/ 4 周（深究） |
| **L2 训练与对齐** | 模型怎么"学会"和"听话" | 🟢 已覆盖（[R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)[R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)[R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md)） | 1 周（薄学）/ 6 周（深究） |
| **L3 推理与部署** | 怎么让模型跑得快、省 | 🟢🟢 系统覆盖（[R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)[R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)[R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)） | 1-2 周（应用者） |
| **L4 Prompt & 上下文** | 怎么让模型说出想要的 | 🟢 已覆盖（[R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md)[R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)） | 2 周 |
| **L5 Agent 工程** | 怎么让模型能"做事" | 🟢🟢🟢 最扎实（15+ 篇） | 3-4 周 |
| **L6 评估与可靠性** | 怎么知道它变好/变差/作妖 | 🟢 已覆盖（[R15](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R15_Skill%E4%B8%8EAgent%E8%AF%84%E4%BC%B0%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)[R17](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R17_%E6%8C%87%E4%BB%A4%E9%81%B5%E5%AE%88%E9%AA%8C%E8%AF%81%E4%B8%8E%E9%95%BF%E6%9C%9F%E6%BC%82%E7%A7%BB%E6%A3%80%E6%B5%8B.md)[R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md)[R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)） | 2 周 |
| **L7 生产落地** | 怎么让别人也能用 | 🟢 已覆盖（[R04](R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)[R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md)[R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)） | 2 周 |

> 🟢🟢🟢 = 本库最扎实阶段；🟢🟢 = 系统覆盖（多篇互补）；🟢 = 核心覆盖

---

## 三、每阶段详细编排

### L0 — 预备知识（1-2 周）

**核心问题**：能不能读懂 Python 异步代码？能不能理解"概率分布"和"向量相似度"？

| 节点 | 内容 | 状态 |
|------|------|------|
| L0.1 Python for Agent | async/await、装饰器、Pydantic、Generator | ✅ [R02](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R02_Agent%E5%BC%80%E5%8F%91Python%E7%9F%A5%E8%AF%86%E6%B8%85%E5%8D%95.md) |
| L0.2 ML 基础 | 监督学习/反向传播/Loss/梯度下降 | ✅ [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)（G1 合篇） |
| L0.3 线性代数与概率直觉 | 向量/矩阵乘法/softmax/KL 散度 | ✅ [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)（G2 合篇） |
| L0.4 深度学习框架 | PyTorch 张量操作/DataLoader/训练循环 | ✅ [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)（G3 合篇） |

> **薄学建议**：[R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 将 G1-G3 合为一篇速查手册（~22KB），适合快速折叠数学/代码基础。若偏好视频学习，外部资源（3Blue1Brown 神经网络系列 + PyTorch 60 分钟闪电战 + Karpathy "Zero to Hero" 前两集）依然是优秀的互补。

---

### L1 — 模型底层（1-4 周）

**核心问题**：当你输入 "Hello" 时，模型内部到底发生了什么？

| 节点 | 内容 | 状态 |
|------|------|------|
| L1.1 Tokenization | BPE/WordPiece/SentencePiece/中英文差异 | ✅ [R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md)（G4） |
| L1.2 Transformer 全景 | Self-Attention/Multi-Head/FFN/残差/LayerNorm | ✅ [R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) |
| L1.3 位置编码演进 | Sinusoidal/Learned/RoPE/ALiBi | ✅ [R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md)（含 RoPE） |
| L1.4 架构变种 | Decoder-only/MoE/Mamba/RWKV 对比 | 🟡 [R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) 有扫边，缺深度（跟踪为 G20）|
| L1.5 Agent 本质视角 | 从"文字接龙"到"Agent 的一个循环" | ✅ [tutorial/Ch02-Agent的本质](../../tutorial/Ch02-Agent%E7%9A%84%E6%9C%AC%E8%B4%A8.md) |
| **L1.6 Reasoning 模型专题** 🆕 | o1/R1/Thinking 训练范式、RLVR/GRPO、Planner-Worker | ✅ [R67](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R67_Reasoning%E6%A8%A1%E5%9E%8B%E4%B8%93%E9%A2%98_o1_R1_Thinking.md)（v1.2 新增）|
| **L1.7 多模态 VLM** 🆕 | VLM 原理、三大实现机制、坐标精度门槛 | ✅ [R66](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R66_%E5%A4%9A%E6%A8%A1%E6%80%81Agent%E4%B8%8EComputerUse%E8%B0%83%E7%A0%94.md)（v1.2 新增）|

**深究分支**：[R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) §"手撕 70 行 Multi-Head Attention" + [R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) 手撕 BPE + Karpathy minGPT。

---

### L2 — 训练与对齐（1-6 周）

**核心问题**：GPT-4 是怎么"学会"说话、"听懂"指令、"避免"胡说的？

| 节点 | 内容 | 状态 |
|------|------|------|
| L2.1 预训练概览 | 数据清洗/Scaling Law/训练一次多少钱 | ✅ [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md)（G5） |
| L2.2 SFT 指令微调 | 数据格式/chat template/全参数 vs LoRA | ✅ [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) |
| L2.3 PEFT 家族 | LoRA/QLoRA/AdaLoRA/Prefix-Tuning | ✅ [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) |
| L2.4 对齐：RLHF 与后继 | PPO→DPO→GRPO/RLVR 演进 | ✅ [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) |
| L2.5 模型蒸馏 | 白盒/黑盒/Reasoning Trace 蒸馏 | ✅ [R53](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R53_%E6%A8%A1%E5%9E%8B%E8%92%B8%E9%A6%8F%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) |
| L2.6 RLHF 的副作用 | 讨好/阿谀/幻觉放大 | ✅ [R16](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R16_AI%E8%BE%93%E5%87%BA%E8%B4%A8%E9%87%8F%E7%A8%B3%E5%AE%9A%E6%80%A7%E4%B8%8E%E5%8F%8D%E8%AE%A8%E5%A5%BD.md) |

**深究分支**：[R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) §Scaling Law + [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) §"5 个 Hello World" + Unsloth QLoRA 实战。

---

### L3 — 推理与部署（�🟢 从最大缺口翻身为系统覆盖）

**核心问题**：训好的模型怎么跑得快、省显存、能服务高并发？

| 节点 | 内容 | 状态 |
|------|------|------|
| L3.1 量化技术 | INT8/INT4/GPTQ/AWQ/GGUF/FP8 | ✅ [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)（G6 合篇） |
| L3.2 推理引擎 | vLLM/TensorRT-LLM/llama.cpp/TGI/SGLang | ✅ [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)（G7 合篇） |
| L3.3 推理优化技术 | PagedAttention/KV Cache/FlashAttention/投机解码 | ✅ [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md)（G8） |
| L3.4 模型服务化 | OpenAI-compatible API / Triton / Ray Serve | ✅ [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)（G9） + [R04](R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) |
| L3.5 成本与延迟 | TPS/TTFT/p99/GPU 选型/Autoscaling | ✅ [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)（G9） |

> **v1.1 重大更新**：L3 从 v1.0 的单一缺口阶段，升级为 **三篇报告互补的系统覆盖阶段**：**R58 选引擎与量化 → R59 理解引擎内部 → R63 开上生产**。对**应用工程师**，读完 R58 TL;DR + 用 Ollama 跑通 Qwen2.5-7B-Q4 即可；对**基础设施工程师**，三篇都是硬技能。

---

### L4 — Prompt 与上下文工程（2 周）

**核心问题**：怎么让模型输出你真正想要的东西？

| 节点 | 内容 | 状态 |
|------|------|------|
| L4.1 Prompt Engineering 系统化 | 结构化提示/CoT/Few-shot/ReAct/Constitutional | ✅ [R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md)（G10） |
| L4.2 上下文工程 | 上下文窗口/注意力衰减/压缩策略 | ✅ [tutorial/Ch05-上下文工程](../../tutorial/Ch05-%E4%B8%8A%E4%B8%8B%E6%96%87%E5%B7%A5%E7%A8%8B.md) |
| L4.3 RAG 四代演进 | Naive→Advanced→Modular→Agentic | ✅ [R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) |
| L4.4 Embedding 与向量检索 | 模型选型/Hybrid/Rerank/Contextual Retrieval | ✅ [R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md)[R48](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md) |
| L4.5 GraphRAG 与知识图谱 | Microsoft GraphRAG/LightRAG/HippoRAG | ✅ [R48](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md)[R22](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R22_Graphify%E7%9F%A5%E8%AF%86%E5%9B%BE%E8%B0%B1%E5%B7%A5%E5%85%B7.md) |
| L4.6 记忆与长期上下文 | 短期/长期/跨会话记忆 | ✅ [R19](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)[R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)[R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md)（v1.2 新增五家横评）|
| **L4.7 主流技术栈速查** 🆕 | 选 Embedding/向量库/Rerank/微调/推理引擎/框架一页看完 | ✅ [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)（v1.2 新增）|

**深究分支**：[R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) 系统化 Prompt 模式家族 + [R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) 生产级 150 行代码 + [R48](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R48_Agent%E7%9F%A5%E8%AF%86%E5%B7%A5%E7%A8%8B%E5%85%A8%E6%99%AF%E8%B0%83%E7%A0%94.md) 行业全景 v2。

---

### L5 — Agent 工程（🟢🟢 本库最扎实阶段，3-4 周）

**核心问题**：怎么让 LLM 从"会说话"变成"会做事"？

| 节点 | 内容 | 状态 |
|------|------|------|
| L5.1 Hello Agent | 跑通第一个 Agent（40 分钟） | ✅ [tutorial/Ch01-跑通第一个Agent](../../tutorial/Ch01-%E8%B7%91%E9%80%9A%E7%AC%AC%E4%B8%80%E4%B8%AAAgent.md) |
| L5.2 Agent 五件武器 | 推理/工具/记忆/规划/观察 | ✅ [R03](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md)[tutorial/Ch03-五件武器](../../tutorial/Ch03-%E4%BA%94%E4%BB%B6%E6%AD%A6%E5%99%A8.md) |
| L5.3 从零搭建 Agent | 8 次迭代 30→1000 行 | ✅ [R24](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R24_%E4%BB%8E%E9%9B%B6%E6%9E%84%E5%BB%BAAgent%E6%B8%90%E8%BF%9B%E5%BC%8F%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF.md)[R44](R44_%E6%B8%90%E8%BF%9B%E5%BC%8FAgent%E6%9E%84%E5%BB%BA%E5%AE%9E%E6%88%98.md) |
| L5.4 工具调用深入 | Tool schema/MCP/A2A/工具四象限 | ✅ [R39](R39_%E9%A3%9E%E4%B9%A6CLI%E4%B8%8EMCP%E9%80%9A%E4%BF%A1%E6%9C%BA%E5%88%B6.md)[R40](R40_%E5%B7%A5%E5%85%B7%E5%BD%A2%E5%BC%8F%E5%9B%9B%E8%B1%A1%E9%99%90%E8%B0%83%E7%A0%94.md)[R50](R50_A2A%E5%8D%8F%E8%AE%AE%E5%85%A5%E9%97%A8%E5%AD%A6%E4%B9%A0%E6%8C%87%E5%8D%97.md) |
| L5.5 框架选型 | OpenAI SDK/LangGraph/CrewAI/ADK/Claude SDK | ✅ [R26](R26_LangChain%E4%B8%8ELangGraph%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md)[R27](R27_ClaudeAgentSDK%E5%85%A5%E9%97%A8%E5%88%B0%E5%AE%9E%E6%88%98.md)[R45](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R45_%E7%8E%B0%E4%BB%A3%E6%99%BA%E8%83%BD%E4%BD%93%E7%BC%96%E6%8E%92%E6%A1%86%E6%9E%B6%E6%B7%B1%E5%BA%A6%E8%B0%83%E7%A0%94.md) |
| L5.6 Skill 工程化 | SKILL.md/Skill-Creator/自迭代 | ✅ [R14](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)[R28](../03-%E5%AE%9E%E9%AA%8C%E9%AA%8C%E8%AF%81/R28_Skill%E8%87%AA%E8%BF%AD%E4%BB%A3%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) |
| L5.7 多 Agent 编排 | Orchestrator-Workers/三种实现方式 | ✅ [R51](R51_%E5%A4%9AAgent%E7%BC%96%E6%8E%92%E4%B8%89%E7%A7%8D%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F.md)[R06](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md) |
| L5.8 SDK vs IDE vs CLI | 三种 Agent 开发模式 | ✅ [R29](R29_SDKvsIDEvsCLI%E4%B8%89%E7%A7%8DAgent%E5%BC%80%E5%8F%91%E6%A8%A1%E5%BC%8F.md) |
| L5.9 钩子与权限 | Hooks/权限评估 5 层/沙箱 | ✅ [R12](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R12_%E9%92%A9%E5%AD%90%E8%AF%A6%E8%A7%A3%E4%B8%8EAgent%E5%B1%82%E7%BA%A7%E5%AF%B9%E6%AF%94.md) |
| **L5.10 产品模式与 HITL 设计** 🆕 | Copilot/Workflow/Autopilot 三模式、10 种 HITL、流式 UX 三层 | ✅ [R68](R68_Agent%E4%BA%A7%E5%93%81%E6%A8%A1%E5%BC%8F%E4%B8%8EHITL%E8%AE%BE%E8%AE%A1.md)（v1.2 新增）|
| **L5.11 Coding Agent 五家横评** 🆕 | Cursor/Cline/Aider/Claude Code/OpenCode、自研路径 | ✅ [R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md)（v1.2 新增）|

---

### L6 — 评估与可靠性（2 周）

**核心问题**：怎么知道模型/Agent 变好了、变差了、还是在悄悄作妖？

| 节点 | 内容 | 状态 |
|------|------|------|
| L6.1 评估全景 | DeepEval/Ragas/Promptfoo/LLM-as-Judge | ✅ [R15](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R15_Skill%E4%B8%8EAgent%E8%AF%84%E4%BC%B0%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) |
| L6.2 标准 Benchmark | MMLU/GSM8K/HumanEval/SWE-bench/τ-bench | ✅ [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md)（G11） |
| L6.3 输出质量与反讨好 | 一致性/幻觉/阿谀 | ✅ [R16](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R16_AI%E8%BE%93%E5%87%BA%E8%B4%A8%E9%87%8F%E7%A8%B3%E5%AE%9A%E6%80%A7%E4%B8%8E%E5%8F%8D%E8%AE%A8%E5%A5%BD.md) |
| L6.4 指令漂移检测 | 长效运行中的规则失守 | ✅ [R17](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R17_%E6%8C%87%E4%BB%A4%E9%81%B5%E5%AE%88%E9%AA%8C%E8%AF%81%E4%B8%8E%E9%95%BF%E6%9C%9F%E6%BC%82%E7%A7%BB%E6%A3%80%E6%B5%8B.md) |
| L6.5 Agent 安全与红队 | Prompt Injection/越狱/数据泄漏/防御四层 | ✅ [R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md)（G12） |
| L6.6 可观测性 | Langfuse/Phoenix/OTel GenAI | ✅ [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)（G9） + [R15](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R15_Skill%E4%B8%8EAgent%E8%AF%84%E4%BC%B0%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) |

---

### L7 — 生产落地与运维（2 周）

**核心问题**：demo 跑通到用户真的能用之间隔着什么？

| 节点 | 内容 | 状态 |
|------|------|------|
| L7.1 部署 9 级方案 | CLI→IM Bot→Docker→K8s→多 Agent 分布式 | ✅ [R04](R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)[tutorial/Ch11-部署上线](../../tutorial/Ch11-%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF.md) |
| L7.2 Docker/K8s 基础 | 容器化/编排/Service Mesh | ✅ Docker与K8s技术科普（原稿交叉引用，本归档未解析） |
| L7.3 长效 Agent Harness | 持久化状态/双角色分工 | ✅ [R33](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) |
| L7.4 开发模式与工具链 | SDK/IDE/CLI/Copilot 跨工作区 | ✅ [R29](R29_SDKvsIDEvsCLI%E4%B8%89%E7%A7%8DAgent%E5%BC%80%E5%8F%91%E6%A8%A1%E5%BC%8F.md)[R32](R32_Copilot%E5%85%A8%E5%B1%80%E8%87%AA%E5%AE%9A%E4%B9%89%E8%B7%A8%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%A4%8D%E7%94%A8.md) |
| L7.5 持续学习机制 | 外部资讯同步三层范式 | ✅ [R46](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R46_%E5%A4%96%E9%83%A8%E8%B5%84%E8%AE%AF%E5%90%8C%E6%AD%A5_Agent%E6%8C%81%E7%BB%AD%E5%AD%A6%E4%B9%A0%E4%B8%89%E5%B1%82%E8%8C%83%E5%BC%8F.md) |
| L7.6 成本优化与 SLA | Token 成本/Prompt Caching/语义缓存/Autoscaling | ✅ [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)（G9） + [R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)[R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) |
| **L7.7 网关与经济学** 🆕 | Agent 网关三层拆解、Token 四维度、ROI 拐点、计费模型 | ✅ [R64](R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) + [R69](R69_LLM_Agent%E7%BB%8F%E6%B5%8E%E5%AD%A6%E4%B8%8E%E5%95%86%E4%B8%9A%E5%86%B3%E7%AD%96.md)（v1.2 新增）|
| **L7.8 AI-Native 团队与工程管理** 🆕 | EDD、4 阶段引入、Agent KPI、事故复盘、双轨组织 | ✅ [R70](R70_AI-Native%E5%9B%A2%E9%98%9F%E4%B8%8E%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86.md)（v1.2 新增）|

---

## 四、两种学习路径

### 🚀 路径 A：应用工程师快速通道（~2 个月）

```
Week 1-2: L0 Python 复习（R02）+ L5.1 Hello Agent 跑通（Ch01）
          数学代码基础忘了？用 R61 速查手册 6h 过一遍
Week 3:   L1 Transformer 薄学（R37 TL;DR + R56 Tokenization 避坑章）
Week 4:   L4 Prompt + RAG 速成（R55 + R30 + Ch05）
Week 5:   L3 部署 Hello World（R58 三连：Ollama → vLLM → 量化对比）
Week 6-7: L5 Agent 扎学（Ch01→R24→R51→R28）
Week 8:   L6+L7 收官（R15 评估 + R57 安全基线 + R63 服务化部署 demo）

跳过/薄过：L2 训练细节、L3 引擎内部（R59）、L6 Benchmark 清单
理由：能调 API + 会起服务 + 有安全底线 = MVP 合格
```

### 🔬 路径 B：LLM 工程师深究通道（~6 个月）

```
Month 1: L0+L1 完整（R61→R02→R56→R37 手撕 + Karpathy Zero to Hero）
Month 2: L2 训练扎学（R62 预训练 → R52 微调 → R53 蒸馏 → LoRA/DPO/GRPO 各跑一次）
Month 3: L3 推理部署三连（R58 选型 → R59 引擎内部 → R63 生产 SLA）
         目标：独立起一套 vLLM + Langfuse + Autoscaling 生产环境
Month 4: L4 上下文全家桶（R55 Prompt + R30 RAG + R48 知识工程 + R22 GraphRAG）
Month 5: L5 Agent 扎学（Ch01-10 + R24+R26+R51+R28 + 自建多 Agent 项目）
Month 6: L6+L7 生产化（R57 红队 + R60 Benchmark 选型 + R33 Harness + R46 持续学习）
```

### 🎯 你该走哪条？

问自己三个问题：
1. **你的工作需不需要微调模型 / 调推理引擎？** 都不需要 → 路径 A 或 C
2. **你愿不愿意为了底层原理花一周跑通一次 LoRA 训练？** 不愿意 → 路径 A 或 C
3. **你未来 2 年想成为哪种人？** 产品型 → A，技术/平台型 → B，**带团队/做架构决策 → C**

### 🎩 路径 C：技术管理者通道（~6-9 个月，v1.2 新增）

> **目标读者**：Tech Lead / Architect / 技术 PM / 想拿 AI 决策权的高级工程师。**不一定要会写代码，但必须会算账、会选型、会带团队走 EDD。**
>
> **设计依据**：[R69](R69_LLM_Agent%E7%BB%8F%E6%B5%8E%E5%AD%A6%E4%B8%8E%E5%95%86%E4%B8%9A%E5%86%B3%E7%AD%96.md) LLM 经济学 + [R70](R70_AI-Native%E5%9B%A2%E9%98%9F%E4%B8%8E%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86.md) AI-Native 工程管理 + [R31](R31_%E7%A0%94%E5%8F%91%E5%B7%A5%E4%BD%9C%E6%B5%81AI%E6%8F%90%E6%95%88%E6%9C%BA%E4%BC%9A%E5%88%86%E6%9E%90.md) 研发提效 + [R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) 安全 + [R64](R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) 网关 + [R68](R68_Agent%E4%BA%A7%E5%93%81%E6%A8%A1%E5%BC%8F%E4%B8%8EHITL%E8%AE%BE%E8%AE%A1.md) 产品模式 五篇报告交叉构成完整的"做 AI 决策需要的知识"。

```
Month 1: 跟路径 A 走 W1-W4（建立动手感觉）+ 重读 R23/R24 把团队画像摸清
         产出：能用 Cursor / Cline 跑通自己的工作流（这是给团队示范的最低门槛）

Month 2: 商业决策层（R69 + R31）
         R69 全篇精读 → token 四维度 / ROI 拐点 / 计费模型 / 开闭源
         R31 重读 → 研发流程哪些环节 AI 提效 ROI 最高
         产出：自己团队的 "AI 投入产出测算表"（按 R69 框架）

Month 3: 工程管理层（R70 + R15 + R17）
         R70 全篇精读 → 4 阶段引入 / EDD / KPI / 事故复盘 / 6 月路线图
         R15 评估全景 + R17 漂移检测 → 把 EDD 落到工具上
         产出：自己团队的 "6 月 AI-Native 路线图"（套 R70 模板）

Month 4: 产品设计层（R68 + R67 + R66）
         R68 → 你团队做的产品该是 Copilot / Workflow / Autopilot 哪种？
         R67 → 哪些场景值得用 reasoning 模型（贵 50-300 倍但能省失败重试）？
         R66 → 多模态 / Computer Use 该上吗？
         产出：自己产品的 "产品模式 + HITL 设计说明书"

Month 5: 基础设施层（R64 + R63 + R47）
         R64 网关三层 → 选 LiteLLM / Portkey / 自建？
         R63 服务化 → SLA / 监控 / 成本治理
         R47 Redis 缓存底座
         产出：自己产品的 "基础设施选型决策树"

Month 6: 安全与合规（R57 + R17 + R70 §事故复盘）
         R57 红队 + Prompt Injection 防御四层
         R17 长期漂移检测
         产出：自己产品的 "安全红线清单 + 事故应急 Runbook"

Month 7-9: 实战（带团队跑一个完整 AI-Native 项目）
         按 R70 路线图 M1-M6 实操，每月一次复盘对照
         同时关注 reports 新增报告（每月 1-2 篇增量阅读）
```

**路径 C 与 A/B 的关系**：
- 路径 C ≠ 跳过技术层。**Month 1 必须走 A 的 W1-W4**——不会跑 Hello Agent 的管理者会被团队戏耍。
- 路径 C ≠ 路径 B 的简化版。**B 是"我要造引擎"，C 是"我要决定造不造、买谁的、怎么用"**——决策需要的视野和动手需要的深度互相不能替代。
- 路径 C 在 Month 4-6 **可以与团队分工**：你读 R68/R69/R70/R64 全篇，让组员 A 深读 R67、组员 B 深读 R66、组员 C 深读 R71，然后开会互相讲。**这本身就是 EDD 团队建设的一部分**。

> **v1.2 新增观察**：很多团队在"AI 转型"时栽在管理者只会背 ChatGPT 段子但不会算 token 账上。R69+R70 不是给工程师准备的，是**给决策者解套的**。


> **v1.1 新增观察**：随着 L3 三篇报告补齐，**路径 A 现在也能（轻度地）涉足推理部署**——读 R58 TL;DR 就能做到"会用 Ollama / 能看懂 vLLM 选型表"，这是以前 v1.0 做不到的。

---

## 五、内容缺口状态（v1.1：全部补齐）

v1.0 识别的 12 个缺口在 2026-04-24 一轮补齐中**全部完成**：

| ID | 缺口 | 所属阶段 | v1.0 优先级 | v1.1 状态 |
|----|------|---------|------------|----------|
| **G1** | ML 基础速览 | L0 | 低 | ✅ [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 合篇 |
| **G2** | 数学直觉（线代/概率/softmax/KL） | L0 | 中 | ✅ [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 合篇 |
| **G3** | PyTorch 入门 | L0 | 低 | ✅ [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 合篇 |
| **G4** | Tokenization 深度解析 | L1 | 🔴 高 | ✅ [R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) |
| **G5** | LLM 预训练全景（Scaling Law） | L2 | 🟡 中 | ✅ [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) |
| **G6** | 模型量化技术 | L3 | 🔴 高 | ✅ [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 合篇 |
| **G7** | 推理引擎调研 | L3 | 🔴 高 | ✅ [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 合篇 |
| **G8** | 推理优化技术（KV Cache / FlashAttn） | L3 | 🟡 中 | ✅ [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) |
| **G9** | 服务化生产部署（SLA / 监控） | L3+L7 | 🟡 中 | ✅ [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) |
| **G10** | Prompt Engineering 系统化 | L4 | 🔴 高 | ✅ [R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) |
| **G11** | LLM Benchmark 速查 | L6 | 🟡 中 | ✅ [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) |
| **G12** | Agent 安全与红队 | L6 | 🔴 高 | ✅ [R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) |

### 新发现的次级空白（v1.1 遗留）

补齐过程中涌现的"次级深度"话题，**不紧急但值得记录**：

| 话题 | 所属阶段 | 现状 | 建议 |
|------|---------|------|------|
| 架构变种深度对比（MoE / Mamba / RWKV） | L1 | [R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) 只扫边 | 未来出现国产 MoE 新标杆时再出专题 |
| Coding Agent 专题（Cursor / Cline / aider / OpenCode） | L5 | 散在 [R29](R29_SDKvsIDEvsCLI%E4%B8%89%E7%A7%8DAgent%E5%BC%80%E5%8F%91%E6%A8%A1%E5%BC%8F.md)[R32](R32_Copilot%E5%85%A8%E5%B1%80%E8%87%AA%E5%AE%9A%E4%B9%89%E8%B7%A8%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%A4%8D%E7%94%A8.md) | 值得出专题，标为 G13 候选 |
| Agent 记忆系统横评（Mem0 / Letta / Zep） | L5 | 散在 [R19](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R19_Copilot%E5%85%A8%E5%B1%80%E8%AE%B0%E5%BF%86%E6%9E%B6%E6%9E%84.md)[R47](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) | 值得出专题，标为 G14 候选 |
| Multimodal LLM（视觉 / 音频 / 视频） | L1+L4 | 基本未覆盖 | 看业务需要再决定 |
| LLM 评估的统计学严谨性（误差棒 / 显著性） | L6 | [R15](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R15_Skill%E4%B8%8EAgent%E8%AF%84%E4%BC%B0%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md)[R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 未深入 | 中等优先级 |

> **决策**：v1.1 不启动新缺口补充，**优先让现有 62 篇沉淀、被使用、被验证**。若 6-8 周后仍未出现"某篇报告从没被交叉引用过"的情况，再考虑上 G13/G14。

---

## 六、推荐的第一个月行动清单（v1.2 重写版：覆盖 A/B/C 三路径）

> **设计变化**：v1.1 的清单只服务路径 A/B 工程师。v1.2 起每周拆"必读"和"按路径分支"两层——所有人共享 W1-W2 基础课，W3 起按你选的路径分流。

### W1：建立直觉与动手感（所有路径共享）

| 任务 | 时长 | 产出 |
|------|------|------|
| 通读 R54 本报告（你正在看） | 1h | 知道路线全貌、三条路径选哪条 |
| 读 [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) §TL;DR 速查卡 | 30min | 主流栈一图流（先建立"地图感"再深入） |
| 跑 [tutorial/Ch01-跑通第一个Agent](../../tutorial/Ch01-%E8%B7%91%E9%80%9A%E7%AC%AC%E4%B8%80%E4%B8%AAAgent.md) + [tutorial/Ch02-Agent的本质](../../tutorial/Ch02-Agent%E7%9A%84%E6%9C%AC%E8%B4%A8.md) | 4h | Hello Agent 跑通 |
| 读 [R61](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R61_LLM%E4%BB%8E%E4%B8%9A%E8%80%85%E6%95%B0%E5%AD%A6%E4%B8%8E%E4%BB%A3%E7%A0%81%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) L0 数学/代码速查 | 4-6h | 数学代码基础复习过关 |

### W2：Transformer 与 Tokenization（所有路径共享）

| 任务 | 时长 | 产出 |
|------|------|------|
| [R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) Transformer 全篇 | 6h | 能讲清"输入 Hello 之后发生了什么" |
| [R56](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R56_Tokenization%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90.md) Tokenization | 3h | 用 tiktoken 对比中英文切分 |
| 手撕 70 行 Multi-Head Attention（[R37](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R37_Transformer%E5%8E%9F%E7%90%86%E4%BB%8E%E7%9B%B4%E8%A7%89%E5%88%B0%E4%BB%A3%E7%A0%81.md) §代码章） | 4h | 跑通的 MHA 代码 |
| **[路径 C 加修]** [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) 全篇 + [R67](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R67_Reasoning%E6%A8%A1%E5%9E%8B%E4%B8%93%E9%A2%98_o1_R1_Thinking.md) §TL;DR | 3h | 知道团队该用 reasoning 模型还是普通模型 |

### W3：分路径走

#### 🚀 路径 A（应用工程师）W3
| 任务 | 时长 | 产出 |
|------|------|------|
| [R03](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) Agent 架构 + [R24](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R24_%E4%BB%8E%E9%9B%B6%E6%9E%84%E5%BB%BAAgent%E6%B8%90%E8%BF%9B%E5%BC%8F%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF.md) 渐进式 8 次迭代 | 6h | 能默写 Agent 五件武器 |
| [R55](R55_PromptEngineering%E7%B3%BB%E7%BB%9F%E5%8C%96%E8%B0%83%E7%A0%94.md) Prompt Engineering | 4h | 用 5 种 Prompt 模式做 A/B |
| [R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md) Coding Agent 五家横评 §TL;DR + 决策树 | 2h | 自己装上 Cline / Cursor 之一 |

#### 🔬 路径 B（深究工程师）W3
| 任务 | 时长 | 产出 |
|------|------|------|
| [R62](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R62_LLM%E9%A2%84%E8%AE%AD%E7%BB%83%E5%85%A8%E6%99%AF_%E4%BB%8E%E6%95%B0%E6%8D%AE%E5%88%B0ScalingLaw.md) LLM 预训练全景 | 6h | 能讲清 Scaling Law 三次校正 |
| [R52](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R52_%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83%E4%B8%8E%E5%BE%AE%E8%B0%83%E6%8A%80%E6%9C%AF%E5%85%A8%E6%99%AF.md) 模型训练与微调 §SFT + LoRA Hello World | 8h | 用 Unsloth 跑通一次 LoRA |
| [R67](../01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R67_Reasoning%E6%A8%A1%E5%9E%8B%E4%B8%93%E9%A2%98_o1_R1_Thinking.md) Reasoning 专题（重点 §训练范式） | 4h | 能讲清 RLVR vs SFT 的根本差异 |

#### 🎩 路径 C（技术管理者）W3
| 任务 | 时长 | 产出 |
|------|------|------|
| [R69](R69_LLM_Agent%E7%BB%8F%E6%B5%8E%E5%AD%A6%E4%B8%8E%E5%95%86%E4%B8%9A%E5%86%B3%E7%AD%96.md) LLM 经济学全篇 | 6h | 自己团队的 token 账算清楚 |
| [R31](R31_%E7%A0%94%E5%8F%91%E5%B7%A5%E4%BD%9C%E6%B5%81AI%E6%8F%90%E6%95%88%E6%9C%BA%E4%BC%9A%E5%88%86%E6%9E%90.md) 研发流程提效分析 + R31b（原稿交叉引用，本归档未解析） 仪表盘 | 4h | 团队哪些环节值得 AI 提效的优先级表 |
| [R71](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md) Coding Agent 五家横评 + [R65](../06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R65_Agent%E4%B8%BB%E6%B5%81%E6%8A%80%E6%9C%AF%E6%A0%88%E6%90%AD%E9%85%8D%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) §决策树 | 4h | 给团队的 Coding Agent 选型建议书 |

### W4：分路径走

#### 🚀 路径 A W4
| 任务 | 时长 | 产出 |
|------|------|------|
| [R30](R30_RAG%E4%BB%8E%E5%85%A5%E9%97%A8%E5%88%B0%E7%94%9F%E4%BA%A7%E8%90%BD%E5%9C%B0.md) RAG 从入门到生产 | 6h | 跑通生产级 RAG 150 行代码 |
| [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) §Hello World 三连（Ollama → vLLM） | 4h | 本地跑起 Qwen2.5-7B-Q4 |
| [R72](../02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R72_Agent%E8%AE%B0%E5%BF%86%E7%B3%BB%E7%BB%9F%E6%A8%AA%E8%AF%84.md) §TL;DR + 决策树 | 1h | 知道"Mem0 / Letta / Zep / 自建"该选谁 |

#### 🔬 路径 B W4
| 任务 | 时长 | 产出 |
|------|------|------|
| [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md) 推理部署全篇 + [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 推理优化 | 8h | 看懂 vLLM / SGLang 选型矩阵 |
| [R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 服务化生产部署全篇 | 6h | 起一套 vLLM + Langfuse + Autoscaling |

#### 🎩 路径 C W4
| 任务 | 时长 | 产出 |
|------|------|------|
| [R70](R70_AI-Native%E5%9B%A2%E9%98%9F%E4%B8%8E%E5%B7%A5%E7%A8%8B%E7%AE%A1%E7%90%86.md) AI-Native 团队管理全篇 | 6h | 自己团队的 6 月 AI-Native 路线图 v0.1 |
| [R68](R68_Agent%E4%BA%A7%E5%93%81%E6%A8%A1%E5%BC%8F%E4%B8%8EHITL%E8%AE%BE%E8%AE%A1.md) 产品模式与 HITL | 4h | 自己产品的"模式定位说明书" |
| [R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) §防御四层 | 2h | 安全红线清单 v0.1 |

### 月末自检（v1.2 重设：分路径出题）

#### 共同必答（5 题）
- 能用 5 分钟讲清楚"Transformer 为什么 Decoder-only 主导"吗？
- 能不看教程写出调用 2 个工具的 Agent 吗？
- 能说出 RAG 四代演进和 Contextual Retrieval 为什么有效吗？
- 能说出"同一段中文在 GPT-4 和 Qwen 的 Token 数差多少、为什么"吗？
- 能说出"Mem0 / Letta / Zep 三家最大的设计哲学差异"吗？

#### 路径 A 加题（2 题）
- 能不看文档配出 Cursor / Cline / Aider 三家中**最适合你工作流**的那一家并说出理由吗？
- 能在 Ollama 上把一个 7B 量化模型跑起来 + 测出 TTFT 吗？

#### 路径 B 加题（2 题）
- 能讲清 GRPO 比 PPO 简化在哪、为什么 R1 能用它训出 reasoning 能力吗？
- 能说出 vLLM / llama.cpp / TensorRT-LLM 三家各自适用场景 + KV Cache 的核心机制吗？

#### 路径 C 加题（3 题）
- 能用 R69 框架算出"我们团队接 OpenAI API vs 自建 vLLM 拐点在多少 DAU"吗？
- 能说出"我的产品该是 Copilot / Workflow / Autopilot 中哪种 + 为什么"吗？
- 能列出"我们团队接下来 6 个月落 AI-Native 的关键里程碑（按 R70 模板）"吗？

> **诚实自评原则**：题目是给自己看的。你说"能"就要能 5 分钟讲给团队听不卡壳。卡了 → 回头补那一项。所有题都能 → **进入 L4-L5 深耕（A/B）或正式启动团队转型（C）**。

---

## 📌 来源清单

- 本工作区 KNOWLEDGE_INDEX（原稿交叉引用，本归档未解析）（62 篇报告编号速查表）
- 本工作区 DELIVERABLES_INDEX（原稿交叉引用，本归档未解析）（46 个产出物登记）
- 本工作区 `tutorial/README.md`（12 章教程已有编排）
- 本工作区 `_inbox/待补调研任务清单.md`（v1.0 G1-G12 调研简报，已全部落地）
- 外部参考：fast.ai "Whole Game" 教学法 / Karpathy "Zero to Hero" 课程大纲

**来源一致性**：本报告为**工作区内部重组型**，未引入新事实，所有节点均对应本库已有报告。

---

## 后续计划（v1.1 重设）

1. ~~v1.0：用户决策补缺口~~ ✅ 已完成（2026-04-24）
2. ~~v1.0：按优先级产出缺口报告~~ ✅ 已完成（R55-R63 共 9 篇）
3. **v1.1 新重心：沉淀与验证**
   - 用 6-8 周时间让新 9 篇报告被使用、被交叉引用
   - 观察哪些报告"读了就忘"（需重写）、哪些"反复被翻"（值得加深）
4. **教程层联动**：
   - Ch11 部署上线 → 补充链接到 [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)[R63](R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md)
   - Ch08 评估与质量 → 补充链接到 [R60](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R60_LLM_Benchmark%E9%80%9F%E6%9F%A5%E6%89%8B%E5%86%8C.md) Benchmark 速查
   - Ch09 安全与可靠性 → 补充链接到 [R57](../05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) 红队
   - 建议新增 `Ch13-LLM推理部署入门` 一章，作为 R58/R59/R63 的教学层入口
5. **v2.0 触发条件**（任一出现即升版）：
   - 本库新增 10+ 篇报告（推到 R72+）
   - 模型范式出现断代（如 Mamba 取代 Transformer、某国产开源模型做到 Claude 3.7 水准）
   - 用户实际使用本路线后反馈哪些地方需要重组
