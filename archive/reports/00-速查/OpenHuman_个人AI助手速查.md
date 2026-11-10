> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# OpenHuman 个人 AI 助手速查

> 调研日期：2026-05-15
> 仓库：[tinyhumansai/openhuman](https://github.com/tinyhumansai/openhuman)
> 状态：Early Beta | GPL-3.0 | Stars 爆发式增长（单日 +3,329）

---

## 一句话判断

**不适合当"本地 AI"用。** 名字叫"隐私优先"，但核心 LLM 推理走的是 OpenHuman 自家云后端，你需要付费订阅他们的服务。本地 Ollama 只跑嵌入和摘要树——占整体能力的 <20%。如果你要的是"数据不出机器、模型跑在本地"的纯本地方案，这不是它。

---

## 定位透镜

### 纵轴 · 它是怎么来的

- **创始人**：senamakel（GitHub 主力 + Claude 联合提交）
- **创世痛点**：所有 LLM 都是无状态的——对话结束上下文就蒸发。"几个 bullet point 的记忆"是便签纸不是智能
- **核心创新**：Memory Tree——把你的邮件/Slack/GitHub/Notion 等 118+ 数据源做成本地 SQLite 的压缩记忆树 + Obsidian vault，灵感来自 Karpathy 的 obsidian-wiki workflow
- **生命周期**：**萌芽→早期上升期**。Early Beta 标签、Issue 里大量基础 Bug（Windows 登录失败、中文重复输出、IME 冲突），说明离生产可用还有距离

### 横轴 · 竞争格局

| 维度 | Cursor/Claude Desktop | OpenClaw/Hermes | OpenHuman |
|------|----------------------|-----------------|-----------|
| 开源 | ❌ 闭源 | ✅ MIT | ✅ GPL-3.0 |
| 记忆 | 聊天级 | 插件依赖/自学习 | Memory Tree + Obsidian vault |
| 集成 | 少量 | BYO | 118+ OAuth 一键连 |
| 模型 | 单模型 | BYO 多供应商 | 自动路由（一个订阅覆盖多供应商） |
| 本地化 | 不支持 | 可选 | 仅嵌入+摘要（via Ollama） |
| 定价 | 订阅 + 额外费 | BYO 模型费 | 一个订阅（含 TokenJuice） |

**设计哲学差异**：OpenHuman 走的是"重记忆轻推理本地化"路线——把数据存取和压缩做在本地 Rust 进程里，但把推理、语音、视觉全留给云端大模型。这不是"本地 AI"，而是"**本地记忆 + 云端大脑**"。

### 交叉判断

单日 3,329 stars 说明社区对"个人 AI 管家"概念有真实需求，但 OpenHuman 当前的兑现程度有限：Early Beta、基础 Bug 多、中文支持差、核心推理依赖云端。星数反映的是**对愿景的投票**，不是对产品成熟度的背书。

---

## 架构速览

```
┌──────────────────────────────────┐
│  Tauri v2 Shell（窗口、OS 集成）   │
└──────────┬───────────────────────┘
           │ JSON-RPC
┌──────────▼───────────────────────┐
│  Rust Core（openhuman sidecar）   │
│  • Memory Tree (SQLite 本地存储)  │
│  • 118+ 集成 + auto-fetch 20min  │
│  • TokenJuice (Token 压缩)       │
│  • Model Router (hint→模型映射)   │
│  • 可选 Ollama 本地嵌入/摘要      │
└──────────┬───────────────────────┘
           │
┌──────────▼───────────────────────┐
│  React Frontend                   │
└──────────────────────────────────┘
           │
     ╔═════▼═══════════════════╗
     ║  OpenHuman 云后端        ║
     ║  • OAuth Token 托管      ║
     ║  • LLM 调用代理          ║
     ║  • 模型路由实际执行       ║
     ╚═════════════════════════╝
```

---

## "本地"到底本地了什么？

| 组件 | 位置 | 说明 |
|------|------|------|
| Memory Tree (SQLite) | **本地** | 你的数据压缩成 ≤3k-token chunks 存本机 |
| Obsidian Wiki vault | **本地** | `.md` 文件可直接用 Obsidian 打开编辑 |
| 嵌入向量生成 | **可选本地** | Ollama + `all-minilm`（23MB），需手动开启 |
| 摘要树构建 | **可选本地** | Ollama + `gemma3:1b-it-qat`（~700MB） |
| 聊天/推理 | **云端** | 走 OpenHuman 后端 → Anthropic/OpenAI/Google |
| 语音 STT/TTS | **云端** | ElevenLabs TTS |
| 视觉理解 | **云端** | 云端视觉模型 |
| OAuth 令牌 | **云端** | OpenHuman 后端持有，不在本地存明文 |
| 会议 Agent | **云端** | Google Meet 加入需云端支持 |

**总结**：数据存储和预处理本地，推理和交互能力全在云端。

---

## Windows 部署实测要点

**系统要求**：4GB+ RAM（基础），16GB+（跑本地 Ollama 或大邮箱）

**安装**：
```powershell
irm https://raw.githubusercontent.com/tinyhumansai/openhuman/main/scripts/install.ps1 | iex
```

**已知 Windows 问题**（从 Issues 摘录）：
- [#1742](https://github.com/tinyhumansai/openhuman/issues/1742) Windows sign-in fails due to unreadable local `.secret_key`
- [#1718](https://github.com/tinyhumansai/openhuman/issues/1718) Chat composer sends while IME composition is active（中文输入法冲突）
- [#1675](https://github.com/tinyhumansai/openhuman/issues/1675) AI repeats every Chinese response twice（中文回复重复）

**判断**：Windows 上跑通基本流程可以，但中文场景体验较差，登录环节可能翻车。

---

## 关键风险清单（Munger 逆向）

1. **"隐私"名不副实**：OAuth 令牌由 OpenHuman 后端持有，所有 LLM 调用经他们代理。你的 prompt 和工具输出都经过他们的服务器。如果你因"隐私"选它，要清醒认识到这一点
2. **GPL-3.0 传染性**：如果你基于它二次开发并分发，必须同样以 GPL-3.0 开源。企业内部使用问题不大，但如果想做成产品对外分发，要留意
3. **订阅锁定**：模型路由走他们后端，不支持直接用你自己的 API Key 调云端模型（BYO Key）。一旦他们涨价或服务中断，你的 Agent 就停摆
4. **Early Beta 质量**：84 个 open issues，核心功能 bug 不少（登录失败、Gmail 拉取 400、中文重复）。不适合生产场景
5. **中文支持弱**：IME 冲突 + 回复重复 = 中文用户体验基本不可用级别

---

## 值得借鉴的设计

虽然整体不适合直接使用，但几个设计思路值得记住：

1. **Memory Tree + Obsidian vault 双写**：压缩后的记忆同时写 SQLite（Agent 查询用）和 `.md` 文件（人类浏览用），这个模式我们自己的知识库已经在用类似思路
2. **TokenJuice 压缩层**：在工具输出进入 LLM 上下文之前先压缩——HTML→Markdown、去噪、截断。值得在我们的 Agent 项目中复用此思路
3. **hint-based 模型路由**：Agent loop 自动根据任务类型（reasoning/fast/vision）选模型，而非让用户手动切换。比手动选模型更优雅
4. **auto-fetch 定时拉取**：每 20 分钟自动从所有数据源拉新数据进记忆树——"Agent 已经有了明天的上下文"这个理念很好

---

## 结论：能不能用？

| 场景 | 判断 | 理由 |
|------|------|------|
| 个人尝鲜体验 | ⚠️ 可以但粗糙 | 能装能跑，但 Windows + 中文 = 一堆 bug |
| 隐私敏感场景 | ❌ 不推荐 | 推理走云端、OAuth 令牌托管在他们后端 |
| 纯本地 AI 需求 | ❌ 不满足 | 本地只有记忆存储和可选的嵌入/摘要 |
| 企业内部部署 | ❌ 不适合 | Early Beta + 云端依赖 + GPL-3.0 |
| 借鉴架构设计 | ✅ 值得 | Memory Tree、TokenJuice、hint 路由都是好思路 |

**一句话**：观望，不入场。等它从 Beta 毕业、中文支持补齐、支持 BYO API Key（或纯本地推理）后再看。当前阶段，把它当作一个"个人 AI 管家应该长什么样"的设计参考来读比实际使用更有价值。

---

> 📌 来源清单
> - [GitHub README](https://github.com/tinyhumansai/openhuman/blob/main/README.md) — 2026-05-15 — 项目概览、对比表、安装方式
> - [官方文档 - Local AI](https://tinyhumans.gitbook.io/openhuman/features/model-routing/local-ai) — 2026-05-10 更新 — 本地 AI 能力范围和限制
> - [官方文档 - Privacy](https://tinyhumans.gitbook.io/openhuman/features/privacy-and-security) — 2026-05-10 更新 — 隐私架构设计
> - [官方文档 - Platform](https://tinyhumans.gitbook.io/openhuman/features/platform) — 2026-05-14 更新 — 架构和平台支持
> - [GitHub Issues](https://github.com/tinyhumansai/openhuman/issues) — 2026-05-15 — 84 个 open issues，关键 bug
> - [LICENSE](https://github.com/tinyhumansai/openhuman/blob/main/LICENSE) — GPL-3.0
>
> ⚖️ 来源一致性：多源一致（官方文档与 README 信息吻合）
> 📅 时效性声明：以上信息获取于 2026-05-15，项目处于快速迭代中
