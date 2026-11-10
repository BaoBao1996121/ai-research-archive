> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# Docker GPU + 大模型服务速查卡

> 补充 `tutorial/Docker与K8s技术科普_面向Agent服务部署.md` 未深入覆盖的 GPU 场景。
> 日期：2026-05-31
> 前置阅读：tutorial 的 §2-§3（Docker 基础三大件 + Dockerfile）

---

## 1. `--gpus` 参数完整语法

**前置条件**：宿主机必须安装两样东西：
1. NVIDIA GPU 驱动（`nvidia-smi` 能看到 GPU）
2. NVIDIA Container Toolkit（原 nvidia-docker2）

```bash
# 验证前置条件
nvidia-smi                    # 能看到 GPU 列表和驱动版本就对了
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi  # 容器内也能看到
```

### 语法速查

| 写法 | 效果 |
|------|------|
| `--gpus all` | 暴露所有 GPU |
| `--gpus device=0` | 只暴露第 0 号 GPU |
| `--gpus '"device=0,2"'` | 暴露第 0 和第 2 号（注意引号嵌套） |
| `--gpus device=GPU-3a23c669-...` | 按 UUID 指定（`nvidia-smi -L` 查 UUID） |
| `--gpus 'all,capabilities=utility'` | 暴露全部 + 指定 capabilities |

**多 GPU 服务器分配策略**：两个模型服务各占一块卡——
```bash
docker run --gpus device=0 -d --name vllm-qwen vllm-image
docker run --gpus device=1 -d --name vllm-deepseek vllm-image
```

---

## 2. NVIDIA Container Toolkit 安装（Linux）

```bash
# Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 配置 Docker 运行时
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

> Windows Docker Desktop：内置支持 WSL2 GPU Passthrough，确保 WSL2 后端开启 + NVIDIA 驱动已装即可，不需要手动装 toolkit。

---

## 3. 大模型服务为什么用 Volume 而不是 COPY

| 对比 | `COPY model/ /app/model/` | `-v /host/models:/models:ro` |
|------|:---:|:---:|
| **镜像大小** | +7~70GB（模型打进层） | 镜像保持 ~2GB |
| **构建时间** | 每次 build 拷贝一遍（分钟级） | 0（不参与 build） |
| **模型更新** | 要重新 build + push 镜像 | 宿主机换文件即可 |
| **多容器共享** | 每个容器各一份副本 | 所有容器共享同一份文件 |
| **镜像分发** | push 到 registry 要传 70GB | 镜像只传推理代码 ~2GB |
| **磁盘占用** | N 个版本 = N × 70GB 层 | 模型只存一份 |

**结论**：模型文件又大又独立于代码变更，**永远用 volume 挂载**。这是行业共识。

---

## 4. `:ro` 只读挂载 vs 可读写挂载

```bash
-v /path/on/host:/path/in/container:ro    # 只读
-v /path/on/host:/path/in/container       # 可读写（默认）
```

| 使用场景 | 推荐权限 | 原因 |
|---------|:--------:|------|
| 模型权重文件 | `:ro` | 容器不应修改模型；防止意外写入 |
| 配置文件 / .env | `:ro` | 运行时只读即可 |
| 日志目录 | 可读写 | 容器需要写入日志 |
| HuggingFace cache | 可读写 | 首次启动要下载/转换模型格式 |
| 推理输出/临时文件 | 可读写 | 容器产出需要持久化 |

**安全原则**：能 `:ro` 就 `:ro`，最小权限。

---

## 5. 实战：GPU 模型服务 docker run 命令解剖

### vLLM（高性能推理引擎）

```bash
docker run -d \
  --gpus '"device=0,1"' \           # 用 GPU 0 和 1
  --name vllm-qwen \                # 容器命名
  -p 8000:8000 \                    # 端口映射
  -v /data/models:/models:ro \      # 模型挂载（只读）
  -v /data/hf-cache:/root/.cache/huggingface \  # HF cache（要读写）
  -e CUDA_VISIBLE_DEVICES=0,1 \     # 环境变量：可见 GPU
  --restart unless-stopped \        # 异常退出自动重启，手动 stop 不重启
  --shm-size=8g \                   # 共享内存（多 GPU tensor parallel 需要）
  vllm/vllm-openai:latest \         # 镜像
  --model /models/Qwen2.5-72B-Instruct-AWQ \  # 以下是容器内命令参数
  --tensor-parallel-size 2 \
  --max-model-len 32768
```

### Ollama（简易本地推理）

```bash
docker run -d \
  --gpus all \
  --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \    # 命名卷存放下载的模型
  --restart unless-stopped \
  ollama/ollama:latest
```

### Text Generation Inference（HuggingFace TGI）

```bash
docker run -d \
  --gpus device=0 \
  --name tgi \
  -p 8080:80 \
  -v /data/models:/data:ro \
  --shm-size=1g \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id /data/Qwen2.5-7B-Instruct \
  --max-input-tokens 4096 \
  --max-total-tokens 8192
```

---

## 6. GPU Docker 常见问题排查

| 症状 | 原因 | 解法 |
|------|------|------|
| `could not select device driver "nvidia"` | 没装 NVIDIA Container Toolkit | 按 §2 安装 |
| `nvidia-smi` 容器内报错 | 驱动版本 < CUDA 要求 | 升级宿主机 NVIDIA 驱动 |
| `CUDA out of memory` | 模型太大 / 显存不够 | 用更小量化版本 / 减 `--max-model-len` |
| 容器启动后秒退 | 查 `docker logs <name>` | 通常是模型路径不对或显存不足 |
| `--shm-size` 不够 | 多 GPU tensor parallel 需要共享内存 | 加 `--shm-size=8g` 或更大 |
| 端口已被占用 | 宿主机 8000 端口已有服务 | 改映射 `-p 8001:8000` |
| volume 里模型文件权限 denied | Linux 用户 UID 不匹配 | `chmod -R 755 /data/models` 或 `--user $(id -u):$(id -g)` |

---

## 7. `--restart` 策略速查

| 策略 | 行为 |
|------|------|
| `no`（默认） | 不自动重启 |
| `on-failure[:max-retries]` | 非 0 退出时重启，可限次数 |
| `always` | 总是重启（含 Docker daemon 重启后） |
| `unless-stopped` | 同 always，但手动 `docker stop` 后不再自动启 |

**模型服务推荐** `unless-stopped`——异常崩溃自动恢复，但你手动停的时候不会自动弹回来。

---

## 8. 你的学习路径建议

基于你的实际场景（本地 GPU + 模型部署），建议的学习顺序：

```
① 读 tutorial/Docker与K8s技术科普_面向Agent服务部署.md 的 §1-§4
   → 30 分钟建立完整概念框架（够日常 95% 使用）

② 跑一遍 §3.5 的动手实验（5 分钟 Hello World）
   → 亲手体验 build → run → logs → exec → stop 完整闭环

③ 本速查卡 §5 的 vLLM/Ollama 命令逐参数理解
   → 对应你实际在用的 P06 Qwen 部署场景

④ 遇到问题 → tutorial §11-§12 + 本卡 §6 排查
```

不需要学 K8s（tutorial §5-§9），除非你的模型服务要上多机集群。
