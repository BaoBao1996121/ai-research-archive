---
title: "Ch7: Skill 工程化 — 写 Agent 真正听的指令"
tags: [教程, skill, 指令, prompt-engineering, spiral-2]
date: 2026-04-12
status: completed
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../ARCHIVE_POLICY.md)。

# Chapter 7: Skill 工程化 — 写 Agent 真正听的指令

> 📍 前置：完成 Chapter 5-6（理解上下文和知识管理）
> 🎯 完成本章后你能：解释 Anthropic 官方的 Skill 设计哲学；写一份符合工程标准的 SKILL.md；理解"解释 Why"比"堆砌 MUST"更有效
> ⏱️ 预计时间：20 分钟阅读 + 20 分钟实践

---

## 为什么 Agent 不听话？（WHY）

你在 Ch1 写了 AGENTS.md 和 SKILL.md 来指导 Agent。Ch6 你学了怎么给 Agent 注入知识。但你可能发现一个问题：

**Agent 不完全按你写的来。**

你写了"输出必须包含来源链接"，它有时候加有时候不加。你写了"不确定的结论标注待验证"，它经常忘。你写了十条规则，它能稳定遵守六条。

这不是 Agent 故意忤逆你。问题出在**你写指令的方式**上。

Anthropic 官方的 Skill-Creator 项目揭示了一个反直觉的真相：

> **全大写的 ALWAYS/NEVER 是黄旗。** 如果你发现自己在写"必须"、"绝对不能"、"一定要"，这恰恰说明你的指令可能有问题。

为什么？因为你在跟一个很聪明但注意力有限的人说话。对这样的人，喊十遍"一定要检查拼写！"不如解释一次"拼写错误会让客户觉得我们不专业，上次因为一个错别字丢了一个大单"。

---

## 核心概念（WHAT）

### Anthropic 的七条设计哲学

Anthropic 不是写了一份最佳实践文档——他们建了一条 Skill 生产流水线（Skill-Creator）：从编写 → 测试 → 盲比评估 → 迭代优化 → 打包发布。从这条流水线里提炼出了七条设计哲学：

#### 哲学 1：解释 Why，而非堆砌 MUST

这是最重要的一条。对比：

| ❌ 堆砌约束 | ✅ 解释原因 |
|------------|-----------|
| `MUST: 输出必须包含三级标题` | `用三级标题是因为读者需要快速扫描跳转——大段无结构文字会让忙碌的工程师直接关掉` |
| `NEVER: 绝对不能用 var` | `用 const/let 而不是 var，因为 var 的函数作用域会导致闭包中的变量泄漏` |
| `ALWAYS: 每个函数必须有 docstring` | `关键 API 加 docstring 是因为此库的用户不看源码，只通过 IDE 提示了解用法` |

**为什么 Why 比 MUST 有效？** 因为 LLM 真正懂了理由后能**举一反三**。堆 MUST 是脆弱的（一个新场景就可能失效），理解 Why 是鲁棒的。

#### 哲学 2：泛化而非过拟合

> "当某个问题反复出现时，本能反应是加更多约束。但正确的做法是换个角度解释。"

SKILL.md 的目标是创造一百万次好的执行，不是在三个测试用例上满分。

#### 哲学 3：保持精简，删掉不拉分的

通过阅读 Agent 的执行 transcript 来判断哪些指令实际上在浪费模型的时间——不是凭感觉删，是**看到模型在某个指令上打转才删**。

#### 哲学 4：发现重复 → 固化为脚本

> "模型反复创造的东西 = 应该被预制的东西。"

如果模型在执行 Skill 时反复写 `create_chart.py`，那个脚本就应该变成 Skill 的 bundled script。

#### 哲学 5：先写草稿，再用新鲜眼光审视

Skill 的编写本身也是迭代的。

#### 哲学 6：Description 要"有攻击性"

模型有"undertrigger"倾向——该用 Skill 时不用。Description 要主动声明触发条件：

```
❌ "How to build a dashboard."
✅ "How to build a dashboard. Make sure to use this skill whenever 
    the user mentions dashboards, data visualization, internal metrics, 
    or wants to display any kind of data, even if they don't explicitly 
    ask for a 'dashboard.'"
```

#### 哲学 7：适配运行环境，优雅降级

同一个 Skill 在 Claude Code（完整功能）、Claude.ai（无 subagent） 和 headless 环境下应该都能工作——没有某个能力就换种方式完成目标，而不是报错。

### SKILL.md 的结构：一个工件而非文档

一份合格的 SKILL.md 包含：

```yaml
---
description: "触发条件声明（要pushy）"
---

# Skill 名称

## 你是谁（角色定位 + Why）
## 工作流程（步骤 + 每步的 Why）
## 输出规范（格式 + Why）
## 边界声明（什么不做 + Why）
## bundled scripts（如果模型反复要写的脚本）
```

关键：**每个规则都跟着 Why**。

---

## 动手做（HOW）

### 练习：写你自己的 SKILL.md

假设你要创建一个"日报总结"Skill：Agent 读取你今天在各个聊天窗口、代码提交、文档修改中的活动，生成一份日报。

**Step 1: 写 Description（触发开关）**

```yaml
---
description: |
  Generate a daily work summary from user's activities. Use this skill 
  when the user asks for a daily report, work summary, standup notes, 
  end-of-day recap, or mentions anything about summarizing today's work, 
  even if they just say "今天干了啥" or "帮我写日报".
---
```

**Step 2: 写角色定位（带 Why）**

```markdown
# Daily Summary

你是一个日报总结助手。你的目标不是记流水账，而是帮用户从今天的碎片活动中
提炼出「做了什么有价值的事」和「明天该优先做什么」。

为什么这样定位：管理者看日报是为了了解进度和风险，不是看你开了几个会。
用户自己回顾日报是为了保持方向感，不是回忆琐事。一份好日报 = 3 个成果 + 
1 个风险 + 1 个明日计划。
```

**Step 3: 写工作流程（每步带 Why）**

```markdown
## 工作流程

1. **搜集活动数据**：读取 git log、聊天记录摘要、文档修改记录
   - 为什么先搜集：不能凭记忆编——人会遗忘琐碎但重要的事
   
2. **按价值排序**：将活动按对项目目标的贡献度排序，而非按时间
   - 为什么按价值：时间线日报读起来像流水账，价值线日报读起来像进展报告
   
3. **识别风险信号**：从活动中提取潜在风险（阻塞、延期、依赖）
   - 为什么单独提风险：风险越早暴露越容易处理，日报是最自然的暴露窗口
   
4. **输出格式**：
   ```
   ## 📅 YYYY-MM-DD 日报
   
   ### ✅ 今日成果（按价值排序）
   1. [最有价值的成果]
   2. [次要成果]
   
   ### ⚠️ 风险与阻塞
   - [如有]
   
   ### 📋 明日计划
   1. [最高优先级]
   ```
```

### 对照检查

写完后用这个清单检查你的 SKILL.md：

- [ ] 每条规则后面都有 Why？
- [ ] Description 包含了多种可能的触发表述？
- [ ] 没有全大写的 MUST / NEVER / ALWAYS？
- [ ] 删掉了所有"显而易见"的规则？（比如"输出要通顺"——LLM 本来就会这么做）
- [ ] 如果模型需要反复写某个脚本，已经预制好了？

### 思考题

1. **本工作区的 copilot-instructions.md 里有没有"黄旗"？** 打开看看，有没有全大写的 ALWAYS/NEVER？如果有，怎么改写成 Why 格式？
2. **Ch1 你写的 SKILL.md 能打几分？** 对照 Anthropic 的七条哲学回头审视一下。
3. **"模型反复创造的东西 = 应该被预制的东西"** — 你在使用 Agent 时，有没有发现 Agent 总是自己写某个辅助脚本？

---

## 深入阅读（IF）

| 主题 | 报告 | 关注章节 |
|------|------|---------|
| Anthropic Skill-Creator 完整源码分析 | [Anthropic官方Skill-Creator设计哲学研究报告](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) | 全文 |
| 七条设计哲学的原引用 | [Anthropic官方Skill-Creator设计哲学研究报告](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) | §二 七个核心设计哲学 |
| Eval-Driven Development 方法 | [Anthropic官方Skill-Creator设计哲学研究报告](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md) | §四 Eval-Driven Development |
| agent-skills 20 个 Skill 全表 | Agent-Skills与LLM-Wiki生态调研报告（原稿交叉引用，本归档未解析） | §2 |
| SKILL.md 格式标准（P6 范式） | Agent-Skills与LLM-Wiki生态调研报告（原稿交叉引用，本归档未解析） | §10 新发现的关键范式 |

---

## 本章小结

| 你学到了 | 对应能力 |
|---------|---------|
| 解释 Why 比堆 MUST 更有效 | 改变写指令的思维方式 |
| Skill = 工件，不是文档 | 用工程化思维对待指令 |
| Description 是触发开关，要 pushy | 解决"该触发时不触发"的问题 |
| 删掉不拉分的、固化重复脚本 | 具备指令优化的具体手法 |

> ⏭️ 下一章：你改了一版 Skill，怎么知道是改好了还是改坏了？→ [Chapter 8: 评估与质量](Ch08-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F.md)
