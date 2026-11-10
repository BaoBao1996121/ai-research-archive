"""
Iter 3 进阶: RAG 向量检索 — 让 Agent 基于知识库回答（~250 行核心代码）
======================================================================
基础版差距：上下文只有简单 KV 记忆，无法从大量文档中精准检索相关信息。
进阶补全：RAG (Retrieval-Augmented Generation) 管线——
         文档分块 → 向量化 → 检索 → 注入上下文 → 生成回答。

Claude Code 对照：
  - context.ts: 从代码仓库中检索相关文件/函数注入 prompt
  - 使用 repo-map + 依赖图 + 向量检索多路召回
  - 核心洞察：不是把所有文档塞进 prompt，而是只放最相关的片段

本文件实现两种检索方案：
  方案 A：TF-IDF 关键词检索（零依赖，教学用）
  方案 B：向量嵌入检索（DashScope Embedding API）

依赖：pip install openai numpy（numpy 仅方案B需要）
运行：python iter3_adv_rag_context.py
"""

import json
import math
import re
from collections import Counter
from config import client, MODEL


# ╔══════════════════════════════════════════════════════════════╗
# ║  Step 1: 文档分块（Chunking）                                ║
# ╚══════════════════════════════════════════════════════════════╝

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[dict]:
    """
    将长文本切分为重叠的小块。

    为什么要分块？
    - LLM 上下文窗口有限，不能塞整篇文档
    - 小块的向量表示更精准（大段文本的 embedding 会被"稀释"）
    - 重叠确保切分边界不丢失信息

    生产级方案会考虑：按段落/标题/代码块等语义边界切分。
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append({
            "text": chunk,
            "start": start,
            "end": end,
        })
        start += chunk_size - overlap
    return chunks


# ╔══════════════════════════════════════════════════════════════╗
# ║  方案 A: TF-IDF 关键词检索（零依赖）                          ║
# ╚══════════════════════════════════════════════════════════════╝

def tokenize(text: str) -> list[str]:
    """简单分词：按非字母数字字符切分"""
    return [w.lower() for w in re.findall(r'[\w\u4e00-\u9fff]+', text) if len(w) > 1]


class TFIDFRetriever:
    """
    基于 TF-IDF 的文档检索器（零依赖实现）。

    TF-IDF = 词频 × 逆文档频率
    - 一个词在当前文档中出现频率高 → TF 高
    - 一个词在所有文档中都出现 → IDF 低（不是好的区分特征）
    - TF × IDF = 对当前文档有区分度的关键词得分

    局限：只看关键词匹配，不理解语义（"汽车"和"轿车"是两个无关的词）
    优势：速度极快、零依赖、对精确匹配效果好
    """
    def __init__(self):
        self.documents: list[dict] = []  # [{text, tokens, tf, metadata}]
        self.idf: dict[str, float] = {}

    def add_documents(self, texts: list[str], metadatas: list[dict] = None):
        """索引文档"""
        metadatas = metadatas or [{}] * len(texts)
        for text, meta in zip(texts, metadatas):
            tokens = tokenize(text)
            tf = Counter(tokens)
            total = len(tokens) or 1
            tf_normalized = {w: c / total for w, c in tf.items()}
            self.documents.append({
                "text": text, "tokens": tokens,
                "tf": tf_normalized, "metadata": meta,
            })

        # 重算 IDF
        n = len(self.documents)
        all_words = set(w for doc in self.documents for w in doc["tokens"])
        for word in all_words:
            df = sum(1 for doc in self.documents if word in doc["tf"])
            self.idf[word] = math.log(n / (df + 1)) + 1

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """检索与 query 最相关的文档"""
        q_tokens = tokenize(query)
        scores = []
        for i, doc in enumerate(self.documents):
            score = sum(doc["tf"].get(w, 0) * self.idf.get(w, 0) for w in q_tokens)
            scores.append((score, i))
        scores.sort(reverse=True)
        return [
            {"text": self.documents[i]["text"], "score": round(s, 4),
             "metadata": self.documents[i]["metadata"]}
            for s, i in scores[:top_k] if s > 0
        ]


# ╔══════════════════════════════════════════════════════════════╗
# ║  方案 B: 向量嵌入检索（DashScope Embedding API）              ║
# ╚══════════════════════════════════════════════════════════════╝

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class EmbeddingRetriever:
    """
    基于向量嵌入的语义检索器。

    流程：文本 → Embedding API → 向量 → 余弦相似度 → 排序

    优势：理解语义（"汽车"≈"轿车"，"快乐"≈"开心"）
    局限：需要 API 调用（有成本）、需要 numpy

    DashScope 的 text-embedding-v3 模型通过 OpenAI 兼容接口调用。
    """
    def __init__(self, model: str = "text-embedding-v3"):
        if not HAS_NUMPY:
            raise RuntimeError("需要 numpy: pip install numpy")
        self.model = model
        self.documents: list[dict] = []
        self.embeddings: list = []

    def _embed(self, texts: list[str]) -> list:
        """调用 Embedding API"""
        resp = client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in resp.data]

    def add_documents(self, texts: list[str], metadatas: list[dict] = None):
        metadatas = metadatas or [{}] * len(texts)
        vectors = self._embed(texts)
        for text, vec, meta in zip(texts, vectors, metadatas):
            self.documents.append({"text": text, "metadata": meta})
            self.embeddings.append(np.array(vec))

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        q_vec = np.array(self._embed([query])[0])
        scores = []
        for i, doc_vec in enumerate(self.embeddings):
            # 余弦相似度
            sim = np.dot(q_vec, doc_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(doc_vec) + 1e-8)
            scores.append((float(sim), i))
        scores.sort(reverse=True)
        return [
            {"text": self.documents[i]["text"], "score": round(s, 4),
             "metadata": self.documents[i]["metadata"]}
            for s, i in scores[:top_k]
        ]


# ╔══════════════════════════════════════════════════════════════╗
# ║  RAG Agent：检索 → 注入上下文 → 生成回答                     ║
# ╚══════════════════════════════════════════════════════════════╝

class RAGAgent:
    """
    RAG (Retrieval-Augmented Generation) Agent。

    工作流程：
    1. 用户提问
    2. 从知识库中检索最相关的文档片段
    3. 将检索结果注入 system prompt 作为上下文
    4. LLM 基于上下文生成回答

    Claude Code 的做法更复杂——多路召回（代码检索 + 文件名匹配 + 依赖图）
    然后排序合并，但核心思路一样：把最相关的信息塞进有限的上下文窗口。
    """
    def __init__(self, retriever, top_k: int = 3):
        self.retriever = retriever
        self.top_k = top_k

    def answer(self, question: str) -> str:
        # Step 1: 检索
        results = self.retriever.search(question, top_k=self.top_k)
        print(f"  🔍 检索到 {len(results)} 个相关片段:")
        for i, r in enumerate(results):
            print(f"     {i+1}. [score={r['score']}] {r['text'][:60]}...")

        if not results:
            context = "（未找到相关信息）"
        else:
            context = "\n\n---\n\n".join(
                f"[来源 {i+1}] {r['text']}" for i, r in enumerate(results)
            )

        # Step 2: 注入上下文，生成回答
        system_prompt = f"""你是一个知识库问答助手。基于以下检索到的参考资料回答用户问题。

## 参考资料
{context}

## 回答规则
- 优先使用参考资料中的信息
- 如果参考资料不足以回答，明确说明
- 标注你的回答基于哪个来源"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content


# ━━━ 示例知识库 ━━━
KNOWLEDGE_BASE = [
    "ReAct 模式是 Agent 的核心循环：推理(Reasoning) → 行动(Acting) → 观察(Observation)。"
    "LLM 先思考下一步该做什么，然后调用工具执行，最后观察工具返回的结果，循环往复直到任务完成。",

    "MCP (Model Context Protocol) 是 Anthropic 发布的开放协议，用于连接 AI 模型和外部工具。"
    "MCP 基于 JSON-RPC 2.0，支持工具发现(tools/list)和工具调用(tools/call)两个核心操作。",

    "Function Calling 是 OpenAI 提出的工具调用协议。LLM 不直接执行工具，"
    "而是返回一个结构化的调用请求（函数名 + 参数），由 Agent 框架执行后把结果回填给 LLM。",

    "上下文窗口管理是 Agent 工程的核心挑战。Claude Code 使用四级压缩策略：\n"
    "1) snip: 截断过长的工具输出\n2) micro: 用廉价模型做微摘要\n"
    "3) auto: 自动全量压缩\n4) reactive: 在 token 即将耗尽时的紧急压缩",

    "Agent 的安全模型通常采用最小权限原则。Claude Code 使用五层权限评估流水线：\n"
    "Hooks → Deny Rules → Permission Mode → Allow Rules → canUseTool。\n"
    "危险操作（如执行 Shell 命令）需要用户明确确认。",

    "向量检索的核心步骤：1) 将文档切分为小块 2) 用 Embedding 模型将文本转为向量 "
    "3) 用余弦相似度找到与查询最相关的文档块 4) 将检索结果注入 LLM 的上下文。",

    "多 Agent 协作常用的编排模式有：\n"
    "1) Orchestrator-Workers: 一个编排者分配任务给多个 Worker\n"
    "2) Supervisor: 一个监督者评估 Worker 结果，决定是否需要重做\n"
    "3) Pipeline: Agent 按顺序接力处理，每个 Agent 处理一个步骤",

    "Prompt Engineering 的核心原则：\n"
    "1) 角色定义：告诉 LLM 它是谁\n"
    "2) 任务描述：明确要做什么\n"
    "3) 输出格式：规定回答的结构\n"
    "4) 示例（Few-shot）：用例子教 LLM 期望的行为\n"
    "5) 约束条件：明确边界和限制",
]


if __name__ == "__main__":
    print("=" * 60)
    print("Iter 3 进阶: RAG 向量检索")
    print("=" * 60)

    # ━━━ 方案 A: TF-IDF 检索 ━━━
    print("\n📝 方案 A: TF-IDF 关键词检索（零依赖）")
    tfidf = TFIDFRetriever()
    tfidf.add_documents(KNOWLEDGE_BASE)
    print(f"  已索引 {len(KNOWLEDGE_BASE)} 个文档块")

    agent_a = RAGAgent(tfidf, top_k=2)

    q1 = "MCP 协议是什么？"
    print(f"\n❓ 问题: {q1}")
    ans1 = agent_a.answer(q1)
    print(f"\n🤖 回答:\n{ans1}")

    q2 = "Agent 有哪些安全机制？"
    print(f"\n{'='*60}")
    print(f"❓ 问题: {q2}")
    ans2 = agent_a.answer(q2)
    print(f"\n🤖 回答:\n{ans2}")

    # ━━━ 方案 B: 向量嵌入检索 ━━━
    if HAS_NUMPY:
        print(f"\n{'='*60}")
        print("📝 方案 B: 向量嵌入检索（语义理解）")
        try:
            embed_retriever = EmbeddingRetriever()
            embed_retriever.add_documents(KNOWLEDGE_BASE)
            print(f"  已向量化 {len(KNOWLEDGE_BASE)} 个文档块")

            agent_b = RAGAgent(embed_retriever, top_k=2)

            # 语义检索的优势：即使关键词不完全匹配也能找到
            q3 = "怎么让 AI 调用外部工具？"  # 没有直接提到 MCP/Function Calling
            print(f"\n❓ 问题: {q3}")
            ans3 = agent_b.answer(q3)
            print(f"\n🤖 回答:\n{ans3}")
        except Exception as e:
            print(f"  ⚠️ 向量检索失败: {e}")
            print("  （可能 DashScope 不支持 text-embedding-v3，可换用其他模型）")
    else:
        print("\n⚠️ 方案 B 需要 numpy: pip install numpy")

    # ━━━ 对比总结 ━━━
    print(f"\n{'='*60}")
    print("📚 两种检索方案对比:")
    print("  TF-IDF   — 零依赖，速度快，只匹配关键词（搜'汽车'找不到'轿车'）")
    print("  向量嵌入  — 理解语义，效果好，需要 API 调用（有成本）")
    print("  生产方案  — 两者结合（混合检索 Hybrid Search），取长补短")
    print()
    print("  Claude Code 的上下文策略:")
    print("  - repo-map（文件结构）+ 依赖图 + 向量检索 = 多路召回")
    print("  - 然后按相关性排序，塞满上下文窗口的预算")
