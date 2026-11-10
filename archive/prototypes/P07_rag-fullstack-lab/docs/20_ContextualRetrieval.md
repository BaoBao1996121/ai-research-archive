> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：full_text（发布前全文隐私审核）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# L16 · Anthropic Contextual Retrieval（SOTA 切片范式）

> 一句话定位：在 embedding 之前，**用 LLM 给每个 chunk 加 50–100 字的"出处说明"**，让 chunk 不再脱离上下文。Anthropic 实测把 top-20 召回失败率降低 49%。
> 论文/官博：[Anthropic · Introducing Contextual Retrieval (2024-09)](https://www.anthropic.com/news/contextual-retrieval)

## 🎯 学完你应该能

- 用一个 case 讲清楚为什么"chunk 单独看缺上下文"是 RAG 的根本痛点
- 描述 Contextual Retrieval 的三步骤
- 评估在你的项目中是否值得上 Contextual（成本-收益账）

---

## 1. 痛点 case：chunk 失去语境

```
原始文档（R34 报告，关于 Hermes 项目 2024 Q3 财报）：

## 营收表现
... 第三季度营收 $1.2B，同比增长 3%，环比下滑 8%。
增长主要由企业版订阅驱动...
```

切片后的某个 chunk：
```
chunk_id: R34::md::15
text: "第三季度营收 $1.2B，同比增长 3%，环比下滑 8%。"
```

用户问：「Hermes 项目 Q3 营收同比是什么情况？」

🤬 这个 chunk **明明就是答案**，但向量检索召回不到——因为它的文本里**没有出现"Hermes"和"Q3"**。embedding 不知道这个 chunk 在讲哪家公司哪个季度。

这就是 RAG 中 30-50% 召回失败的根本原因——**chunk 在被切碎的瞬间，丢失了来自父级标题、引言、前后文的语境信息**。

---

## 2. Contextual Retrieval 的解法：三步

### Step 1 · 给每个 chunk 生成上下文说明

用 LLM 看着**完整原文**，为每个 chunk 写 50–100 字的语境注解：

```
原 chunk: "第三季度营收 $1.2B，同比增长 3%，环比下滑 8%。"

上下文说明（LLM 生成）:
"以下内容来自 R34 报告中关于 Hermes 项目 2024 Q3 财报的"营收表现"章节。"

最终用于 embedding 和 BM25 的文本:
"以下内容来自 R34 报告中关于 Hermes 项目 2024 Q3 财报的"营收表现"章节。
第三季度营收 $1.2B，同比增长 3%，环比下滑 8%。"
```

### Step 2 · 用增强后的文本做双索引

- **Contextual Embedding**：dense 向量库
- **Contextual BM25**：稀疏倒排

两者都用「上下文 + 原文」一起算。

### Step 3 · 检索时 RRF 融合

和普通 hybrid 一样，RRF 融合两路结果，再 rerank 取 top-K。

---

## 3. Anthropic 公布的效果数据

| 配置 | top-20 召回失败率 |
|---|---|
| Embedding only | 5.7% |
| Embedding + BM25 (Hybrid) | 3.7% |
| **Contextual Embedding + Contextual BM25 + Rerank** | **1.9%** |

相对 baseline 降低 67%。这是 RAG 领域近两年最显著的"几乎免费午餐"提升之一。

---

## 4. 成本账：值不值得上？

每个 chunk 都要调一次 LLM——这听起来很贵。

**Anthropic 用 Prompt Caching 把成本压到 1/10**：
- 把"完整原文"放在 prompt 前面，对所有 chunk 复用 → 缓存命中
- 只有"当前 chunk"是变量
- Anthropic Claude API 报价：用 Prompt Caching 后约 **$1.02 / 1M tokens 文档**

折算：
- 1000 篇 1000 字文档（共 1M token）→ ~$1
- 100 万篇文档 → ~$1000（一次性，索引时）

**结论**：
- 数据量小（几千篇）：随便上，成本可忽略
- 数据量中（几十万篇）：值得评估——通常一次几百美元的索引成本能换来长期 30%+ 的召回提升
- 数据量大（千万级）：考虑选择性上下文（只对短 chunk 加，长 chunk 跳过）

---

## 5. 在 P07 里实现（待落地任务）

P07 当前版本未实现 Contextual Retrieval，留作进阶练习。实现要点：

```python
# pipeline/ingest.py 新增策略
CONTEXTUAL_PROMPT = """以下是完整文档：
<document>
{full_doc}
</document>

请为下面这个 chunk 生成 50-100 字的上下文说明，
用于让独立阅读这个 chunk 的人理解它在文档中的位置和讨论的对象。
直接输出说明文字，不要任何前言。

<chunk>
{chunk_text}
</chunk>

上下文说明："""

def chunk_contextual(text, source, *, llm, base_strategy="markdown_header", **kwargs):
    base_chunks = chunk_markdown_header(text, source, **kwargs) if base_strategy == "markdown_header" else chunk_fixed(text, source, **kwargs)
    out = []
    for c in base_chunks:
        ctx = llm.complete(CONTEXTUAL_PROMPT.format(full_doc=text[:8000], chunk_text=c.text), max_tokens=200)
        c.text = f"{ctx.strip()}\n\n{c.text}"
        c.metadata["context_added"] = True
        out.append(c)
    return out
```

**配方加 v5_contextual.yaml**：
```yaml
ingest:
  strategy: contextual
  base_strategy: markdown_header
  llm:
    model: qwen3:8b
    base_url: ${OLLAMA_BASE_URL}
    api_key: ${OLLAMA_API_KEY}
```

⚠️ 实现后注意：本地 Ollama 没有 Prompt Caching，所以教学用要用小模型 + 限制语料规模（几十篇 reports/）以控制时间。

---

## 6. 避坑指南

| 坑 | 现象 | 解法 |
|---|---|---|
| 上下文写得太长 | embedding 主体被淹没 | 限制 50-150 字 |
| 上下文用错语种 | 中文文档配英文上下文，BM25 失效 | prompt 明确要求"用与文档相同的语言" |
| 没用 Prompt Caching | 成本爆炸 | 必须把 full_doc 放在 prompt 头部 |
| 对超长文档（10万字+）一次性塞进 prompt | LLM 上下文不够 | 分段处理：每段单独做 contextual，相邻段之间允许重叠 |

---

## 7. 与已有报告的关系

| 报告/资源 | 内容 |
|---|---|
| [R09](../../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md) 大规模知识库检索方案 | § Contextual Retrieval 章节有理论介绍 |
| [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook/tree/main/skills/contextual-embeddings) | 官方完整代码 |

---

## 8. 进一步阅读

- [Anthropic 官博 · Introducing Contextual Retrieval (2024-09)](https://www.anthropic.com/news/contextual-retrieval)
- [Anthropic Cookbook · Contextual Embeddings](https://github.com/anthropics/anthropic-cookbook/tree/main/skills/contextual-embeddings)
- [LlamaIndex 实现](https://docs.llamaindex.ai/en/stable/examples/cookbooks/contextual_retrieval/)


> 本次归档补注：文中的效果数字、排名和生产经验属于原稿陈述；本次未重跑 RAG 实验，未将预期指标确认为实际测量结果。
