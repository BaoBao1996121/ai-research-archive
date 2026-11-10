---
name: copilot-efficiency-analyzer
description: >
  分析 VS Code Copilot Chat 会话数据，诊断个人 AI 沟通效率，提供可操作的改进建议。
  Use when: user wants to analyze their Copilot Chat usage patterns;
  user asks "分析我的对话效率", "我和 AI 沟通得怎么样", "提示词质量分析",
  "analyze my Copilot usage", "improve my prompting", "沟通模式分析",
  "copilot 效率", "对话分析", "提示词优化".
applyTo: "**"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Copilot Efficiency Analyzer Skill

> 从 VS Code Copilot Chat 的本地会话数据中挖掘用户的沟通模式，诊断效率瓶颈，输出个性化改进建议。

## Overview

和 AI 对话是一项可训练的技能。但"感觉自己用得不错"和"用数据证明在变好"之间，差一个诊断工具。

本 Skill 读取 VS Code 本地存储的 Copilot Chat 会话记录（`chatSessions/`），从 7 个维度分析用户的沟通效率，输出一份包含数据支撑的个人画像报告。它不上传任何数据——所有分析在本地完成。

**核心价值**：把"我觉得我的提示词还行"变成"数据说我 59% 的消息没给约束，重做税是 15.7%"。

## 1. 触发条件

当用户提出以下类型的请求时激活此 Skill：
- "分析我和 Copilot 的对话效率"
- "我的提示词质量怎么样？"
- "帮我看看我的 AI 使用习惯"
- "有什么沟通上可以改进的？"
- 任何隐含"评估/改善我与 AI 交互质量"的需求

## 2. 数据源：chatSessions

### 2.1 路径自动检测

VS Code 将 Copilot Chat 会话持久化在 `workspaceStorage` 的 `chatSessions/` 子目录中。路径因操作系统不同：

| OS | 路径 |
|----|------|
| Windows | `%APPDATA%/Code/User/workspaceStorage/{ws_id}/chatSessions/` |
| macOS | `~/Library/Application Support/Code/User/workspaceStorage/{ws_id}/chatSessions/` |
| Linux | `~/.config/Code/User/workspaceStorage/{ws_id}/chatSessions/` |

**注意**：VS Code Insiders 用 `Code - Insiders` 替换 `Code`。Remote SSH 用 `.vscode-server`。

### 2.2 JSONL 增量 Patch 格式

每个 `.jsonl` 文件是一个会话的增量记录。**格式未公开文档化，可能随 VS Code 版本变更**。

当前已知结构（2026-05 验证）：

```
Line 0:  {"kind": 0, "v": {"sessionId": "...", "creationDate": 1715...}}   ← 头
Line N:  {"kind": 1, "k": ["customTitle"], "v": "会话标题"}                 ← 元数据 patch
Line N:  {"kind": 1, "k": ["requests", 0, "completionTokens"], "v": 12345} ← token 统计
Line N:  {"kind": 2, "k": ["requests"], "v": [{...}]}                      ← 用户请求（核心）
Line N:  {"kind": 2, "k": ["requests", 0, "response"], "v": [...]}         ← Agent 响应追加
```

**关键**：用户消息在 `kind=2, k=["requests"]` 的 `v` 数组中，每个元素的 `message.text` 是用户输入。

### 2.3 数据完整性问题

已知的数据缺失场景：

1. **VS Code 自动清理**：历史数据可能被清理，导致只能看到最近 N 个月
2. **多设备不同步**：如果用户在多台电脑上使用 VS Code，每台只有本地数据
3. **格式变更**：VS Code 更新可能改变 JSONL 结构，需要容错解析
4. **空会话**：打开但未使用的会话文件（`kind=0` 后无 `kind=2`）
5. **completionTokens 缺失**：部分旧版本的会话不记录 token 数

**处理策略**：
- 解析失败的行跳过并计数，在报告中报告数据健康度
- Token 数为 0 时标注"不可用"而非假装没消耗
- 时间跨度在报告中明确声明

## 3. 分析维度

### 维度 1：基础统计画像

| 指标 | 说明 | 诊断意义 |
|------|------|---------|
| 每会话消息数 | 中位数 + 平均值 | <2 = 高委托型，>10 = 可能在反复调试 |
| 每消息 Response Parts | Agent 每次响应的复杂度 | 高 RP = Agent 在做大量探索 |
| 消息长度分布 | 四档：<50 / 50-200 / 200-500 / >500 | 200-500 区间缺失 = "中等任务表达盲区" |
| Token 消耗 | 总量 + 按任务类型分布 | 找出最"烧钱"的任务类型 |

### 维度 2：提示词质量评估

用启发式关键词匹配评估三个质量维度（准确率约 70-80%）：

- **具体度**：是否说了做什么、怎么做、做到什么程度
- **上下文**：是否提供了背景、引用了文件、给了示例
- **约束明确性**：是否指定了格式、范围、技术栈

### 维度 3：会话轨迹分类

按 RP 变化趋势分类每个会话：
- **收敛型**：RP 递减——用户越来越精准
- **发散型**：RP 递增——scope creep 信号
- **平稳型**：RP 波动不大
- **单轮/双轮**：快速任务或放弃
- **空会话**：打开未使用

### 维度 4：时段 × 质量矩阵

按小时统计消息质量，回答"几点钟的 prompt 最好"。

### 维度 5：口头禅指纹

提取高频动词、填充词、语气增强词，计算模糊动词占比。

### 维度 6：重做税（Redo Tax）

检测"重新""再来""不对"等关键词，量化浪费的 RP 占比。

### 维度 7：会话节奏

消息间隔时间分布，区分快速连发 vs 深思后追问 vs 长暂停。

## 4. 执行流程

### Step 1: 环境检测

```
1. 自动检测 VS Code workspaceStorage 路径（跨平台）
2. 列出所有含 chatSessions/ 的工作区
3. 识别当前工作区（按最近修改时间）
4. 报告数据概况：几个工作区、多少会话文件、总大小
```

如果路径检测失败，提示用户手动指定。

### Step 2: 数据解析

```
1. 遍历 chatSessions/*.jsonl
2. 按 kind/k/v 结构提取用户消息、时间戳、模型、Agent、RP、Token
3. 跳过解析失败的行，记录错误数
4. 输出数据健康度报告
```

### Step 3: 七维分析

按维度 1-7 依次执行分析。每个维度独立，某个维度数据不足不影响其他维度。

### Step 4: 报告生成

输出结构：

```markdown
# Copilot Chat 深度洞察报告
> 元数据（日期、范围、会话数、消息数）

## 0. 数据健康度
## 1. 会话轨迹分类
## 2. 时段 × 质量矩阵
## 3. 口头禅指纹
## 4. 重做税
## 5. 会话节奏
## 6. 综合效率画像
## 7. 可操作建议（基于实际数据个性化生成）
```

### Step 5: 对比分析（可选）

如果用 `--all` 模式，追加全局其他工作区的同维度分析，与当前工作区对比。

## 5. 核心脚本

分析器脚本位于本 Skill 目录下：

| 文件 | 用途 |
|------|------|
| `analyze.py` | 主分析脚本（可独立运行） |
| `report_html.py` | HTML 可视化报告生成器（Chart.js CDN） |
| `SKILL.md` | 本文件——Skill 说明 |

### 运行方式

```bash
# 当前工作区
python analyze.py

# 全部工作区 + 对照分析
python analyze.py --all

# 指定工作区 ID
python analyze.py --ws <workspace_id>

# 同时输出 JSON 原始数据
python analyze.py --all --json

# 生成 HTML 可视化报告（带 Chart.js 交互图表）
python analyze.py --html

# 全局分析 + HTML + JSON 全量输出
python analyze.py --all --html --json
```

### 环境要求

- Python 3.8+
- 无第三方依赖（仅用 stdlib）
- VS Code 已使用 Copilot Chat（需要有 chatSessions 数据）

## 6. 已知局限与应对

| 局限 | 影响 | 应对 |
|------|------|------|
| 启发式质量评估 | 准确率 ~70-80% | 报告中标注"基于关键词启发式"，不作为精确度量 |
| Response Parts ≠ 真实工作量 | 多工具并发调用会膨胀 RP | 同时看中位数和平均值 |
| 分类器"其他"占比高 | 33-51% 消息被归为"其他" | 后续可考虑用 LLM 做精确分类 |
| JSONL 格式可能变更 | 新版 VS Code 可能改结构 | 容错解析 + 报告健康度 |
| 单设备数据 | 无法跨设备聚合 | 在报告中声明数据范围 |

## 7. 健壮性保障（v3.1 新增）

| 场景 | 处理方式 |
|------|----------|
| 大文件（>200MB） | 跳过并警告，不影响其他文件解析 |
| 权限不足 | 友好提示，继续处理其他可访问目录 |
| 编码异常 | 尝试 utf-8 → utf-8-sig → latin-1 多级 fallback |
| 时间戳异常值 | 过滤负值和超2100年的时间戳 |
| 零除操作 | 所有分母操作使用 safe_div 保护 |
| 空数据 | 任何维度数据不足时降级输出而非崩溃 |
| 大量文件 | 每 50 文件显示进度反馈 |
| 单文件解析异常 | 隔离异常，跳过此文件继续其他 |

## 8. 迭代路线

```
v1: 本地脚本，七维分析，Markdown 报告
v3: 增强分析维度，会话轨迹/口头禅/重做税/节奏
v3.1 (当前): 
  ✔ 健壮性增强（大文件/编码/权限/零除全场景保护）
  ✔ HTML 可视化报告（Chart.js 交互图表，12 个图表 + KPI 仪表盘）
  ✔ 进度反馈（大数据量时显示解析进度）
    ↓
v4 (计划):
  - 用 LLM 替代关键词启发式做质量评估（更准确）
  - 纵向趋势追踪（月度对比）
    ↓
v5 (远期):
  - VS Code 扩展形态（侧边栏实时仪表盘）
  - 团队级匿名聚合分析
  - 个性化提示词推荐引擎
```

## 9. 隐私声明

- 所有数据分析在本地完成，不上传任何信息
- 分析脚本不联网，不调用任何 API
- 报告中的消息预览会脱敏（替换 URL、User ID）
- 用户可随时删除生成的报告文件
