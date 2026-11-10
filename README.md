# AI 研究与实践归档

从 RAG、Agent、记忆与上下文，到模型基础、评估、部署和源码学习。这是个人 Obsidian 技术积累的公开历史归档，保留长篇研究、教程、方法与原型，方便读者沿着问题查找和比较。

本轮收录 **378 份 Markdown 文档 + 125 个配套代码或配置文件**，于 **2026-11-10** 发布。原稿的日期和探索过程保留在文中；Git 提交采用真实发布时间。材料包含 AI 辅助研究和整理，个人归纳、上游观点及原稿中的实验结论需要结合证据阅读。

## 按主题找内容

| 专题 | 文档数（可交叉） |
|---|---:|
| [RAG 与检索](topics/rag.md) | 33 |
| [Agent 架构与编排](topics/agent.md) | 152 |
| [记忆、知识与上下文](topics/memory.md) | 29 |
| [评估、质量与安全](topics/evaluation.md) | 24 |
| [模型基础与训练](topics/models.md) | 27 |
| [部署与工程工具](topics/engineering.md) | 117 |

[全部文档目录](CATALOG.md) · [原目录浏览](archive/) · [范围与阅读状态](ARCHIVE_POLICY.md) · [逐文件来源与校验值](manifest.json)

## 建议的阅读顺序

1. 想系统学习：从 [教程](archive/tutorial/) 入手，再按专题找长篇材料。
2. 想理解 RAG：读 RAG 专题，再看 [RAG 教学原型](archive/prototypes/P07_rag-fullstack-lab/README.md)。
3. 想学开源 Agent 的实现：看 [PI Agent 渐进式源码学习系列](archive/reports/04-工程实践/R157_PI_Agent渐进式源码学习系列/README.md)。
4. 想拿方法解决问题：浏览 [方法与 Skill 历史稿](archive/skills/)，根据自己的环境取用。

## 与精选仓库的关系

| 仓库 | 用途 |
|---|---|
| [AI Agent 学习笔记](https://github.com/BaoBao1996121/ai-agent-notes) | 从概念与练习开始，阅读篇幅较短 |
| [Agent 工程方法手册](https://github.com/BaoBao1996121/agent-engineering-playbook) | 已整理的选型、源码分析和交接模板 |
| [Agent 优化实验室](https://github.com/BaoBao1996121/agent-evolution-lab) | 带历史结果与离线复算入口的实验 |
| 本仓库 | 更完整的历史研究、长篇教程、方法和原型资料 |

## 阅读边界

这是历史材料归档。多数文档仅经过程序扫描，部分做了风险上下文审阅，少量全文已读；具体状态在每篇开头及来源清单中标明。本轮没有逐项复核时效性、重新执行所有代码或复现实验。原文的“已验证”“生产级”等表述只代表当时的记录，不等于本次确认。

内部工作材料、私人记录、凭据、会话转录、第三方源码副本及来源待核的内容不在本公开归档内。部分关联材料或附件未发布，原链接已改为明确的缺失说明。代码是历史配套快照，可能缺少环境、私有依赖或其他文件，不保证可以直接运行。

发现问题欢迎提交 Issue，附文档位置和可核验来源。公开可读不代表上游权利转移；本仓库未给全部内容授予统一的开源许可，参见[内容与权利说明](CONTENT_POLICY.md)。
