"""tune.py — Qwen3.6 在 8GB 显卡上的性能调优一键工具。

干两件事:
    1. 检查并设置关键环境变量（KV q8_0 / FlashAttn / KEEP_ALIVE / NUM_PARALLEL=1 / MODELS 路径）
    2. 创建一个调优过的 Modelfile（num_gpu / num_ctx / sampling 全部预设好）

用法:
    python tune.py --check              # 只看当前设置，不改
    python tune.py --apply              # 设置环境变量（用户级，永久生效）
    python tune.py --create-modelfile   # 生成 qwen3.6-tuned 模型
    python tune.py --all                # 全套：apply + create

调优后启动:
    ollama run qwen3.6-tuned --verbose

参考: R75 阶段 3 性能优化清单。
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_ENV = {
    "OLLAMA_KV_CACHE_TYPE": "q8_0",          # KV 量化，省 50% 显存
    "OLLAMA_FLASH_ATTENTION": "1",            # Flash Attention，长上下文必开
    "OLLAMA_KEEP_ALIVE": "24h",               # 模型常驻 RAM，避免冷启动 30 秒
    "OLLAMA_NUM_PARALLEL": "1",               # 8GB 显卡老老实实串行
    "OLLAMA_NUM_GPU": "32",                   # Qwen3.6-35B-A3B 推荐 GPU 层数
}

OPTIONAL_ENV = {
    "OLLAMA_MODELS": r"F:\ollama_models",     # 模型存非 C 盘
}


MODELFILE_TEMPLATE = """FROM {base_model}
PARAMETER num_gpu {num_gpu}
PARAMETER num_ctx {num_ctx}
PARAMETER num_predict 4096
PARAMETER temperature {temperature}
PARAMETER top_p {top_p}
PARAMETER top_k 20
PARAMETER min_p 0.0
PARAMETER repeat_penalty 1.0
"""


def check_env() -> dict[str, tuple[str | None, str]]:
    """返回 {key: (current_value, recommended_value)}"""
    out = {}
    for k, v in {**REQUIRED_ENV, **OPTIONAL_ENV}.items():
        out[k] = (os.environ.get(k), v)
    return out


def print_env_status():
    print("=== 当前 Ollama 优化环境变量 ===\n")
    status = check_env()
    for k, (cur, rec) in status.items():
        if cur == rec:
            mark = "✅"
        elif cur is None:
            mark = "❌ 未设置"
        else:
            mark = f"⚠️  当前={cur}"
        print(f"  {mark:<22} {k}={rec}")
    print()


def apply_env(only_required: bool = True):
    """通过 setx 命令设置用户级环境变量（Windows 永久生效）。"""
    if platform.system() != "Windows":
        print("[!] 非 Windows 平台，请手动设置环境变量。")
        return

    targets = REQUIRED_ENV.copy()
    if not only_required:
        targets.update(OPTIONAL_ENV)

    print("=== 设置用户级环境变量（永久）===\n")
    for k, v in targets.items():
        try:
            # setx 是 Windows 内置命令，影响新终端
            subprocess.run(["setx", k, v], check=True, capture_output=True, text=True)
            print(f"  ✅ setx {k}={v}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ setx {k} 失败: {e.stderr}")

    print("\n⚠️  关键提醒:")
    print("   1. 这些变量在 *新打开* 的终端才生效")
    print("   2. 必须重启 Ollama 服务才能应用 KV q8_0 / FlashAttention")
    print("      执行: Get-Process ollama* | Stop-Process -Force")
    print("           然后重新启动 Ollama 桌面应用")


def create_tuned_model(base_model: str, target_name: str, num_gpu: int,
                       num_ctx: int, thinking: bool):
    """创建一个调优过的 Ollama 模型。"""
    if not shutil.which("ollama"):
        print("[!] ollama 命令不可用，请确认 PATH 包含 Ollama 安装目录")
        return False

    temperature = 1.0 if thinking else 0.7
    top_p = 0.95 if thinking else 0.8

    modelfile_content = MODELFILE_TEMPLATE.format(
        base_model=base_model,
        num_gpu=num_gpu,
        num_ctx=num_ctx,
        temperature=temperature,
        top_p=top_p,
    )

    workdir = Path(__file__).parent
    modelfile = workdir / f"Modelfile.{target_name}"
    modelfile.write_text(modelfile_content, encoding="ascii")
    print(f"[OK] Modelfile 写入: {modelfile}")
    print("---")
    print(modelfile_content)
    print("---")

    print(f"\n执行: ollama create {target_name} -f {modelfile.name}")
    try:
        result = subprocess.run(
            ["ollama", "create", target_name, "-f", str(modelfile)],
            capture_output=True, text=True, timeout=120,
        )
        print(result.stdout or "")
        if result.returncode != 0:
            print(f"[FAIL] {result.stderr}")
            return False
        print(f"\n✅ 创建成功！现在可以跑：ollama run {target_name} --verbose")
        return True
    except FileNotFoundError:
        print("[!] ollama 不在 PATH，请先 setx Path …")
        return False
    except subprocess.TimeoutExpired:
        print("[!] ollama create 超时（>2分钟），可能 base 模型未拉")
        return False


def main():
    parser = argparse.ArgumentParser(description="Qwen3.6 在 8GB 显卡上的性能调优")
    parser.add_argument("--check", action="store_true", help="只查当前环境变量")
    parser.add_argument("--apply", action="store_true", help="设置环境变量")
    parser.add_argument("--apply-all", action="store_true",
                        help="设置环境变量（含可选项 OLLAMA_MODELS）")
    parser.add_argument("--create-modelfile", action="store_true",
                        help="创建调优后的 Modelfile + ollama create")
    parser.add_argument("--all", action="store_true", help="一键全做：apply + create")
    parser.add_argument("--base-model", default="qwen3.6:35b")
    parser.add_argument("--target-name", default="qwen3.6-tuned")
    parser.add_argument("--num-gpu", type=int, default=32,
                        help="GPU 层数（Qwen3.6-35B-A3B 共 40 层，推荐 28-36）")
    parser.add_argument("--num-ctx", type=int, default=16384,
                        help="上下文窗口（必开 KV q8 + FlashAttn 才能拉到 32768）")
    parser.add_argument("--thinking", action="store_true",
                        help="为 thinking 模式优化采样（temp=1.0, top_p=0.95）")
    args = parser.parse_args()

    if not any([args.check, args.apply, args.apply_all, args.create_modelfile, args.all]):
        # 默认动作：check
        args.check = True

    if args.check or args.all:
        print_env_status()

    if args.apply or args.all:
        apply_env(only_required=True)
        print()
    elif args.apply_all:
        apply_env(only_required=False)
        print()

    if args.create_modelfile or args.all:
        ok = create_tuned_model(
            base_model=args.base_model,
            target_name=args.target_name,
            num_gpu=args.num_gpu,
            num_ctx=args.num_ctx,
            thinking=args.thinking,
        )
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()
