---
name: agent-harness-scaffolder
description: >
  Generates the four core artifacts for long-running Agent tasks that span multiple context windows.
  Use when: user has a large task for an Agent that will take many turns or sessions;
  user wants to set up a "harness" for Agent-driven development; user says "搭个脚手架",
  "帮我拆解这个大任务", "长效Agent", "多会话任务", "scaffold", "harness", "multi-session agent task",
  "break down this project for an Agent".
applyTo: "**"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Agent Harness Scaffolder Skill

> 给定一个大型任务描述，自动生成"双 Agent Harness"所需的四大工件（Feature List / Init Script / Progress File / Agent Prompt），让 Agent 在多个上下文窗口间保持目标一致性和进度感知。

### Overview

当 Agent 需要跨越多个上下文窗口完成大型任务时，单靠 Compaction（对话摘要压缩）远远不够。Anthropic 在实验中验证了"Initializer + Coding Agent"双角色 Harness 模式，通过四大持久化工件系统性解决长效 Agent 的五大失败模式。

本 Skill 将 [长效Agent-Harness工程化研究报告](../../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R33_%E9%95%BF%E6%95%88AgentHarness%E5%B7%A5%E7%A8%8B%E5%8C%96.md) 中的方案固化为可一键触发的脚手架生成器。

核心范式：
- **P17 双角色分工**：Initializer（搭环境）+ Worker（做增量）
- **P18 显式状态传递 > 隐式摘要**：文件系统 + Git 替代 Compaction

## 1. 触发条件

当以下情况出现时激活此 Skill：
- 任务复杂度预计超过单次对话能完成的范围
- 用户描述了一个较大的项目/功能，需要多步实现
- 用户说"这个任务比较大"、"需要分多次做"
- 用户想让 Agent 自主完成一个完整项目

## 2. 执行流程

### Phase 1: 任务理解与分解

#### 向用户确认

| 问题 | 目的 |
|------|------|
| 这个项目的最终目标是什么？（一句话） | 锚定目标，防止 Agent 偏移 |
| 有没有已有的代码基础？还是从零开始？ | 决定 Init Script 内容 |
| 最关键的功能是哪 3 个？ | 确定优先级排序 |
| 有没有技术限制？（语言/框架/部署环境） | 约束 Feature List |

#### 任务分解原则

分解的粒度很关键——太粗了 Agent 不知道怎么做，太细了就变成人在写伪代码。

定义"一个好的功能点"：
- **独立可验证**：做完这一条，能运行/测试/看到效果
- **单次会话可完成**：一个 Agent 会话（~100K 上下文）内能完成
- **有明确的完成标准**：不是"优化性能"，而是"页面加载时间 < 2s"

### Phase 2: 生成 Feature List（feature_list.json）

这是整个 Harness 的核心——Agent 的"任务清单 + 目标锚点"。

**用 JSON 而非 Markdown**，因为结构化格式约束 Agent 行为比自然语言更可靠（防止 Agent 修改目标描述来"宣布"完成）。

```json
{
  "project_name": "项目名",
  "goal": "一句话目标描述",
  "created_at": "YYYY-MM-DD",
  "features": [
    {
      "id": "F001",
      "name": "功能名称",
      "description": "具体描述（2-3句话）",
      "priority": "P0|P1|P2",
      "acceptance_criteria": [
        "验收标准1：具体可测试的条件",
        "验收标准2：..."
      ],
      "status": "not_started",
      "dependencies": ["F000"],
      "estimated_complexity": "small|medium|large"
    }
  ],
  "tech_stack": {
    "language": "...",
    "framework": "...",
    "constraints": ["..."]
  }
}
```

#### 功能点数量参考

| 项目规模 | 功能点数 | 示例 |
|---------|---------|------|
| 小型（1-2天） | 10-30 | CLI 工具、简单 API |
| 中型（1-2周） | 30-80 | Web 应用、Bot |
| 大型（1月+） | 80-200 | 全栈应用、平台 |

#### 优先级排序

- **P0**（必须先做）：项目骨架、核心功能、基础设施
- **P1**（必须有）：主要功能、边界处理
- **P2**（锦上添花）：优化、美化、高级功能

P0 功能之间按**依赖关系拓扑排序**——有依赖的排在后面。

### Phase 3: 生成 Init Script（init.sh / init.ps1）

Boot Sequence 启动脚本——每个新 Agent 实例"上班"时第一件事执行的脚本。

```bash
#!/bin/bash
# === Agent Boot Sequence ===
# 每个新 Agent 会话开始时运行此脚本

echo "=== 项目状态概览 ==="

# 1. 当前位置
echo "📁 工作目录: $(pwd)"

# 2. 进度状态
echo ""
echo "=== 当前进度 ==="
cat progress.txt 2>/dev/null || echo "（尚未创建进度文件）"

# 3. 最近变更
echo ""
echo "=== 最近 Git 提交 ==="
git log --oneline -10 2>/dev/null || echo "（尚未初始化 Git）"

# 4. 待完成项
echo ""
echo "=== 待完成功能 ==="
python3 -c "
import json
with open('feature_list.json') as f:
    data = json.load(f)
todo = [f for f in data['features'] if f['status'] != 'completed']
print(f'总计: {len(data[\"features\"])} 个功能点')
print(f'已完成: {len(data[\"features\"]) - len(todo)}')
print(f'待完成: {len(todo)}')
if todo:
    next_f = todo[0]
    print(f'\n下一个: [{next_f[\"id\"]}] {next_f[\"name\"]} (Priority: {next_f[\"priority\"]})')
" 2>/dev/null || echo "（feature_list.json 不存在）"

echo ""
echo "=== Boot Sequence 完成 ==="
echo "请阅读 feature_list.json 了解完整功能清单"
echo "完成一个功能后，更新 feature_list.json 和 progress.txt"
```

### Phase 4: 生成 Progress File（progress.txt）

自由格式的进度日志——Agent 每完成一个功能点后追加记录。

```
# 项目进度日志
# 每完成一个功能点，在末尾追加一条记录

=== 项目启动 ===
日期：YYYY-MM-DD
目标：[一句话目标]
功能点总数：N

---
（以下由 Agent 在每次完成功能点后追加）
```

**为什么不用 Git log 替代？** Git log 记录的是代码变更，progress.txt 记录的是"项目层面的进展和决策"——比如"尝试了方案 A 但发现不行，改用方案 B"这种决策上下文，Git commit message 放不下。两者互补。

### Phase 5: 生成 Agent System Prompt

给 Coding Agent 使用的系统提示词，包含 Boot 读取序列和工作规范：

```markdown
# Coding Agent 工作规范

## 启动序列（每次新会话必须执行）

1. 运行 `./init.sh`（或 `.\init.ps1`）获取项目状态
2. 阅读 `feature_list.json` 了解完整功能清单
3. 阅读 `progress.txt` 了解历史进展和决策
4. 运行 `git log --oneline -10` 查看最近代码变更

## 工作循环

每个功能点执行以下循环：

1. 从 feature_list.json 中选择下一个 not_started 的功能点（按 priority + dependencies 排序）
2. 实现该功能
3. 测试验证（对照 acceptance_criteria）
4. 更新 feature_list.json 中该功能的 status 为 "completed"
5. 在 progress.txt 追加记录
6. Git commit（message 格式：`[F{ID}] {功能名}`）
7. 继续下一个功能点

## 关键规则

- **不要一次性尝试实现所有功能** — 一个一个来，每个功能点完成后都要 commit
- **不要修改 feature_list.json 中的 description 或 acceptance_criteria** — 这些是你的"合同"，不能自己改目标
- **遇到阻塞时记录到 progress.txt** — 下一个 Agent 实例需要知道你卡在哪了
- **每次完成功能点后检查总进度** — 如果剩余功能多于已完成的 3 倍，考虑先做 P0 再做 P1
```

## 3. 输出清单

执行完本 Skill 后，应在项目目录下生成以下文件：

```
项目目录/
├── feature_list.json    ← 结构化功能清单（Agent 的"合同"）
├── init.sh              ← Boot Sequence（Linux/Mac）
├── init.ps1             ← Boot Sequence（Windows）
├── progress.txt         ← 进度日志模板
└── AGENT_PROMPT.md      ← Coding Agent 系统提示词
```

## 4. 防御五大失败模式

| 失败模式 | 表现 | 本 Skill 的防御机制 |
|---------|------|-------------------|
| **一次性尝试过多** | Agent 试图一口气实现全部 | feature_list.json 强制拆分 + 工作循环约束 |
| **过早宣布完成** | Agent 看到一些进展就说完了 | JSON status 字段 + acceptance_criteria 验收 |
| **上下文丢失** | 新 Agent 不知道前任做了什么 | init.sh Boot 序列 + progress.txt + git log |
| **目标篡改** | Agent 修改需求来"匹配"自己的实现 | JSON 结构（比 Markdown 更难篡改）+ "不能改合同"规则 |
| **决策丢失** | 为什么当初选了方案 A？ | progress.txt 记录决策上下文 |

## 5. 适用边界

**适合**：
- 需要多会话完成的项目（> 1 次对话）
- Agent 自主开发场景（给 Agent 一个目标，让它自己做）
- 团队中使用 Agent 持续开发的场景

**不适合**：
- 单次对话能完成的小任务（过度工程）
- 需要频繁人工干预和方向调整的探索性任务（Harness 假设目标稳定）
- 需要创造性决策的任务（Harness 擅长执行，不擅长创新）
