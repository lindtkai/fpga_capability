#!/bin/bash
# FPGA Toolbox — 跨平台 build 脚本
# 在有 Python 3.10+ 的 Linux/macOS 上跑, 生成 runtime/ 目录
# 目标机器无需装 Python, 也无需联网
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=========================================="
echo "  FPGA Toolbox — Build Portable Runtime"
echo "=========================================="
echo
echo "  Project root: $(dirname $DIR)"
echo "  Target:       $(dirname $DIR)/runtime"
echo

# 找系统 Python
PY=""
for p in python3 python; do
    if command -v "$p" &>/dev/null; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
    echo "[X] python3 not found in PATH"
    exit 1
fi
echo "  Source Python: $($PY --version)"
echo

# 调用 Python build 脚本
exec $PY "$DIR/build_portable_runtime.py"
