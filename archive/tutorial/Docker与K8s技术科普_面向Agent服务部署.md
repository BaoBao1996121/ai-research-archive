> 历史研究归档 · 2026-11-10 发布 · 发布审核状态：scan_only（发布前程序化隐私扫描）。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；见[归档说明](../../ARCHIVE_POLICY.md)。

# Docker 容器化与 Kubernetes：AI Agent 服务部署指南

> 从原理到生产，把你的 Agent 稳稳地跑起来
>
> 撰写日期：2026-04-22 | 学习向扩充：2026-04-23

---

## 📋 学习路线图：你在哪里，该去哪里

在跳进技术细节之前，先看一张地图——你不必一次走完，根据自己的位置挑需要的段落。

```
你目前在哪一层？                   对应章节           预计学习时间
───────────────────────────────────────────────────────────────
Level 0: 完全不了解容器              第1-2章             30 min
         "Docker 是什么？"           → 搞清楚概念
                  ↓
Level 1: 知道概念，没动手过          第3章 + 动手实验     1 hour
         "Dockerfile 怎么写？"       → 自己 build 一个
                  ↓
Level 2: 能打包单个服务              第4章 + 动手实验     30 min
         "多服务怎么管？"            → Compose 编排
                  ↓
Level 3: 本地多服务能跑              第5-6章             30 min
         "生产环境怎么搞？"          → K8s 概念入门
                  ↓
Level 4: 理解 K8s 概念              第7章 + 动手实验     1 hour
         "怎么部署上去？"            → K8s 实战
                  ↓
Level 5: 能写 YAML 部署              第8-9章             30 min
         "Agent 有什么特殊的？"      → 特殊考量 + 选型
                  ↓
Level 6: 能独立做部署决策             第11-12章           按需
         "出问题怎么排查？"          → 避坑 + 排障
```

> **投入产出比建议**：如果你只是想让自己的 Agent 在团队内稳定运行，**学到 Level 2（Docker Compose）就够了**——这覆盖了 80% 的实际场景。K8s 留给需要的时候再学。

---

## 目录

1. [为什么 Agent 服务需要容器化？](#1-为什么-agent-服务需要容器化)
2. [Docker 核心原理](#2-docker-核心原理)
3. [Dockerfile 实战：打包一个 Agent 服务](#3-dockerfile-实战打包一个-agent-服务)
4. [Docker Compose：本地编排多服务 Agent](#4-docker-compose本地编排多服务-agent)
5. [Kubernetes 是什么？](#5-kubernetes-是什么)
6. [K8s 核心概念](#6-k8s-核心概念)
7. [K8s 实战：部署 Agent 到集群](#7-k8s-实战部署-agent-到集群)
8. [Agent 服务的特殊部署考量](#8-agent-服务的特殊部署考量)
9. [三种部署方案对比与选型](#9-三种部署方案对比与选型)
10. [附录：命令速查](#10-附录命令速查)
11. [新手避坑指南：十个常犯的错误](#11-新手避坑指南十个常犯的错误)
12. [排障手册：出了问题怎么查](#12-排障手册出了问题怎么查)
13. [心智模型总结：一张图串起所有概念](#13-心智模型总结一张图串起所有概念)

---

## 1. 为什么 Agent 服务需要容器化？

> 🎯 **学完本章你应该能**：向同事解释清楚"为什么不能直接 `python main.py` 就完事了"，以及容器化到底解决了什么痛点。

### 1.1 Agent 服务不是普通的 Web 应用

一个典型的 AI Agent 服务长这样：

```
用户请求
    ↓
┌──────────────────────────────────────┐
│            Agent Runtime             │
│                                      │
│  Python 3.x + LLM SDK (openai等)    │  ← 语言 & SDK
│  Tool 执行环境 (CLI 工具、浏览器等)   │  ← 外部工具链
│  向量数据库客户端 / RAG pipeline     │  ← 检索增强
│  Memory / State 管理                │  ← 状态持久化
│  Prompt 模板 / 知识文件              │  ← 静态资源
│                                      │
└──────────────────────────────────────┘
    ↓            ↓            ↓
 LLM API     外部工具      数据库/缓存
(OpenAI等)  (搜索/代码执行)  (Redis/PG)
```

它的依赖链比普通 Web 服务长得多：Python 版本、N 个 pip 包、可能还需要 Node.js（某些 CLI 工具）、系统级库（PDF 解析、OCR）、甚至浏览器（Playwright/Selenium）。

### 1.2 "在我电脑上能跑"综合征

```
你的电脑：Python 3.13 + Node.js 20 + pdfplumber + lark-cli + ...
同事电脑：Python 3.10 + 没有 Node.js + pip 版本冲突
服务器上：Python 3.8 + 没有 GPU driver + 网络不通外网 API
```

容器化的核心价值：**把代码 + 所有依赖 + 运行环境打成一个不可变的包**，在任何地方以完全相同的方式运行。

### 1.3 Agent 服务的部署需求光谱

| 需求 | 方案 |
|------|------|
| 自己电脑跑着就行 | 直接 `python main.py`，或用系统服务（Task Scheduler / systemd） |
| 换台机器也能跑 | **Docker 容器化** |
| 要稳定、要自愈、要扩容 | **Kubernetes** |
| 要零运维、按量付费 | 云函数 / Serverless（但 Agent 的长连接/状态场景不太适合） |

> 🤔 **停下来想一想**：回顾你自己的 Agent 项目，它的依赖链有多长？数一数 `requirements.txt` 里有几个包、需不需要额外的系统工具（PDF 解析？浏览器？CLI 工具？）。如果让另一个同事从零搭环境，他会遇到什么问题？
>
> 这个心理实验能帮你直觉地感受到容器化的价值——**你列出的每一个"可能的坑"，都是容器化替你抹平的**。

---

## 2. Docker 核心原理

> 🎯 **学完本章你应该能**：画出 Dockerfile → Image → Container 的关系图，说清楚 Docker 和虚拟机的本质区别，理解"分层缓存"为什么能让 build 变快。

### 2.1 Docker 不是虚拟机

这是最常见的误解，必须先纠正：

```
┌─────────────────────────┐   ┌─────────────────────────┐
│       虚拟机 (VM)        │   │     Docker 容器          │
│                          │   │                          │
│  ┌─────┐  ┌─────┐       │   │  ┌─────┐  ┌─────┐       │
│  │App A│  │App B│       │   │  │App A│  │App B│       │
│  ├─────┤  ├─────┤       │   │  ├─────┤  ├─────┤       │
│  │Libs │  │Libs │       │   │  │Libs │  │Libs │       │
│  ├─────┤  ├─────┤       │   │  └──┬──┘  └──┬──┘       │
│  │OS   │  │OS   │ ←重复! │   │     └────┬───┘          │
│  └─────┘  └─────┘       │   │    ┌─────┴──────┐       │
│  ┌────────────────┐     │   │    │ Docker Engine│       │
│  │   Hypervisor   │     │   │    └─────┬──────┘       │
│  └────────────────┘     │   │    ┌─────┴──────┐       │
│  ┌────────────────┐     │   │    │  宿主机 OS   │ ←共享! │
│  │   Host OS      │     │   │    └────────────┘       │
│  └────────────────┘     │   └─────────────────────────┘
└─────────────────────────┘
```

| 对比 | 虚拟机 | Docker 容器 |
|------|--------|------------|
| 隔离方式 | 硬件级模拟，每个 VM 一个完整 OS | 进程级隔离，共享宿主机内核 |
| 启动速度 | 分钟级 | 秒级（甚至 100ms） |
| 资源占用 | 每个 VM 占 GB 级（因为有完整 OS） | 只有应用 + 依赖，MB 级 |
| 性能损耗 | 5-15%（虚拟化开销） | 接近原生（<1%） |
| 类比 | 每家住独栋别墅（独立地基水电） | 每家住公寓（共享地基水电，房间隔离） |

> 💡 **类比深化**：虚拟机像是在一块地上盖了好几栋独立的房子，每栋房子有自己的地基、水管、电线。Docker 容器像是一栋公寓楼——住户共享地基和主水管（宿主机内核），但每套房间有自己的锁和隔音墙（Namespace + Cgroup）。公寓的建造成本远低于独栋——这就是容器启动快、占用少的根本原因。

### 2.2 Docker 三大件

```
 Dockerfile ──── build ────→ Image ──── run ────→ Container
  (设计图)                  (模具)                (产品)
```

**Dockerfile**：文本文件，一行行描述「怎么构建环境」——装什么系统包、什么 Python 库、把什么代码拷进去、启动时跑什么命令。

**Image（镜像）**：Dockerfile 构建后的只读产物。可以推到镜像仓库（Docker Hub / 私有仓库），别人拉下来就能用。

**Container（容器）**：从 Image 启动的一个运行中进程。同一个 Image 可以同时启动 N 个 Container。容器停止后，内部的修改默认丢失（除非用 Volume 持久化）。

### 2.3 分层存储：为什么 Docker build 快？

Docker 镜像由多个只读层叠加而成：

```
Layer 5: COPY *.py ./                     ← 你的代码（几 KB）
Layer 4: RUN pip install -r requirements.txt  ← Python 依赖（~200 MB）
Layer 3: RUN apt-get install -y nodejs    ← 系统包（~80 MB）
Layer 2: RUN apt-get update               ← 包索引
Layer 1: FROM python:3.13-slim            ← 基础镜像（~150 MB）
```

关键机制：**每一层有缓存**。改了代码只需要重建 Layer 5，下面四层全部复用。所以日常迭代的 build 通常只要几秒。

> **实践技巧**：把变化频率低的层放在前面（系统包 → Python 依赖 → 代码），变化频率高的放最后。requirements.txt 单独 COPY 就是这个原因——只有依赖变了才重装。

### 2.4 Docker 底层原理（了解即可）

Docker 利用 Linux 内核的两个特性实现「不装完整 OS 也能隔离」：

- **Namespace（命名空间）**：让每个容器有自己的进程表、网络栈、文件系统视图。容器 A 看不到容器 B 的进程。
- **Cgroup（控制组）**：限制每个容器能用多少 CPU、内存、磁盘 IO。防止一个容器吃光资源。

> Windows / macOS 上的 Docker Desktop 内部跑了一个轻量 Linux 虚拟机（WSL2 / HyperKit），容器在这个 Linux 里运行。所以 Windows 上 Docker 的性能会比 Linux 原生稍差。

> 🤔 **停下来想一想**：既然 Docker 共享宿主机内核，那么——
> 1. 一个 Linux 容器能不能跑在 Windows 上？（提示：思考一下 Docker Desktop 是怎么做的）
> 2. 容器 A 里的进程理论上能不能影响容器 B？（提示：想想"公寓隔音墙"类比的局限性）
>
> 答案：1. 不能直接跑，Docker Desktop 内部启了一个 WSL2 Linux 虚拟机来"借"一个 Linux 内核。2. 理论上是有可能的——内核漏洞可能导致"越墙"。这就是为什么生产环境还需要配合安全扫描和权限控制。**Docker 的隔离是进程级的，不是硬件级的，没有虚拟机那么"铁"。**

---

## 3. Dockerfile 实战：打包一个 Agent 服务

> 🎯 **学完本章你应该能**：自己写一个 Dockerfile 并成功 build 出镜像、启动容器、看到日志。

### 3.1 典型 Agent 服务的 Dockerfile

以一个需要 Python + Node.js CLI 工具 + PDF 解析能力的 Agent 为例：

```dockerfile
# ── 第 1 层：基础镜像 ──────────────────────────────────
# slim 版比 full 版小 ~700MB，够用就行
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# ── 第 2 层：系统级依赖 ────────────────────────────────
# 有些 Agent 需要 Node.js CLI 工具、Playwright 浏览器等
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        # 如果需要 Playwright：chromium fonts-liberation
        # 如果需要 OCR：tesseract-ocr
    && rm -rf /var/lib/apt/lists/*   # ← 清理缓存，减小镜像

# 如果需要 Node.js（例如某些 CLI 工具）
# RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
#     apt-get install -y nodejs && \
#     npm install -g some-cli-tool

# ── 第 3 层：Python 依赖 ───────────────────────────────
# 先只拷 requirements.txt，利用缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 第 4 层：应用代码 ──────────────────────────────────
COPY . .

# ── 运行时配置 ─────────────────────────────────────────
# 日志和临时文件挂载出去（不打包进镜像）
VOLUME ["/app/logs", "/app/data"]

# 声明端口
EXPOSE 8000

# 健康检查（K8s 和 Docker 都会用到）
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# 启动命令
CMD ["python", "main.py", "serve", "--port", "8000"]
```

### 3.2 .dockerignore（不要把垃圾打进镜像）

```
# .dockerignore
.env
.git/
__pycache__/
*.pyc
logs/
tmp/
data/
*.md
tests/
```

### 3.3 构建与运行

```bash
# 构建
docker build -t my-agent:v1.0 .

# 运行
docker run -d \
  --name my-agent \
  --restart always \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  my-agent:v1.0

# 查看
docker ps
docker logs my-agent -f --tail 50
```

### 3.4 参数备忘

| 参数 | 含义 | 示例 |
|------|------|------|
| `-d` | 后台运行 | |
| `--restart always` | 崩溃 / 宿主机重启后自动拉起 | |
| `-p 宿主:容器` | 端口映射 | `-p 8000:8000` |
| `-v 宿主:容器:权限` | 文件/目录挂载 | `-v ./.env:/app/.env:ro` |
| `-e KEY=VALUE` | 环境变量 | `-e OPENAI_API_KEY=sk-xxx` |
| `--name` | 容器名 | `--name my-agent` |
| `--gpus all` | 挂载 GPU（需要 nvidia-docker） | 本地模型推理场景 |

### 3.5 🔥 动手实验：5 分钟打包你的第一个容器

> **前提**：已安装 Docker Desktop（[Windows 安装指南](https://docs.docker.com/desktop/install/windows-install/)）

**实验目标**：把一个最简单的 Python 脚本容器化，验证"镜像一次构建，到处运行"。

**Step 1**：创建一个实验目录，写一个最小的 Python 服务

```bash
mkdir docker-hello && cd docker-hello
```

创建 `app.py`：
```python
# app.py —— 最小的 HTTP 服务
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        data = {
            "message": "Hello from Docker!",
            "hostname": os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'unknown'),
            "python_version": os.sys.version
        }
        self.wfile.write(json.dumps(data, indent=2).encode())

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running on port 8000...")
    server.serve_forever()
```

**Step 2**：写 Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
```

**Step 3**：构建并运行

```bash
docker build -t hello-agent:v1 .       # 构建（注意最后的点）
docker run -d -p 8000:8000 --name test hello-agent:v1  # 运行
curl http://localhost:8000              # 测试！
```

你应该看到类似这样的 JSON 输出：
```json
{
  "message": "Hello from Docker!",
  "hostname": "a1b2c3d4e5f6",
  "python_version": "3.13.x ..."
}
```

**Step 4**：感受容器隔离

```bash
docker exec -it test bash               # 进入容器
ls /app                                  # 只有 app.py，没有宿主机文件
exit                                     # 退出
```

**Step 5**：清理

```bash
docker stop test && docker rm test
docker rmi hello-agent:v1
```

> ✅ **自检**：如果你能看到 JSON 输出，说明你已经成功完成了：编写 Dockerfile → 构建镜像 → 启动容器 → 验证服务。这就是 Docker 工作流的完整闭环。

> 🔥 **进阶挑战**：修改 `app.py` 的返回内容，重新 `docker build`，观察 build 速度——因为 `FROM python:3.13-slim` 层已缓存，所以只需要重建最后一层，是不是很快？

---

## 4. Docker Compose：本地编排多服务 Agent

> 🎯 **学完本章你应该能**：用一个 `docker-compose.yml` 同时启动 Agent + Redis + 向量数据库，理解"服务发现"是怎么回事。

### 4.1 为什么需要 Compose？

真实的 Agent 系统往往不止一个进程：

```
                        ┌─────────────────┐
  用户请求 ──→           │  Agent Service  │  ← 主服务
                        │  (Python)       │
                        └───┬──────┬──────┘
                            │      │
                    ┌───────▼┐  ┌──▼──────────┐
                    │ Redis  │  │ Vector DB   │
                    │ (缓存/ │  │ (Chroma/    │
                    │  队列) │  │  Qdrant)    │
                    └────────┘  └─────────────┘
```

用 `docker run` 一个个启动太繁琐。Docker Compose 用一个 YAML 文件把所有服务声明在一起：

### 4.2 docker-compose.yml 示例

```yaml
services:
  # ── 主 Agent 服务 ──────────────────────────
  agent:
    build: .
    container_name: my-agent
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./.env:/app/.env:ro
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Shanghai
      - REDIS_URL=redis://redis:6379    # 容器间用服务名互相访问
      - VECTOR_DB_URL=http://qdrant:6333
    depends_on:           # 声明启动顺序
      - redis
      - qdrant

  # ── Redis（对话记忆 / 任务队列）──────────
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  # ── 向量数据库（RAG 检索）────────────────
  qdrant:
    image: qdrant/qdrant:latest
    restart: always
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

# 持久化卷声明
volumes:
  redis_data:
  qdrant_data:
```

### 4.3 常用操作

```bash
docker compose up -d --build    # 构建 + 后台启动所有服务
docker compose logs -f agent    # 只看 agent 服务日志
docker compose ps               # 查看所有服务状态
docker compose down             # 停止并移除所有容器
docker compose restart agent    # 只重启 agent
```

### 4.4 Compose 的核心价值

| 能力 | 说明 |
|------|------|
| **服务发现** | 容器间直接用服务名访问（`redis:6379`），不用管 IP |
| **依赖管理** | `depends_on` 声明启动顺序 |
| **一键操作** | `up -d` 全起，`down` 全停 |
| **环境一致** | 把 yml 文件给任何人，`docker compose up` 就是一模一样的环境 |

### 4.5 🔥 动手实验：Compose 编排 Agent + Redis

**实验目标**：体验多服务编排，理解容器间怎么通过服务名互相访问。

**Step 1**：创建 `docker-compose.yml`

```yaml
services:
  app:
    build: .                        # 用上一个实验的 Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis            # 注意：用的是服务名，不是 IP
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Step 2**：修改 `app.py`，让它连接 Redis

```python
# 在 app.py 中添加 Redis 连接测试
import os, socket

# 测试能否解析 redis 服务名
redis_host = os.environ.get("REDIS_HOST", "localhost")
try:
    redis_ip = socket.gethostbyname(redis_host)
    redis_status = f"resolved to {redis_ip}"
except:
    redis_status = "cannot resolve"
```

**Step 3**：启动并验证

```bash
docker compose up -d --build
docker compose ps                   # 两个服务都应该是 running
docker compose logs app             # 看 app 服务日志

# 验证容器间网络互通
docker compose exec app ping redis -c 2   # 能 ping 通！
```

> 🤔 **想一想**：为什么 `app` 容器能直接用 `redis` 这个名字访问 Redis 容器？答案：Docker Compose 自动创建了一个虚拟网络，所有服务都加入这个网络，服务名被注册为 DNS 记录。这就是"服务发现"——你不需要知道对方的 IP。

**Step 4**：清理

```bash
docker compose down                 # 一键停止并移除所有容器
```

---

## 5. Kubernetes 是什么？

> 🎯 **学完本章你应该能**：向别人解释 Docker 和 K8s 的关系（"集装箱 vs 港口"），说清楚什么时候需要 K8s、什么时候 Docker Compose 就够了。

### 5.1 Docker 的天花板

Docker（含 Compose）解决了「环境一致性」和「单机编排」，但面对以下场景力不从心：

| 场景 | Docker 能力 |
|------|------------|
| 服务挂了自动重启 | ✅ `--restart always` |
| 服务器宕机了呢？ | ❌ 容器跟着一起没了 |
| 流量暴涨，要加实例 | ❌ 手动 `docker run` |
| 新版本上线不中断 | ❌ 停旧容器 → 启新容器，有间隔 |
| 几十个服务互相调用 | ❌ Compose 只管单机 |

### 5.2 一句话定义

> **Kubernetes（K8s）= 跨多台机器的容器编排平台**
>
> Docker 是「集装箱」，K8s 是「港口调度系统」——决定集装箱放哪条船、坏了自动补、忙了自动加。

### 5.3 名字由来

Kubernetes 来自希腊语 κυβερνήτης，意为「舵手」。K8s 是缩写（K + 8 个字母 + s）。由 Google 内部容器编排系统 Borg 的设计理念演化而来，2014 年开源。

> 💡 **建立直觉——Docker vs K8s 的职责边界**：
>
> 把部署想象成一家物流公司：
> - **Docker** = 标准集装箱。把货物（代码+依赖）装进统一规格的箱子，不管走公路还是海运，箱子是一样的。
> - **Docker Compose** = 本地仓库管理员。管一个仓库（单机）里的多个集装箱，能按顺序摆放。
> - **Kubernetes** = 全球港口调度系统。管 N 个港口（多台机器），自动决定集装箱放哪、坏了补、忙了加。
>
> 关键判断：如果你的"物流量"一个仓库就能搞定，不需要建调度系统。

---

## 6. K8s 核心概念

> 🎯 **学完本章你应该能**：看到一个 K8s YAML 文件不懵——认识 Pod、Deployment、Service 是什么、为什么需要，理解"声明式"和"调谐循环"这两个核心思想。

### 6.1 集群架构

```
              ┌─────────────────────────────────────┐
              │         Control Plane（大脑）         │
              │                                      │
              │  API Server ← 唯一入口，所有操作经过它│
              │  Scheduler  ← 决定 Pod 放到哪个 Node  │
              │  Controller ← 持续监控 + 自愈         │
              │  etcd       ← 分布式 KV 数据库（状态）│
              └──────────────────┬──────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │    Node 1    │    │    Node 2    │    │    Node 3    │
   │   (工作机)   │    │   (工作机)   │    │   (工作机)   │
   │              │    │              │    │              │
   │  ┌────┐     │    │  ┌────┐     │    │  ┌────┐     │
   │  │Pod │ ... │    │  │Pod │ ... │    │  │Pod │ ... │
   │  └────┘     │    │  └────┘     │    │  └────┘     │
   │              │    │              │    │              │
   │  kubelet     │    │  kubelet     │    │  kubelet     │
   │  kube-proxy  │    │  kube-proxy  │    │  kube-proxy  │
   └──────────────┘    └──────────────┘    └──────────────┘
```

### 6.2 核心概念速查

| 概念 | 一句话解释 | 通俗类比 |
|------|-----------|---------|
| **Cluster** | 一组协同工作的机器 | 一家物流公司 |
| **Node** | 集群中的一台机器（物理/虚拟） | 一个仓库 |
| **Pod** | 最小调度单位，包含 1~N 个容器 | 一个工位 |
| **Deployment** | 声明「我要 N 个 Pod 副本」 | 排班表（保证始终 N 人在岗） |
| **Service** | 稳定的网络入口，自动负载均衡到 Pod | 前台总机（客户不用知道分机号） |
| **ConfigMap** | 非敏感配置（环境变量、配置文件） | 文件柜 |
| **Secret** | 敏感配置（API Key、密码） | 保险箱（base64 编码存储） |
| **Namespace** | 逻辑隔离（不同项目/环境） | 不同楼层 |
| **Ingress** | HTTP 路由入口（域名 → Service） | 门牌号 + 导航系统 |
| **HPA** | 水平自动伸缩（根据 CPU/自定义指标） | 自动招临时工 |
| **PVC** | 持久化存储声明 | 租一块硬盘 |

### 6.3 声明式 —— K8s 的灵魂

传统运维是**命令式**的——告诉系统「做什么」：

```
# 命令式（传统）
启动 3 个容器
→ 第 2 个挂了
→ 手动重启第 2 个
→ 凌晨 3 点报警，爬起来重启
```

K8s 是**声明式**的——告诉系统「我要什么状态」，它自己想办法达到：

```yaml
# 声明式（K8s）
spec:
  replicas: 3   # "我要 3 个副本始终运行"
```

```
K8s Controller 持续循环：
  观察 → 当前有几个 Pod？
  对比 → 期望 3 个，实际 2 个
  行动 → 自动创建 1 个新 Pod
  ↻ 无限循环
```

这个循环叫 **Reconciliation Loop（调谐循环）**，是 K8s 所有自愈能力的根基。

### 6.4 自愈演示

```
正常：  Pod-1 ✓   Pod-2 ✓   Pod-3 ✓
故障：  Pod-1 ✓   Pod-2 ✗   Pod-3 ✓     ← Pod-2 挂了
自愈：  Pod-1 ✓   Pod-2' ✓  Pod-3 ✓     ← 秒级自动补一个

甚至：
Node-2 整台机器挂了 → K8s 把上面的 Pod 全部迁移到其他 Node
```

> 🤔 **停下来想一想**：声明式 vs 命令式不只是 K8s 的概念，你在编程中早就遇到了：
> - **命令式**：一步步告诉计算机怎么做——`for 循环、if 分支、操作 DOM`
> - **声明式**：告诉计算机你要什么——`SQL 查询、HTML、React JSX`
>
> K8s 的 YAML 就是"声明式"——你不写"启动容器→等 3 秒→检查健康→挂载网络"的脚本，你只写"我要 3 个健康的 Pod"，K8s 的调谐循环帮你搞定一切。
>
> **灵魂追问**：如果某个 Pod 反复崩溃重启（CrashLoopBackOff），调谐循环会无限重启它吗？如果会，这算不算一种问题？（提示：想想"自愈"和"掩盖 bug"的区别——K8s 确实会无限重试，但退避间隔会指数增长。这就是为什么你还需要监控和告警。）

### 6.5 核心概念关系图

上面的概念比较多，这张图帮你理清它们的关系：

```
                    用户
                     │
                     ▼
              ┌─────────────┐
              │   Ingress    │  ← 域名路由 (my-agent.company.com → Service)
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │   Service    │  ← 稳定入口 + 负载均衡
              └──────┬──────┘
                     │ 自动发现
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       ┌──────┐  ┌──────┐  ┌──────┐
       │ Pod  │  │ Pod  │  │ Pod  │  ← Deployment 管理副本数
       │  v1  │  │  v1  │  │  v1  │
       └──┬───┘  └──┬───┘  └──┬───┘
          │         │         │
     ConfigMap   Secret     PVC
     (配置)     (密钥)    (存储)
```

> 💡 **记忆锚点**：Pod 是最小的"工位"，Deployment 是"排班表"，Service 是"前台总机"。你给公司打电话（Service），前台把你转到有空的工位（Pod）。排班表（Deployment）保证每天都有人在。

---

## 7. K8s 实战：部署 Agent 到集群

> 🎯 **学完本章你应该能**：看懂一套完整的 K8s 部署 YAML（Deployment + Service + Secret + HPA），理解每个字段的含义，能按模板改出自己项目的部署文件。

### 7.1 Deployment（部署清单）

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-agent
  labels:
    app: my-agent
spec:
  replicas: 2                       # 跑 2 个副本
  selector:
    matchLabels:
      app: my-agent
  template:
    metadata:
      labels:
        app: my-agent
    spec:
      containers:
      - name: my-agent
        image: registry.company.com/my-agent:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: TZ
          value: Asia/Shanghai
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:           # 从 Secret 读取，不硬编码
              name: agent-secrets
              key: openai-api-key
        # ── 健康检查 ──
        livenessProbe:              # 存活探针：失败 → 重启容器
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:             # 就绪探针：失败 → 从负载均衡摘除
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        # ── 资源限制 ──
        resources:
          requests:                 # 最低保证
            memory: "256Mi"
            cpu: "200m"            # 0.2 核
          limits:                   # 上限（超了会被 OOM Kill）
            memory: "1Gi"
            cpu: "1000m"           # 1 核
```

### 7.2 Service（网络入口）

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-agent
spec:
  selector:
    app: my-agent
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP           # 集群内部访问
  # type: LoadBalancer      # 需要外部访问时用这个
```

### 7.3 Secret（API Key 管理）

```bash
# 从命令行创建（生产环境建议用 Vault 等工具）
kubectl create secret generic agent-secrets \
  --from-literal=openai-api-key=sk-xxxx
```

### 7.4 HPA（自动伸缩）

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-agent
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70    # CPU 超 70% 就扩容
```

### 7.5 完整部署流程

```bash
# 1. 构建并推送镜像
docker build -t registry.company.com/my-agent:v1.0 .
docker push registry.company.com/my-agent:v1.0

# 2. 部署
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# 3. 查看状态
kubectl get pods -l app=my-agent
kubectl logs -f deployment/my-agent

# 4. 滚动更新（零停机）
docker build -t registry.company.com/my-agent:v1.1 .
docker push registry.company.com/my-agent:v1.1
kubectl set image deployment/my-agent my-agent=registry.company.com/my-agent:v1.1
kubectl rollout status deployment/my-agent   # 看更新进度

# 5. 出问题了？一键回滚
kubectl rollout undo deployment/my-agent
```

### 7.6 🔥 动手实验：本地体验 K8s（无需真集群）

> 如果你没有 K8s 集群，也可以用 Docker Desktop 自带的 K8s 或 [Minikube](https://minikube.sigs.k8s.io/) 在本地体验。

**Option A：Docker Desktop 启用 K8s**

Settings → Kubernetes → Enable Kubernetes → Apply & Restart，等几分钟就好。

**Option B：在线免费体验**

打开 [Play with Kubernetes](https://labs.play-with-k8s.com/)，在浏览器里直接操作 K8s 集群。

**验证 K8s 可用**：

```bash
kubectl version --client           # 看到版本号就对了
kubectl get nodes                  # 看到至少一个 Ready 的 node
```

**最小部署实验**：

```bash
# 用 nginx 快速体验一个完整流程
kubectl create deployment hello-k8s --image=nginx --replicas=2
kubectl expose deployment hello-k8s --port=80 --type=NodePort
kubectl get pods                   # 看到 2 个 Running 的 Pod
kubectl get service hello-k8s      # 看到分配的端口

# 感受自愈：手动删一个 Pod，K8s 秒补
kubectl delete pod <任意一个pod名>
kubectl get pods                   # 马上又回到 2 个！
```

> ✅ **自检**：如果你手动删了一个 Pod 后，`kubectl get pods` 立刻又显示 2 个 Running 的 Pod——恭喜，你亲眼见证了 K8s 调谐循环的自愈能力。

**清理**：
```bash
kubectl delete deployment hello-k8s
kubectl delete service hello-k8s
```

---

## 8. Agent 服务的特殊部署考量

> 🎯 **学完本章你应该能**：说出 Agent 服务与普通 Web 服务在部署上的 5 个关键差异，并知道每个差异的应对方案。

Agent 服务和普通 Web API 相比，有一些特殊的部署要点：

### 8.1 长时间请求 & 超时

LLM 调用一次可能要 5-30 秒（streaming 场景更久），Agent 多步推理可能要几分钟。

```yaml
# Ingress / 负载均衡器需要配长超时
annotations:
  nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
  nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
```

### 8.2 资源消耗模式：脉冲式

Agent 平时闲着（等请求），来了请求后 CPU/内存瞬间飙升（LLM 客户端处理、Tool 执行、PDF 解析等），处理完又回落。

```
CPU 使用率
100% │        ┌──┐     ┌────┐
 75% │        │  │     │    │
 50% │   ┌──┐ │  │  ┌──┤    │
 25% │───┘  └─┘  └──┘  └────└───
  0% └──────────────────────────→ 时间
         请求A   请求B   请求C
```

**建议**：
- `requests`（保证值）设低一些，保证调度灵活
- `limits`（上限）给够，避免 LLM 响应处理时被 OOM Kill
- 用 HPA 基于请求延迟或队列深度扩容，而非单纯 CPU

### 8.3 API Key 安全

**绝对不要做的事：**
- 把 API Key 写进 Dockerfile 或代码
- 把 .env 文件打进 Docker 镜像

**正确做法：**

| 方案 | 适合场景 |
|------|---------|
| Docker: `-v .env:/app/.env:ro` 挂载 | 本地 / 单机 |
| K8s: Secret + `valueFrom.secretKeyRef` | 集群 |
| HashiCorp Vault / AWS Secrets Manager | 生产环境最佳实践 |

### 8.4 状态管理

Agent 常常需要维护对话历史、Memory 等状态。容器本身是「用完即弃」的，状态必须外置：

```
          ❌ 状态存在容器内（容器重启就丢了）

          ✅ 状态外置：
          ┌──────────┐
          │  Agent   │──→ Redis（对话历史、短期记忆）
          │  容器    │──→ PostgreSQL（用户数据、长期记忆）
          │          │──→ 向量数据库（RAG 知识库）
          └──────────┘
```

### 8.5 可观测性

Agent 的调试比普通服务更难（LLM 输出不确定、Tool 调用链长），建议至少监控：

| 指标 | 原因 |
|------|------|
| LLM API 延迟 & 错误率 | 上游 API 出问题第一时间知道 |
| Token 消耗量 | 成本控制（这是 Agent 的"水电费"） |
| Tool 调用成功率 | 某个 Tool 挂了会导致 Agent 整体行为异常 |
| 端到端处理时间 | 用户体感 |
| 容器重启次数 | 反映稳定性 |

### 8.6 优雅关停（Graceful Shutdown）

Agent 可能正在执行多步推理。突然杀进程会导致用户请求丢失或中间状态不一致。

```python
# Python 示例：捕获 SIGTERM（K8s 停止 Pod 时发送）
import signal
import sys

def graceful_shutdown(signum, frame):
    print("收到停止信号，等待当前请求完成...")
    # 停止接收新请求
    # 等待正在进行的请求完成（设超时）
    # 清理资源
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
```

```yaml
# K8s Deployment 中配置优雅关停等待时间
spec:
  terminationGracePeriodSeconds: 60   # 给 60 秒完成当前请求
```

### 8.7 🤔 Agent 部署思维检查清单

在部署一个 Agent 服务之前，过一遍这张清单：

| # | 检查项 | 你的回答 |
|---|--------|---------|
| 1 | API Key 存在哪里？（绝不能在代码/镜像里） | |
| 2 | Agent 的一次请求最长要多久？超时配够了吗？ | |
| 3 | 对话历史/Memory 存在哪里？容器重启会丢吗？ | |
| 4 | LLM API 调用失败时有重试逻辑吗？ | |
| 5 | 能看到 Token 消耗量吗？（成本可控性） | |
| 6 | 容器突然被杀时，正在处理的请求怎么办？ | |
| 7 | 同时来 100 个请求，系统扛得住吗？ | |

> 💡 **经验法则**：如果你只能做一件事，做好 **#1（API Key 安全）** 和 **#3（状态外置）**。前者是安全底线，后者是稳定性基石。

---

## 9. 三种部署方案对比与选型

> 🎯 **学完本章你应该能**：根据自己的项目情况，做出合理的部署方案选择——而不是"别人用 K8s 我也用 K8s"。

### 9.1 对比矩阵

| 维度 | 直接运行 / 系统服务 | Docker (Compose) | Kubernetes |
|------|:---:|:---:|:---:|
| **部署难度** | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **环境一致性** | ❌ | ✅ | ✅ |
| **自愈能力** | ⭐⭐ 崩溃重启 | ⭐⭐⭐ restart:always | ⭐⭐⭐⭐⭐ 跨节点自愈 |
| **弹性伸缩** | ❌ | ❌ 手动 | ✅ HPA 自动 |
| **零停机更新** | ❌ | ⚠️ 短暂中断 | ✅ 滚动更新 |
| **多服务编排** | ❌ | ✅ Compose | ✅ 原生支持 |
| **学习成本** | 无 | 低 | 中高 |
| **基础设施要求** | 无 | 装 Docker | 需要 K8s 集群 |
| **适合团队规模** | 1-2 人 | 2-10 人 | 10+ 人 / 多服务 |

### 9.2 选型决策树

```
你的 Agent 服务需要……

Q1: 只在一台固定电脑上跑？
 └─ 是 → 系统服务（Task Scheduler / systemd）
 └─ 否 ↓

Q2: 需要在多台机器上运行 / 需要团队协作部署？
 └─ 是，但只有 1-3 个服务 → Docker Compose
 └─ 是，而且 >5 个服务 / 需要自动伸缩 → Kubernetes
 └─ 否，只是想「换台机器也能跑」 → Docker（单容器）

Q3: 有没有现成的 K8s 集群？
 └─ 有 → 直接上 K8s
 └─ 没有，但有云账号 → 考虑托管 K8s（AKS/EKS/GKE）
 └─ 没有，也不想折腾 → Docker Compose 到头了，够用
```

### 9.3 渐进式演进路径

```
阶段 1：本地开发
  python main.py
  ↓
阶段 2：本地稳定运行
  系统服务（Task Scheduler / systemd）
  ↓
阶段 3：可移植 & 团队共享
  Docker + docker-compose
  ↓
阶段 4：生产级 & 弹性
  Kubernetes
```

> 不需要一步到位。从当前需求出发，在痛点出现时再升级方案。

---

## 10. 附录：命令速查

### Docker

```bash
# ── 镜像 ──
docker build -t name:tag .              # 构建
docker images                            # 列出本地镜像
docker rmi name:tag                      # 删除镜像
docker push registry/name:tag            # 推送到仓库
docker pull registry/name:tag            # 从仓库拉取

# ── 容器 ──
docker run -d --name xxx image           # 创建并启动
docker ps                                # 查看运行中
docker ps -a                             # 查看全部（含已停止）
docker stop / start / restart xxx        # 停止 / 启动 / 重启
docker rm xxx                            # 删除容器
docker logs xxx -f --tail 100            # 查看日志
docker exec -it xxx /bin/bash            # 进入容器 shell
docker inspect xxx                       # 详细信息（含 IP、挂载等）

# ── Compose ──
docker compose up -d --build             # 构建 + 后台启动
docker compose down                      # 停止 + 移除
docker compose logs -f service_name      # 看某个服务的日志
docker compose ps                        # 查看所有服务状态
docker compose exec service_name bash    # 进入某个服务容器
```

### Kubernetes

```bash
# ── 查看 ──
kubectl get pods / services / deployments / nodes
kubectl describe pod pod_name            # 详情（含事件日志）
kubectl logs pod_name -f                 # 容器日志
kubectl logs pod_name -c container_name  # 多容器 Pod 指定容器

# ── 部署 ──
kubectl apply -f file.yaml              # 声明式部署（幂等）
kubectl delete -f file.yaml             # 删除资源
kubectl scale deployment xxx --replicas=5  # 手动扩容
kubectl set image deployment/xxx container=image:tag  # 更新镜像

# ── 更新 & 回滚 ──
kubectl rollout status deployment xxx    # 查看更新进度
kubectl rollout history deployment xxx   # 查看历史版本
kubectl rollout undo deployment xxx      # 回滚到上一版本

# ── 调试 ──
kubectl exec -it pod_name -- bash        # 进入 Pod
kubectl port-forward pod/xxx 8080:8000   # 本地端口转发
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl top pods                         # 资源使用（需 metrics-server）

# ── 配置 ──
kubectl create secret generic name --from-literal=key=value
kubectl create configmap name --from-file=config.yaml
kubectl get secret name -o yaml          # 查看（base64 编码）
```

---

## 11. 新手避坑指南：十个常犯的错误

> 以下是初学者（以及一些不那么初学的人）最常踩的坑。每个坑附带"为什么会犯"和"怎么修"。

### 坑 1：把 `.env` 文件打进了镜像

**症状**：`docker history` 或 `docker inspect` 能看到你的 API Key。

**为什么犯**：`COPY . .` 会拷贝当前目录下的所有文件，包括 `.env`。

**修复**：
```
# .dockerignore 中加上
.env
.env.*
```

> **严重程度：🔴 高**。一旦镜像被推到公共仓库或泄露，API Key 就暴露了。

### 坑 2：镜像体积爆炸（几个 GB）

**症状**：`docker images` 显示镜像 2-3 GB。

**常见原因**：
- 用了 `python:3.13` 而不是 `python:3.13-slim`（相差 ~700MB）
- 没有在 `apt-get install` 后清理缓存
- 把测试数据、日志、`.git` 目录打进了镜像

**修复**：
```dockerfile
# 用 slim 基础镜像
FROM python:3.13-slim

# apt 安装后清理
RUN apt-get update && apt-get install -y --no-install-recommends xxx \
    && rm -rf /var/lib/apt/lists/*

# pip 不缓存
RUN pip install --no-cache-dir -r requirements.txt
```

### 坑 3：每次改一行代码，pip install 重跑 10 分钟

**症状**：改了一行 Python 代码，build 要重新安装所有依赖。

**根因**：`requirements.txt` 和代码一起 `COPY`，导致代码变动让依赖层缓存失效。

**修复**：先拷依赖文件再拷代码（利用分层缓存）：
```dockerfile
COPY requirements.txt .                 # 单独拷，这层不常变
RUN pip install --no-cache-dir -r requirements.txt   # 缓存住
COPY . .                                # 代码层，改代码只重建这层
```

### 坑 4：容器里 `localhost` 访问不到宿主机服务

**症状**：Agent 容器里配置 `REDIS_HOST=localhost`，连不上宿主机的 Redis。

**根因**：容器有自己的网络命名空间，`localhost` 指的是容器自己，不是宿主机。

**修复**：
- Docker Compose：用服务名（`redis`）而不是 `localhost`
- 单独运行：用 `host.docker.internal`（Docker Desktop 特有）或 `--network host`

### 坑 5：容器时区不对，日志时间乱了

**症状**：日志里的时间比本地少 8 小时（UTC vs CST）。

**修复**：
```yaml
# docker-compose.yml 或 docker run 时
environment:
  - TZ=Asia/Shanghai
```

### 坑 6：数据存在容器内，重建后全丢了

**症状**：`docker compose down && docker compose up` 后，之前上传的文件、数据库内容全没了。

**根因**：容器默认是"无状态"的，容器删除 = 容器内文件全删。

**修复**：需要持久化的数据用 Volume：
```yaml
volumes:
  - ./data:/app/data         # 挂载宿主机目录
  - db_data:/var/lib/mysql   # 命名卷（Docker 管理）
```

### 坑 7：K8s Pod 一直 `CrashLoopBackOff`

**症状**：`kubectl get pods` 显示 `CrashLoopBackOff`，Restarts 数字不断增加。

**排查流程**：
```bash
kubectl logs <pod-name>                 # 看崩溃前的日志
kubectl logs <pod-name> --previous      # 看上一次崩溃的日志
kubectl describe pod <pod-name>         # 看事件（Events）
```

**常见原因**：
- 启动命令（CMD）不对
- 缺少环境变量（API Key 没配）
- 内存 limit 太小，被 OOM Kill

### 坑 8：K8s 里两个 Service 端口混淆

**概念澄清**：
```yaml
spec:
  ports:
    - port: 80           # Service 暴露的端口（集群内访问用这个）
      targetPort: 8000   # Pod 里容器实际监听的端口
      nodePort: 30080    # Node 上暴露的端口（type: NodePort 时）
```

> 记忆法：`port` 是"门牌号"，`targetPort` 是"房间号"，`nodePort` 是"大楼号"。

### 坑 9：YAML 缩进错误导致部署失败

**症状**：`kubectl apply` 报 `error parsing YAML`。

**根因**：YAML 对缩进极其敏感，用了 Tab 或缩进不一致。

**防御**：
- 编辑器设置 YAML 文件用 2 空格缩进，禁用 Tab
- 部署前用 `kubectl apply --dry-run=client -f file.yaml` 验证
- 安装 VS Code 的 YAML 插件（自动校验）

### 坑 10：过早引入 K8s

**症状**：团队 3 个人，1 个 Agent 服务，花了两周搭 K8s 集群。

**诊断**：K8s 的运维复杂度是真实成本。如果你的场景 Docker Compose 就够了，不要为了"技术前瞻性"上 K8s。

**判断标准**：
- 只有 1-3 个服务 + 单机 → Docker Compose
- 需要跨机器 + 自动伸缩 + 零停机更新 → K8s
- 有现成 K8s 集群（公司平台或云托管）→ 直接用

---

## 12. 排障手册：出了问题怎么查

> "问题不可怕，不知道怎么查才可怕。"

### 12.1 Docker 排障思路

```
容器没跑起来？
  │
  ├── docker ps -a 看状态
  │     └── Exited? → docker logs <name> 看退出原因
  │     └── Created（没启动）? → docker inspect <name> 看配置
  │
  ├── 镜像 build 失败？
  │     └── 看报错在哪一层（RUN 命令行号）
  │     └── 进入前一层调试：docker run -it <前一层镜像> bash
  │
  └── 端口访问不了？
        └── docker ps 确认端口映射对不对
        └── docker exec 进容器 curl localhost:端口 测试
        └── 防火墙/安全组是否放行
```

### 12.2 K8s 排障思路

```
Pod 起不来？
  │
  ├── kubectl describe pod <name>  ← 看 Events 段
  │     ├── ImagePullBackOff → 镜像名/仓库权限/网络
  │     ├── CrashLoopBackOff → 应用崩溃，看 logs
  │     ├── Pending → 资源不够，describe 看 Conditions
  │     └── OOMKilled → 内存 limit 太小
  │
  ├── kubectl logs <pod> ← 看应用日志
  │     └── --previous 看上一次崩溃日志
  │
  ├── 服务访问不了？
  │     ├── kubectl get svc → Service 创建了吗？
  │     ├── kubectl get endpoints → 有没有 Pod 关联上？
  │     └── kubectl port-forward pod/xxx 8080:8000 → 绕过 Service 直测
  │
  └── 不确定？万能排查三连：
        1. kubectl get events --sort-by='.metadata.creationTimestamp'
        2. kubectl describe pod <name>
        3. kubectl logs <name> --previous
```

### 12.3 常用调试命令速记

```bash
# Docker
docker logs <container> -f --tail 100    # 实时日志
docker exec -it <container> bash         # 进容器
docker inspect <container> | grep -i ip  # 查容器 IP
docker stats                             # 实时资源监控

# K8s
kubectl run debug --image=busybox -it -- sh   # 启临时 Pod 测网络
kubectl top pods                               # 资源使用（需 metrics-server）
kubectl get events -w                          # 实时事件流
```

---

## 13. 心智模型总结：一张图串起所有概念

学完所有章节后，这张图帮你把所有概念关系连起来：

```
         你的代码 + 依赖
              │
              ▼
    ┌─────────────────┐
    │   Dockerfile     │  "设计图"
    └────────┬────────┘
        docker build
              │
              ▼
    ┌─────────────────┐
    │     Image        │  "模具" ──推到──→ Registry（镜像仓库）
    └────────┬────────┘
        docker run                     kubectl apply
              │                              │
    ┌─────────▼───────┐          ┌───────────▼──────────┐
    │   Container      │          │     K8s Cluster       │
    │   (单机运行)     │          │                       │
    │                  │          │  Deployment           │
    │  ▸ 端口映射      │          │    └→ ReplicaSet      │
    │  ▸ 卷挂载        │          │        └→ Pod ×N      │
    │  ▸ 环境变量      │          │            └→Container│
    └─────────────────┘          │                       │
                                 │  Service (负载均衡)    │
    Docker Compose               │  Ingress (域名路由)    │
    (单机多容器编排)              │  HPA (自动伸缩)       │
                                 │  Secret (密钥管理)     │
                                 └───────────────────────┘

    ← 简单 ──────────── 复杂度 ──────────── 复杂 →
    适合: 1-3人/单机               适合: 团队/多机/生产
```

### 学习完成自检 ✅

| 能力检查点 | 对应章节 | 你能做到吗？ |
|-----------|---------|:-----------:|
| 向非技术人员解释容器化的价值 | §1 | ☐ |
| 画出 Dockerfile → Image → Container 的关系 | §2 | ☐ |
| 独立编写 Dockerfile 并成功构建 | §3 | ☐ |
| 用 Compose 编排 2+ 服务并验证互通 | §4 | ☐ |
| 说出 Docker 和 K8s 的职责边界 | §5 | ☐ |
| 认识 Pod / Deployment / Service 三件套 | §6 | ☐ |
| 读懂 K8s 部署 YAML 的核心字段 | §7 | ☐ |
| 列出 Agent 部署的 3 个特殊考量 | §8 | ☐ |
| 根据场景做出 Docker vs K8s 的选型决策 | §9 | ☐ |
| 遇到问题时知道第一步查什么 | §12 | ☐ |

> 如果你能勾上前 5 项，你已经足以在日常工作中独立使用 Docker 部署 Agent 服务了。后面的 K8s 部分可以在需要时再回来看。

---

## 延伸阅读

### 入门推荐（按优先级排序）

| 资源 | 说明 | 推荐指数 |
|------|------|:-------:|
| [Docker 官方入门](https://docs.docker.com/get-started/) | 动手实验，2 小时入门 | ⭐⭐⭐⭐⭐ |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Windows / Mac 安装 Docker | ⭐⭐⭐⭐⭐ |
| [《Docker — 从入门到实践》](https://yeasy.gitbook.io/docker_practice/) | 中文社区经典电子书 | ⭐⭐⭐⭐ |
| [K8s 官方中文教程](https://kubernetes.io/zh-cn/docs/tutorials/) | 交互式学习 | ⭐⭐⭐⭐ |
| [Play with K8s](https://labs.play-with-k8s.com/) | 浏览器里体验 K8s 集群 | ⭐⭐⭐⭐ |
| [Awesome-Docker](https://github.com/veggiemonk/awesome-docker) | Docker 资源大全 | ⭐⭐⭐ |

### 进阶深入

| 资源 | 说明 |
|------|------|
| [Docker 多阶段构建](https://docs.docker.com/build/building/multi-stage/) | 进一步压缩镜像体积 |
| [K8s Patterns](https://k8spatterns.io/) | K8s 设计模式，理解"为什么这样设计" |
| [Helm](https://helm.sh/) | K8s 的"包管理器"，管理复杂部署 |
| [ArgoCD](https://argo-cd.readthedocs.io/) | GitOps 持续部署——用 Git 管理 K8s 状态 |

### 学习路径建议

```
Week 1: Docker 基础（本文 §1-4 + 动手实验）
   ↓
Week 2: 把自己的真实项目容器化
   ↓
Week 3: Docker Compose 编排多服务（含 Redis/数据库）
   ↓
------- 以上足以应对大部分场景 -------
   ↓
需要时: K8s 概念（§5-7）→ 公司有集群就直接上手
   ↓
需要时: Helm + CI/CD 管道 → 自动化部署
```

---

*撰写日期：2026-04-22 | 学习向扩充：2026-04-23*
