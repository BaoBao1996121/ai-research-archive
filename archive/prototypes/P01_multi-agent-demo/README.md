> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Multi-Agent 最小原型

> 关联报告：[AI-Agent学习路线与项目整合全景报告](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R23_AIAgent%E5%AD%A6%E4%B9%A0%E8%B7%AF%E7%BA%BF%E4%B8%8E%E9%A1%B9%E7%9B%AE%E6%95%B4%E5%90%88.md) G-E
> 关联理论：[Agent架构深度研究报告](../../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R03_Agent%E6%9E%B6%E6%9E%84%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6.md) → 多 Agent 编排模式
> 关联模式：[Google ADK五大Agent技能设计模式研究报告](../../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R06_GoogleADK%E4%BA%94%E5%A4%A7Agent%E6%8A%80%E8%83%BD%E8%AE%BE%E8%AE%A1%E6%A8%A1%E5%BC%8F.md) → Delegate / Sequential

## 概述

演示 **Collector → Researcher → Reporter** 三 Agent 协作模式，用 Python + OpenAI API 实现最小可运行版本。

## 架构

```
用户请求
  ↓
Orchestrator (调度器)
  ├── Collector Agent: 采集信号（模拟 GitHub 搜索）
  ├── Researcher Agent: 深度分析（对高分项目做深入研究）
  └── Reporter Agent: 生成报告（整合成结构化文档）
```

## 运行方式

```bash
# 设置环境变量
set OPENAI_API_KEY=<your-key>
set OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 运行
python multi_agent_orchestrator.py
```

## 设计要点

1. **Agent 即函数**：每个 Agent 是一个带 system prompt + 工具定义的函数调用
2. **消息传递**：Agent 之间通过结构化 JSON 传递数据
3. **Orchestrator 模式**：调度器决定调用顺序和数据流向
4. **可观测性**：每步打印调用日志，便于学习理解

## 与龙虾项目的关系

龙虾当前是单 Agent + 多 Skill 模式。本原型演示了如何将其进化为多 Agent 协作模式，
其中 Collector 对应 github-ai-researcher skill，Researcher 对应 deep-research 能力。
