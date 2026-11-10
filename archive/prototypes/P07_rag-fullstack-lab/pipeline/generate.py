"""⑧ Generate 环节：把 (question + context) 喂给 LLM 出答案。

提供 3 种 prompt 模板：
- standard: 经典 RAG prompt
- with_citations: 强制让 LLM 在每句话后标 [来源1] [来源2] 引用
- chain_of_note: Self-Note 范式（LLM 先写 notes 再答），降低幻觉
"""
from __future__ import annotations

from .llm import LLMClient

STANDARD_PROMPT = """你是基于资料库的问答助手。请只依据下面提供的「上下文」回答问题。
- 如果上下文中没有足够信息，明确说"根据现有资料无法回答"，不要编造。
- 回答要简洁、有条理，必要时分点。
- 引用具体内容时尽量贴近原文表述。

【上下文】
{context}

【问题】
{question}

【回答】"""


WITH_CITATIONS_PROMPT = """你是严谨的问答助手。请基于「上下文」回答问题，并在每个事实后标注引用来源 [来源N]。

规则：
- 上下文中每段以 "--- 来源: <path> ---" 开头，请用 [来源1] [来源2] ... 的形式引用对应段落
- 上下文之外的内容一律不要写
- 无信息时直接说"根据现有资料无法回答"

【上下文】
{context}

【问题】
{question}

【带引用的回答】"""


CHAIN_OF_NOTE_PROMPT = """你是严谨的问答助手。请按以下两步回答：

【第一步】"研读笔记"：从上下文中摘出与问题最相关的 3-5 条事实，每条一行，前面加"-"。
【第二步】"最终回答"：基于这些笔记综合回答问题。如笔记不足以回答，明确说明。

【上下文】
{context}

【问题】
{question}

【输出】
研读笔记：
- ...

最终回答："""


PROMPTS = {
    "standard": STANDARD_PROMPT,
    "with_citations": WITH_CITATIONS_PROMPT,
    "chain_of_note": CHAIN_OF_NOTE_PROMPT,
}


def generate(question: str, context: str, *, llm: LLMClient, prompt_template: str = "standard", max_tokens: int = 1024) -> str:
    template = PROMPTS.get(prompt_template, STANDARD_PROMPT)
    prompt = template.format(question=question, context=context or "(空)")
    return llm.complete(prompt, max_tokens=max_tokens)
