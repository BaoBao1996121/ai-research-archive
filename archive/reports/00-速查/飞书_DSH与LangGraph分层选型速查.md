> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# 飞书入口、DSH工作台与业务流程编排：SE选型速查

日期：2026-10-23｜状态：研究建议，未做联动实验，未获选型确认。

推荐分层：飞书负责发起/通知/简单反馈；DSH网页扩展负责案例与Skill调优操作；SE后端保存权威案例、输入修订与结果；LangGraph作为业务状态编排候选；阶段执行器选择一个默认Agent或直接模型调用。工作台与流程引擎解决不同问题，7个Skill不需要7个Agent，也不必须对应7个图节点。

## 已有基础与本轮增量

已有R131 SDK选型、R164 Cordis插件、R165 DSH会话与子Agent研究。本轮核对本地DSH dd6322d604e00eec1ba5e0c8541159906a21094a 的部分接口源码，并查询当前官方文档；未更新或启动该源码树。旧研究中的版本、星数与“LangGraph自托管依赖LangSmith”不作为当前事实。

## 取舍

- DSH是插件化Agent运行环境与Web/Desktop界面，当前README仍提示开发者预览与兼容性变化；优先扩展插件和面板，固定基线，避免深改核心循环。
- LangGraph是业务有状态流程的候选：确定性代码控制允许的转移，节点内部允许Agent选择检索、分析与补查步骤。可独立于LangChain使用，自托管开源库不要求LangSmith。
- SDK、CLI和Pi不等于只能靠Prompt编排。SDK/RPC能被代码调用，外层可手写持久状态机；区别是业务恢复等能力自己承担多少。
- DSH当前workflow文档明确不对脚本、中间值和子任务进度建立检查点，重启不能续跑；DSH Session有日志不能推出workflow具备业务恢复。
- DSH当前Codex/Claude Code原生子Agent提供方为一次性任务，不能直接承诺多轮续接、任意中途切换Agent或完整共享上下文。
- 模型切换、Agent实现切换、业务阶段转移分别设计。案例状态保存在SE后端，Agent只接收某阶段需要的材料；切换优先发生在新运行或阶段边界。
- 图的重放会重新执行后续节点和外部API；检查点不撤销已发消息或Task写入。补件形成新输入，旧报告标记待更新，外部动作去重/结果核实由程序保证。

## 最小验证与限制

在用户选定账号和范围后，验证飞书发起同一案例→工作台单Skill运行→等人工补件→服务重启后继续→同输入换版本比较→历史输入新分支。此验证不替代全7个Skill及三份报告的真实回测。当前没有实测，不能宣布已打通。

现有源码快照不是最终魔改分支的确认。多人身份、资料隔离、网络、飞书内网页与模型线路均待验证。额外编排框架有学习和状态迁移成本，DSH复用也有界面改造与预览版本维护成本。

## 官方来源（2026-10-23检索）

- [DSH README](https://github.com/deepseek-ai/deepseek-harness)：插件化及预览状态。
- [DSH Session Controller](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/api/session-controller/README.md)：会话接口。
- [DSH workflow](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/workflow/workflow/README.md)：当前无检查点与重启恢复。
- [DSH Codex适配器](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/subagent/subagent-codex/README.md)、[Claude Code适配器](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/subagent/subagent-claude-code/README.md)：一次性任务及能力限制。
- [LangGraph概览](https://docs.langchain.com/oss/python/langgraph/overview)、[持久化](https://docs.langchain.com/oss/python/langgraph/persistence)、[时间旅行](https://docs.langchain.com/oss/python/langgraph/use-time-travel)：独立使用、状态保存与重新执行语义。
- [Claude SDK](https://code.claude.com/docs/en/agent-sdk/overview)、[Pi](https://github.com/earendil-works/pi/tree/main/packages/coding-agent)：可编程执行接口。
- [飞书网页应用](https://www.feishu.cn/content/7317091221654224898)：网页与飞书入口结合。

一致性：DSH本地接口与当前上游能力方向一致，具体实现已有变化；采用当前文档限制，未逐包审计。方法复用：不新增模式卡，本轮是已有分层方法的项目应用，无新运行证据。

项目当前决定以SE仓库文档为准；此速查只保存研究时点，不作为实施授权或最新项目状态。

## 同日补充：未来BU可能增减步骤

稳定执行机制不要求所有BU业务路径固定。建议区分专业Skill、已有能力的流程组合、新系统能力：前两类在支持的工具/数据/步骤类型范围内可配置，第三类仍需实现。编排Skill可以生成明确的候选步骤方案，程序校验与试跑后选用；执行中模型可在允许范围内动态路由。流程、Skill、输入及程序版本组合需固定；暂停中的旧案例不能因新配置删除节点而失去恢复路径。

[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)支持条件边、Command/Send及图构建；按BU配置组装图是项目适配工作，不是内建任意Skill编辑器。迁移规则对中断线程删除/重命名节点有限制。仅先支持当前步骤，不预建万能平台，候选验证不冒充第二BU验收。84部署的网页默认内网访问，飞书入口不自动提供公网可达性。以上仍为待确认设计，未实测。

## 同日补充：可操作的阶段与制品工作台

用户草图新增了查看阶段、编辑中间制品、回退和撤销回退的设想。建议把业务进度、制品修订、历史尝试和当前选用结果分别保存；原始证据保留，修改后按依赖提示下游待更新。查看历史不触发执行；从某步重跑产生新尝试；恢复此前整套结果不再次生成。编辑结论不等于验证成立，切回历史也不自动撤销外部消息或Task回填。旧运行晚到不得覆盖新输入或新选择。

[LangGraph时间旅行](https://docs.langchain.com/oss/python/langgraph/use-time-travel)与[人工中断](https://docs.langchain.com/oss/python/langgraph/interrupts)（2026-10-23定向核对）支持恢复/分支底层机制，但业务制品编辑、引用关系、失效提示和工作台仍需实现。阶段视图可按BU流程定义生成；case操作与修改BU模板分开，首轮可先纵向列表和少量制品编辑，无需同时建任意拖拽设计器。这加强了持久编排的适用性，不证明LangGraph或DSH方案已实测可用。项目中已记为候选，未确定首轮增量或重估预算；无新增通用经验卡。
