---
name: llm-service-stack
description: >
  Decide and assemble a complete LLM serving stack across three layers — gateway, ops, engine.
  Use when: planning LLM deployment for a team or product; choosing between LiteLLM / Portkey / Kong AI Gateway; deciding whether to add vLLM Production Stack / SGLang behind the gateway; sizing for DAU and budget; user says "怎么部 LLM 服务", "LLM 网关选哪个", "上 vLLM 还是 LiteLLM", "LLM 服务栈", "self-host LLM stack", "LLM gateway selection", "production LLM serving".
applyTo: "**"
---

> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# LLM Service Stack Skill

> 给定一个团队或产品的 LLM 服务化需求，按"网关层 / 运维层 / 引擎层"三层结构推荐组合，避免**只买网关却没引擎**或**只起引擎却没治理**的偏科部署。

## Why this skill exists

[R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) 把"网关"在 Agent 语境拆成三层（消息通道 / LLM Gateway / Agent-MCP Gateway），[R63](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) 给出 LLM 服务化的成本-延迟-SLA 方法论，D50（原稿交叉引用，本归档未解析）（P04_llm-gateway-lab）提供 LiteLLM 三模式可跑实验台。**三者拼起来 = 完整 LLM 服务栈**——本 Skill 把这个组合固化为决策流程，避免每次新团队都从零选型。

核心理念：**LLM 服务栈不是单点选型，是三层组合**。只起 vLLM 没网关 → 团队代码散落 5 种 SDK；只起 LiteLLM 没运维 → 成本和 SLA 黑盒。

## 1. 触发条件

- "怎么给团队部 LLM 服务"
- "LLM 网关选 LiteLLM 还是 Portkey 还是 Kong"
- "要不要上 vLLM Production Stack"
- "我们日均 N 万次调用，怎么省钱"
- 团队规模 / DAU / 预算明确，问端到端架构

## 2. 三层架构速查

```
┌────────────────────────────────┐
│  Layer 1 · 网关层 Gateway       │  统一入口、路由、缓存、限流、计费、Guardrails
│  代表：LiteLLM / Portkey / Kong │
├────────────────────────────────┤
│  Layer 2 · 运维层 Ops           │  监控、SLA、成本归因、容量规划、灰度
│  代表：Langfuse / Helicone /    │
│       Prometheus + 自建仪表盘    │
├────────────────────────────────┤
│  Layer 3 · 引擎层 Engine        │  推理引擎（自托管模型时才需要）
│  代表：vLLM / SGLang / TGI /    │
│       OpenAI API（托管）         │
└────────────────────────────────┘
```

**铁律**：从顶层往下，**第一层永远要有**，第二层在 ≥ 5 人团队 / 日均 ≥ 1k 调用时必上，第三层只在自托管时才需要——80% 团队用闭源 API，第三层 = OpenAI/Anthropic 的事。

## 3. 决策流程（PSEV 实例化）

### Phase P · 约束画像（5 分钟）

填以下表，**任何空白格都禁止跳到 Phase S**：

| 维度 | 取值 | 触发分支 |
|------|------|---------|
| 模型来源 | 闭源 API / 开源自托管 / 混合 | 自托管 → 引擎层必选 |
| 团队规模 | < 5 / 5-50 / > 50 | < 5 → 网关层最简版即可 |
| 日均调用量 | < 1k / 1k-100k / > 100k | > 100k → 必上语义缓存 + 引擎层 |
| 月预算 | < $500 / $500-5k / > $5k | < $500 → 不要上 Portkey 商业版 |
| 数据合规要求 | 公开 / 内部 / 强合规 | 强合规 → 必自托管 + 必 Guardrails |
| 团队技术栈 | Python-only / 多语言 | 多语言 → OpenAI 兼容协议是必选 |
| 现有基础设施 | 裸服务器 / Docker / K8s | K8s 才考虑 vLLM Production Stack |

### Phase S · 候选策略与淘汰

按上表填的取值，沿决策树往下走：

```
Phase P 表填完
    ↓
模型来源？
├── 闭源 API only
│     ↓
│   团队规模 < 5？ → 直接调 OpenAI SDK，跳过本 Skill（杀鸡用牛刀）
│   团队规模 ≥ 5？
│     ↓
│   预算 < $500？ → LiteLLM Proxy（开源版）+ Langfuse（self-host） + ❌ 引擎层
│   预算 ≥ $500？ → LiteLLM 或 Portkey + Langfuse Cloud + ❌ 引擎层
│
├── 开源自托管 only
│     ↓
│   有 K8s？ → vLLM Production Stack + LiteLLM + Prometheus
│   无 K8s？ → 单机 vLLM/SGLang + LiteLLM + 自建简单监控
│
└── 混合（部分托管 + 部分自建）
      ↓
    必选 LiteLLM（统一 OpenAI 兼容接口）+ vLLM/SGLang（自托管部分）+ Langfuse
```

**淘汰原则**：

- ❌ 团队 < 5 人 + 日均 < 1k → 不要上任何"产品级"网关，OpenAI SDK 直连即可
- ❌ 月预算 < $500 → 不要上 Portkey 商业版（光控制台就 $99/月）
- ❌ 强合规但走闭源 API → 矛盾，必须自托管
- ❌ 无 K8s 经验团队上 vLLM Production Stack → 运维炸
- ❌ Python-only 团队上 Kong AI Gateway → 杀鸡用牛刀

### Phase E · 推荐栈组合（5 个典型档位）

| 档位 | 适用场景 | 网关 | 运维 | 引擎 | 起步成本 |
|------|---------|------|------|------|---------|
| **极简档** | 个人 / 2-3 人原型 | 无（OpenAI SDK 直连） | 无 | 闭源 API | $0/月 |
| **入门档** | 5-20 人团队，闭源为主 | LiteLLM Proxy（self-host） | Langfuse self-host | 闭源 API | $50-200/月 |
| **生产档** | 20-100 人团队，混合 | LiteLLM 或 Portkey | Langfuse Cloud | 闭源 + 单机 vLLM | $500-3k/月 |
| **企业档** | 100+ 人，多团队，多模型 | Kong AI Gateway 或 Portkey | Datadog/自建 | 闭源 + vLLM Production Stack | $3k-20k/月 |
| **强合规档** | 金融/医疗，全自托管 | LiteLLM（self-host） | self-host 全栈 | vLLM/SGLang on K8s | 主要是人工成本 |

### Phase V · 验证

栈装完后必跑的 4 个验证：

1. **统一接口**：随机切换 3 个底层模型（GPT-4o / Claude Sonnet / Llama 70B）→ 上层代码不改一行
2. **Fallback**：故意把主模型 API key 改错 → 自动切到备用模型
3. **成本归因**：跑 100 次调用 → 仪表盘按 user_id / project / model 分别可见
4. **延迟基线**：P50 / P95 / P99 三档延迟 → 与裸 SDK 对比，网关引入开销 < 50ms

## 4. 常见反模式

| 反模式 | 后果 | 正解 |
|--------|------|------|
| 只起 vLLM 不起网关 | 5 种 SDK 散落代码、换模型改 N 处 | 引擎前面**必须**有网关 |
| 只起网关不起运维 | 跑了 3 个月不知道钱花哪了 | 网关 + 运维**同时**起，运维不是 V2 才加 |
| 上来就买 Portkey 商业版 | 早期没价值，烧钱 | 先 LiteLLM 开源版跑 1 个月，确认需求再升级 |
| 自托管 vLLM 但跑 K8s 没经验 | 运维炸、可用性低 | 先用单机 vLLM，业务量起来再上 Production Stack |
| 强合规但走闭源 API | 数据出境，合规事故 | 强合规 = 必自托管，没有第二个选项 |

## 5. 落地工件清单

部署完后，**必须**有这些工件（缺一项就是没装完）：

- [ ] `litellm_config.yaml`：模型清单 + 路由策略 + fallback 链
- [ ] `.env.example`：所有 API Key 占位符（不入 git）
- [ ] `docker-compose.yml` 或 K8s manifests：一键起栈
- [ ] 仪表盘：至少能看 token 用量 / 成本 / P95 延迟 / 错误率四张图
- [ ] runbook.md：常见故障的应急步骤（API 限流、模型故障、网关崩溃）
- [ ] eval 集：5-20 个核心场景的回归 case（防 prompt/模型升级翻车）

## 6. 与其他产出物的协同

| 协同对象 | 价值 |
|---------|------|
| D50（原稿交叉引用，本归档未解析） P04_llm-gateway-lab | 直接复用三模式实验台 docker-compose 起 LiteLLM |
| skill-evaluator（原稿交叉引用，本归档未解析） | 用它构造第 5 项 eval 集 |
| [R47](../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) Redis 在 Agent 中的应用 | 网关的语义缓存依赖 Redis，参考其部署模式 |
| [R57](../../reports/05-%E8%AF%84%E4%BC%B0%E4%B8%8E%E8%B4%A8%E9%87%8F/R57_Agent%E5%AE%89%E5%85%A8%E4%B8%8E%E7%BA%A2%E9%98%9F%E6%94%BB%E9%98%B2%E4%BD%93%E7%B3%BB.md) 红队与防御 | 在网关层加 Guardrails 时参考四层防御 |

## 7. 参考报告

- [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) · 网关三层拆解（必读）
- [R63](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R63_LLM%E6%9C%8D%E5%8A%A1%E5%8C%96%E7%94%9F%E4%BA%A7%E9%83%A8%E7%BD%B2_%E6%88%90%E6%9C%AC%E5%BB%B6%E8%BF%9F%E7%9B%91%E6%8E%A7SLA.md) · LLM 服务化生产部署
- [R69](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R69_LLM_Agent%E7%BB%8F%E6%B5%8E%E5%AD%A6%E4%B8%8E%E5%95%86%E4%B8%9A%E5%86%B3%E7%AD%96.md) · LLM 经济学（成本测算）
- D50（原稿交叉引用，本归档未解析） · P04_llm-gateway-lab（可跑实验台）
