---
name: knowledge-base-organizer
description: >
  Analyzes knowledge bases and selects the optimal organization strategy.
  Use when: user provides a directory of documents/code and needs it organized
  for LLM consumption; user asks how to make a knowledge base LLM-friendly;
  user wants to analyze knowledge base characteristics before choosing a strategy.
applyTo: "**"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Knowledge Base Organizer Skill

> 给定一个知识库路径，自动分析其组成，选择最优策略，执行知识库的组织与转化。

### Overview

本 Skill 自动完成知识库的 **画像分析 → 策略决策 → 组织执行 → 验证** 全流程。
核心依赖：LLM Wiki 三层架构（Raw Sources → Wiki → Schema）。

## 1. 触发条件

当用户提出以下类型的请求时激活此 Skill：
- "帮我组织/整理这个知识库"
- "分析这个知识库，选最好的方式给 LLM 用"
- "把这些文档变成 LLM 友好的格式"
- "这个知识库太大了，怎么让 AI 能用"
- 提供了一个目录路径，期望将其作为 Agent 的业务知识

## 2. 执行流程

### Phase 0: 意图确认（Ask）

**目标**：在分析知识库之前，先弄清楚"这个知识库要用来做什么"。用途直接影响格式选择和策略修正。

**必须交互式向用户确认以下问题**（如果用户未主动说明）：

#### 问题 1：使用场景

> 这个知识库将用于什么场景？
> 1. 🖥️ **Coding Agent 编码上下文** — 给 AI 编程助手提供代码/架构/API 参考
> 2. ✍️ **文字创作规则参考** — 给 AI 写作助手提供风格指南/规范/示例
> 3. 📋 **业务流程/SOP** — 给 AI 助手提供标准操作流程和业务规则
> 4. 💬 **客服/问答系统** — 给 AI 客服提供FAQ和产品知识
> 5. 📚 **研究/分析素材** — 给 AI 提供分析和推理的原始素材
> 6. 🎓 **培训/教育材料** — 给 AI 导师提供教学内容
> 7. 🔧 **其他（请描述）**

#### 问题 2：精度要求

> 对回答的精度要求是？
> - **零容错**：涉及数值计算、法规、医疗等（必须保留所有细节）
> - **高精度**：业务规则、SOP（关键信息不能丢）
> - **允许概括**：研究素材、教育内容（核心观点对即可）

#### 问题 3：交互模式

> Agent 将如何使用这个知识库？
> - **常驻上下文**：每次对话都需要完整知识（如编码规范、写作规则）
> - **按需查询**：用户提问时才需要检索（如FAQ、文档查询）
> - **混合模式**：核心规则常驻 + 细节按需查询

---

#### 用途 → 策略修正矩阵

用途确认后，Phase 2 的策略选择需要叠加以下修正：

| 使用场景 | 格式偏好 | 策略修正 | 蒸馏重点 | 输出结构 |
|----------|---------|---------|---------|---------|
| **Coding Agent** | XML 标签（精确边界） | 代码类→走分层架构（实验报告方案）；文档类→正常流程 | 保留 API 签名、类型定义、import 关系 | 符号索引 + 依赖图 + 分层 Map |
| **文字创作规则** | YAML（规则）+ Markdown（示例） | 强制提取规则为 IF-THEN；示例必须完整保留 | 规则显式化、示例配对、反面案例 | 规则清单 + 示例库 + 术语表 |
| **业务 SOP** | Markdown + Mermaid 流程图 | 流程图提取优先；条件分支必须完整 | 步骤序列化、审批流程、异常处理 | 流程图 + 步骤文档 + 检查清单 |
| **客服/问答** | Markdown（Q&A 格式） | 强制生成 QA 对；BM25 索引优先于语义搜索 | 问题变体覆盖、精确答案 | QA 知识库 + BM25 索引 |
| **研究/分析** | Markdown + 表格 | GraphRAG 权重上调（跨文档推理重要） | 论据-结论映射、数据表格、来源标注 | 知识图谱 + 主题摘要 + 数据表 |
| **培训/教育** | 分层 Markdown | RAPTOR 权重上调（渐进式理解重要） | 概念层次、从简到繁、练习题 | 多层级文档（入门→进阶→深入） |

#### 代码类知识库的特殊处理

**当使用场景 = "Coding Agent 编码上下文" 且知识库主要由代码文件组成时**，跳过标准的 Phase 1~3 流程，改用以下专用流程：

```
代码知识库专用流程（参考《Claude-Code源码上下文策略实验报告》）：

1. Tree-sitter AST 解析 → 提取所有符号（类、函数、类型）
2. Import 依赖图构建 → 识别核心-外围结构
3. PageRank 重要性排序 → 决定哪些文件始终在上下文
4. 生成分层上下文：
   - Layer 0: Directory Map (~20K tokens, 常驻)
   - Layer 1: 核心文件签名 + 编辑焦点 (~20-50K, 动态)
   - Layer 2: Agent 工具按需深入 (0-50K, 按需)
5. 大文件（4000+ 行）特殊处理：局部 + 符号 Map
```

此流程的详细实现见 `Claude-Code源码上下文策略实验报告.md` 的第 7 节。

---

### Phase 1: 知识库画像（Profile）

**目标**：量化了解知识库的六个维度。

执行 `analyze_kb.py`（位于本 Skill 同目录），或手动完成以下分析：

```bash
python skills/knowledge-base-organizer/analyze_kb.py "<知识库路径>"
```

如果无法运行脚本，手动完成以下分析步骤：

#### 1.1 规模评估

扫描知识库目录，收集以下数据并填入表格：

| 指标 | 值 |
|------|-----|
| 总文件数 | |
| 总字符数 | |
| 估算 Token 数 | （字符数 ÷ 4） |
| 文件类型分布 | .md: X, .txt: X, .pdf: X, .docx: X, ... |
| 最大单文件 Token 数 | |
| 中位数文件 Token 数 | |

#### 1.2 结构化程度

| 指标 | 值 |
|------|-----|
| Markdown 文件占比 | |
| 有标题层级（#）的文件占比 | |
| 有目录/索引文件 | 是/否 |
| 目录嵌套深度 | |
| llms.txt 是否存在 | 是/否 |

#### 1.3 互联度

| 指标 | 值 |
|------|-----|
| 交叉引用链接数 | （统计 `xxx（原稿引用文件未随本次归档发布）` 和 `参见/see also` 的数量） |
| 引用密度 | （引用数 ÷ 文件数） |
| 是否有明显的"核心→外围"结构 | 是/否 |

#### 1.4 内容类型

| 类型 | 占比 |
|------|------|
| 纯文本/说明 | |
| 表格/数据 | |
| 代码/配置 | |
| 问答对 | |
| 流程/SOP | |
| 图片/图表（仅统计引用） | |

#### 1.5 更新频率

| 指标 | 值 |
|------|-----|
| 最近 30 天修改文件占比 | |
| 最近 90 天修改文件占比 | |
| 文件平均年龄 | |
| 更新频率评级 | 高频/中频/低频/静态 |

#### 1.6 领域评估

| 指标 | 值 |
|------|-----|
| 领域 | （由内容判断：技术/医学/法律/通用/...） |
| 专业术语密度 | 高/中/低 |
| 是否需要保留精确数值 | 是/否 |

### Phase 2: 策略决策（Decide）

**决策 = Phase 1 数据（知识库画像）× Phase 0 数据（用途修正）**

#### Step 0: 用途前置过滤

如果 Phase 0 确认的使用场景有专用流程，**优先走专用流程**：

```
使用场景判断（优先级高于规模判断）：
├── Coding Agent + 代码文件为主 ──→ 代码专用流程（分层架构，见 Phase 0）
├── 客服/问答 + 任何规模 ─────────→ 策略修正：强制叠加 QA 生成 + BM25 索引
└── 其他 ──────────────────────→ 进入 Step 1（按规模决策）
```

#### Step 1-3: 基于画像选择基础策略（原决策树）

```
Step 1: 判断规模
├── 总 Token ≤ 50K  ────────→ 策略 A：Context Stuffing
├── 总 Token 50K~200K ──────→ 策略 B：Wiki 法 + Prompt Caching
├── 总 Token 200K~2M ───────→ 进入 Step 2
└── 总 Token > 2M ──────────→ 进入 Step 3

Step 2: 中大型知识库（200K~2M tokens）
├── 结构化程度高（Markdown 占比>60%, 有标题层级）
│   ├── 互联度高（引用密度>0.5）────→ 策略 C：知识蒸馏 → Wiki → Cache
│   └── 互联度低 ───────────────────→ 策略 D：知识蒸馏 → 分段 Cache
└── 结构化程度低
    ├── 内容以文本为主 ──────────────→ 策略 E：知识蒸馏 → RAPTOR
    └── 内容以数据/表格为主 ─────────→ 策略 F：知识蒸馏 → 结构化提取

Step 3: 超大型知识库（> 2M tokens）
├── 需要跨文档关联推理 → 策略 G：GraphRAG + Agent 工具检索
├── 需要多层次理解 ────→ 策略 H：RAPTOR + Contextual Retrieval
├── 查询类型混合 ──────→ 策略 I：Self-Route 混合路由
└── 简单问答为主 ──────→ 策略 J：Contextual Retrieval + BM25 + Reranking
```

#### Step 4: 用途修正叠加

选定基础策略后，根据 Phase 0 的用途信息叠加修正：

```
基础策略 + 用途修正 → 最终策略

修正规则：
┌─────────────────────┬──────────────────────────────────────────────┐
│ 使用场景             │ 叠加修正                                      │
├─────────────────────┼──────────────────────────────────────────────┤
│ 文字创作规则         │ +规则提取（YAML IF-THEN）                     │
│                     │ +示例完整保留（不压缩示例段落）                  │
│                     │ +反面案例标注                                  │
│                     │ 格式改为 YAML（规则部分）+ Markdown（示例部分）  │
├─────────────────────┼──────────────────────────────────────────────┤
│ 业务 SOP            │ +流程图提取（Mermaid 语法）                     │
│                     │ +步骤必须编号且标注前置条件                      │
│                     │ +异常处理路径必须保留                           │
│                     │ +审批节点显式标注                               │
├─────────────────────┼──────────────────────────────────────────────┤
│ 客服/问答           │ +QA 对生成（覆盖问题变体）                      │
│                     │ +BM25 索引构建                                 │
│                     │ +答案精确度优先于压缩率                         │
│                     │ 格式改为 Q&A Markdown                         │
├─────────────────────┼──────────────────────────────────────────────┤
│ 研究/分析           │ +来源标注强化（每条信息标注出处）                │
│                     │ +交叉引用关系保留                              │
│                     │ GraphRAG 权重上调（即使规模不够大也考虑使用）    │
├─────────────────────┼──────────────────────────────────────────────┤
│ 培训/教育           │ +分层组织（入门→进阶→深入）                     │
│                     │ +概念间先后依赖关系标注                         │
│                     │ RAPTOR 权重上调                               │
├─────────────────────┼──────────────────────────────────────────────┤
│ 精度=零容错          │ 禁止摘要压缩数值/公式/编号                     │
│                     │ 蒸馏时必须保留原文（可添加摘要但不删原文）        │
├─────────────────────┼──────────────────────────────────────────────┤
│ 交互=常驻上下文      │ 输出必须控制在 200K tokens 内                  │
│                     │ 推荐 Prompt Caching                           │
│ 交互=按需查询        │ 必须生成索引 + Agent 工具配置                   │
│ 交互=混合            │ 核心部分 ≤ 50K 常驻 + 其余按需                 │
└─────────────────────┴──────────────────────────────────────────────┘
```

**输出策略报告**（必须包含）：

```markdown
## 知识库分析报告

### 使用意图
- 使用场景：[Coding Agent / 文字创作规则 / 业务SOP / 客服问答 / 研究分析 / 培训教育]
- 精度要求：[零容错 / 高精度 / 允许概括]
- 交互模式：[常驻上下文 / 按需查询 / 混合模式]

### 画像摘要
- 规模：XXX 个文件，约 XXX tokens（≈ XXX 页）
- 结构化程度：高/中/低
- 互联度：高/中/低
- 内容类型：以 XXX 为主
- 更新频率：高频/中频/低频/静态
- 领域：XXX

### 选定策略：策略 X — [策略名称]
- 选择理由：...
- 用途修正：[具体叠加了什么修正，或"无修正"]
- 输出格式：[Markdown / XML / YAML / 混合]
- 预期效果：召回率 XX%，Token 利用率 XX%
- 预处理成本：一次性 / 持续
- 推荐更新方式：...

### 备选策略
- 策略 Y：[为什么不选，什么情况下可切换]
```

### Phase 3: 执行组织（Execute）

根据选定策略，执行对应的组织流程：

---

#### 策略 A：Context Stuffing（≤ 50K tokens）

```
1. 收集所有文件内容
2. 按目录结构排列，每个文件加 "## 文件名" 标题
3. 在最前面加全局概述（由 LLM 自动生成）
4. 输出单个 Markdown 文件
```

**输出格式**：
```markdown
# [知识库名称] — 完整知识库

> 概述：[LLM 生成的 1-2 句总结]

## 目录
- [文件1](#文件1)
- [文件2](#文件2)
- ...

---

## 文件1: xxx.md
[完整内容]

## 文件2: yyy.md
[完整内容]
```

---

#### 策略 B：Wiki 法 + Prompt Caching（50K~200K tokens）

```
1. 将所有文件转为 Markdown（如果还不是）
2. 生成 llms.txt 索引文件
3. 按主题分类组织，每个主题一个 Markdown 文件
4. 生成全局概览文件（00-overview.md）
5. 如果有 Repomix 可用，打包为单文件
6. 标注 Prompt Caching 使用建议
```

**llms.txt 模板**：
```markdown
# [知识库名称]

> [一句话描述]

## 核心文档（始终加载）
- 00-overview.md（原稿引用文件未随本次归档发布）: 全局概览和核心概念
- 01-glossary.md（原稿引用文件未随本次归档发布）: 术语表

## 主题文档（按需加载）
- topic-a.md（原稿引用文件未随本次归档发布）: [描述]，当问题涉及 [关键词] 时加载
- topic-b.md（原稿引用文件未随本次归档发布）: [描述]，当问题涉及 [关键词] 时加载

## 参考数据
- data-tables.md（原稿引用文件未随本次归档发布）: [描述]

## 常见问题路由
- "如何 XXX" → 参见 topic-a.md#section-2
- "YYY 的标准是什么" → 参见 topic-b.md#standards
```

---

#### 策略 C/D：知识蒸馏 → Wiki / 分段 Cache

```
1. 将知识库分为合理的分组（按目录 / 按主题）
2. 对每组调用 LLM 生成：
   a. 核心概念提取（定义 + 关键事实）
   b. 业务规则整理（IF-THEN 格式）
   c. 流程图生成（Mermaid 语法）
   d. 数值参数表格化
3. 整合为精炼 Wiki（目标：原始 token 的 20%-30%）
4. 生成 llms.txt 索引
5. 标注来源映射（精炼内容 → 原始文档位置）
```

**蒸馏 Prompt 模板：**
```
你是知识蒸馏专家。请阅读以下原始文档，提取核心知识并生成精炼版本。

要求：
1. 保留所有精确数值、日期、编号（零信息损失）
2. 将冗余描述压缩为要点
3. 将隐含的业务规则显式化为 IF-THEN 格式
4. 为每条信息标注来源（原文件名+章节）
5. 生成术语对照表
6. 目标：压缩到原始内容的 25% 以内

<source>
{文档内容}
</source>
```

---

#### 策略 E：知识蒸馏 → RAPTOR

```
1. 先执行策略 C/D 的蒸馏步骤
2. 对蒸馏结果进行语义分块（参见本 Skill 的 hybrid_chunk 函数）
3. 用 embedding 模型对 chunks 聚类
4. 对每个聚类生成摘要
5. 递归聚类+摘要，构建 2-3 层树
6. 输出树结构 + 各层级摘要
```

---

#### 策略 F：结构化提取

```
1. 识别所有表格、数据项、公式
2. 提取为结构化格式（YAML 或 JSON）
3. 文本部分蒸馏为摘要
4. 生成数据索引
5. 输出：结构化数据文件 + 文本摘要 + 索引
```

---

#### 策略 G：GraphRAG + Agent 工具

```
1. 指导用户安装 graphrag：pip install graphrag
2. 构建 GraphRAG 索引（警告：预处理时间长、成本高）
3. 同时生成核心知识蒸馏（用于 Agent 的基础理解）
4. 设计 Agent 工具集：
   - search_knowledge: GraphRAG local search
   - global_question: GraphRAG global search
   - read_source: 读取原始文档
5. 输出：工具配置 + 核心知识摘要 + 使用指南
```

---

#### 策略 H：RAPTOR + Contextual Retrieval

```
1. 构建 RAPTOR 树（同策略 E）
2. 对所有 chunks（含摘要层）添加上下文说明（Contextual Retrieval）
3. 同时创建 BM25 索引
4. 输出：RAPTOR 树 + 增强索引 + 检索配置
```

---

#### 策略 I：Self-Route 混合路由

```
1. 将知识库做两套准备：
   a. 全量格式化（Wiki 法 / Prompt Caching）—— 供 LC 模式使用
   b. Contextual Retrieval 索引 —— 供 RAG 模式使用
2. 实现路由逻辑：RAG 先答 → 自评估 → 不确定则切 LC
3. 输出：两套知识产物 + 路由配置 + 使用指南
```

---

#### 策略 J：Contextual Retrieval + BM25 + Reranking

```
1. 语义分块（hybrid_chunk）
2. 对每个 chunk 用 LLM 生成上下文说明
3. 上下文+chunk 一起做 embedding
4. 同时建立 BM25 索引
5. 配置 Reranking（推荐 Cohere Reranker 或 Voyage AI）
6. 输出：向量索引 + BM25 索引 + Reranking 配置 + 检索代码模板
```

### Phase 4: 验证与输出

每次执行完成后，必须：

1. **输出产物清单**：
   ```markdown
   ## 输出产物
   - `output/00-overview.md` — 全局概览
   - `output/llms.txt` — LLM 索引文件
   - `output/topic-xxx.md` — 主题文档 x N
   - `output/analysis_report.json` — 知识库画像数据
   ```

2. **验证检查**：
   - [ ] 输出总 Token 数是否在目标窗口内
   - [ ] 核心信息是否保留（抽查 3-5 个关键事实）
   - [ ] 来源映射是否完整
   - [ ] 索引文件是否可用

3. **使用指南**（附在输出中）：
   ```markdown
   ## 使用方式
   
   ### 直接注入（推荐用于 ≤ 200K tokens 的输出）
   将 `output/` 目录下所有文件内容拼接后作为 system prompt。
   配合 Prompt Caching 降低成本。
   
   ### Agent 工具模式（推荐用于 > 200K tokens 的输出）
   1. 将 `output/00-overview.md` 作为常驻 system prompt
   2. 注册以下工具供 Agent 按需调用：
      - read_topic(topic_name) → 读取对应主题文档
      - search_knowledge(query) → BM25 搜索
   ```

## 3. Workflow: 增量编译（External KB Compile）

> **适用场景**：研发团队已有大量 .md 业务文档，希望作为 AI coding 时的业务知识上下文，但文件太多需要管理。

### 与标准流程（Phase 0-4）的区别

| 维度 | 标准流程（Phase 0-4） | 增量编译 |
|------|---------------------|---------|
| 适用时机 | 一次性组织/转化知识库 | **持续维护**，文件会反复变更 |
| 核心价值 | 选策略 + 执行重组 | **追踪变更 + 路由索引** |
| 产出物 | 重组后的文档 | 原文不动，生成 `.kb_manifest.json` + `kb_index.md` |
| 成本 | 一次性（可能需要大量 LLM 调用做蒸馏） | 增量（只处理变更文件） |

### 何时用增量编译（而非标准流程）

```
用户的文件...
├── 已经是 .md 格式 + 不需要格式转换 ──→ ✅ 增量编译
├── 文件会持续更新（不是静态归档） ────→ ✅ 增量编译
├── 只需要索引 + 按需加载（不需要蒸馏重组）→ ✅ 增量编译
├── 是 PDF/Word/HTML 需要先转格式 ────→ ❌ 走标准流程 Phase 3
├── 总量 > 2M tokens 需要深度蒸馏 ────→ ❌ 走标准流程 Phase 2-3
└── 只是一次性使用 ──────────────────→ ❌ 走标准流程
```

### 工具

```bash
# 位于 skills/knowledge-base-organizer/compile_kb.py
python compile_kb.py scan   <kb_path>                    # 扫描 + 变更检测
python compile_kb.py update <kb_path> <summaries.json>   # 合并 LLM 摘要
python compile_kb.py index  <kb_path>                    # 生成路由索引
python compile_kb.py status <kb_path>                    # 查看编译状态
```

### Step 1: 扫描变更

```bash
python compile_kb.py scan /path/to/docs
```

输出包含：
- 变更 diff（新增/变更/删除/未变文件数量）
- 每个待处理文件的元数据（标题、章节列表、首段文字、token 数）
- 编译计划保存到 `.kb_compile_plan.json`

### Step 2: 生成摘要（LLM 智能工作）

读取 `.kb_compile_plan.json`，为每个待处理文件生成摘要。

**快速模式**（推荐首选）——只读元数据，不读全文：

从编译计划中的 `title` + `headers` + `first_paragraph` 直接生成：
- `summary`：1-2 句话描述文件核心内容
- `tags`：3-5 个关键词标签
- `category`：分类名（如 "API文档"、"业务规则"、"架构设计"、"部署运维"）

**深度模式**——读全文（用于重要文件或元数据不足时）：

读取文件完整内容，生成更详细的摘要。

**摘要 Prompt 模板**：

```
你是知识库编译助手。根据以下文件信息，生成摘要、标签和分类。

文件路径: {path}
标题: {title}
章节: {headers}
首段: {first_paragraph}
Token 数: {tokens}

请输出 JSON 格式：
{
  "summary": "1-2 句话描述核心内容（面向不了解此文件的开发者）",
  "tags": ["标签1", "标签2", "标签3"],
  "category": "分类名"
}
```

将所有文件的摘要写入一个 JSON 文件 `summaries.json`：

```json
{
  "api/auth.md": {
    "summary": "OAuth2.0 认证流程规范，包含 JWT Token 管理和刷新机制",
    "tags": ["auth", "oauth", "jwt", "api"],
    "category": "API文档"
  },
  "business/order-flow.md": {
    "summary": "订单全生命周期流程：创建→支付→履约→售后，含状态机和异常处理",
    "tags": ["order", "workflow", "state-machine"],
    "category": "业务流程"
  }
}
```

### Step 3: 合并摘要

```bash
python compile_kb.py update /path/to/docs summaries.json
```

### Step 4: 生成路由索引

```bash
python compile_kb.py index /path/to/docs
```

产出 `kb_index.md`——按分类组织的路由表，包含：
- 分类总览（每个分类的文档数和 token 数）
- 每个文件的一行摘要 + token 数
- 标签路由表（按标签查找文档）
- 大文件提醒（>10K tokens 的文件）
- 规模适配的使用建议

### Step 5: 集成到 AI Coding 工作流

根据知识库总量选择集成方式：

```
总量 ≤ 50K tokens
  → 直接全量注入 + kb_index.md 在最前面
  → 集成方式: 将全部文件拼接后放入 copilot-instructions / CLAUDE.md

总量 50K~200K tokens
  → kb_index.md 常驻 + 全量文件配合 Prompt Caching
  → 集成方式: kb_index.md 作为 system prompt 前缀，文件通过 @file 按需引用

总量 200K~2M tokens（最常见场景）
  → kb_index.md 常驻 + LLM 按索引摘要判断读哪些文件 + 按需加载
  → 集成方式: 在 copilot-instructions.md 中引用 kb_index.md，
    声明"需要业务知识时先查索引，再读具体文件"

总量 > 2M tokens
  → 增量编译不够，需切回标准流程做蒸馏
  → 运行 analyze_kb.py 获取策略建议
```

### 增量更新（日常维护）

```bash
# 文件变更后重新扫描
python compile_kb.py scan /path/to/docs
# → 输出: "3 个文件变更，2 个新增"

# 只为变更文件生成摘要（LLM 处理）
# → 读 .kb_compile_plan.json，只处理 action=compile_new 或 recompile 的文件

# 合并 + 重新生成索引
python compile_kb.py update /path/to/docs new_summaries.json
python compile_kb.py index /path/to/docs
```

### 与标准流程的组合使用

增量编译和标准流程不是互斥的：

1. **先跑 `analyze_kb.py`**（了解知识库全貌和推荐策略）
2. **如果策略是 A/B/C/D** → 用增量编译做日常维护
3. **如果策略是 E~J** → 用标准流程做一次性深度处理，之后切增量编译维护索引

---

## 4. 辅助函数库

以下 Python 函数可在分析和组织过程中使用：

```python
import os
import re
from pathlib import Path
from collections import Counter

def profile_knowledge_base(kb_path: str) -> dict:
    """Phase 1: 知识库画像（含代码仓库检测 + 有效结构化率 + 空目录保护）"""
    kb = Path(kb_path)
    files = list(kb.rglob("*"))
    files = [f for f in files if f.is_file()]
    
    # 空目录保护
    if not files:
        return {
            "total_files": 0, "total_chars": 0, "total_tokens_est": 0,
            "file_types": {}, "md_ratio": 0, "structured_ratio": 0,
            "cross_ref_count": 0, "cross_ref_density": 0,
            "size_tier": "empty", "is_code_repo": False,
            "content_types": {}, "file_stats": [],
        }
    
    # 代码文件扩展名集合
    CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp",
                 ".h", ".hpp", ".go", ".rs", ".rb", ".php", ".cs", ".swift",
                 ".kt", ".scala", ".sh", ".bash", ".ps1", ".lua", ".r",
                 ".sql", ".html", ".css", ".scss", ".vue", ".svelte"}
    
    # 规模 & 内容类型
    total_chars = 0
    code_file_chars = 0
    file_stats = []
    ext_counter = Counter()
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            chars = len(content)
            total_chars += chars
            if f.suffix.lower() in CODE_EXTS:
                code_file_chars += chars
            file_stats.append({"path": str(f.relative_to(kb)), "chars": chars, "tokens_est": chars // 4})
            ext_counter[f.suffix.lower()] += 1
        except:
            pass
    
    # 代码仓库检测
    is_code_repo = (code_file_chars / max(total_chars, 1)) > 0.5
    
    # 结构化程度
    md_files = [f for f in files if f.suffix.lower() in (".md", ".markdown")]
    md_with_headers = 0
    for f in md_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'^#{1,3}\s', content, re.MULTILINE):
                md_with_headers += 1
        except:
            pass
    
    # 互联度（仅统计内部文件引用，排除 http/mailto/纯锚点）
    total_refs = 0
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'\[.*?\]\(([^)]*)\)', content):
                link = m.group(1).split('#')[0].strip()
                if not link:
                    continue
                if link.startswith(('http://', 'https://', 'mailto:')):
                    continue
                total_refs += 1
            for m in re.finditer(r'(?:参见|see\s+also)', content, re.IGNORECASE):
                after = content[m.end():m.end()+5]
                if re.match(r'\s*[\[`]', after):
                    total_refs += 1
        except:
            pass
    
    total_tokens = total_chars // 4
    md_ratio = len(md_files) / len(files)
    structured_ratio = md_with_headers / max(len(md_files), 1)
    
    return {
        "total_files": len(files),
        "total_chars": total_chars,
        "total_tokens_est": total_tokens,
        "file_types": dict(ext_counter),
        "md_ratio": md_ratio,
        "structured_ratio": structured_ratio,
        "cross_ref_count": total_refs,
        "cross_ref_density": total_refs / len(files),
        "is_code_repo": is_code_repo,
        "size_tier": (
            "tiny" if total_tokens <= 50_000
            else "small" if total_tokens <= 200_000
            else "medium" if total_tokens <= 2_000_000
            else "large"
        ),
        "file_stats": sorted(file_stats, key=lambda x: -x["tokens_est"])[:20],
    }


def select_strategy(profile: dict) -> dict:
    """Phase 2: 基于画像选择策略（含有效结构化率修正 + 代码仓库检测）"""
    tier = profile["size_tier"]
    
    if tier == "tiny":
        return {"strategy": "A", "name": "Context Stuffing", "reason": f"知识库仅 {profile['total_tokens_est']} tokens，直接全量塞入"}
    
    if tier == "small":
        return {"strategy": "B", "name": "Wiki 法 + Prompt Caching", "reason": f"知识库 {profile['total_tokens_est']} tokens，在 200K 窗口内，用 Cache 降低成本"}
    
    # 有效结构化率 = MD占比 × 有标题的MD占比（避免少量 MD 高 structured_ratio 误导）
    effective_structure = profile["md_ratio"] * profile["structured_ratio"]
    
    if tier == "medium":
        if effective_structure > 0.5:
            if profile["cross_ref_density"] > 0.5:
                return {"strategy": "C", "name": "知识蒸馏 → Wiki → Cache", "reason": "有效结构化率高、互联度高，适合蒸馏为 Wiki"}
            else:
                return {"strategy": "D", "name": "知识蒸馏 → 分段 Cache", "reason": "结构化好但互联度低，分段蒸馏更高效"}
        else:
            if profile["md_ratio"] > 0.3:
                return {"strategy": "E", "name": "知识蒸馏 → RAPTOR", "reason": "有效结构化率低，RAPTOR 树状检索更适合"}
            else:
                return {"strategy": "F", "name": "知识蒸馏 → 结构化提取", "reason": "非 Markdown 内容多，需要先结构化提取"}
    
    # large — 先检测代码仓库
    is_code = profile.get("is_code_repo", False)
    if is_code:
        return {"strategy": "CODE", "name": "代码专用流程", "reason": "大型代码仓库，走 Tree-sitter + PageRank + 分层架构"}
    if profile["cross_ref_density"] > 1.0:
        return {"strategy": "G", "name": "GraphRAG + Agent 工具", "reason": "超大型高互联知识库，知识图谱最适合"}
    elif effective_structure > 0.4:
        return {"strategy": "H", "name": "RAPTOR + Contextual Retrieval", "reason": "超大型半结构化知识库，多层检索"}
    else:
        return {"strategy": "I", "name": "Self-Route 混合路由", "reason": "超大型知识库，Self-Route 兼顾质量和成本"}


def hybrid_chunk(text: str, max_tokens: int = 1000) -> list:
    """按 Markdown 结构 + 大小限制分块"""
    sections = re.split(r'\n(?=#{1,3}\s)', text)
    chunks = []
    for section in sections:
        tokens_est = len(section) // 4
        if tokens_est <= max_tokens:
            chunks.append(section.strip())
        else:
            # 按段落细分
            paragraphs = section.split("\n\n")
            current = []
            current_tokens = 0
            for para in paragraphs:
                para_tokens = len(para) // 4
                if current_tokens + para_tokens > max_tokens and current:
                    chunks.append("\n\n".join(current).strip())
                    current = [para]
                    current_tokens = para_tokens
                else:
                    current.append(para)
                    current_tokens += para_tokens
            if current:
                chunks.append("\n\n".join(current).strip())
    return [c for c in chunks if c]
```

## 5. 反理性化表（Anti-Rationalization）

Agent 可能试图跳过步骤的常见借口及反驳：

| 借口 | 反驳 |
|------|------|
| "文件太多了，直接用 RAG 吧" | 先画像再决策。小于 200K tokens 的知识库用 Wiki 法比 RAG 召回率高 100% |
| "这个知识库结构很清晰，不需要分析" | 除非你跑了 analyze_kb.py，否则"看起来清晰"是主观判断 |
| "直接全量塞进去就行" | 必须先确认 token 数。超过 200K 会导致注意力稀释和成本浪费 |
| "代码库不需要 Wiki 化" | 每次 agent session 都从零开始读代码是巨大浪费。CodeWiki 方案已验证有效 |
| "Schema(CLAUDE.md) 不重要" | Schema 是 Wiki 法的灵魂。没有 Schema，LLM 只是聊天机器人，不是知识维护者 |
| "Phase 0 意图确认太慢" | 错误的策略选择比多问 3 个问题浪费更多时间 |

## 6. 出错信号（Red Flags）

- 推荐策略后用户困惑 → 可能 Phase 0 意图确认不充分
- 分析报告显示 0 个文件 → 路径错误或权限问题
- 有效结构化率 >80% 但用户说"文档很乱" → md_ratio 和 structured_ratio 计算可能有误
- 策略 CODE 但知识库是文档 → is_code_repo 检测异常
- 策略推荐 A/B 但知识库实际很大 → token 估算可能不准确（encode vs chars/4）
- 编译后的 Wiki 没有交叉链接 → 编译过程缺少互联步骤

## 7. 验证要求（Verification）

每次执行完成后，必须确认以下证据：

- [ ] analyze_kb.py 成功运行并输出 JSON 报告
- [ ] 推荐策略与知识库特征逻辑一致（size_tier ↔ strategy 对应正确）
- [ ] 如果推荐 Wiki 法 → 具体工具建议已给出（llm-wiki-compiler / llm-knowledge-bases / CodeWiki）
- [ ] 如果生成了 Wiki → 存在 Schema 文件（CLAUDE.md 或等效文件）
- [ ] 如果执行了编译 → lint 检查通过（无断开链接、无孤立页面）
- [ ] 用户确认推荐方案合理

## 8. 参考资料

- 方案详解与原始调研 → `大规模知识库检索方案调研.md`（同工作区）
- 代码类知识库分层策略 → `Claude-Code源码上下文策略实验报告.md`（同工作区）
- Agent Skills + LLM Wiki 生态 → `Agent-Skills与LLM-Wiki生态调研报告.md`（同工作区）
- Karpathy Wiki 法 → YC AI Startup School 2025 演讲
- LLM Wiki 三层架构 → Raw Sources + Wiki + Schema (CLAUDE.md)
- Anthropic Contextual Retrieval → anthropic.com/news/contextual-retrieval
- RAPTOR → arXiv:2401.18059
- GraphRAG → github.com/microsoft/graphrag
- Self-Route → arXiv:2407.16833 (EMNLP 2024)
- llms.txt 规范 → llmstxt.org
- 工具：Repomix → github.com/yamadashy/repomix
- 工具：llm-wiki-compiler → github.com/nicobailon/llm-wiki-compiler
- 工具：llm-knowledge-bases → github.com/rvk7895/llm-knowledge-bases
- 工具：CodeWiki → github.com/morgangallant/codewiki
- 工具：agent-skills → github.com/addyosmani/agent-skills
- 工具：browser-use → github.com/browser-use/browser-use
