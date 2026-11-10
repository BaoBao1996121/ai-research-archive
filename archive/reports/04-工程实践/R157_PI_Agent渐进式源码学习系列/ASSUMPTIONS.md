> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../../ARCHIVE_POLICY.md)。

# 实现前假设验证

> 状态：3/3 通过（2026-07-31）。正式编写 `.ts` 实验代码的前置条件已满足。

| ID | 关键假设 | 失败影响 | 验证脚本 | 状态 |
|---|---|---|---|---|
| A1 | Bundled Node 版本满足 PI 的 `>=22.19.0` 约束 | 无法可信复现 PI 当前运行基线 | `work/pi-learning-spikes/verify-runtime.ps1` | ✅ v24.14.0 |
| A2 | 不安装依赖也能直接执行带类型标注的 `.ts` 片段和 `node:test` | 课程必须引入构建器，增加认知与安装成本 | `work/pi-learning-spikes/verify-native-ts.ps1` | ✅ 1/1 测试通过 |
| A3 | 确定性假模型可产生“模型→工具→模型”的完整事件序列 | 离线实验无法承载 Agent Loop 的核心学习目标 | `work/pi-learning-spikes/verify-scripted-loop.ps1` | ✅ 严格序列通过 |

## 判定标准

- 三个脚本都必须退出码为 0。
- A2 必须真实运行 TypeScript 类型标注并通过一个 `node:test` 断言。
- A3 必须得到严格顺序：`assistant(tool_call) → tool_result → assistant(stop)`。

## 执行记录

| 时间 | 结果 | 证据 / 修正 |
|---|---|---|
| 2026-07-31 | A1 通过 | 输出 `v24.14.0`，高于上游 `package.json` 的 `>=22.19.0` |
| 2026-07-31 | A2 首次失败 | Node 不允许 `--test` 与 `--eval` 同时使用；随后改为直接调用 `node:test` API |
| 2026-07-31 | A2 第二次失败 | `--input-type=module` 不处理 eval 内 TypeScript；改为 `module-typescript` |
| 2026-07-31 | A2 通过 | TAP：`tests 1, pass 1, fail 0` |
| 2026-07-31 | A3 通过 | 输出 `assistant(tool_call) -> tool_result -> assistant(stop)` |

这些失败记录会保留：它们说明“Node 支持 TypeScript”不等于“所有入口参数组合都支持 TypeScript”。
