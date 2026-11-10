---
title: "Ch1: 跑通你的第一个 Agent"
tags: [教程, 入门, hands-on, spiral-1]
date: 2026-04-12
status: completed
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../ARCHIVE_POLICY.md)阅读。

# Chapter 1: 跑通你的第一个 Agent

> 📍 前置：无。这是起点。
> 🎯 完成本章后你能：在自己电脑上跑通一个能自动搜集信息的 AI Agent
> ⏱️ 预计时间：10 分钟阅读 + 30 分钟动手

---

## 为什么从这里开始？（WHY）

David Perkins 在《Making Learning Whole》里说过一个概念叫 **elementitis（零件病）**：传统教育总是先教你所有零部件——语法、算子、矩阵乘法——然后才让你做一个完整的东西。结果大部分人在学零件的时候就放弃了，因为不知道这些零件拼起来是什么。

fast.ai 的解药是 **"先玩完整游戏"（Whole Game）**：小孩学棒球是先去打几局，体会投球、跑垒、接球是怎么回事，然后才去练习挥棒姿势。不是先练三年挥棒才第一次上场。

所以这个教程的第一章不是"什么是 LLM"、不是"Transformer 架构"、不是"ReAct 论文解读"。

**第一章是：装一个 Agent，让它干一件事，你看到结果。**

---

## 你要做的事（WHAT）

你即将搭建的系统长这样：

```
你的电脑
  ├── OpenClaw (Agent 运行时)     ← 就像操作系统，管理 Agent 的一切
  │   ├── Agent (AI 大脑)         ← 一个 LLM + 一套行为规则
  │   ├── Skill (Agent 的技能)    ← 告诉 Agent "怎么做某件事"
  │   └── Tool (Agent 的手脚)     ← web_fetch、文件读写等
  │
  └── 通义千问 API (远程大脑)      ← 提供推理能力
```

用一个类比：你要雇一个远程实习生。
- **OpenClaw** 是他的工位（电脑、网络、文件系统）
- **通义千问 API** 是他的大脑（会思考、会理解指令）
- **AGENTS.md** 是入职培训手册（"你是谁、你的职责是什么"）
- **SKILL.md** 是工作 SOP（"怎么搜集 AI 新闻、输出什么格式"）

你要做的就是：搭工位 → 接大脑 → 写培训手册 → 写 SOP → 让他开始干活。

---

## 动手做（HOW）

### Step 1: 安装 OpenClaw（搭工位）

打开 PowerShell：

```powershell
# 检查 Node.js 版本（需要 v18+）
node --version

# 没有的话去 https://nodejs.org 下载 LTS 版本

# 安装 OpenClaw
npm install -g openclaw

# 验证
openclaw --version
```

### Step 2: 获取通义千问 API Key（接大脑）

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录 → "API-KEY 管理" → 创建 Key
3. 新用户有免费额度，足够学习

> 💡 为什么选通义千问？零成本起步。对初学者来说，**能跑起来**比选最强的模型重要 1000 倍。

### Step 3: 初始化并配置

```powershell
# 初始化 OpenClaw
openclaw init
```

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "models": {
    "default": {
      "provider": "qwen",
      "model": "qwen3.5-plus",
      "apiKey": "你的API_KEY",
      "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }
  }
}
```

### Step 4: 写 Agent 的"灵魂"（培训手册）

编辑 `~/.openclaw/workspace/AGENTS.md`：

```markdown
# 我的第一个 AI Agent

你是一个 AI 研究助手，帮我追踪 AI 领域的最新进展。

## 核心规则
- 使用中文输出
- 引用来源附上 URL
- 不确定的信息标注"待验证"
```

就这么几行。这就是你的 Agent 的行为边界定义。

### Step 5: 写第一个 Skill（工作 SOP）

创建 `~/.openclaw/workspace/skills/ai-news/SKILL.md`：

```markdown
# AI 新闻速报

## 触发方式
- 手动: "搜索 AI 新闻"

## 执行步骤

### 1. 搜索热门 AI 新闻
使用 browser 工具访问：
- https://news.ycombinator.com/（筛选 AI 相关标题）
- https://github.com/trending（筛选 AI/ML 项目）

收集：标题、URL、简短描述、热度指标

### 2. 筛选 TOP 5
- 优先有实际创新的项目
- 排除纯营销或重复报道

### 3. 输出报告
写入 `workspace/reports/YYYY-MM-DD-ai-news.md`，格式：

# AI 新闻速报 — YYYY-MM-DD
## TOP 5
### 1. 标题（原稿引用文件未随本次归档发布）
- 热度: ⭐⭐⭐
- 简评: 一句话

## 趋势观察
一段话总结今天的趋势
```

### Step 6: 启动！

```powershell
# 终端 1：启动 Gateway
openclaw gateway --force --verbose

# 终端 2：触发 Agent
openclaw agent --message "搜索 AI 新闻"
```

然后等待。你会看到 Agent：
1. 读取 AGENTS.md（理解自己是谁）
2. 匹配 SKILL.md（知道该做什么）
3. 调用 web_fetch（去搜信息）
4. 生成报告文件（输出结果）

```powershell
# 查看结果
Get-ChildItem ~/.openclaw/workspace/reports/
cat ~/.openclaw/workspace/reports/*ai-news*
```

**🎉 恭喜。你的第一个 Agent 刚刚完成了它的第一份工作。**

### Step 7: 加上自动化（选做）

让它每天早上自动执行：

编辑 `~/.openclaw/cron/jobs.json`：

```json
[
  {
    "id": "daily-ai-news",
    "cron": "0 8 * * *",
    "message": "搜索 AI 新闻",
    "session": "isolated"
  }
]
```

重启 Gateway，Agent 从此每天 8:00 自动工作。

---

## 停下来想想：你刚才做了什么？

花几分钟回顾一下，你在 30 分钟内搭建的东西，分别对应 Agent 领域的哪些概念。现在不需要记住这些术语——但下一章我们会深入：

| 你做的事 | 它叫什么 | 你暂时不需要知道的 |
|---------|---------|------------------|
| 安装 OpenClaw | 安装 Agent Runtime | 为什么要有 Runtime？用 Python 脚本行不行？ |
| 配置 API Key | 接入 LLM 推理层 | 不同模型的差异？怎么选？ |
| 写 AGENTS.md | 定义 System Prompt | 怎么写才能让 Agent 真正听话？（Ch7） |
| 写 SKILL.md | 定义 Skill 模块 | Skill 的设计哲学是什么？（Ch7） |
| Agent 自动搜索+生成报告 | ReAct 循环 | 循环是怎么运转的？（**Ch2 马上讲**） |
| 配置 Cron | L3 级部署 | 生产级部署长什么样？（Ch11） |

---

## 三种开发模式预告

你刚才用的是 OpenClaw（一个 Agent Runtime）。但 Agent 开发不止这一条路。整个教程中你会接触到三种模式：

| 模式 | 类比 | 代表 | 你在哪里学 |
|------|------|------|-----------|
| **IDE 模式** | 开别人的车——你坐副驾驶，Agent 开车 | VS Code Copilot、Cursor | Ch1（你刚做的） |
| **SDK 模式** | 买发动机装自己的车——Agent 是你应用的引擎 | Claude Agent SDK、OpenAI SDK | Ch4（从零搭 Agent） |
| **CLI 模式** | 叫出租车——给指令等结果 | Claude Code CLI、OpenClaw | Ch11（批量自动化） |

**核心区别在于"谁是主体"**：IDE 模式下 Agent 是同事，SDK 模式下 Agent 是引擎，CLI 模式下 Agent 是命令执行者。

现在不需要纠结选哪个——先跑通整个教程，Ch4 和 Ch10 会让你对三种模式都有手感。详见 [SDK-vs-IDE-vs-CLI三种Agent开发模式对比研究](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R29_SDKvsIDEvsCLI%E4%B8%89%E7%A7%8DAgent%E5%BC%80%E5%8F%91%E6%A8%A1%E5%BC%8F.md)。

---

## 检查点

回答以下问题。能回答就说明你真学到了东西：

1. **Agent 和直接调 ChatGPT API 的区别是什么？**（提示：你的 Agent 做了不止一步的事情）
2. **AGENTS.md 和 SKILL.md 分别控制 Agent 的什么？**（提示：一个是"你是谁"，一个是"你怎么做"）
3. **如果 Agent 搜索某个网页失败了，它会怎么办？**（提示：你在 SKILL.md 里写了"跳过不报错"）

> 如果你回答不上来第 1 题，不用担心——**Chapter 2 就是为了回答这个问题**。

---

## 深入阅读（IF）

以下是相关研究报告，如果你现在就想深挖，可以去看。但完全可以先跳过，学完后面的章节再回来。

| 想了解的 | 去看 |
|---------|------|
| Hello World 的完整版（更多细节和故障排除） | [Agent-Hello-World实践教程](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R25_AgentHelloWorld%E5%AE%9E%E8%B7%B5%E6%95%99%E7%A8%8B.md) |
| Agent 四大能力的理论框架 | [Agent架构深度研究报告](../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) §1.3 |
| 部署级别的完整光谱（L0-L8） | [Agent部署上线方案全景调研报告](../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R04_Agent%E9%83%A8%E7%BD%B2%E4%B8%8A%E7%BA%BF%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) |
| SKILL.md 格式的来历和设计哲学 | Agent-Skills与LLM-Wiki生态调研报告（原稿交叉引用，本归档未解析） |

---

> **下一章预告**：你的 Agent 跑起来了，但你可能心里嘀咕——"它到底是怎么做到的？'搜索 AI 新闻'这几个字，怎么就变成了一连串的搜索→筛选→生成报告？" Chapter 2 拆开这个黑盒。
