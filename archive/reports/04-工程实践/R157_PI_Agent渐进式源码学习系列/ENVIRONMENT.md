> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../../ARCHIVE_POLICY.md)阅读。

# PI Agent 学习系列：环境清单

> 结论：本系列实验只依赖本机随 Codex 提供的 Node.js 24，默认不安装 npm 包、不调用真实模型 API，因此可以离线、确定性地复现。

| 依赖 | 版本 / 位置 | 用途 | 可达性 |
|---|---|---|---|
| PI 源码 | `work/pi`，提交 `063fb963c5c33d099faa593d17e60e0a875430cd` | 源码对照 | 已验证：Git 工作树存在且提交可读取 |
| 上游仓库 | `https://github.com/earendil-works/pi` | 来源追溯 | 已验证：本地 clone 的 `origin` 指向该地址；课程不依赖实时网络 |
| Node.js | `C:/Users/USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`，v24.14.0 | 原生运行 TypeScript 与 `node:test` | 已验证：A1/A2 通过 |
| TypeScript checker | `typescript@5.9.3`，通过一次性 `npm exec` 调用 | 最终严格静态检查，不是 Lab 运行依赖 | 已验证：2026-07-31 `tsc --strict --noEmit` 通过 |
| 外部模型 API | 无 | 用确定性 `ScriptedModel` 替代 | 不需要网络、Key 或 Token 成本 |
| 第三方 npm 包 | 无 | 降低环境摩擦 | 不需要安装 |

## 运行约定

- 文档中的 `$NODE` 指上表的 Node.js 绝对路径。
- PI 上游自身要求 Node.js `>=22.19.0`；系统默认 Node.js v22.14.0 不满足，因此实验显式使用 v24.14.0。
- Node 24 对 `--eval` 中的 TypeScript 要使用 `--input-type=module-typescript`；普通 `module` 不会剥离类型。课程正式测试直接运行 `.ts` 文件，不受这个差异影响。
- 实验只模拟协议和控制流，不声称模拟模型质量、供应商流式传输细节或真实 Token 计费。
- `npm exec` 仅用于作者最终 QA，未向 Lab 写入 `node_modules` 或依赖锁；学习主路径仍可完全离线运行。
