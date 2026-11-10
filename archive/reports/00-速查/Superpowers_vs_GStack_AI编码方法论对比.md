> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Superpowers vs GStack：AI 编码方法论对比速查

> 两个 2026 年现象级项目的定位、设计哲学、核心能力对比
> 日期：2026-05-21
> 关联：[R118 Superpowers 三大机制拆解](../04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R118_Superpowers%E4%B8%89%E5%A4%A7%E5%8F%AF%E5%80%9F%E9%89%B4%E6%9C%BA%E5%88%B6%E6%B7%B1%E5%BA%A6%E6%8B%86%E8%A7%A3.md) | [Superpowers 速查卡](Superpowers_Agentic%E6%8A%80%E8%83%BD%E6%A1%86%E6%9E%B6%E9%80%9F%E6%9F%A5.md)

---

## 定位透镜

### 纵轴 · 演化脉络

两个项目诞生于同一时期（2025Q4～2026Q1），解决同一个根本问题：**让 AI 编码 Agent 从"随机帮忙"变成"可预测的工程流程"**。

| 维度 | Superpowers (obra) | GStack (garrytan) |
|------|-------------------|-------------------|
| 创始人 | Jesse Vincent（Perl/RT/系统工具老炮，20 年开源） | Garry Tan（Y Combinator CEO，Palantir 早期员工） |
| 创建时间 | 2025-10-09 | 2026-03-11 |
| 引爆事件 | Jesse 的博客 "Superpowers" 一文被 HN 顶上首页 | Garry 在推特晒 "810× 产出倍率"，争议引流 |
| 生命周期 | 成熟期（200K ⭐，Plugin Marketplace 已上线） | 快速上升期（100K ⭐，创建仅 2 个月） |
| 许可证 | MIT | MIT |
| 语言 | Shell（粘合层，Skills 是纯 Markdown） | TypeScript（完整 CLI + 浏览器工具链） |

**关键转折**：2026Q1，Anthropic 推出 Claude Code Plugin 机制后，superpowers 成为第一批 "官方 Marketplace" 上架的第三方插件，实现了原生集成。gstack 则走"git clone 安装 + 自动更新"的分发路径，更偏向自有基建。

### 横轴 · 竞争格局

两者解决同一问题但**设计哲学根本不同**：

| 设计哲学 | Superpowers | GStack |
|---------|-------------|--------|
| 核心隐喻 | **方法论框架** — "一套完整的软件开发方法论" | **虚拟团队** — "把 Claude 变成 CEO+工程经理+设计师+QA" |
| 执行模型 | Agent 自动触发 Skill → subagent 执行 → 双阶段 Review | 用户通过 slash command 主动调用角色 |
| 控制权 | Agent 主导，人类审批设计后放手 | 人类主导，逐个命令调度角色 |
| 完备性哲学 | "Boil the lake" 但以纯 Markdown 为界 | "Boil the lake" + 完整工具链（浏览器、遥测、gbrain 记忆） |
| 扩展模型 | Plugin/Marketplace 生态 | 单仓一体化 + host adapters 适配多 Agent |

### 交叉判断

**superpowers 适合**：想要"说清需求后放手让 Agent 自主执行 2 小时"的场景，TDD 方法论强信仰者，开源社区贡献者。

**gstack 适合**：Solo founder / CEO 型用户（设计+产品+工程一人全包），需要"完整的产品思维链"（不只是写代码，而是从 office hours 到 ship 的全生命周期），想要浏览器自动化 QA 能力。

---

## 核心能力对比

### Skills/命令覆盖范围

| 阶段 | Superpowers Skills | GStack Slash Commands |
|------|-------------------|---------------------|
| **需求/构思** | brainstorming | /office-hours, /plan-ceo-review |
| **架构设计** | writing-plans | /plan-eng-review, /plan-design-review |
| **分支管理** | using-git-worktrees | — (依赖 Git 标准流程) |
| **执行** | subagent-driven-development, executing-plans | /autoplan (自动规划+执行) |
| **测试** | test-driven-development | (内嵌于 review 中) |
| **调试** | systematic-debugging | /investigate |
| **代码审查** | requesting-code-review, receiving-code-review | /review |
| **设计审查** | — | /design-review, /design-consultation, /design-shotgun |
| **QA** | verification-before-completion | /qa, /qa-only (真实浏览器！) |
| **安全** | — | /cso (OWASP + STRIDE 审计) |
| **发布** | finishing-a-development-branch | /ship, /land-and-deploy, /canary |
| **文档** | — | /document-release, /document-generate |
| **回顾** | — | /retro |
| **元技能** | writing-skills, using-superpowers | /learn, /skillify |
| **浏览器** | — | /browse, /connect-chrome (Playwright 集成) |
| **持久记忆** | — | gbrain 集成（Postgres + pgvector + 知识图谱） |

**结论**：superpowers 是"深而窄"——14 个 Skill 每个都经过严格 TDD 验证；gstack 是"广而全"——23+ 命令覆盖产品全生命周期但单个命令的方法论厚度略薄。

### 技术架构差异

```
Superpowers 架构：
─────────────────────────────────────
Plugin (纯 Markdown + Shell hooks)
    ├── .claude-plugin/     → Claude Code 插件入口
    ├── .codex-plugin/      → Codex 适配
    ├── .cursor-plugin/     → Cursor 适配
    ├── skills/14个/SKILL.md  → 纯 Markdown 行为定义
    ├── hooks/              → Session 启动注入
    └── tests/              → Skill TDD 测试集

GStack 架构：
─────────────────────────────────────
CLI + Runtime (TypeScript + Playwright)
    ├── hosts/              → 10 种 Agent 适配器
    ├── 23+ skill dirs/     → Markdown + Bash preamble
    ├── browse/             → Playwright 无头浏览器 CLI
    ├── bin/                → gstack-update, gstack-config 等运维工具
    ├── lib/                → 共享库
    ├── benchmark/          → 模型性能测试
    ├── test/               → E2E + LLM-as-judge 评测
    └── extension/          → 编辑器扩展
```

### 质量保证策略对比

| 维度 | Superpowers | GStack |
|------|-------------|--------|
| Skill 测试 | **Skill TDD** — 7 种压力类型模拟 Agent 跳过行为 | E2E 测试 (claude -p) + LLM-as-judge 评分 |
| 代码质量 | 双阶段 Review（Spec 合规 → Code Quality） | /review（单阶段但含 SQL 安全/LLM 信任边界检查） |
| QA | verification-before-completion（逻辑验证） | **/qa（真实 Playwright 浏览器打开 URL 测试！）** |
| 安全 | 无专门机制 | /cso（OWASP Top 10 + STRIDE 威胁模型） |
| 反 Slop | description 中预判 Agent 行为偏差 | slop-scan 配置文件 + 自动扫描 |
| 贡献门槛 | 94% PR 被拒率，极严格（反 AI 刷 PR） | 标准 GitHub Flow |

---

## 设计哲学深挖

### Superpowers："方法论纯粹主义"

核心信仰：
1. **TDD 是铁律** — "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST. Delete means delete."
2. **Subagent 隔离** — 每个任务派生全新 subagent，不继承上下文 → 避免污染
3. **Plugin 零依赖** — 纯 Markdown + Shell，不引入任何外部工具链
4. **Skill 描述即行为** — description 字段精心设计，预判 Agent 的 12 种跳过借口并提前封堵

Jesse 的开发哲学用一句话概括："**Agent 是一个热情但缺乏判断力的初级工程师，你需要给他一套不可协商的规则。**"

### GStack："产品完备主义"

核心信仰：
1. **Boil the Lake** — 边际成本为零时，做完整的事比做"够用的事"便宜
2. **角色分工** — CEO 审产品 → Eng Manager 锁架构 → Designer 杀 AI slop → QA 开浏览器 → CSO 审安全
3. **Search Before Building** — 三层知识体系（Tried & True / New & Popular / First Principles）
4. **Builder 记忆（gbrain）** — Postgres + pgvector 存储长期知识，每个 Skill 可查询历史决策

Garry 的开发哲学用一句话概括："**一个人 + AI = 20 人团队，前提是你给 AI 配齐完整的角色和工具。**"

---

## 与我们体系的关联

| 我们的组件 | 对应 Superpowers | 对应 GStack | 差距/机会 |
|-----------|-----------------|-------------|----------|
| agent.md（行为定义） | CLAUDE.md + Skills 的 description 字段 | CLAUDE.md + ETHOS.md + 各 Skill 的 preamble | 我们的 agent.md ~600 行，已接近他们的复杂度 |
| skills/ 目录 | skills/14 个 | 23+ 命令目录 | 我们 Skill 偏研究流程，他们偏编码流程 |
| KNOWLEDGE_INDEX | — | gbrain（Postgres 级） | 他们有持久化 + 向量检索，我们是文件级 |
| PATTERN_LIBRARY | — | — | **我们独有**，两者都没有显式的"外部模式借鉴库" |
| 质量保证 | Skill TDD（我们 R118 已借鉴了核心思路） | E2E + LLM-judge | 我们在此维度最弱，缺实际运行的评测脚本 |
| 产出物管理 | — | — | **我们独有**（DELIVERABLES_INDEX） |

### 可借鉴的新模式（gstack 独有、R118 未覆盖）

1. **Boil the Lake 完备性思维** — "AI 让边际成本趋零时，做完整比做'够用'更便宜"。这个理念可应用到我们的研究流程：**既然用 AI 跑完整调研流程只多花 5 分钟，就不要跳步**。
2. **角色化 Slash Command** — 把不同质量维度拆成独立角色（CEO/Eng/Design/QA/CSO），每个角色有自己的审查视角。我们的 agent.md 可以考虑在 Forge 阶段加入类似的"多角色审视"。
3. **真实浏览器 QA** — gstack 通过 Playwright 打开真实 URL 做 QA，超越了"看代码逻辑"的验证层级。对我们的原型项目（P01-P08）有直接参考价值。
4. **gbrain 持久记忆** — 跨会话的 Postgres+pgvector 记忆系统，与我们的 KNOWLEDGE_INDEX 是同一问题的不同解法：我们用 Markdown 文件 + Agent 读取，他们用数据库 + 向量检索。**他们的方案在规模化时更优，但我们的方案在可读性和版本控制上更优**。
5. **Telemetry + Analytics** — gstack 有 skill-usage.jsonl 追踪哪些命令被使用，可以数据驱动地优化。我们的 interaction-log 做了类似的事但更偏"人的沟通模式"而非"工具使用模式"。

---

## 选型决策指引

| 你的场景 | 推荐 | 理由 |
|---------|------|------|
| Claude Code 重度用户 + TDD 信仰者 | **Superpowers** | 方法论更纯粹，subagent 自治能力更强 |
| Solo founder 一人全栈 | **GStack** | 覆盖产品→设计→实现→QA→发布全链路 |
| 想要"说完需求就走开 2 小时" | **Superpowers** | subagent-driven-development 为此设计 |
| 需要浏览器自动化 QA | **GStack** | Playwright 集成是其独有能力 |
| 安全审计需求 | **GStack** | /cso 做 OWASP+STRIDE，superpowers 无此模块 |
| 多 Agent 环境（Cursor+Claude+Codex） | **两者都支持** | superpowers 8 种 Agent，gstack 10 种 |
| 研究/知识管理场景 | **都不直接适用** | 两者都是编码方法论，我们的 agent.md 更匹配研究流程 |

---

## 数据快照（2026-05-21 获取）

| 指标 | Superpowers | GStack |
|------|-------------|--------|
| GitHub Stars | 200,462 | 100,137 |
| Forks | 17,867 | 14,912 |
| Open Issues | 293 | 555 |
| Language | Shell | TypeScript |
| License | MIT | MIT |
| 创建日期 | 2025-10-09 | 2026-03-11 |
| 最后更新 | 2026-05-21 | 2026-05-21 |
| Skills/Commands 数 | 14 | 23+ |
| 支持的 AI Agent 数 | 8 | 10 |
| 分发方式 | Plugin Marketplace (原生) | git clone + 自动更新 |
| 外部依赖 | 零（纯 Markdown + Shell） | Bun + Node.js + Playwright |

---

## 来源清单

- [obra/superpowers](https://github.com/obra/superpowers) — GitHub API 获取 — 2026-05-21
- [garrytan/gstack](https://github.com/garrytan/gstack) — GitHub API 获取 — 2026-05-21
- [jnMetaCode/superpowers-zh](https://github.com/jnMetaCode/superpowers-zh) — 中文社区版 — 3,597⭐
- [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) — 官方 Marketplace — 990⭐
- 本工作区已有：R118, Superpowers 速查卡

⚖️ 来源一致性：GitHub API 数据为第一手，多源一致
📅 时效性声明：以上信息获取于 2026-05-21，两项目更新极为活跃（当日有新提交）
