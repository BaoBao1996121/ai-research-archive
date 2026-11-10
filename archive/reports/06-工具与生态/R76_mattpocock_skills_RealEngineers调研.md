---
title: mattpocock/skills（Skills For Real Engineers）调研
aliases: [R76, mattpocock skills调研, Skills For Real Engineers]
date: 2026-04-30
type: research-report
category: 工具与生态
tags:
  - skills
  - claude-code
  - mattpocock
  - prompt-engineering
  - tdd
status: published
report_id: R76
related:
  - "[R71_Coding_Agent深度对比_五家横评](R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md)"
  - "[skills/skill-evaluator/SKILL](../../skills/skill-evaluator/SKILL.md)"
  - "[skills/terse-mode/SKILL](../../skills/terse-mode/SKILL.md)"
---

> 脱敏公开版 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../ARCHIVE_POLICY.md)。

# mattpocock/skills —— "Skills For Real Engineers" 调研

> **一句话**：Matt Pocock（Total TypeScript 作者）从自己 `.claude` 目录提取的 14 个 Claude Code Skill，主张"用工程基本功对抗 vibe coding"。一周内冲到 46k+ stars，是当前 Claude Skills 生态最火的"个人精华集"，与 Anthropic 官方 skills 仓互补。
> **研究日期**：2026-04-30
> **关联报告**：[R71_Coding_Agent深度对比_五家横评](R71_Coding_Agent%E6%B7%B1%E5%BA%A6%E5%AF%B9%E6%AF%94_%E4%BA%94%E5%AE%B6%E6%A8%AA%E8%AF%84.md)

---

## 目录
- [一、TL;DR：30 秒看完](#一tldr30-秒看完)
- [二、定位透镜：纵横坐标](#二定位透镜纵横坐标)
- [三、核心理念：四个失败模式 → 四类解药](#三核心理念四个失败模式--四类解药)
- [四、Skill 全景拆解（14 个）](#四skill-全景拆解14-个)
- [五、设计哲学的工程深度](#五设计哲学的工程深度)
- [六、与本工作区 skills/ 的对照](#六与本工作区-skills-的对照)
- [七、值得借鉴 vs 值得警惕](#七值得借鉴-vs-值得警惕)
- [八、落地建议](#八落地建议)
- [九、来源清单与开放问题](#九来源清单与开放问题)

---

## 一、TL;DR：30 秒看完

| 维度 | 结论 |
|------|------|
| **是什么** | 14 个 Claude Code/Codex 通用的 Markdown Skill，按 engineering / productivity / misc 三类组织 |
| **作者** | Matt Pocock，TypeScript 教育界知名 IP（Total TypeScript、AI Hero），订阅者 6w+ |
| **热度** | 46,246 stars（截至 2026-04-30），近 24 小时仍在更新，处于**爆发上升期** |
| **核心主张** | "Real Engineering ≠ Vibe Coding"。强调对齐、共享语言、反馈回路、架构演进四件基本功 |
| **安装方式** | `npx skills@latest add mattpocock/skills` —— 配套 CLI（skills.sh）做选择性安装 |
| **是否值得抄** | **值得抄理念，谨慎抄实现**。它的 Skill 个体设计水准高于 Anthropic 官方示例；但它是单人风格，硬塞进团队会水土不服 |

---

## 二、定位透镜：纵横坐标

### 纵轴 · 演化脉络

- **创世背景**：2025 Q3 Anthropic 推出 Skills 机制后，社区涌现一批"Skill 包"，但绝大多数只是 demo 拼盘。Matt Pocock 在自己日常工作中沉淀了一套 `.claude/`，发现真正能用的就 10 多个，于是干净地剥出来开源。
- **关键转折**：2026 年 4 月发布后一周内冲上 GitHub Trending TypeScript/Shell 第一，因为它**第一次把"个人生产力"打包成可复用资产**——之前的 Skill 仓要么是企业流程示范（如 OpenAI/Anthropic 官方），要么是玩具集合。
- **生命周期定位**：**早期上升期**。还没有形成插件生态、还没有版本化分支、还没有跨语言适配。但配套 `npx skills` CLI 暗示作者在做"Skills 包管理器"的中长期赌注。

### 横轴 · 竞争格局

| 项目 | Stars | 定位差异 | 设计哲学 |
|------|------:|---------|---------|
| **mattpocock/skills** | 46k+ | 个人精华、强观点、TS 重 | "工程基本功优先于自动化" |
| **anthropics/skills**（官方） | 高 | 企业示例、流程参考、覆盖面广 | "展示能力边界，等用户自定制" |
| **simonw/llm 插件生态** | 几千 | LLM 工具调用层，非 Skill | "Unix 哲学，组合优先" |
| **GSD / BMAD / Spec-Kit** | 中 | 完整方法论框架，强约束 | "接管流程，换来可重复性" |
| 各种"awesome-claude-skills" | 数百 | 链接合集、无质量过滤 | 无 |

**设计哲学差异（读 README 自述提炼）**：
> "GSD、BMAD、Spec-Kit 通过接管流程来帮你，但代价是夺走控制权、让流程里的 bug 难以排查。这些 skill 设计成**小、易改、可组合**，跟任何模型都能用。"

—— 这是典型的 **"Unix 哲学派" vs "全套框架派"** 的分歧。Matt 押注前者。

### 交叉判断

- **靠不靠谱**：作者背书强（Total TypeScript 商业课变现验证过他的内容质量）+ 仓库每日提交 + 社区 fork 出现独立维护版本（如 smll-ai/mattpocock-skills），**短期靠谱**。但长期单人维护 = bus factor 1，**机构采用要做内部 fork**。
- **该不该用**：
  - 个人开发者、独立项目、TypeScript 重栈 → **直接抄**
  - 团队协作、强流程要求、合规场景 → **抄理念，自己写**
  - 已经有成熟 SDLC 的大组织 → 价值有限，主要看 grill-with-docs 和 caveman 两个

---

## 三、核心理念：四个失败模式 → 四类解药

README 用了一个很费曼式的结构——**先描述病状，再开药方**。这是它教育属性强的本质。

### 失败模式 #1：Agent 没做你想要的（misalignment）

> 引 Pragmatic Programmer："No-one knows exactly what they want."

**药方**：在动手前强制 Agent 反向"拷问"你（grilling），把每个决策分支都问清楚再写代码。
- `/grill-me`（非代码场景）
- `/grill-with-docs`（代码场景，附加共享语言更新）

**这是 Matt 自称最受欢迎的 Skill**，对应 PSEV 框架里的 **Profile + Strategy 阶段被显式强制化**。

### 失败模式 #2：Agent 太啰嗦（缺共享语言）

> 引 Eric Evans Domain-Driven Design："With a ubiquitous language, conversations among developers and expressions of the code are all derived from the same domain model."

**药方**：维护 `CONTEXT.md`（项目术语表）+ `docs/adr/`（架构决策记录）。
- 例子：原本说 "There's a problem when a lesson inside a section of a course is made 'real'" → 共享语言后说 "There's a problem with the materialization cascade"
- 收益：变量/函数命名一致、Agent 浏览代码更快、"思考 token"消耗降低

这个洞察非常**反直觉但极重要**：很多人把 LLM 啰嗦归因为模型问题，Matt 指出**啰嗦本质是"项目缺少凝练词汇"**——Agent 只能用 20 个词描述本该 1 个词的东西。

### 失败模式 #3：代码不工作（缺反馈回路）

> 引 Pragmatic Programmer："The rate of feedback is your speed limit."

**药方**：静态类型 + 浏览器访问 + 自动化测试，配合 Red-Green-Refactor 循环。
- `/tdd` —— 强制垂直切片（一个测试 → 一段实现 → 重复），明令禁止"水平切片"（一次写完所有测试再写所有代码）
- `/diagnose` —— reproduce → minimise → hypothesise → instrument → fix → regression-test 的固定调试流程

`/tdd` 内部对 "horizontal slicing" 有非常清晰的批判，是整个仓库工程深度最高的一个 SKILL.md。

### 失败模式 #4：建成了一团泥球（架构腐化）

> 引 Kent Beck XP："Invest in the design of the system every day."
> 引 John Ousterhout："The best modules are deep."

**药方**：把"关心架构"嵌入每个 Skill。
- `/to-prd` 在写 PRD 之前先问你**要动哪些模块**
- `/zoom-out` 让 Agent 从"我在改这一行"上升到"我在改整个系统的哪一部分"
- `/improve-codebase-architecture` 周期性运行的"防腐烂"扫描

---

## 四、Skill 全景拆解（14 个）

### Engineering 类（9 个）—— 日常代码工作

| Skill | 功能 | 何时触发 |
|-------|------|---------|
| `setup-matt-pocock-skills` | 一次性脚手架配置（issue tracker、triage 标签、文档目录） | 接入这套 Skill 后 per-repo 跑一次 |
| `grill-with-docs` | 用 CONTEXT.md + ADR 拷问你的方案 | 每次开新功能前 |
| `to-prd` | 把对话浓缩成 PRD 并提 GitHub Issue | grill 完后 |
| `to-issues` | 把 PRD 拆成"垂直切片"的可独立认领 Issue | PRD 后 |
| `triage` | 用状态机模式做 Issue 分类（Triager → Refiner → Designer → Approver 四角色） | 收到新 Issue 时 |
| `tdd` | 红-绿-重构循环，强制垂直切片 | 实施阶段 |
| `diagnose` | 固定调试流程 | 遇 Bug 时 |
| `improve-codebase-architecture` | 找"加深模块"的机会（结合 CONTEXT.md/ADR） | 周期性卫生扫描 |
| `zoom-out` | 让 Agent 给出更高层视角 | 在不熟悉代码区时 |

### Productivity 类（3 个）—— 通用工作流

| Skill | 功能 | 亮点 |
|-------|------|------|
| `caveman` | "原始人模式"——丢掉冠词/客套/对冲词，省约 75% token | 持久化（一旦触发整个会话保持），自动豁免（destructive 操作时短暂正常表达） |
| `grill-me` | 对任何计划/设计做无情面试 | Skill 之母，被 grill-with-docs 复用 |
| `write-a-skill` | 创建新 Skill 的元 Skill（含 progressive disclosure 规范） | 自举：用 Skill 写 Skill |

### Misc 类（3 个）—— 偶尔用

| Skill | 功能 |
|-------|------|
| `git-guardrails-claude-code` | 用 Claude Code hooks 拦截 `push`/`reset --hard`/`clean` 等危险命令 |
| `migrate-to-shoehorn` | TS 测试文件从 `as` 类型断言迁移到 `@total-typescript/shoehorn` |
| `scaffold-exercises` | 创建练习目录结构（明显是为他自己的课程产品服务的） |
| `setup-pre-commit` | Husky + lint-staged + Prettier + 类型检查 + 测试的预提交钩子 |

> **观察**：misc 类暴露了"个人仓"的属性——shoehorn 和 scaffold-exercises 几乎只对 Matt 自己有意义。这也提醒我们：**抄这套 Skill 时要做品类筛选，不要全盘接收**。

---

## 五、设计哲学的工程深度

挑三个细节展开，看 Matt 的设计内功：

### 5.1 `tdd` 对"水平切片"的批判

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  ...
```

附详细论证：批量写测试会"测试想象的行为而非实际行为"、"测的是数据结构的形状而非用户行为"、"在理解实现前就锁死了测试结构"。

**这不是写给新手看的**，是写给那些自以为懂 TDD 但其实在做"假 TDD"的工程师。深度高于绝大多数博客文章。

### 5.2 `grill-with-docs` 对 ADR 的克制

> "Only offer to create an ADR when all three are true:
> 1. **Hard to reverse** — the cost of changing your mind later is meaningful
> 2. **Surprising without context** — a future reader will wonder 'why did they do it this way?'
> 3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons
> If any of the three is missing, skip the ADR."

这个"三件齐备才创建"的判定规则，**直接解决了 ADR 实践中最大的痛点：滥用导致 ADR 文件夹变成噪声**。这就是经验沉淀，不是理论搬运。

### 5.3 `caveman` 的持久化设计

```
ACTIVE EVERY RESPONSE once triggered. No revert after many turns. 
No filler drift. Still active if unsure.
Off only when user says "stop caveman" or "normal mode".
```

并配 **Auto-Clarity Exception**：销毁性操作、安全警告、多步骤序列时**自动短暂退出**简洁模式。

这个设计意识到了"过度简洁会害人"——当 Agent 要确认 `DROP TABLE users` 时，原始人模式会让用户漏看警告。**有责任感的简洁**，比单纯的"省 token"高一个层次。

---

## 六、与本工作区 skills/ 的对照

| 我们已有 | mattpocock 对应物 | 关系 |
|---------|------------------|------|
| `terse-mode` | `caveman` | **高度同构**。我们的 terse-mode 偏"短句优雅"，caveman 更激进（碎片化+箭头逻辑）。可以借鉴它的**持久化机制和 Auto-Clarity 豁免**——这两点我们没做 |
| `skill-evaluator` | （无对应） | 我们独有。他的 `write-a-skill` 是"如何写"，我们的 `skill-evaluator` 是"如何评"，**互补关系** |
| `tech-selector` | `grill-me` 的子集 | 我们更结构化（约束→枚举→淘汰→对比→推荐），他更对话化。各有所长 |
| `source-code-dissector` | `zoom-out` 的反向 | 他从局部到全局，我们从全局到局部。**可以合并成"双向缩放"系列** |
| `knowledge-base-organizer` | （无对应） | 我们独有 |
| `agent-harness-scaffolder` | `setup-matt-pocock-skills` | **同类**，都是 per-repo 一次性配置。可借鉴他的"问→记→生成 config"三步交互模式 |
| `llm-service-stack` | （无对应） | 我们独有，他的仓没有部署相关 |
| （我们无） | `grill-with-docs` + CONTEXT.md/ADR 体系 | **明显缺失**，这是我们最值得引入的能力 |
| （我们无） | `tdd` 强制垂直切片 | **明显缺失** |
| （我们无） | `diagnose` 固定调试循环 | **明显缺失** |
| （我们无） | `git-guardrails-claude-code` 钩子防护 | 价值高，可用于危险 Git 操作的安全边界 |

**结论**：我们 7 个 Skill 偏"研究/沉淀/选型"，他 14 个 Skill 偏"日常 SDLC 流程"。**几乎不重叠**，组合起来才完整。

---

## 七、值得借鉴 vs 值得警惕

### ✅ 值得借鉴

1. **README 的"病-药"结构**：先讲失败模式再讲解药，比直接列功能清单**说服力强 10 倍**
2. **每个 Skill 的 frontmatter 写法**：`description` 字段精确写明"何时触发"，让 Claude 自动调用（model-invocation）能命中
3. **`disable-model-invocation: true`** 用于必须手动触发的 Skill（如 grill），避免被 Claude 误判
4. **CONTEXT.md / docs/adr 的轻量化引入**：不强制全套 DDD，只做"两个文件"的最小可行版
5. **CLI 配套（`npx skills`）**：把 Skill 安装做成包管理器体验，降低试用门槛
6. **垂直切片原则**：可以应用到我们的实验脚本设计、PBI 拆解
7. **caveman 的持久化 + Auto-Clarity 豁免**：直接抄到我们的 terse-mode

### ⚠️ 值得警惕

1. **单人 bus factor**：仓库一旦 Matt 不维护就死。机构采用必须 fork 后内部维护
2. **TypeScript 偏向**：`migrate-to-shoehorn`、`setup-pre-commit` 默认 Husky/Prettier，非 TS 项目要剥离
3. **流程依赖性**：`triage` → `to-prd` → `to-issues` → `tdd` 是一条流水线，部分采用会导致中间断链
4. **文化匹配**：grill-with-docs 假设你能接受被 Agent "无情面试"——团队里有人会觉得烦
5. **`/setup-matt-pocock-skills` 命令名暴露品牌捆绑**：不适合在内部直接使用，要重命名

---

## 八、落地建议

### 短期（1-2 周内可做）

1. **抄 `grill-with-docs` 的理念**，融入我们的 `tech-selector` 第一阶段——在画约束画像前先做一轮"灵魂拷问"
2. **抄 `caveman` 的持久化和豁免机制**，升级我们的 [skills/terse-mode/SKILL](../../skills/terse-mode/SKILL.md)
3. **新建 `tdd-vertical-slice` Skill**：把他的反水平切片论证提炼为我们的实验脚本编写规范
4. **新建 `diagnose` Skill**：固化调试流程，可与 [skills/source-code-dissector/SKILL](../../skills/source-code-dissector/SKILL.md) 配套使用

### 中期（1-2 月内）

5. **评估是否引入 CONTEXT.md / docs/adr 双轨体系**：
   - 选一个项目做试点
   - 跑 1 个月看 ADR 是否真在按"三件齐备"原则被克制创建
6. **Fork 一份 mattpocock/skills 到内部仓**，剔除 misc 类，重命名 setup 命令，作为团队"日常工程基本功 Skill 包"
7. **写 R76 的姊妹篇**：对照 anthropics/skills 官方仓，看官方 vs 个人精华仓的差异

### 长期观察

8. **跟踪 `npx skills` CLI 是否演化成事实标准**——如果是，我们的 `skills/` 目录组织方式可能需要适配它的 schema
9. **观察是否有"团队版 mattpocock/skills"出现**——如果社区开始 fork 出企业适配版，那是一个明确信号

---

## 九、来源清单与开放问题

### 📌 来源清单
- [mattpocock/skills GitHub README](https://github.com/mattpocock/skills) — 2026-04-30 抓取 — 主要事实来源
- [skills/engineering/tdd/SKILL.md](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/tdd/SKILL.md) — 2026-04-30 — 工程深度示例
- [skills/engineering/grill-with-docs/SKILL.md](https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/grill-with-docs/SKILL.md) — 2026-04-30 — ADR 三件齐备规则
- [skills/productivity/caveman/SKILL.md](https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/caveman/SKILL.md) — 2026-04-30 — 持久化与豁免设计
- [GitHub 搜索 "Skills For Real Engineers"](https://github.com/search?q=Skills+For+Real+Engineers&type=repositories) — 2026-04-30 — 热度与 fork 情况

⚖️ **来源一致性**：作者一手仓库，单源，但有多个独立 fork（smll-ai、David-TheBridgeDev、zunyiqingfeng-code 等）反映了真实社区采用，可视为间接交叉验证
📅 **时效性声明**：以上信息获取于 2026-04-30，stars 数随时变动

### 开放问题（待后续追踪）

1. **`npx skills` CLI 的代码在哪？** README 引用了它但 GitHub 主仓没看到 CLI 源码，可能在另一个仓
2. **`disable-model-invocation: true` 的官方 spec 在哪？** 这是 Claude Skills 的一个不太常被讨论的字段，值得专门考察
3. **`triage` 的状态机详细流程** 没读到 SKILL.md 全文，可能值得单独深拆
4. **真实采用率如何？** 46k stars 不等于 46k 用户，需要看 issue/discussion 活跃度才能判断真实生命力
5. **是否会出现"反 mattpocock"派？** 历史上每个强观点的 Skill 集合都会催生反对派（如 GSD vs BMAD），值得观察 6 个月

---

## 锻造审视

> 阶段六（Forge）的强制审视。

- **重复信号**：本次调研中，第三次写"个人开源工具集 vs 企业框架"的对比表（前两次见 R36/R71）。可以考虑把"对比纵横坐标"做成模板放进 `wiki/templates/`
- **可固化产物候选**：
  - **建议固化**：caveman 的持久化机制（直接合并到 terse-mode）—— 高确定性，立刻动手
  - **候选**：grill-with-docs 改写版（融入 tech-selector）—— 需先在 1-2 个真实场景试用，不急着固化
  - **不固化**：mattpocock 全套流程链（triage→to-prd→to-issues→tdd）—— 跨场景适用性存疑，留在报告里供查
- **PSEV 映射**：grill-with-docs ≈ Profile 强化版；to-prd/to-issues ≈ Strategy；tdd ≈ Execute 强化版；diagnose ≈ Verify 强化版。**整套 Skill 几乎完美映射 PSEV**，反向印证 PSEV 框架的普适性
- **更新索引**：本报告完成后需更新 KNOWLEDGE_INDEX（原稿交叉引用，本归档未解析） §二（新报告条目）、§三（"个人 Skill 包 vs 企业框架"作为新范式进入"已确立范式"待沉淀清单）

