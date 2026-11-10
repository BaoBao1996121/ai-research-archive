> 历史研究归档 · 2026-11-10 发布 · 全文已读；公开副本处理了内部引用。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# L09 · HyDE：用"假答案"找"真文档"

> 一句话定位：先让 LLM **凭空写一个像答案的东西**，用假答案的向量去检索——把"问题向量"换成"答案向量"，匹配到文档时更准。
> 在本项目对应：[pipeline/query_transform.py](../pipeline/query_transform.py) · `transform_hyde`

## 🎯 学完你应该能

- 解释为什么"问题向量"和"文档向量"在分布上不匹配
- 知道 HyDE 适合什么场景，什么场景反而会变差
- 在 P07 里用 v3_hyde 配方验证这一切

---

## 1. 一个让你立刻懂的失败场景

> 问题："为什么我们要用 RAG 而不是直接微调？"

dense 检索会把这个问题向量化，然后去文档库找相似向量。但问题向量和文档向量长得很不一样：

```
问题向量编码的：「为什么...而不是...」← 疑问句结构、对比意图
文档向量编码的：「RAG 适合知识快速更新；微调适合改变模型风格」← 陈述句、平铺事实
```

两个向量在嵌入空间里**不在一片云里**。这是 dense 检索的固有问题：**问题分布 ≠ 文档分布**。

HyDE 的解法：先让 LLM 写一个**看起来像答案的伪文档**：

```
HyDE 输出（凭空写的）：
"RAG 和微调适合不同场景。RAG 通过检索外部知识库让 LLM 引用最新资料，
适合知识频繁更新的场景；微调则把知识固化进模型权重，适合改变模型行为风格..."
```

这个伪文档的向量在嵌入空间里**和真实文档的向量是同一类分布**——用它去检索，命中率显著提升。

---

## 2. 它是什么：先生成，再检索

```
原始流程：    Question → embed → search
HyDE 流程：   Question → LLM 生成假答案 → embed(假答案) → search
```

**注意一个反直觉点**：HyDE 生成的"假答案"**事实可能完全是错的**——这没关系。我们要的不是它的事实，是它的**语言形态分布**和真文档对齐。

P07 实现里用的是「假答案 + 原问题」并查：

```python
def transform_hyde(q, *, llm, **_):
    fake_answer = llm.complete(HYDE_PROMPT.format(q=q), max_tokens=300)
    return [fake_answer.strip(), q]   # 两路都查
```

这是对原始 HyDE 的稳健改良：避免假答案离谱时拖累检索。

---

## 3. 适合 / 不适合的场景

### ✅ HyDE 强势的场景

- **长尾概念问题**："什么是 PSEV 的 Verify 阶段？"——LLM 即使不知道 PSEV，也会生成一段像"评估验证流程"样子的伪答案，把检索锚到对的方向
- **跨领域映射**：用户用通俗话问，文档用专业术语写——HyDE 帮你"翻译"
- **问题和答案在词汇上高度不重叠**：典型的"为什么/怎么样"开头

### ❌ HyDE 反而变差的场景

- **简单事实题**："PSEV 谁提出的？"——LLM 会瞎编一个"由 OpenAI 在 2023 年提出"的伪答案，把检索带偏到 OpenAI 相关文档
- **罕见专有名词**："Qwen3.6-A3B 显存占用是多少？"——LLM 没见过这个模型，编造的伪答案可能完全不沾边
- **多义词检索**："python 是什么"——LLM 可能写成动物，文档讲编程语言

> 🔑 这就是为什么 P07 的 v3_hyde 在某些 case 上**通过率反而下降**——HyDE 不是银弹，是双刃剑。

**实战策略**：HyDE 不要在所有问题上无脑用，而要**让 LLM 先判断问题类型**再决定要不要 HyDE（这是 Adaptive RAG 的核心，见 L19）。

---

## 4. 在 P07 里立刻验证

```bash
# 不带 HyDE
python eval/run_eval.py -c configs/v2_rerank.yaml

# 带 HyDE
python eval/run_eval.py -c configs/v3_hyde.yaml

# Diff
python eval/run_eval.py --compare configs/v2_rerank.yaml configs/v3_hyde.yaml
```

**逐 case 看**——这次的 diff 表会很有教育意义：
- 哪几道概念题变好了？（HyDE 救了它们）
- 哪几道事实题变坏了？（HyDE 把假答案带偏了）

---

## 5. Multi-Query：HyDE 的近亲（更稳）

如果嫌 HyDE 太冒险，可以用 **Multi-Query**：让 LLM 把问题改写成 3 个版本，并集召回。

```python
# pipeline/query_transform.py
def transform_multi_query(q, *, llm, n=3, **_):
    out = llm.complete(MULTIQ_PROMPT.format(q=q))
    variants = [...]
    return [q] + variants
```

为什么 Multi-Query 比 HyDE 稳？因为它是**对问题做语义保持的改写**，不是凭空生成内容——错的概率更小。

P07 的 v4_full 默认用 Multi-Query 而非 HyDE，正是因为它更稳健。

---

## 6. 避坑指南

| 坑 | 现象 | 解法 |
|---|---|---|
| 用最强模型生成假答案 | 慢且贵，假答案太"工整"可能反而不像真文档 | 用中等模型（qwen3:8b）足够 |
| 假答案 temperature=0 | 太呆板，多样性差 | temperature=0.7 让它放飞一点 |
| 只用假答案不带原问题 | 假答案离谱时检索全偏 | 一定要 [假答案, 原问题] 两路并查 |
| 在所有问题上无脑用 HyDE | 整体分数可能不升反降 | 用 Adaptive 思路：先分类问题再决定 |

---

## 7. 与生产的距离

生产 RAG 系统通常这样用 query transform：
- **路由层**：先让小模型判断问题类型（事实/概念/多步推理）
- 事实题 → 不改写或仅 Multi-Query
- 概念题 → HyDE 或 Step-back
- 多步题 → Decomposition（拆子问题）
- **缓存**：同一问题的改写结果缓存（Multi-Query 输出稳定，缓存命中率高）

---

## 8. 进一步阅读

- [Gao et al. 2022 · Precise Zero-Shot Dense Retrieval without Relevance Labels (HyDE)](https://arxiv.org/abs/2212.10496)
- LangChain 文档：[MultiQueryRetriever](https://python.langchain.com/docs/how_to/MultiQueryRetriever/)
- 工作区：[R09](../../../reports/02-%E7%9F%A5%E8%AF%86%E7%AE%A1%E7%90%86%E4%B8%8E%E4%B8%8A%E4%B8%8B%E6%96%87/R09_%E5%A4%A7%E8%A7%84%E6%A8%A1%E7%9F%A5%E8%AF%86%E5%BA%93%E6%A3%80%E7%B4%A2%E6%96%B9%E6%A1%88.md) § Query Transformation


> 本次归档补注：文中的效果数字、排名和生产经验属于原稿陈述；本次未重跑 RAG 实验，未将预期指标确认为实际测量结果。
