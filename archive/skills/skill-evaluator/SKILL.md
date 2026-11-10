---
name: skill-evaluator
description: >
  Evaluates Skill and Agent quality through rule-based assertions and optional LLM-as-Judge.
  Use when: iterating on a Skill/Prompt and need to know if changes improved or degraded quality;
  checking if a SKILL.md follows best practices; comparing two versions of Agent output;
  running regression tests on Skill changes.
applyTo: "skills/**"
---

> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：risk_context_review（发布前程序扫描并重点审核风险上下文）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# Skill Evaluator

> 为 Skill 和 Agent 的迭代提供可量化的评估反馈回路。

### Overview

本 Skill 实现了 [Skill与Agent评估方案全景调研报告](../../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R15_Skill%E4%B8%8EAgent%E8%AF%84%E4%BC%B0%E6%96%B9%E6%A1%88%E5%85%A8%E6%99%AF.md) 中设计的最小可行评估系统。
核心理念来自 [Anthropic官方Skill-Creator设计哲学研究报告](../../reports/01-%E7%90%86%E8%AE%BA%E4%B8%8E%E6%9E%B6%E6%9E%84/R14_AnthropicSkillCreator%E8%AE%BE%E8%AE%A1%E5%93%B2%E5%AD%A6.md)：**先建立确定性基线（纯规则），再叠加 LLM-Judge。**

评估系统由三层组成：
- **Skill（本文件）** = 方法论 — 定义评估工作流和何时触发
- **脚本（run_eval.py）** = 执行力 — 跑测试、算分、对比版本
- **数据（test_cases/*.json）** = 记忆力 — 测试用例集和历史基线

## 1. 评估命令（Step-by-step 执行流程）

### Step 1: Skill 文档质量检查（纯规则，无需 API）

```bash
python skills/skill-evaluator/run_eval.py check-skill skills/knowledge-base-organizer
```

检查维度（基于 Anthropic Skill-Creator 最佳实践）：
- 结构完整性：frontmatter、触发条件、执行流程
- 描述质量：是否解释 Why（而非堆砌 MUST）、是否具体可执行
- 配套资源：是否有 companion scripts

### Step 2: 输出断言评估（纯规则，无需 API）

```bash
python skills/skill-evaluator/run_eval.py eval test_cases/knowledge_base_organizer.json
```

对预录的 Skill/Agent 输出运行确定性断言。断言类型：
`contains`, `not_contains`, `regex_match`, `min_length`, `max_length`,
`has_sections`, `has_code_block`, `json_valid`, `word_count_range`, `starts_with`

### Step 3: LLM-as-Judge 评估（需要 API）

```bash
python skills/skill-evaluator/run_eval.py judge test_cases/knowledge_base_organizer.json
```

对每个测试用例的 `llm_criteria` 用 LLM 打分（1-5 分）。
支持任何 OpenAI 兼容 API（推荐通义千问 qwen-plus）。

### Step 4: 版本对比

```bash
python skills/skill-evaluator/run_eval.py compare result_v1.json result_v2.json
```

自动计算 pass rate 变化、逐 case 回归/提升分析、LLM 分数变化，输出 verdict。

## 2. 评估工作流

```
修改 Skill → check-skill（秒级反馈）
         → eval test_cases（分钟级，需预录输出）
         → judge test_cases（分钟级，需 API）
         → compare old_result new_result（决策依据）
```

推荐的迭代节奏：
1. **每次修改后**：跑 `check-skill` 确保文档质量没退化
2. **关键改动后**：跑 `eval` + `judge` 生成完整评估
3. **决策时**：跑 `compare` 对比新旧版本数据，不凭感觉

## 3. 测试用例格式

```json
{
  "suite_name": "my-skill-name",
  "skill_path": "skills/my-skill",
  "test_cases": [
    {
      "id": "tc01",
      "name": "描述这个 case 测什么",
      "input": "模拟的用户输入",
      "output": "预录的 Agent 输出（可后续填入）",
      "assertions": [
        {"type": "contains", "value": "必须包含的关键词"},
        {"type": "min_length", "value": 200},
        {"type": "has_sections", "value": ["期望的章节标题"]}
      ],
      "llm_criteria": {
        "relevance": "输出是否切题？",
        "completeness": "是否覆盖所有必要步骤？"
      }
    }
  ]
}
```

## 4. API 配置（仅 LLM-Judge 需要）

设置环境变量后即可使用 `judge` 命令：

```powershell
# Windows PowerShell
$env:OPENAI_API_KEY = "EXAMPLE_API_KEY"
$env:OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:EVAL_MODEL = "qwen-plus"  # 可选，默认 qwen-plus
```

```bash
# Linux/Mac
export OPENAI_API_KEY=sk-your-qwen-key
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

## 5. 设计原则

因为每个设计决策都有原因，所以记录在这里而不是藏在代码里：

| 决策 | 为什么 |
|------|--------|
| 纯规则优先，LLM 可选 | LLM-Judge 有成本和不稳定性。确定性断言是可信基线 |
| 盲比而非打分对比 | 来自 Anthropic：直接打分有版本偏见，盲比更可靠 |
| JSON 测试用例 | 机器可读、可版本控制、可 diff |
| 无外部依赖 | 只用 Python 标准库，降低上手门槛 |
| 结果都是 JSON | 方便 compare、可视化、趋势追踪 |

## 6. 示例：完整评估流程

以下示例演示对 knowledge-base-organizer 的完整评估：

```bash
# Step 1: 检查 Skill 文档质量
python skills/skill-evaluator/run_eval.py check-skill skills/knowledge-base-organizer

# Step 2: 运行断言评估（需要预录输出）
python skills/skill-evaluator/run_eval.py eval skills/skill-evaluator/test_cases/knowledge_base_organizer.json --output results/v1.json

# Step 3: 修改 Skill 后再跑一次
python skills/skill-evaluator/run_eval.py eval skills/skill-evaluator/test_cases/knowledge_base_organizer.json --output results/v2.json

# Step 4: 对比两个版本
python skills/skill-evaluator/run_eval.py compare results/v1.json results/v2.json
```
