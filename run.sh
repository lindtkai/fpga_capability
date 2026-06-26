#!/bin/bash
# FPGA Toolbox — Linux 启动入口
# 优先使用便携 runtime (runtime_linux/), 退回系统 Python
# 用法: ./run.sh [参数...]

# 不让任何错误静默吞掉, 关键步骤失败要让用户看到
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# ── 1. 优先使用便携 runtime_linux/ (cbs-zig 跨平台预编译) ──
# cbs-zig install_only 解压后结构:
#   runtime_linux/
#     bin/python3, bin/python3.13
#     lib/python3.13/...
#     include/...
#     share/...
#     python3.13._pth (配置 site-packages 路径)
# 第三方库需要装到 lib/python3.13/site-packages/
RT_PY=""
for cand in \
    "$DIR/runtime_linux/bin/python3" \
    "$DIR/runtime_linux/bin/python3.13" \
    "$DIR/runtime_linux/python" \
    "$DIR/runtime_linux/bin/python"; do
    if [ -f "$cand" ] && [ -x "$cand" ]; then
        RT_PY="$cand"
        break
    fi
done

# ── 2. 兼容旧版本: 单一 runtime/ 也支持 (Windows 版或早期 Linux 版) ──
if [ -z "$RT_PY" ]; then
    for cand in \
        "$DIR/runtime/python/bin/python3" \
        "$DIR/runtime/python/bin/python3.13" \
        "$DIR/runtime/bin/python3" \
        "$DIR/runtime/python" \
        "$DIR/runtime/bin/python"; do
        if [ -f "$cand" ] && [ -x "$cand" ]; then
            RT_PY="$cand"
            break
        fi
    done
fi

if [ -n "$RT_PY" ]; then
    echo "[run.sh] 使用便携 Python: $RT_PY"
    exec "$RT_PY" "$DIR/src/gen_inst.py" "$@"
fi

# ── 3. 退回系统 Python (兜底) ──
PY=""
for p in python3 python; do
    if command -v "$p" &>/dev/null; then PY="$p"; break; fi
done

if [ -z "$PY" ]; then
    echo "==========================================="
    echo "  [x] 未找到 Python 运行环境"
    echo "==========================================="
    echo
    echo "此工具需要 Python 3 运行时, 当前系统没有安装 Python,"
    echo "且 runtime_linux/ 目录中没有便携版 Python (Linux 端需要 runtime_linux/bin/python3)。"
    echo
    echo "解决方法:"
    echo "  1. 在 Windows / Linux 开发机上运行 build_portable_runtime.py 自动下载 cbs-zig 包"
    echo "     生成的 runtime_linux/ 拷到目标机器, 即可在无网无 Python 环境运行"
    echo "  2. 或在 Ubuntu/Debian:  sudo apt install python3 python3-tk python3-pip"
    echo "     CentOS/RHEL:        sudo yum install python3 python3-tkinter python3-pip"
    echo "     Fedora:             sudo dnf install python3 python3-tkinter python3-pip"
    echo "  3. 或查看 docs/README_SETUP.txt 了解手动配置方法"
    echo
    exit 1
fi

# 检查 tkinter
if ! $PY -c "import tkinter" 2>/dev/null; then
    echo "==========================================="
    echo "  [!] tkinter 缺失"
    echo "==========================================="
    echo
    echo "  Ubuntu/Debian:  sudo apt install python3-tk"
    echo "  CentOS/RHEL:    sudo yum install python3-tkinter"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo
    echo "  提示: 如果要无网无 Python 运行, 请在开发机上生成 runtime_linux/"
    echo "        (见 build_portable_runtime.py)"
    echo
    echo "  注意: cbs-zig 的 install_only Linux 版不含 _tkinter.so,"
    echo "        重建时必须用 --linux-variant full 系列 (默认 noopt-full):"
    echo "          python scripts/build_portable_runtime.py --target linux"
    echo
    exit 1
fi

echo "Python: $($PY --version)"
exec $PY "$DIR/src/gen_inst.py" "$@"
