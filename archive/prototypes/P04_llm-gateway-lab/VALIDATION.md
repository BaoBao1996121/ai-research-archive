> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../../ARCHIVE_POLICY.md)。

# P04 LLM Gateway Lab · 验证记录

> **配套**：[R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) / [README.md](README.md)
> **最后验证**：2026-04-25

---

## ✅ Dry-run 验证（零依赖）

执行命令：

```powershell
cd prototypes/P04_llm-gateway-lab
pip install -r requirements.txt
python -m demo.run_all --mode dry --out output/run_all_dry.json
```

完整输出 5/5 通过：

| Demo | 验证点 | 结果 |
|------|------|-----|
| `smoke_test` | OpenAI SDK 改 `base_url` 即工作 | ✅ 路由到 `openai/gpt-4o-mini`，17 tokens |
| `fallback` | 主模型故障自动切备份 | ✅ `fast` (mock 故障) → `anthropic/claude-sonnet-4`，业务无感 |
| `semantic_cache` | 相似 Prompt 命中同一缓存 | ✅ 1/4 命中（`今天天气怎么样` ↔ `今天的天气如何`） |
| `virtual_key` | 预算超额 + 模型白名单生效 | ✅ 第 3 次调用 `429 budget_exceeded`；`smart` 被白名单拒绝 |
| `load_balance` | 权重 3:1:1 分发 | ✅ 实际 64% / 21% / 15%（容差 ±15%） |

输出文件：`output/run_all_dry.json`

---

## ⚠️ Mock 实现的局限（诚实声明）

`demo/_common.py` 中的 `MockGateway` 是教学用复刻，**不是 LiteLLM 替代**。已知简化：

| 方面 | Mock 行为 | 真 LiteLLM 行为 |
|------|----------|---------------|
| 语义相似度 | 字符 bigram + Jaccard（阈值 0.15） | embedding cosine（阈值 0.95） |
| Token 计费 | `len(text)//4` 粗估 | tiktoken / 厂商 API 真实计数 |
| LB 算法 | `random.choices(weights=...)` | 加权 round-robin / least-busy |
| Fallback 触发 | 只能用 `simulate_failure_for` 集合人工模拟 | 真 HTTP 错误码 / 超时 / RPM 限速 |
| Virtual Key | 内存字典 | Postgres 持久化 + Audit Log |

**dry-run 验证的是"行为框架是否正确"，不是"LiteLLM 是否实现了这些功能"**——后者需走 `--mode local/full`。

---

## 🧪 待补：Local 模式验证（需真 API Key）

执行命令：

```powershell
copy .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY 至少一项
litellm --config litellm_config.yaml --port 4000
# 新终端
python -m demo.run_all --mode local --out output/run_all_local.json
```

预期：`smoke_test` 与 `fallback` 应该真实跑通；`semantic_cache` / `virtual_key` / `load_balance` 在 local 模式下脚本会跳过（需 advanced 配置）。

> **验证人**：待补
> **验证日期**：待补

---

## 🧪 待补：Full 模式验证（Docker + Postgres + Redis）

执行命令：

```powershell
docker-compose up -d
litellm --config litellm_config.advanced.yaml --port 4000
python -m demo.run_all --mode full --out output/run_all_full.json
```

预期：5/5 全部跑真链路，Postgres 中可查到 Virtual Key 表，Redis 中可看到缓存键。

> **验证人**：待补
> **验证日期**：待补

---

## 🔄 与已有报告的链接

- [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) §三-2 Fallback ↔ `demo/fallback.py`
- [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) §三-3 Load Balance ↔ `demo/load_balance.py`
- [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) §三-4 语义缓存 ↔ `demo/semantic_cache.py`
- [R64](../../reports/04-%E5%B7%A5%E7%A8%8B%E5%AE%9E%E8%B7%B5/R64_Agent%E7%BD%91%E5%85%B3%E8%AE%BE%E8%AE%A1_AI_Gateway_LLM_Gateway_MCP_Gateway%E4%B8%89%E5%B1%82%E6%8B%86%E8%A7%A3.md) §三-5 Virtual Key ↔ `demo/virtual_key.py`
- [R47](../../reports/06-%E5%B7%A5%E5%85%B7%E4%B8%8E%E7%94%9F%E6%80%81/R47_Redis%E5%9C%A8Agent%E4%B8%AD%E7%9A%84%E5%BA%94%E7%94%A8%E4%B8%8E%E6%9B%BF%E4%BB%A3%E6%96%B9%E6%A1%88.md) Redis 在 Agent 中的应用 ↔ 共享 Redis 实例（配 `REDIS_HOST=localhost:6379`）
