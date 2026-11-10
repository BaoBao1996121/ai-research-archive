---
title: 端到端 Agent 测试报告
aliases: [R11, 端到端测试, E2E测试, 端到端Agent测试报告]
tags: [experiment, e2e, agent, testing, pipeline]
date: 2026-04-10
category: 实验验证
report_id: R11
tokens: 1267
status: completed
related:
  - "[意图到工作流实验报告](R10_%E6%84%8F%E5%9B%BE%E5%88%B0%E5%B7%A5%E4%BD%9C%E6%B5%81%E5%AE%9E%E9%AA%8C.md)"
  - "[代码检索能力实验报告](R07_%E4%BB%A3%E7%A0%81%E6%A3%80%E7%B4%A2%E8%83%BD%E5%8A%9B%E5%AE%9E%E9%AA%8C.md)"
  - "Claude-Code源码上下文策略实验报告（原稿交叉引用，本归档未解析）"
prev_path: reports/端到端Agent测试报告.md
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# 实验6: 端到端 Agent 测试 — 管道上下文质量验证

## 实验目的

验证**检索管道输出的上下文是否足够让 Agent 正确理解代码并完成任务**。

这是整个研究中最关键的一个验证——前5个实验证明了"能找到文件"，但找到以后 Agent 真的能干活吗？

## 测试设计

### 查询
```
BashTool 执行命令时的权限检查是怎么工作的？
我想添加一条安全规则，禁止执行 rm -rf / 这样的危险命令
```

### 管道输出
| 指标 | 值 |
|------|-----|
| 检索 Top-1 | tools/BashTool/BashTool.tsx (score=1335.8) ✅ 正确 |
| 检索 Top-2 | tools/BashTool/bashPermissions.ts (score=1272.0) ✅ 正确 |
| 工作流文件数 | 55 个 |
| 工作流总 token | ~71,017 |
| Context 总字符 | 228,499 (~57K tokens) |
| 管道耗时 | 索引构建 3.57s + 检索 <0.1s |

### 测试方法
- 启动一个 **Explore subagent**
- 只告诉它管道检索到的文件列表和角色描述
- 让它自己去读取这些文件
- 回答 3 个问题
- 我用 ground truth（直接精读源码）来验证它的回答

---

## 评估结果

### 问题1: 权限检查流程描述

**Agent 的回答** 描述了一个 8 步流程图：
```
AST解析 → 沙箱检查 → 精确匹配 → 分类器 → 命令分割+前缀匹配 → 路径检查 → sed检查 → 只读检查
```

**Ground Truth 验证**：

| Agent 描述的步骤 | 是否正确 | 验证 |
|------------------|---------|------|
| (0) AST 安全解析 parseCommandRaw → parseForSecurityFromAst → checkSemantics | ✅ 完全正确 | bashPermissions.ts:1681-1695 |
| (1) too-complex → checkEarlyExitDeny → ask | ✅ 正确 | bashPermissions.ts:1731-1747 |
| (1b) simple 但语义不安全 → checkSemanticsDeny | ✅ 正确 | bashPermissions.ts:1753-1768 |
| 沙箱自动允许 checkSandboxAutoAllow | ✅ 正确 | bashPermissions.ts:1830-1840 |
| 精确匹配 bashToolCheckExactMatchPermission | ✅ 正确 | bashPermissions.ts:1844 |
| 分类器 classifyBashCommand | ✅ 正确 | bashPermissions.ts:1855-1945 |
| 路径检查 checkDangerousRemovalPaths | ✅ 正确 | pathValidation.ts:59-90 |
| stripSafeWrappers 去除包装器 | ✅ 正确 | bashPermissions.ts:625 |

**但遗漏了**：
- Shadow Mode 分支（tree-sitter 影子测试逻辑）—— 这是内部 A/B 测试细节，不影响主流程
- 复合命令的 `commandOperatorResult` 管道处理 —— Agent 提到了 `splitCommand` 但没展开管道 `|` 的递归处理

**流程准确度：~90%**。主干流程完全正确，遗漏了一些二级分支。

---

### 问题2: 修改方案建议

**Agent 给了 3 个方案**：

| 方案 | Agent 建议 | Ground Truth 验证 |
|------|-----------|------------------|
| 方案A: 现有 checkDangerousRemovalPaths 已存在 | ✅ **完全正确** | pathValidation.ts:59-90 确实已存在此函数，调用 isDangerousRemovalPath() |
| 方案B: 用户配置 deny 规则 | ✅ 正确 | 规则系统确实支持 `Bash(rm -rf /:deny)` 格式 |
| 方案C: 加强 isDangerousRemovalPath 黑名单 | ✅ 正确方向 | 该函数在 utils/permissions/pathValidation.js 中 |

**关键发现**：Agent 准确识别到 **现有代码已经有 `checkDangerousRemovalPaths()` 函数**来处理这个场景！这意味着 Agent 不仅理解了代码结构，还能判断"不需要新加功能，现有机制已覆盖"。

**方案准确度：~95%**。

---

### 问题3: 变体覆盖分析

这里有一个**关键错误**需要记录：

| 变体 | Agent 判断 | Ground Truth | 是否正确 |
|------|-----------|-------------|---------|
| `rm -rf /` | ✅ checkDangerousRemovalPaths 拦截 | ✅ 正确 | ✅ |
| `rm -rf /*` | ✅ 路径验证捕获 | ✅ 正确 | ✅ |
| **`sudo rm -rf /`** | ❌ "stripAllLeadingEnvVars 去除 sudo" | **错误！** sudo 不是环境变量！ | ❌ |
| `timeout 5 rm -rf /` | ✅ stripSafeWrappers 去除 timeout | ✅ 正确(SAFE_WRAPPER_PATTERNS) | ✅ |
| `FOO=bar rm -rf /` | ✅ stripAllLeadingEnvVars | ✅ 正确(deny/ask 规则时) | ✅ |
| `nohup rm -rf /` | ✅ stripSafeWrappers | ✅ 正确 | ✅ |
| `nice rm -rf /` | ✅ stripSafeWrappers | ✅ 正确 | ✅ |
| `echo a && rm -rf /` | ✅ splitCommand 分割 | ✅ 正确 | ✅ |
| `sh -c 'rm -rf /'` | ⚠️ AST too-complex | ✅ 正确 | ✅ |
| `eval rm -rf /` | ⚠️ checkSemantics 阻止 | ✅ 正确 | ✅ |

#### 关于 `sudo rm -rf /` 的详细分析

**Agent 的错误**：声称 `stripAllLeadingEnvVars()` 能去除 `sudo` 前缀。这是错误的——`sudo` 不是 `VAR=value` 格式的环境变量赋值，`stripAllLeadingEnvVars` 的正则 `ENV_VAR_PATTERN` 不会匹配它。

**实际处理路径**：
1. `sudo` 在 `BARE_SHELL_PREFIXES` 集合中（bashPermissions.ts:223），所以 **`sudo:*` 型规则不会被建议给用户**
2. `sudo` **不在** `SAFE_WRAPPER_PATTERNS` 中，所以 `stripSafeWrappers` 不会剥离它
3. 实际路径：AST 解析 → `stripWrappersFromArgv`（pathValidation.ts:894/1263）**也不剥离 sudo**
4. 最终 `sudo rm -rf /` 作为整体命令，baseCmd 是 `sudo`，不在 `SUPPORTED_PATH_COMMANDS` 中
5. 所以 **`sudo rm -rf /` 不会触发 `checkDangerousRemovalPaths`**！
6. 它最终走到默认的 "ask" 路径——因为没有 allow 规则匹配

**这是一个很好的测试结果**：Agent 在10个变体中错了1个，而且错的这个恰好暴露了一个**真实的安全边界问题**——`sudo` 命令确实是权限系统的一个盲区。

**变体分析准确度：90%（9/10 正确）**

---

## 总体评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **流程理解** | ★★★★☆ (90%) | 主干流程完全正确，遗漏影子模式等二级分支 |
| **修改方案** | ★★★★★ (95%) | 准确识别现有机制已覆盖，给出3个层次的方案 |
| **变体分析** | ★★★★☆ (90%) | 10个变体中9个正确，sudo 处理机制判断错误 |
| **代码引用** | ★★★★☆ (85%) | 函数名、行号大部分正确，个别行号有偏差 |
| **综合质量** | ★★★★☆ (90%) | Agent 基于管道上下文能有效完成开发任务 |

---

## 结论

### 管道上下文质量验证通过 ✅

**检索管道输出的 55 个文件 / 71K tokens 上下文，足以让 Agent：**

1. ✅ 正确描述一个 2000+ 行复杂函数的 8 步执行流程
2. ✅ 准确识别"已有机制已覆盖此场景"（不需要新功能）
3. ✅ 分析 10 个命令变体中 9 个的处理路径
4. ✅ 给出具体的文件名、函数名、行号引用

**关键缺陷（1个）：**
- `sudo rm -rf /` 的处理机制判断错误，混淆了环境变量剥离和命令包装器剥离

**根因分析**：
这个错误源于 bashPermissions.ts 有 2200+ 行，权限检查涉及多个相互关联的函数（stripSafeWrappers, stripAllLeadingEnvVars, stripWrappersFromArgv, BARE_SHELL_PREFIXES），理解它们各自的边界需要交叉阅读多个代码片段。管道提供了所有相关文件，但 Agent 在**多函数交叉逻辑推理**上犯了错。

这不是检索的问题，是 LLM 推理深度的问题。

### 对比："无管道直接搜索" vs "管道上下文"

| 能力 | 无管道（Agent 自由搜索） | 有管道（55 文件上下文） |
|------|------------------------|----------------------|
| 定位核心文件 | 需要多轮 grep/search（~30s） | 管道直接给出 Top-1 命中（<0.1s） |
| 发现同目录模块 | 需要 list_dir + 逐个读取 | 圈层1 自动包含 |
| 发现依赖关系 | 需要手动追踪 import 链 | 圈层2 按 PageRank 排序提供签名 |
| 发现消费者 | 几乎不可能主动做 | 圈层3 列出 10 个消费者 |
| 总耗时 | 5-15 分钟（多轮交互） | 3.6s 索引 + <0.1s 检索 |

---

## 附录: Subagent 被提供的信息 vs 其回答质量

```
输入:
  - 55 个文件的名称 + 角色描述
  - 被告知可以去读取这些文件
  - 1 个具体的开发问题

输出:
  - 8 步权限检查流程图 (90% 准确)
  - 3 个修改方案 (95% 准确)  
  - 10 个变体处理分析 (90% 准确)
  - 具体的代码引用 (85% 准确)

综合: 管道上下文 → Agent 可有效工作 ✅
```
