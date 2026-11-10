"""④ QueryTransform 环节：在检索前改写问题。

可选：
- none: 直接用原问题
- hyde: HyDE - 让 LLM 先生成"假答案"，用假答案的向量去检索
- multi_query: 把问题改写成 N 个不同表述，并集召回
- step_back: 先抽象到上位问题（"PSEV 是什么" → "本工作区有哪些方法论框架"）
- decomposition: 分解成子问题（适合复合问题）

返回的是 list[str]——一个或多个查询字符串。后续检索环节对每个字符串都跑一次再合并。
"""
from __future__ import annotations

from .llm import LLMClient


def transform_none(q: str, **_) -> list[str]:
    return [q]


HYDE_PROMPT = """请用一段 100-200 字的回答，假设这个问题是关于一份技术文档的。
直接给出答案的样子，不要说"我不知道"或"作为 AI"。即使你不确定具体答案，也写一段看起来像真实答案的文字。

问题：{q}

假设答案："""


def transform_hyde(q: str, *, llm: LLMClient, **_) -> list[str]:
    fake_answer = llm.complete(HYDE_PROMPT.format(q=q), max_tokens=300)
    # 用「假答案 + 原问题」一起检索效果通常更稳
    return [fake_answer.strip(), q]


MULTIQ_PROMPT = """你是检索专家。请把下面的问题改写成 3 个语义相同、但措辞和侧重点不同的版本，每行一个，不要编号、不要解释。

原问题：{q}

3 个改写："""


def transform_multi_query(q: str, *, llm: LLMClient, n: int = 3, **_) -> list[str]:
    out = llm.complete(MULTIQ_PROMPT.format(q=q), max_tokens=300)
    variants = [line.strip("- 1234567890. ").strip() for line in out.splitlines() if line.strip()]
    variants = [v for v in variants if len(v) > 3][:n]
    return [q] + variants  # 原问题 + 改写 N 个


STEPBACK_PROMPT = """请把下面的具体问题"抽象一级"，变成一个更一般、更上位的问题。
只输出一行抽象后的问题。

具体问题：{q}

更抽象的问题："""


def transform_step_back(q: str, *, llm: LLMClient, **_) -> list[str]:
    abstract = llm.complete(STEPBACK_PROMPT.format(q=q), max_tokens=100).strip()
    return [q, abstract]


DECOMP_PROMPT = """如果下面的问题是复合的，请拆成 2-3 个独立子问题，每行一个。
如果问题已经是单一的，只输出原问题。不要编号、不要解释。

问题：{q}

子问题："""


def transform_decompose(q: str, *, llm: LLMClient, **_) -> list[str]:
    out = llm.complete(DECOMP_PROMPT.format(q=q), max_tokens=200)
    subs = [line.strip("- 1234567890. ").strip() for line in out.splitlines() if line.strip()]
    subs = [s for s in subs if len(s) > 3]
    return subs or [q]


TRANSFORMS = {
    "none": transform_none,
    "hyde": transform_hyde,
    "multi_query": transform_multi_query,
    "step_back": transform_step_back,
    "decompose": transform_decompose,
}


def transform_query(q: str, mode: str = "none", *, llm: LLMClient | None = None, **kwargs) -> list[str]:
    fn = TRANSFORMS.get(mode)
    if not fn:
        raise ValueError(f"未知 query transform={mode}")
    return fn(q, llm=llm, **kwargs)
