> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：full_text（发布前全文隐私审核）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P07 · RAG 全链路实验台 — 学习导航中心

> 一个项目摸完主流 RAG 技术栈：从基础切片/嵌入/检索/生成，到进阶 HyDE/Multi-Query/Rerank/Parent-Doc/Contextual Retrieval，再到前沿 Self-RAG/CRAG/Adaptive RAG。
> 每个技术点都配三件套：**📄 原理文档 → 💻 可运行代码 → 📊 量化效果对比**。

---

## TL;DR

```bash
# 1. 装依赖（首次约 5 分钟）
cd prototypes/P07_rag-fullstack-lab
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

# 2. 启 Ollama（确认有可用模型）
ollama list   # 没有就：ollama pull qwen3:8b

# 3. 单题问答（首次会下载 bge-m3 ~2GB + 建索引 ~3min）
python run.py -c configs/baseline.yaml -q "PSEV 框架是什么？"

# 4. 跑全量 eval 拿 baseline 分数
python eval/run_eval.py -c configs/baseline.yaml

# 5. 对比两个配方（最关键的学习动作）
python eval/run_eval.py --compare configs/baseline.yaml configs/v4_full.yaml
```

**首次跑通预期**：baseline 通过率 50–60%，v4_full 通过率 80%+。差距来自每一个环节的优化叠加——这就是这个项目要让你亲手看见的东西。

---

## 项目定位

| 维度 | 说明 |
|---|---|
| 学习深度 | 从"我知道 RAG 是什么"→"我会调每个环节"→"我能讲清楚 trade-off" |
| 与生产的距离 | 教学型，但每个技术都有生产对应物（标注在每篇 lesson） |
| 语料 | **本工作区 `reports/` + `tutorial/`**（你最熟悉、能秒判对错） |
| 评测 | EDD 范式：硬断言 + 关键词召回 + LLM-as-judge + 跨配方 diff |
| 模型 | 默认本地 Ollama（qwen3:8b/qwen3.6:35b-a3b），可换任何 OpenAI 兼容端点 |

---

## 全链路架构（你将完全掌握的 8 个环节）

```
                  ┌─────────────────────────────────────────────────────────┐
索引时（一次性） │  Corpus → ① Ingest 切片 → ② Embed 编码 → ③ Index 索引  │
                  └─────────────────────────────────────────────────────────┘

                  ┌─────────────────────────────────────────────────────────┐
查询时（每次）   │  Question → ④ QueryTransform 改写 → ⑤ Retrieve 召回    │
                  │           → ⑥ Rerank 重排 → ⑦ Compress 压缩            │
                  │           → ⑧ Generate 生成 → Answer                    │
                  └─────────────────────────────────────────────────────────┘
```

每一环都可独立替换、独立度量。这是这个项目的核心炫技。

---

## 📚 学习路径（先读文档，再跑代码）

> 推荐顺序：先把 [docs/00_RAG导论.md](docs/00_RAG%E5%AF%BC%E8%AE%BA.md) 读完建立心智模型，再按下表逐个 lesson 推进。每个 lesson 都是 **「为什么需要 → 是什么 → 怎么做 → 这样改之后效果如何」**。

### 🥚 Stage 1 · 基础——跑通最简 RAG（半天）

| Lesson | 主题 | 文档 | 对应配方 | 关键问题 |
|---|---|---|---|---|
| L00 | RAG 导论：为什么需要 RAG | [docs/00_RAG导论.md](docs/00_RAG%E5%AF%BC%E8%AE%BA.md) | — | 什么时候用 RAG，什么时候用微调 |
| L01 | 文档切片（Chunking） | [docs/01_切片策略.md](docs/01_%E5%88%87%E7%89%87%E7%AD%96%E7%95%A5.md) | baseline | fixed vs semantic vs structural 怎么选 |
| L02 | 向量嵌入（Embedding） | docs/02_嵌入模型.md（原稿引用文件未随本次归档发布） | baseline | bge-m3 vs Qwen3-Embedding 怎么测 |
| L03 | 向量索引（Vector Index） | docs/03_索引存储.md（原稿引用文件未随本次归档发布） | baseline | Chroma/FAISS/Milvus 怎么选 |
| L04 | 朴素检索（Dense Retrieval） | docs/04_朴素检索.md（原稿引用文件未随本次归档发布） | baseline | 双塔的天花板在哪里 |

✅ Stage 1 完成标志：能讲清楚 baseline.yaml 里每一行配置在做什么，并跑出第一份 eval 分数。

### 🐣 Stage 2 · 进阶——召回与精度的博弈（1-2 天）

| Lesson | 主题 | 文档 | 对应配方 | 关键问题 |
|---|---|---|---|---|
| L05 | BM25 与稀疏检索 | docs/05_BM25与稀疏.md（原稿引用文件未随本次归档发布） | v1_hybrid | 为什么 dense 永远干不掉 BM25 |
| L06 | Hybrid 检索 + RRF 融合 | [docs/06_Hybrid与RRF.md](docs/06_Hybrid%E4%B8%8ERRF.md) | v1_hybrid | 为什么是 RRF 不是加权和 |
| L07 | Cross-Encoder Rerank | [docs/07_Rerank.md](docs/07_Rerank.md) | v2_rerank | 召回-精度 trade-off 的钥匙 |
| L08 | LLM-as-Reranker | [docs/07_Rerank.md](docs/07_Rerank.md) | （切 rerank.model: llm_judge） | 慢但可解释的 reranker |

✅ Stage 2 完成标志：v2_rerank vs baseline 跑出 ≥10% 通过率提升，并能解释收益主要来自哪里。

### 🐤 Stage 3 · 进阶——查询侧的智慧（1-2 天）

| Lesson | 主题 | 文档 | 对应配方 | 关键问题 |
|---|---|---|---|---|
| L09 | HyDE：用假答案找真文档 | [docs/08_HyDE.md](docs/08_HyDE.md) | v3_hyde | 为什么有时反而变差 |
| L10 | Multi-Query：一题三问 | docs/09_MultiQuery.md（原稿引用文件未随本次归档发布） | v4_full | 比 HyDE 更稳的查询扩展 |
| L11 | Step-Back Prompting | docs/10_StepBack.md（原稿引用文件未随本次归档发布） | （切 query.transform: step_back） | DeepMind 范式：先抽象再具体 |
| L12 | Query Decomposition | docs/11_Decompose.md（原稿引用文件未随本次归档发布） | （切 query.transform: decompose） | 复合问题怎么拆 |

✅ Stage 3 完成标志：理解每种 query transform 的适用边界，能根据问题类型选对策略。

### 🐤 Stage 4 · 进阶——上下文工程（1 天）

| Lesson | 主题 | 文档 | 对应配方 | 关键问题 |
|---|---|---|---|---|
| L13 | Parent-Document Retrieval | docs/12_ParentDoc.md（原稿引用文件未随本次归档发布） | v4_full | 召回小，喂大 |
| L14 | Sentence-Window / Auto-Merging | docs/13_AutoMerge.md（原稿引用文件未随本次归档发布） | — | LlamaIndex 范式 |
| L15 | LLM 摘要压缩 | docs/14_Compression.md（原稿引用文件未随本次归档发布） | （切 compress.mode: llm_summary） | 何时值得多一轮 LLM |

### 🦅 Stage 5 · 前沿——SOTA 范式（持续追踪）

| Lesson | 主题 | 文档 | 状态 |
|---|---|---|---|
| L16 | Anthropic Contextual Retrieval | [docs/20_ContextualRetrieval.md](docs/20_ContextualRetrieval.md) | 📋 重点待写 |
| L17 | Self-RAG（自我评估再检索） | docs/21_SelfRAG.md | 📋 待写 |
| L18 | Corrective RAG (CRAG) | docs/22_CRAG.md | 📋 待写 |
| L19 | Adaptive RAG / Routing | docs/23_AdaptiveRAG.md | 📋 待写 |
| L20 | GraphRAG / HippoRAG | docs/24_GraphRAG.md | 📋 待写（关联 D27（原稿交叉引用，本归档未解析）） |
| L21 | ColBERT / Late Interaction | docs/25_ColBERT.md | 📋 待写 |

### 🎯 Stage 6 · 评估与上线

| Lesson | 主题 | 文档 |
|---|---|---|
| L22 | 评估体系：Hit@K / MRR / Faithfulness | [docs/30_评估体系.md](docs/30_%E8%AF%84%E4%BC%B0%E4%BD%93%E7%B3%BB.md) |
| L23 | RAGAS 框架对照 | docs/31_RAGAS.md |
| L24 | 上线 checklist：监控 / 漂移 / 增量索引 | docs/40_上线清单.md |

---

## 配方速查（configs/）

| 文件 | 改了什么 | 期望提升 |
|---|---|---|
| `baseline.yaml` | fixed chunk + bge-m3 + dense | 起点 |
| `v1_hybrid.yaml` | + markdown 切片 + BM25 + RRF | +5~10% pass_rate |
| `v2_rerank.yaml` | + bge-reranker-v2-m3 精排 | +10~15% pass_rate |
| `v3_hyde.yaml` | + HyDE 改写 + with_citations prompt | +5%（也可能 -5%） |
| `v4_full.yaml` | + Multi-Query + parent_doc + chain_of_note | 综合最优 |

**自由组合**：复制任一 yaml，改其中**任意一行**的策略，再跑 eval —— 这就是这个项目的本意。

---

## 项目结构

```
P07_rag-fullstack-lab/
├── README.md                ← 你在这里
├── docs/                    ← 📚 教学文档（先读这里）
│   ├── 00_RAG导论.md
│   ├── 01_切片策略.md
│   ├── 06_Hybrid与RRF.md
│   ├── 07_Rerank.md
│   └── ...
├── pipeline/                ← 💻 8 环节可插拔实现
│   ├── ingest.py            ① 切片
│   ├── embed.py             ② 嵌入
│   ├── index.py             ③ 索引（Chroma/Numpy/BM25）
│   ├── query_transform.py   ④ HyDE/Multi-Query/Step-back/Decompose
│   ├── retrieve.py          ⑤ dense/bm25/hybrid_rrf
│   ├── rerank.py            ⑥ bge-reranker / LLM-as-judge
│   ├── compress.py          ⑦ topk / parent_doc / llm_summary
│   ├── generate.py          ⑧ standard / with_citations / chain_of_note
│   ├── llm.py
│   └── factory.py           配置 → 完整 pipeline
├── configs/                 ← 🎚️ 配方文件
│   ├── baseline.yaml
│   ├── v1_hybrid.yaml
│   ├── v2_rerank.yaml
│   ├── v3_hyde.yaml
│   └── v4_full.yaml
├── eval/                    ← 📊 评测
│   ├── eval_set.yaml        12 条种子 case（建议扩到 30+）
│   ├── run_eval.py          评测引擎 + 对比 + Gate
│   └── results/
├── run.py                   ← 单题问答入口
└── requirements.txt
```

---

## 与已有产出的关系

| 已有 | 与本项目的关系 |
|---|---|
| D27（原稿交叉引用，本归档未解析） E08 GraphRAG 实验脚本 | GraphRAG 是 RAG 的图谱形态；本项目是 vanilla RAG 全链路对比，可作为 GraphRAG 的基线 |
| D46（原稿交叉引用，本归档未解析） P03 Redis Lab 04_vector_rag | P03 04 章只是最简 RAG 演示；本项目把每个环节都打开做实验 |
| [R09](../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md) 大规模知识库检索方案 | R09 是理论调研；本项目是把理论跑出来的实验台 |
| skill-evaluator（原稿交叉引用，本归档未解析） | 评测引擎复用其设计哲学（断言 + judge + compare） |
| KNOWLEDGE_INDEX（原稿交叉引用，本归档未解析） §四 Tools | 学完本项目后可作为知识库的实际查询入口替代手动翻索引 |

---

## 推荐阅读顺序（如果你只有 1 小时）

1. [docs/00_RAG导论.md](docs/00_RAG%E5%AF%BC%E8%AE%BA.md) — 10 分钟建立心智模型
2. [docs/01_切片策略.md](docs/01_%E5%88%87%E7%89%87%E7%AD%96%E7%95%A5.md) — 切片决定召回上限
3. [docs/06_Hybrid与RRF.md](docs/06_Hybrid%E4%B8%8ERRF.md) — RAG 中最反直觉但最强的招
4. [docs/07_Rerank.md](docs/07_Rerank.md) — 召回精度的 trade-off 钥匙
5. 跑 `python eval/run_eval.py --compare configs/baseline.yaml configs/v4_full.yaml`
6. 看 diff 表，理解每一条 case 变好/变坏的原因

---

## 文档完成度

写完核心 lesson（00、01、06、07）作为范本，其余 lesson 在你需要时按相同模板续写。模板见 [docs/_TEMPLATE.md](docs/_TEMPLATE.md)。

License：教学项目，本工作区内自由使用。引用本项目方法论请标注 P07（原稿交叉引用，本归档未解析）。


> 本次归档补注：文中的效果数字、排名和生产经验属于原稿陈述；本次未重跑 RAG 实验，未将预期指标确认为实际测量结果。
