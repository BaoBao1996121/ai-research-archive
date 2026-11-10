> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P04 · LLM Gateway Lab

> **配套报告**：[R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) Agent 网关设计：AI Gateway / LLM Gateway / MCP Gateway 三层拆解
> **目标**：把 [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) 的"先部 LiteLLM Proxy"建议落地为可一键启动的本地实验台，让 `experiments/` 全部走它，自动获得统一计费、Fallback、语义缓存。

---

## 🗂️ TL;DR

```powershell
# 0. 进入目录
cd prototypes/P04_llm-gateway-lab

# 1. （可选）启动 Postgres + Redis（语义缓存+Virtual Key 持久化）
docker-compose up -d

# 2. 启动 LiteLLM Proxy（连真模型）
$env:OPENAI_API_KEY="sk-..."
$env:LITELLM_MASTER_KEY="sk-master-local-dev"
litellm --config litellm_config.yaml --port 4000

# 3. dry-run 跑全量演示（不需任何真 Key、不需 Docker）
python -m demo.run_all --mode dry
```

输出会展示：①统一 OpenAI 兼容调用 ②Fallback 链触发 ③语义缓存命中 ④Virtual Key 计费——每一项都打印**预期 vs 实际**对比。

---

## 📁 目录结构

```
P04_llm-gateway-lab/
├── README.md                       ← 你正在看
├── litellm_config.yaml             ← 网关主配置（最小版）
├── litellm_config.advanced.yaml    ← 进阶版（fallback + 语义缓存 + virtual key）
├── docker-compose.yml              ← Postgres + Redis 一键起
├── .env.example                    ← 环境变量样板
├── requirements.txt                ← Python 依赖
├── VALIDATION.md                   ← 验证记录
└── demo/
    ├── __init__.py
    ├── _common.py                  ← Mock 客户端（dry-run 模式）
    ├── smoke_test.py                ← 一行打通：用 OpenAI SDK 调 Proxy
    ├── fallback.py                  ← 主模型挂掉自动切备份
    ├── semantic_cache.py            ← 相似 Prompt 命中缓存（cosine ≥ 0.95）
    ├── virtual_key.py               ← 创建 Virtual Key + 预算限制
    ├── load_balance.py              ← 多副本权重分发
    └── run_all.py                   ← 串联跑完上面 5 个，输出 JSON 报告
```

---

## 🚀 三种使用模式

### 模式 A · Dry-run（零依赖，5 秒看效果）

不需要真 Key、不需要 Docker、甚至不需要 LiteLLM 本身——`demo/_common.py` 里有个 Mock 客户端模拟所有行为。**跑通本机 Python 即可**：

```powershell
pip install -r requirements.txt
python -m demo.run_all --mode dry
```

适合：快速理解网关行为、CI 烟雾测试、无网络环境。

### 模式 B · Local（真模型 + 真网关，无外部依赖服务）

启动 LiteLLM 本机进程，连接真 OpenAI/Anthropic API，不挂数据库（Virtual Key 用内存）：

```powershell
copy .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY / ANTHROPIC_API_KEY
litellm --config litellm_config.yaml --port 4000
# 新开一个终端
python -m demo.run_all --mode local
```

适合：开发调试、本机做 demo。

### 模式 C · Full（全栈生产仿真）

带上 Postgres（持久化 Virtual Key/用量）+ Redis（语义缓存 + 速率限制）：

```powershell
docker-compose up -d              # 起 postgres + redis
litellm --config litellm_config.advanced.yaml --port 4000
python -m demo.run_all --mode full
```

适合：评估生产部署成本、benchmark 缓存命中率、做 ROI 测算。

---

## ✅ 验证清单（与 R64 报告呼应）

跑 `python -m demo.run_all --mode dry` 应当看到：

| 步骤 | 预期 | 对应 R64 章节 |
|------|------|--------------|
| 00 烟雾测试 | OpenAI SDK 改 base_url 即工作 | §二 为什么需要 |
| 01 Fallback | 主模型抛错时自动切备份且业务无感 | §三-2 七大能力 |
| 02 语义缓存 | "今天天气如何"和"今日气温怎样"命中同一缓存条目 | §三-4 |
| 03 Virtual Key | 超预算的 Key 被 4xx 拒绝 | §三-5 |
| 04 Load Balance | 100 次请求按权重 3:1:1 分发 | §三-3 |

---

## 🔗 与本工作区其他模块的对接（下一步 Forge）

- **让 `experiments/single/E*.py` 全部走网关**：把脚本里 `base_url` 改成 `http://localhost:4000`，自动获得统一计费 + 缓存
- **与 P03（原稿交叉引用，本归档未解析） Redis Agent Lab 共享 Redis**：语义缓存复用同一 Redis 实例
- **配套 [R47](../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md)**：Redis 在 Agent 中的应用，验证语义缓存键设计

---

## 📌 备注

- 本原型不替代 [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) 报告，而是其"上手实战轨道"的可执行落地
- 所有 demo 脚本均遵循"可运行代码标准"——含依赖版本、预期输出注释、dry-run 兜底
- LiteLLM 版本钉在 `1.83.x`（2026-04 stable），升级前请跑回归
