---
title: Docker 部署踩坑与防护体系
aliases: [部署经验, Docker部署]
tags: [engineering, deployment, docker, devops, lessons-learned]
date: 2026-05-24
category: 工程实践
status: evergreen

---

> 脱敏节选 · 2026-11-10 补充 · 发布审核状态：redacted_full_review（发布前全文隐私审核、脱敏与改动复核）。保留通用技术内容，非公开案例、引用或数据已删除；编辑替换处另作说明。历史结论未在本次重新核实，代码未整体运行复现。见[归档说明](../../../ARCHIVE_POLICY.md)。

# R139：Docker 部署踩坑与防护体系

> **适用范围**：所有 Python + Docker + 向量数据库的项目部署

---

## 一、防护体系

以下脚本名为检查职责示例，需按实际项目准备脚本。

### 1.1 推送前检查（本地）

```python
# scripts/pre_push_check.py
# - py_compile 所有核心入口文件
# - 检查 docker-compose.prod.yml 和 .env 的关键配置是否一致
python scripts/pre_push_check.py
```

### 1.2 部署前检查（服务器）

```bash
# scripts/deploy_check.sh
# - .env 存在且 API Key 已设置
# - .env 权限 600
# - logs/ 可写
# - Milvus/LLM/Docker/GPU 可达
bash scripts/deploy_check.sh
```

### 1.3 部署 SOP

```
1. git pull
2. bash scripts/deploy_check.sh     ← 环境就绪？
3. docker build → docker run        ← 或 docker compose up -d --build
4. curl /health                      ← 验证
5. docker logs --tail 20             ← 无报错？
```

---

## 二、Docker 部署速查

| 概念 | 要点 |
|------|------|
| `environment:` in compose | 直接注入容器环境变量，不依赖 .env 文件 |
| `.env` 文件 | 本地开发用 python-dotenv 读取；生产用 compose `environment` |
| volume 权限 | 容器内 root → host 文件 root 所有；host 用户写入需 chown |
| compose vs docker | `docker compose`(插件) 和 `docker-compose`(独立) 是两个包 |
| healthcheck | 容器启动不代表服务就绪，必须有 /health 端点 |
| --build | 代码改了必须 `--build`，否则用旧镜像 |

---

## 三、向量数据库部署特殊点

- **编辑修订**：更换 embedding 模型时，先核对维度与 schema 兼容性并备份。需要重建时，在新集合中生成向量、验证检索与数据完整性后再迁移；保留回退所需旧集合，只有精确确认目标、备份和授权后才清理。不能无备份直接删除全部旧集合。
- `list_collections()` 是验证真相的唯一方式（不能信日志输出的集合名）
- 多个 Milvus 实例共存时注意端口映射别搞混

---

## 四、安全最佳实践

| 场景 | 方案 | 适用 |
|------|------|------|
| 内网单机 | `.env` + chmod 600 | 单机部署 |
| 多节点 | Docker secrets / K8s secrets | 中大型 |
| 合规审计 | HashiCorp Vault / 云 KMS | 金融级 |

**铁则**：
- `.env` 永远在 `.gitignore` 里
- API Key 不硬编码在任何 .py 文件中
- 部署文档里标注"需手动创建 .env"
