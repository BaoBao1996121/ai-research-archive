> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：full_text（发布前全文隐私审核）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# L07 · Cross-Encoder Rerank：召回精度 trade-off 的钥匙

> 一句话定位：**召回求"宽"（K=50 不漏），rerank 求"精"（top-5 准）。** Rerank 是 RAG 中性价比最高的一招，是把 60 分系统拉到 80 分的关键。
> 在本项目对应：[pipeline/rerank.py](../pipeline/rerank.py) · `rerank.model`

## 🎯 学完你应该能

- 解释为什么"召回要宽，精排要精"是 RAG 工程的核心范式
- 区分双塔（bi-encoder）和交叉编码（cross-encoder）的本质差异
- 知道 bge-reranker / LLM-as-judge 各自适合什么场景

---

## 1. 双塔的天花板：信息瓶颈

回想一下 dense 检索是怎么做的：

```
query  →  encoder  →  q_vec (768 维)
                                      } cosine 相似度
doc    →  encoder  →  d_vec (768 维)
```

注意一个关键事实：**query 和 doc 是分别被编码的**，相互之间没有任何 token 级别的交互。

这就像两个考生独立答完一份卷子，然后把各自的答案纸折起来比 Hash——**根本看不到对方写的具体内容**。

768 维向量能塞下多少信息？把"Anthropic 的 Skill-Creator 在哪一篇？"压缩进 768 个浮点数，再去和文档向量比——这个压缩**必然损失大量细节**。

这就是双塔的天花板。

---

## 2. Cross-Encoder：让 query 和 doc 真正"见面"

```
[CLS] query 文本 [SEP] doc 文本 [SEP]  →  BERT  →  相关性分数
```

把 query 和 doc 拼在一起，整段进 Transformer。**注意力机制让每个 query token 都和每个 doc token 直接交互**——它能精细判断"用户问的是 A 还是 B 含义？这段文档讨论的是 A 还是 B？"

**bge-reranker-v2-m3** 就是这种 cross-encoder，中英文 SOTA。

代价是什么？**慢**。
- 双塔：query 编码 1 次，doc 编码可以离线预先做 → 检索时只需 1 次 vector search
- Cross-Encoder：每对 (q, doc) 都要现场过一次 BERT → N 个候选就要 N 次推理

> 这就是为什么 RAG 要做"召回-精排"两段式：
> - 第一段（dense / hybrid）：从百万级文档中宽召回 top-50（快）
> - 第二段（cross-encoder）：从 50 个候选中精排出 top-5（慢但只跑 50 次）

---

## 3. 一个让你一秒明白的对比 case

> 问题："Self-RAG 和 Corrective RAG 的核心区别是什么？"

**仅 dense 召回 top-3**：
1. ✅ Self-RAG 论文摘要（确实相关）
2. ❌ 一篇综述里讲 RAG 历史的段落（topic 相关但没正面回答）
3. ❌ Corrective RAG 简介，但只讲了流程图

**dense top-50 + bge-reranker top-3**：
1. ✅ Self-RAG vs CRAG 对比章节（直接回答！）
2. ✅ Self-RAG 自评估机制详解
3. ✅ CRAG 的检索质量判别器

差距在哪里？dense 看的是"这一段在不在讲 RAG"，cross-encoder 看的是"这一段是不是在**回答用户问的对比问题**"——后者是只有 cross-encoder 能做出的判断。

---

## 4. P07 里的两种 rerank

### bge-reranker-v2-m3（推荐默认）

```python
# pipeline/rerank.py
class BGEReranker(Reranker):
    def __init__(self, model_name="BAAI/bge-reranker-v2-m3"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, max_length=512)

    def rerank(self, query, candidates, top_n=5):
        pairs = [[query, c.text] for c, _ in candidates]
        scores = self.model.predict(pairs)
        ...
```

- 模型大小：~600MB（首次下载）
- 推理速度：CPU 上 50 个 pairs 约 5-10 秒；GPU 上 <1 秒
- 中英文都强

### LLM-as-Reranker（慢但万能）

```python
class LLMReranker(Reranker):
    def rerank(self, query, candidates, top_n=5):
        for c, _ in candidates:
            score = self.llm.complete(JUDGE_PROMPT.format(q=query, c=c.text))
            # 让 LLM 输出 0-10 分
```

- **优势**：可解释（能要求 LLM 给出"为什么这段相关"的理由）、零样本适应新领域（不用训练）
- **劣势**：每个候选一次 LLM 调用，50 个候选 = 50 次推理 = 慢且贵
- **适合**：高价值场景（一天调几十次的客服 / 法律检索），或冷启动期没标注数据微调专用 reranker

---

## 5. 在 P07 里立刻验证

```bash
# 不带 rerank
python eval/run_eval.py -c configs/v1_hybrid.yaml

# 加 rerank
python eval/run_eval.py -c configs/v2_rerank.yaml

# 对比 - 这里通常能看到 +10~15% 通过率
python eval/run_eval.py --compare configs/v1_hybrid.yaml configs/v2_rerank.yaml
```

**重点观察**：rerank 救回来的 case 通常是「dense 把『话题相关』排在前，但『正面回答』排在第 5-15 位」的题——cross-encoder 把第 5-15 位提到了 top-3。

---

## 6. 怎么调

| 参数 | 默认 | 说明 |
|---|---|---|
| 召回 K | 20-50 | 太小给 rerank 的候选不够，太大 rerank 时间爆炸 |
| Rerank top_n | 5 | LLM 上下文能装多少而定。GPT-4 可 10，本地 8B 模型建议 3-5 |
| max_length | 512 | bge-reranker 默认。chunk 长就要截断，再长会爆显存 |

**经验公式**：召回 K = rerank top_n × 5~10。比如要 top-5，召回 30 比较合适。

---

## 7. 避坑指南

| 坑 | 现象 | 解法 |
|---|---|---|
| 直接对召回 top-3 做 rerank | 几乎没变化 | rerank 的价值是"把 K=30 中真正相关的拉前"，K=3 太小 |
| 用 base 版 bge-reranker | 中英文混合差 | 用 v2-m3，多语言专门训练 |
| LLM judge 用同一个生成模型 | judge 偏向自己生成的话 | judge 最好用更强或不同家的模型 |
| 没截断超长 chunk | 显存爆 | 设 max_length=512，超出截断 |
| 召回阶段就丢了相关文档 | rerank 救不回来（巧妇难为无米之炊） | 先确保召回 K 内有相关文档（看 hit@K），再上 rerank |

---

## 8. 与生产的距离

| P07（教学） | 生产 |
|---|---|
| sentence-transformers 直接跑 | 部署成独立 reranker 服务（Triton / vLLM rerank API） |
| 同步阻塞调用 | 异步并发 / 批处理 |
| 单一 reranker | Cascade rerank：先轻量 reranker 过滤到 K=10，再大 reranker 精排 top-3 |
| 通用 model | 业务数据微调专用 reranker（DPR / LCE 范式） |

---

## 9. 进一步阅读

- [bge-reranker GitHub](https://github.com/FlagOpen/FlagEmbedding/tree/master/research/reranker)
- [Cohere Rerank API](https://cohere.com/rerank) — 商业方案对照
- [LCE: Listwise Cross-Encoder](https://arxiv.org/abs/2401.16164)


> 本次归档补注：文中的效果数字、排名和生产经验属于原稿陈述；本次未重跑 RAG 实验，未将预期指标确认为实际测量结果。
