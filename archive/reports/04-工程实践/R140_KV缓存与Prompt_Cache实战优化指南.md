> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# KV 缓存与 Prompt Cache 实战优化指南

> **一句话概括**：KV Cache 是推理引擎内部加速解码的机制（对 API 用户透明），Prompt Cache 是 API 层面基于前缀匹配的成本/延迟优化手段（用户可控）。两者的交集是——保持输入前缀稳定，就能同时受益于两层缓存。本文从原理到实操，覆盖 Copilot / 直连 API / 自建 Agent 三种场景的优化策略。
> **研究日期**：2026-05-27
> **关联报告**：[R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 推理优化技术深解（KV Cache 理论）· R109（原稿交叉引用，本归档未解析） Claude Code Prompt Cache 深度拆解（工程实现）· P19（原稿交叉引用，本归档未解析） Prompt Cache 断裂检测
> **目标读者**：正在使用 LLM API 开发应用、想要降本增效的工程师；自建 Agent 的开发者

---

## 目录

- [定位透镜：两层缓存的关系](#定位透镜两层缓存的关系)
- [一、KV Cache 原理速通](#一kv-cache-原理速通)
- [二、Prompt Cache 原理：各平台机制对比](#二prompt-cache-原理各平台机制对比)
- [三、场景一：Copilot 用户如何提高缓存命中](#三场景一copilot-用户如何提高缓存命中)
- [四、场景二：直连 LLM API 的缓存优化](#四场景二直连-llm-api-的缓存优化)
- [五、场景三：自建 Agent 的缓存工程](#五场景三自建-agent-的缓存工程)
- [六、反模式与避坑](#六反模式与避坑)
- [七、成本估算速查](#七成本估算速查)
- [结论与最佳实践](#结论与最佳实践)
- [开放问题](#开放问题)
- [来源清单](#来源清单)

---

## 定位透镜：两层缓存的关系

### 纵轴 · 为什么存在两层缓存

```
┌──────────────────────────────────────────────────────┐
│  用户视角                                             │
│                                                      │
│  "我发了同样的 system prompt，为什么还收全价？"         │
│       │                                              │
│       ▼                                              │
│  ┌─ Prompt Cache（API 层）─────────────────────┐      │
│  │  字节级前缀匹配，命中后跳过 prefill 计算     │      │
│  │  直接复用已有 KV → 用户侧省钱+首字更快      │      │
│  └──────────────────────────────────────────────┘      │
│       │                                              │
│       ▼                                              │
│  ┌─ KV Cache（推理引擎层）──────────────────────┐      │
│  │  缓存每层每 head 的 K/V 张量               │      │
│  │  让 decode 从 O(n²) → O(n)                 │      │
│  │  对 API 用户完全透明                        │      │
│  └──────────────────────────────────────────────┘      │
│       │                                              │
│       ▼                                              │
│  GPU HBM / 磁盘                                       │
└──────────────────────────────────────────────────────┘
```

**本质区别**：

| 维度 | KV Cache | Prompt Cache |
|------|----------|--------------|
| 谁管理 | 推理引擎（vLLM/TensorRT-LLM/等） | API 提供商（Anthropic/OpenAI/DeepSeek） |
| 用户能否直接控制 | ❌ 透明的 | ✅ 可通过设计 prompt 结构影响 |
| 缓存什么 | 每层每 head 的 K、V 张量 | "已计算过的 KV"的引用（前缀匹配） |
| 命中条件 | 同一请求内的历史 token | 跨请求的相同前缀 |
| 失效条件 | 请求结束/被驱逐 | TTL 过期/前缀变化 |
| 对用户的好处 | 每步生成不重算历史（加速） | 重复前缀不重新计费（省钱+降延迟） |

**交叉判断**：作为应用开发者，你唯一能主动优化的是 **Prompt Cache 层**——通过保持输入前缀稳定来提高命中率。KV Cache 的优化是引擎的事（选好引擎就行，见 [R58](R58_LLM%E6%8E%A8%E7%90%86%E9%83%A8%E7%BD%B2%E5%B7%A5%E7%A8%8B%E6%8C%87%E5%8D%97_%E9%87%8F%E5%8C%96%E4%B8%8E%E6%8E%A8%E7%90%86%E5%BC%95%E6%93%8E.md)）。但理解 KV Cache 原理有助于理解**为什么前缀稳定能省钱**——因为 Prompt Cache 本质上是"跨请求复用已经算好的 KV 张量"。

### 横轴 · 各平台 Prompt Cache 对比

| 特性 | Anthropic | OpenAI | DeepSeek | Google Gemini | 自建 vLLM/SGLang |
|------|-----------|--------|----------|---------------|-----------------|
| 控制方式 | 显式 `cache_control` | 全自动 | 全自动（磁盘） | 显式 CachedContent | 启动参数开关 |
| 最小缓存长度 | 1024 tokens | 1024 tokens | 无硬性限制 | 32K tokens | 1 block（16 tokens） |
| 匹配粒度 | 字节级前缀 | 128-token 增量前缀 | 前缀单元 | 整个缓存对象 | Block 级（RadixTree） |
| TTL | 5min / 1h | 5-10min | 数小时-数天 | 用户控制 | 请求期间/LRU 驱逐 |
| 命中折扣 | **90%**（0.1x） | **50%**（0.5x） | **~90%**（接近0） | 按存储时间计费 | 免费（自建） |
| 缓存共享 | org / global | 同组织 | 同用户 | 显式管理 | 同引擎实例 |

**生命周期定位**：Prompt Caching 处于**上升期→成熟期过渡**。Anthropic 和 OpenAI 2024 年下半年相继发布，2025-2026 年功能持续迭代（scope 扩展、TTL 延长、cache_edits）。自建部署的 Prefix Caching 已是事实标准（vLLM/SGLang 默认支持）。

---

## 一、KV Cache 原理速通

> 详细原理见 [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) §2。这里给 3 分钟版本。

### 1.1 为什么需要 KV Cache

Transformer 生成第 t 个 token 时，需要与前面所有 token 做 Attention。**但前面 token 的 K 和 V 在每一步都不变**，所以缓存下来：

```python
# 无 KV Cache：每步处理所有历史 token → O(t²) 总计算
for t in range(max_len):
    output = model(all_tokens[:t+1])  # 第 100 步要重算前 99 个

# 有 KV Cache：每步只处理 1 个新 token → O(t) 总计算
kv_cache = []
for t in range(max_len):
    output, new_kv = model_one_step(new_token, kv_cache)
    kv_cache.append(new_kv)  # 追加，不重算
```

**效果**：decode 阶段单步计算从 O(t) → O(1)，总吞吐提升 10 倍起。

### 1.2 KV Cache 大小（为什么它是瓶颈）

以 Qwen2.5-72B 为例：

```
KV 每 token = 2(K+V) × 80(层) × 8(GQA heads) × 128(head_dim) × 2(FP16 bytes)
           = 327 KB/token

4096 序列 × 32 并发 = 41 GB  ← 仅 KV 就吃掉半张 H100
```

这就是为什么推理引擎发明了 PagedAttention（消除碎片）、GQA/MLA（压缩 KV 尺寸）、KV 量化（FP8）等技术。

### 1.3 Prefix Caching = 跨请求复用 KV

当多个请求共享相同的前缀（如 system prompt），它们的 KV 张量完全相同。**不重新计算，直接复用** = Prompt Cache 的本质。

```
请求 A: [System Prompt 5K tokens] [User: Hello]
请求 B: [System Prompt 5K tokens] [User: World]
                    ↑
        这 5K tokens 的 KV 只需算一次
        第二次直接从缓存读 → 跳过 prefill → 省钱 + 快
```

---

## 二、Prompt Cache 原理：各平台机制对比

### 2.1 Anthropic（Claude）

**机制**：显式控制 + 字节级前缀匹配

```json
{
  "system": [
    {"type": "text", "text": "..静态内容..", 
     "cache_control": {"type": "ephemeral", "ttl": "1h", "scope": "global"}},
    {"type": "text", "text": "..动态内容.."}
  ]
}
```

**关键规则**：
- 从第一个字节开始匹配，**任何中间变化打断后续所有缓存**
- 最小缓存长度 1024 tokens
- `scope: 'global'` 可跨组织共享（不含用户数据的静态内容）
- 写入 1.25x，命中 0.1x（命中比未命中**便宜 12.5 倍**）

**最大优势**：精细控制 + 极高折扣。代价是需要手动管理 `cache_control` 标记位置。

### 2.2 OpenAI（GPT-4o / o1 系列）

**机制**：全自动 + 前缀匹配

- ≥ 1024 tokens 的前缀自动缓存，128-token 增量
- 无需改代码，直接生效
- 命中 0.5x（折扣 50%）
- TTL 5-10 分钟（不活跃时自动清除）

**最大优势**：零配置即可受益。代价是折扣力度不如 Anthropic（50% vs 90%），且无法主动控制缓存边界。

**使用 Copilot 时**：Copilot 底层调用 OpenAI 模型，**自动受益于此机制**。Copilot 的 prompt engineering 层已做了"稳定前缀"优化（如 neighboring tabs 排序策略）。

### 2.3 DeepSeek

**机制**：自动磁盘缓存 + 智能前缀检测

独特之处：
1. **请求边界持久化**：每次请求在 user 输入末尾和 model 输出末尾生成缓存单元
2. **公共前缀检测**：系统自动识别多个请求的公共前缀，持久化为独立缓存单元
3. **固定间隔持久化**：超长输入按固定 token 间隔切分缓存

```
请求 1: [A + B]   → 持久化 [A+B] 这个单元
请求 2: [A + C]   → 无法命中 [A+B]（必须完整匹配单元）
                    但系统发现公共前缀 A，持久化 [A] 为新单元
请求 3: [A + D]   → 命中 [A] ✅
```

**最大优势**：免费且自动，缓存命中的 token 直接不计费。代价是"尽力而为"（best-effort），不保证命中率，且首次建立缓存需要 2+ 请求。

### 2.4 自建部署（vLLM / SGLang）

| 引擎 | Prefix Caching 实现 | 使用方式 |
|------|---------------------|---------|
| vLLM | Hash-based block matching | `--enable-prefix-caching` 启动参数 |
| SGLang | **RadixAttention**（Radix Tree） | 默认开启，自动 LRU 驱逐 |

SGLang 的 RadixAttention 是目前最精细的实现——用基数树管理所有已缓存的 KV 前缀，自动合并/分叉/驱逐，无需任何客户端标记。

**自建部署的命中条件**：同一引擎实例内的请求共享相同前缀即可命中，无 TTL 限制（仅受显存 LRU 驱逐影响）。

---

## 三、场景一：Copilot 用户如何提高缓存命中

> Copilot 用户对底层 prompt 结构控制有限，但可以通过使用习惯间接提高缓存效率。

### 3.1 Copilot 的缓存机制（推断）

Copilot 底层使用 OpenAI 模型（GPT-4o / o1），自动受益于 OpenAI 的 Prompt Caching。Copilot 的 prompt 构造逻辑是：

```
[System 指令（固定）] + [项目上下文（neighboring tabs 等）] + [用户当前代码/问题]
```

前两部分若保持稳定，OpenAI 的自动缓存就会命中。

### 3.2 实操优化

| 策略 | 原理 | 操作 |
|------|------|------|
| **保持编辑器 tab 稳定** | neighboring tabs 是上下文来源；频繁开关 tab 改变 prompt 前缀 | 工作时保持相关文件打开，不频繁切换 |
| **instructions.md 内容稳定** | Copilot 会把 instruction 文件内容注入 system prompt | 不要频繁修改 `.github/copilot-instructions.md` |
| **单次对话内保持话题连贯** | 多轮对话的前缀自然累积 | 避免在同一个 Chat 面板里频繁切换无关话题 |
| **善用 `@workspace` 而非碎片化提问** | 一次性提供充分上下文比多次小请求更利于缓存 | 把完整需求一次说清 |
| **使用稳定的模型** | 切换模型 = 换缓存命名空间 | 除非必要，不频繁在 GPT-4o / Claude 间切换 |

### 3.3 诚实的局限

Copilot 的缓存优化主要由**产品团队在后台完成**（prompt 构造、排序策略），普通用户能做的有限。节省效果量级：

- 系统稳定使用：大约能省 10-20% 的 token（估算，基于 OpenAI 50% 折扣 × 缓存前缀占比）
- 用户端的直接感知更多是**延迟降低**（缓存命中时 TTFT 更短）

---

## 四、场景二：直连 LLM API 的缓存优化

> 这是投入产出比最高的场景——你完全控制 prompt 结构。

### 4.1 核心原则：前缀稳定性

所有平台的 Prompt Cache 都基于**前缀匹配**。优化的第一性原理：

```
越靠前的内容越稳定 → 缓存命中率越高
```

具体排列顺序：

```
┌─ 最稳定（几乎不变）─────────────────────────┐
│  ① 系统人设 / 安全规则 / 行为准则            │  ← 全局缓存
│  ② 工具定义 schema                          │  ← 会话级缓存
│  ③ 固定参考文档 / Few-shot examples          │  ← 会话级缓存
├─ 中等稳定（会话内不变）──────────────────────┤
│  ④ 用户上传的长文档 / RAG 检索结果           │  ← 请求级缓存
│  ⑤ 对话历史                                 │  ← 每轮追加
├─ 不稳定（每次请求都不同）────────────────────┤
│  ⑥ 当前用户输入                             │  ← 不缓存
└──────────────────────────────────────────────┘
```

### 4.2 Anthropic API 优化策略

**策略 1：Static/Dynamic 分区**

```python
system_blocks = [
    # 静态区 — 跨所有用户/会话相同 → scope='global'
    {"type": "text", "text": SYSTEM_PERSONA + SAFETY_RULES + BEHAVIOR_GUIDE,
     "cache_control": {"type": "ephemeral", "scope": "global"}},
    
    # 动态区 — 每个会话不同 → 不标记 cache_control
    {"type": "text", "text": f"当前时间: {now}\n用户偏好: {user_prefs}"}
]
```

**策略 2：工具定义排序稳定**

工具 schema 通常紧跟 system prompt，在前缀中。**工具列表的顺序必须固定**：

```python
# ❌ 错误：每次请求随机顺序
tools = random.shuffle(all_tools)

# ✅ 正确：按名称排序，保证字节一致
tools = sorted(all_tools, key=lambda t: t["name"])
```

**策略 3：消息末尾标记**

Claude Code 的做法：只在最后一条消息上标记 `cache_control`（R109（原稿交叉引用，本归档未解析） §三），确保历史对话的 KV 被保留：

```python
messages[-1]["content"][-1]["cache_control"] = {"type": "ephemeral"}
```

**策略 4：避免动态内容污染静态区**

```python
# ❌ 在 system prompt 前部插入动态 feature flag
system = f"Features: {json.dumps(feature_flags)}\n{STATIC_PROMPT}"

# ✅ 动态内容放到 boundary 之后
system_blocks = [
    {"type": "text", "text": STATIC_PROMPT,
     "cache_control": {"type": "ephemeral"}},
    {"type": "text", "text": f"Features: {json.dumps(feature_flags)}"}
]
```

### 4.3 OpenAI API 优化策略

OpenAI 的缓存是全自动的，但你可以通过以下方式提高命中率：

```python
# 核心：保持 system prompt + tools 部分 ≥ 1024 tokens 且跨请求不变
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        # ✅ 稳定的长 system prompt（超过 1024 tokens）
        {"role": "system", "content": LONG_STABLE_SYSTEM_PROMPT},
        # ✅ 对话历史只追加不修改
        *conversation_history,
        # 新消息
        {"role": "user", "content": user_input}
    ],
    # ✅ tools 列表顺序固定
    tools=SORTED_TOOLS,
)

# 检查缓存命中情况
cached = response.usage.prompt_tokens_details.cached_tokens
print(f"缓存命中: {cached}/{response.usage.prompt_tokens} tokens")
```

**关键技巧**：
- System prompt 长度最好 > 1024 tokens（不足则无法触发缓存）
- 如果 system prompt 较短，可以把固定的 few-shot examples 或参考文档放入 system 消息
- 不要在 system prompt 里放时间戳或随机 ID

### 4.4 DeepSeek API 优化策略

DeepSeek 的缓存更智能但不可预测，关键是让系统**有机会发现公共前缀**：

```python
# ✅ 多轮对话自然受益（历史消息保持不变，自动命中请求边界缓存）
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "第一个问题"},
    {"role": "assistant", "content": "第一个回答"},
    {"role": "user", "content": "第二个问题"},  # ← 前缀完全匹配，命中
]

# ✅ 同一文档多次提问（利用公共前缀检测）
# 第 1-2 次可能不命中，但系统会持久化公共前缀
# 第 3 次开始稳定命中
for question in questions_about_same_doc:
    response = call_api(system=SYSTEM, user=f"{DOC_CONTENT}\n\n{question}")
```

**验证命中**：
```python
usage = response.usage
hit = usage.prompt_cache_hit_tokens
miss = usage.prompt_cache_miss_tokens
print(f"命中: {hit}, 未命中: {miss}, 命中率: {hit/(hit+miss):.1%}")
```

---

## 五、场景三：自建 Agent 的缓存工程

> 自建 Agent 是优化空间最大的场景——因为你同时控制 prompt 结构**和**调用模式。

### 5.1 Agent Loop 的缓存特性

典型 Agent 循环：

```
Turn 1: [System] [User Task]                        → 全量 prefill
Turn 2: [System] [User Task] [Asst] [Tool Result]   → 前缀命中 System+Task
Turn 3: [System] [User Task] [Asst] [Tool] [Asst] [Tool]  → 前缀累积
...
Turn N: [System] [...长历史...]                       → 前缀越来越长
```

**天然优势**：Agent 多轮对话的前缀自然增长，每轮新增的只有最后一个 tool_result 和 assistant 回复。如果不做上下文压缩，缓存命中率天然很高。

**天然风险**：一旦做了 context truncation/compaction（截断历史），整个前缀失效。

### 5.2 System Prompt 稳定化策略

从 Claude Code 的实践中提炼（来源：R109（原稿交叉引用，本归档未解析））：

```python
class AgentPromptBuilder:
    """Agent 的 prompt 构造器，保证缓存友好"""
    
    # 编译时确定的内容 — 整个 agent 生命周期不变
    STATIC_SECTIONS = [
        PERSONA,           # 身份定义
        SAFETY_RULES,      # 安全规则
        BEHAVIOR_GUIDE,    # 行为准则
        TOOL_USAGE_GUIDE,  # 工具使用指南
        OUTPUT_FORMAT,     # 输出格式要求
    ]
    
    # 会话级确定的内容 — 单个 session 内不变
    SESSION_SECTIONS = [
        # memory_content,  # CLAUDE.md 等记忆
        # env_info,        # 环境信息
    ]
    
    def build_system(self, session_ctx):
        static = "\n\n".join(self.STATIC_SECTIONS)
        dynamic = self.build_session_context(session_ctx)
        
        # Anthropic API
        return [
            {"type": "text", "text": static,
             "cache_control": {"type": "ephemeral", "scope": "global"}},
            {"type": "text", "text": dynamic}
        ]
```

### 5.3 工具 Schema 稳定化

工具定义位于 system prompt 之后、消息列表之前，是缓存前缀的关键组成部分：

```python
# ❌ 反模式：动态生成工具描述
tools = [
    {"name": "search", 
     "description": f"搜索文档（当前索引 {index_size} 条，更新于 {last_update}）"}
]

# ✅ 正确：工具描述在 session 内固定
tools = [
    {"name": "search",
     "description": "搜索文档库中的相关内容"}
]
# 动态信息放到 system prompt 的动态区
```

### 5.4 子 Agent 共享缓存

当一个 orchestrator 分发多个子任务时：

```python
# Claude Code 的 buildForkedMessages 策略
def build_sub_agent_messages(parent_history, directive):
    """所有子 agent 共享父级的对话前缀"""
    return [
        *parent_history,  # 完全相同的前缀 → 缓存命中
        {"role": "user", "content": [
            # 占位符 tool_result（所有子 agent 相同）
            {"type": "tool_result", "tool_use_id": "xxx", 
             "content": "Output not available."},
            # 只有 directive 不同
            {"type": "text", "text": directive}
        ]}
    ]
```

多个子 agent 只有最后的 directive 不同，**前缀完全共享一份缓存**。

### 5.5 Context Compaction 的缓存感知设计

上下文压缩是 Agent 的刚需（防止超出窗口），但它会打断缓存。**缓存感知压缩**策略：

```python
def compact_with_cache_awareness(messages, max_tokens):
    """
    压缩时保留前缀，只压缩中间消息。
    
    保留结构:
      [System（不动）] [前 N 条关键消息（不动）] [摘要] [最近 K 条（不动）]
    """
    system = messages[0]           # 永远不动
    recent = messages[-K:]         # 最近的保持原样
    middle = messages[1:-K]        # 中间部分压缩为摘要
    
    summary = summarize(middle)
    return [system, summary_message, *recent]
```

**关键**：压缩后的第一次请求会 cache miss（不可避免），但后续请求基于新前缀再次累积缓存。设计压缩策略时要考虑"压缩频率 vs 缓存收益"的平衡。

### 5.6 自建部署的 Prefix Caching 配置

**vLLM**：
```bash
# 启动时开启
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-72B-Instruct \
    --enable-prefix-caching \
    --max-model-len 32768
```

**SGLang**（默认开启 RadixAttention）：
```bash
python -m sglang.launch_server \
    --model Qwen/Qwen2.5-72B-Instruct \
    --port 8000
# RadixAttention 默认启用，无需额外参数
```

**验证命中**：
```python
# vLLM 的 usage 返回中检查
# prompt_tokens vs cached_tokens 比例
```

---

## 六、反模式与避坑

### 6.1 缓存杀手清单

| 反模式 | 为什么致命 | 正确做法 |
|--------|-----------|---------|
| System prompt 开头插时间戳 | 第一个字节就不同，整个前缀失效 | 时间放到动态区末尾 |
| 工具列表每次请求顺序不同 | 工具 schema 在前缀中，顺序变 = 缓存断裂 | `sorted(tools, key=name)` |
| Feature flag 写进 system prompt | flag 翻转时静态区变化 | 运行时条件放动态区 |
| 对话历史删除/修改中间消息 | 打断前缀连续性 | 只追加不修改；压缩时保留前缀 |
| 频繁切换模型 | 不同模型的缓存是隔离的 | session 内锁定模型 |
| 随机 ID / nonce 写入 prompt | 每次请求唯一 → 永远不命中 | 把 trace ID 等放到 metadata 而非 prompt |

### 6.2 Anthropic 特有陷阱

- **cache_control 标记太多**：每多一个标记位 = 多保留一组 KV 页面 = 浪费。最优是**恰好 1-2 个标记**
- **scope='global' 包含了用户数据**：安全违规，且不同用户的数据不同 → 缓存碎片化
- **TTL 5min 但请求间隔 > 5min**：缓存过期。解决：使用 1h TTL（付费用户）或保持请求频率

### 6.3 DeepSeek 特有注意

- 首次使用新前缀**不会**命中缓存（需要 2+ 请求才能建立）
- 公共前缀检测是异步的，**不保证**第二次就能命中
- 缓存基于"尽力而为"，不能作为成本预算的确定性依据

### 6.4 Prefix Caching 命中率 < 30% 时的反噬

来自 [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 的警告：当命中率过低时，缓存管理的元数据开销（hash 计算、LRU 维护、block table 管理）反而让性能更差。

**何时关闭**：
- 每个请求的 prompt 都完全不同（如 one-shot 批量处理不相关任务）
- 并发极低（< 4）且序列极短（< 128 tokens）

---

## 七、成本估算速查

### 7.1 Anthropic（Claude Sonnet 4）

| 场景 | System Prompt | 每轮对话 | 15 轮会话总成本 | 节省 |
|------|--------------|---------|---------------|------|
| 无缓存 | 30K × $3/M = $0.09/轮 | + history avg 20K | $2.48 | — |
| 有缓存(5min) | 首次 $0.11，后续 $0.009/轮 | + history | $1.17 | **53%** |
| 有缓存(1h+global) | 共享命中 $0.009/轮 | + history | $0.97 | **61%** |

### 7.2 OpenAI（GPT-4o）

| 场景 | System Prompt 30K | 15 轮总成本 | 节省 |
|------|------------------|------------|------|
| 无缓存 | 30K × $2.5/M = $0.075/轮 | $1.65 | — |
| 自动缓存命中 | 30K × $1.25/M = $0.0375/轮 | $1.06 | **36%** |

### 7.3 DeepSeek

DeepSeek 缓存命中的 token 按 cache hit 价格计费（约为正常 input 的 10%），效果接近 Anthropic。

### 7.4 自建部署

Prefix Caching 的好处不是省钱（本来就不按 token 计费），而是**提高吞吐**——相同 GPU 可以服务更多请求：

```
无 Prefix Caching: 每请求 5K prefill → GPU 每秒处理 ~20 请求
有 Prefix Caching: 每请求 500 token prefill → GPU 每秒处理 ~100 请求
```

---

## 结论与最佳实践

### 核心规则（按重要性排序）

1. **把不变的内容放前面**：system prompt > tools > 固定文档 > 对话历史 > 用户输入
2. **保持工具定义顺序固定**：`sorted(tools, key=name)`，会话内不增删工具
3. **不在前缀中放动态值**：时间戳、随机 ID、feature flag 都放到动态区/metadata
4. **对话历史只追加不修改**：删除或修改中间消息 = 缓存断裂
5. **压缩时保护前缀**：只压缩中间消息，保留 system + 前 N 条 + 最近 K 条
6. **Anthropic 用户：主动标记 `cache_control`**：利用 90% 折扣，比 OpenAI 的 50% 更值得投入工程
7. **监控缓存命中率**：所有平台都在 usage 中返回 cached_tokens，据此优化

### 场景决策树

```
你在什么场景？
├── 用 Copilot → 保持 tab 稳定 + instructions.md 不频繁改 + 单话题连贯对话
├── 直连 API
│   ├── Anthropic → 全力优化 cache_control（ROI 最高，90% 折扣）
│   ├── OpenAI → 确保 system prompt > 1024 tokens + 顺序固定
│   └── DeepSeek → 多轮对话自然受益 + 同文档多次提问
└── 自建 Agent
    ├── 调用云 API → 上述 API 策略 + sub-agent 前缀共享
    └── 自建推理引擎 → vLLM --enable-prefix-caching / SGLang 默认开启
```

---

## 开放问题

1. **Copilot 的具体缓存效果无法直接测量**：用户无法看到 cached_tokens 数据，只能通过响应速度间接判断
2. **OpenAI 是否未来会支持显式 cache_control**：当前全自动方案折扣力度有限（50%），如果支持显式标记可能给出更高折扣
3. **DeepSeek 的磁盘缓存在冷启动场景的表现**：新用户/新话题的前几次请求必然不命中，是否有预热机制
4. **cache_edits（Anthropic 2026 新特性）**：允许在不破坏缓存的情况下删除旧消息，对 Agent context compaction 有重大影响，值得持续跟踪
5. **Prefix Caching vs Sliding Window Attention**：DeepSeek V3 使用 SWA，其缓存单元是独立完整的，与传统"前缀连续性"假设不同，需要特殊处理

---

## 来源清单

📌 **来源清单**
- [R59](R59_%E6%8E%A8%E7%90%86%E4%BC%98%E5%8C%96%E6%8A%80%E6%9C%AF_KVCache%E4%B8%8EFlashAttention%E4%B8%8E%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81.md) 推理优化技术深解 — 2026-04-24 — KV Cache 内部原理和 PagedAttention/Prefix Cache 理论
- R109（原稿交叉引用，本归档未解析） Claude Code Prompt Cache 深度拆解 — 2026-05-10 — Anthropic 缓存机制和 Claude Code 工程实践
- P19（原稿交叉引用，本归档未解析） Prompt Cache Break Detection — 2026-05-12 — 12 维断裂检测和抑制机制
- [OpenAI Prompt Caching 公告](https://openai.com/index/api-prompt-caching/) — 2024-10-01 — 自动缓存机制和定价
- [DeepSeek Context Caching 文档](https://api-docs.deepseek.com/guides/kv_cache) — 2025 — 磁盘缓存和前缀匹配规则
- [GitHub Blog: How Copilot understands your code](https://github.blog/ai-and-ml/github-copilot/how-github-copilot-is-getting-better-at-understanding-your-code/) — 2023-05 — Copilot 的上下文构造策略（neighboring tabs、FIM）
- Claude Code 源码 `utils/api.ts` + `promptCacheBreakDetection.ts` — 2026-05 — 工程级缓存管理参考

⚖️ **来源一致性**：高。API 文档、源码分析和实际使用经验互相验证。
📅 **时效性声明**：信息获取于 2026-05-27。各平台 Prompt Cache 功能仍在快速迭代。
