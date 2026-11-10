> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Superpowers — Agentic 技能框架速查

> 实际仓库名：**obra/superpowers** | GitHub 显示名可能为 "agentic-skills-framework"
> 一句话：给 Claude Code / Codex / Cursor / Gemini CLI 等编码 Agent 注入一套**强制工作流** Skill 体系，让 Agent 不再跳过设计直接写代码。
> 调查日期：2026-05-15

---

## 基本数据

| 维度 | 值 |
|------|-----|
| 仓库 | [obra/superpowers](https://github.com/obra/superpowers) |
| Stars | ~191K（截至 2026-05-15，GitHub 历史 top 级别项目） |
| Forks | ~17K |
| 创建时间 | 2025-10-09 |
| 最近提交 | 2026-05-14（活跃） |
| 主语言 | Shell（实质是 Markdown Skill 文件集合） |
| 许可证 | MIT |
| 作者 | Jesse Vincent（[blog.fsck.com](https://blog.fsck.com)）/ Prime Radiant 团队 |
| 最新版本 | v5.1.0（2026-05-上旬） |
| 开放 Issues | ~265 |

---

## 定位透镜

### 纵轴 · 演化脉络

**创世故事**：Jesse Vincent 在 2025 年 9-10 月发现，Claude Code 等编码 Agent 的核心痛点不是"写不了代码"，而是**跳过设计直接堆代码**——没有 spec、没有 plan、不跑 TDD、不做 review。他把自己的个人工作流（brainstorm → plan → implement → review）提炼成一套**可自动触发的 Markdown Skill 文件**，让 Agent 在正确的时机"被迫"遵循流程。

**关键转折**：2025-10-09 Anthropic 同日推出 Claude Code Plugin System，Superpowers 成为首批 Plugin，一夜爆发。之后陆续支持 Codex CLI/App、Cursor、Gemini CLI、OpenCode、Factory Droid、GitHub Copilot CLI。

**生命周期定位**：**成熟上升期**。191K stars 说明社区已广泛验证，v5.1.0 说明在快速迭代，但核心 Skill 体系已基本稳定。

### 横轴 · 竞争格局

| 对比维度 | Superpowers | 我们的工作区 Skill 体系 | Hermes Agent |
|----------|-------------|----------------------|--------------|
| 定位 | 编码 Agent 工作流框架 | 研究 Agent 方法论框架 | 开源 Agent 运行时 |
| 核心理念 | "让 Agent 不跳步" | "让研究不跳步 + 知识沉淀" | "可插拔 Skill + Memory + Tool" |
| Skill 触发 | **自动触发**（bootstrap 注入） | 手动/半自动（靠 agent.md 约束） | 自动匹配（按 description） |
| 场景 | 纯软件开发 | AI 技术研究 + 方案落地 | 通用 Agent 平台 |
| Skill 内容 | 编码方法论（TDD、Plan、Review） | 研究方法论（Radar→Dissect→Forge） | 从 obra/superpowers 适配 |

**关键洞察**：Hermes Agent 的 `_samples` 中 5 个 software-development Skill（writing-plans、subagent-driven-development、test-driven-development 等）均标注 `adapted from obra/superpowers`。说明 Superpowers 已成为编码 Skill 的事实标准上游。

### 交叉判断

Superpowers 不是"竞品"，是**互补层**。我们的 Skill 体系专注研究方法论，Superpowers 专注编码工作流。两者的 Skill 格式和触发理念一致（都是 Markdown SKILL.md），可以共存。

---

## 核心工作流（7 个 Skill 的流水线）

```
brainstorming ──► using-git-worktrees ──► writing-plans
                                              │
                    ┌─────────────────────────┘
                    ▼
        subagent-driven-development
        或 executing-plans
                    │
                    ▼
        test-driven-development
        （RED → GREEN → REFACTOR）
                    │
                    ▼
        requesting-code-review
                    │
                    ▼
        finishing-a-development-branch
```

**强制性**：Agent 在 session 启动时加载 bootstrap（`using-superpowers` Skill），之后在检测到"用户要写东西"时**自动触发** brainstorming，不需要用户主动调用。这是和"可选使用的 Skill 集合"最大的区别。

---

## 14 个 Skill 速查

| Skill | 作用 | 关键机制 |
|-------|------|---------|
| **using-superpowers** | Bootstrap，教 Agent 有 Skill、必须用 | Session 启动注入 |
| **brainstorming** | 苏格拉底式需求澄清，阻止直接写代码 | 分段展示 spec |
| **writing-plans** | 生成实施计划，每任务 2-5 分钟粒度 | 假设实施者零上下文 |
| **executing-plans** | 批量执行计划 + 人类检查点 | 非 subagent 模式 |
| **subagent-driven-development** | 每任务派新 subagent + 双阶段 review | Spec 合规→代码质量 |
| **dispatching-parallel-agents** | 并发 subagent 编排 | 上下文隔离 |
| **test-driven-development** | RED-GREEN-REFACTOR 强制循环 | 先写测试再写实现，否则删代码 |
| **systematic-debugging** | 4 阶段根因分析 | 含 defense-in-depth 技巧 |
| **verification-before-completion** | 验证修复确实生效 | 反"宣称修好了但没跑过" |
| **requesting-code-review** | Review checklist | Critical 阻塞推进 |
| **receiving-code-review** | 响应 review 反馈 | GitHub thread 回复 |
| **using-git-worktrees** | 并行开发分支隔离 | 自动创建 worktree |
| **finishing-a-development-branch** | 合并/PR/放弃决策 | 清理 worktree |
| **writing-skills** | Meta-skill：教 Agent 写新 Skill | 含 Skill TDD 方法论 |

---

## 支持的编码 Agent（Harness）

Claude Code、Codex CLI、Codex App、Factory Droid、Gemini CLI、OpenCode、Cursor、GitHub Copilot CLI

安装方式因 harness 而异，多数支持 Plugin Marketplace 一行安装。

---

## 设计哲学

1. **Test-Driven Development** — 测试先行，始终
2. **Systematic over ad-hoc** — 流程胜过猜测
3. **Complexity reduction** — 简洁为首要目标
4. **Evidence over claims** — 验证后才能宣称完成
5. **Skills are code, not prose** — Skill 不是文档，是塑造 Agent 行为的"代码"
6. **Persuasion principles** — 借鉴 Cialdini 的影响力原则（权威、承诺、稀缺等）强化 Skill 遵从性

---

## 亮点与创新

- **Skill 自动触发机制**：Bootstrap 在 session 启动时注入，Agent 不需要用户手动调用就会执行对应 Skill。这解决了"Agent 知道规则但不遵守"的问题。
- **Subagent-driven development**：每个任务派一个干净 subagent → 双阶段 review → 下一个任务。Agent 能自主工作数小时不偏离计划。
- **Skill TDD**：writing-skills Skill 教 Agent 用"对抗性压力测试"验证新 Skill 是否真的有效（设计时间压力/沉没成本等场景让 subagent 尝试跳过 Skill）。
- **94% PR 拒绝率**：maintainer 对质量要求极高，任何"AI slop"直接关闭。

---

## 局限与风险

| 维度 | 问题 |
|------|------|
| **纯编码场景** | 不覆盖研究、调研、文档撰写、方案设计等非编码工作流 |
| **Claude 中心** | 虽支持 7+ harness，但核心在 Claude Code 上测试最充分，其他 harness 效果不一 |
| **零依赖执行** | 所有 Skill 是纯 Markdown，通过 Prompt 引导行为——效果高度依赖模型的指令跟随能力 |
| **强制流程开销** | brainstorm → plan → implement 全套跑完，小任务可能过度流程化 |
| **不接受领域 Skill** | 官方明确拒绝领域特定 Skill PR，只保留通用软件开发技能 |

---

## 对我们的价值

### 直接可借鉴

1. **Bootstrap 自动触发模式**：我们的 agent.md 是手动约束，Superpowers 的 bootstrap 注入 + 自动 Skill 检测更优雅。值得在我们的 Skill 体系中借鉴"session 启动时注入检查逻辑"的模式。
2. **Skill TDD（对抗性压力测试）**：用 subagent 模拟"时间压力""沉没成本"等场景测试 Skill 是否真的被遵守。这比"读一遍觉得没问题"有效得多。
3. **双阶段 Review**：先检查 spec 合规，再检查代码质量。可以引入我们的报告 review 流程（先检查调研流程完整性，再检查内容质量）。

### 不需要引入

- 编码工作流本身（brainstorming、TDD、git worktree）——我们的 Hermes sample 已有适配版。
- Superpowers 本体——我们不用 Claude Code / Codex 做日常开发。

### 潜在的 Skill 锻造机会

"Skill TDD 框架"这个概念值得固化：定义"Skill 验证场景模板"（压力、沉没成本、快捷诱惑等对抗性场景），用于测试我们自己写的 Skill/instruction 是否真正生效。当前我们的 skill-evaluator 更偏向评分，缺少这种"红队对抗性验证"维度。

---

## 来源清单

| 来源 | 日期 | 用途 |
|------|------|------|
| [GitHub API: obra/superpowers](https://api.github.com/search/repositories?q=agentic-skills-framework+user:obra) | 2026-05-15 | 确认仓库名/stars/forks |
| [README.md（GitHub API raw）](https://github.com/obra/superpowers/blob/main/README.md) | 2026-05-15 | 项目概述、Skill 列表、安装方式 |
| [CLAUDE.md（贡献者指南）](https://github.com/obra/superpowers/blob/main/CLAUDE.md) | 2026-05-15 | PR 要求、设计哲学差异 |
| [发布博客文章](https://blog.fsck.com/2025/10/09/superpowers/) | 2025-10-09 | 创世故事、Skill TDD、说服原则 |
| 本地 `_samples/hermes/skills/software-development/` | N/A | 验证 Hermes 对 Superpowers 的适配 |

⚖️ 来源一致性：**一致**（GitHub 数据 + README + 博客 + 本地 Hermes sample 互相印证）
📅 时效性声明：以上信息获取于 2026-05-15
