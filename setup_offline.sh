#!/bin/bash
# FPGA Toolbox — Linux 离线环境部署向导
# 把当前系统的 Python + 依赖打包到 runtime/ 目录
# 目标机器无需装 Python, 也无需联网, 直接 ./run.sh 启动
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo
echo "=========================================="
echo "  FPGA Toolbox — 离线部署向导 (Linux)"
echo "=========================================="
echo
echo "当前目录: $DIR"
echo

# 检查 runtime 是否已完整
# 完整性条件: 1) python 解释器存在  2) paramiko 已装  3) Linux 还要 _tkinter.so (GUI 必需)
RUNTIME_OK=0
for py_cand in \
    "$DIR/runtime_linux/bin/python3" \
    "$DIR/runtime_linux/bin/python3.13" \
    "$DIR/runtime_linux/python" \
    "$DIR/runtime/python/bin/python3" \
    "$DIR/runtime/bin/python3" \
    "$DIR/runtime/python.exe" ; do
    if [ -f "$py_cand" ]; then
        # 找 paramiko + _tkinter
        for sp in \
            "$DIR/runtime_linux/lib/python3.13/site-packages" \
            "$DIR/runtime/python/lib/python3.13/site-packages" \
            "$DIR/runtime/Lib/site-packages" \
            "$DIR/runtime/lib/python3.13/site-packages" ; do
            if [ -d "$sp/paramiko" ]; then
                # Linux runtime 必须有 _tkinter.so (install_only 没有)
                if [ -f "$py_cand" ] && [[ "$py_cand" == *linux* || "$py_cand" == *runtime_linux* ]]; then
                    if ls "$sp"/../../lib-dynload/_tkinter*.so >/dev/null 2>&1 \
                       || ls "$DIR/runtime_linux/lib/python3.13/lib-dynload/_tkinter*.so" >/dev/null 2>&1 \
                       || ls "$DIR/runtime/python/lib/python3.13/lib-dynload/_tkinter*.so" >/dev/null 2>&1; then
                        RUNTIME_OK=1
                    fi
                else
                    # Windows install_only 自带 _tkinter.pyd
                    RUNTIME_OK=1
                fi
            fi
        done
    fi
done
if [ "$RUNTIME_OK" = "1" ]; then
    echo "[OK] runtime 已就绪"
    echo
    echo "直接执行 ./run.sh 启动 FPGA Toolbox"
    exit 0
fi

# 查找系统 Python
PY=""
for p in python3 python; do
    if command -v "$p" &>/dev/null; then PY="$p"; break; fi
done

if [ -z "$PY" ]; then
    echo "[!] 当前系统没有 Python, 无法自动部署"
    echo
    echo "请在有 Python 的电脑上:"
    echo "  1. 安装 Python 3.10+ 和 tkinter"
    echo "  2. 运行 ./scripts/make_portable.sh 生成 runtime/"
    echo "  3. 把整个工程目录 (含 runtime/) 复制到目标电脑"
    echo
    echo "或者直接在目标电脑安装:"
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-tk python3-pip"
    echo "  CentOS/RHEL:    sudo yum install python3 python3-tkinter python3-pip"
    echo "  Fedora:         sudo dnf install python3 python3-tkinter python3-pip"
    echo
    exit 1
fi

echo "[1/3] Python: $($PY --version)"
echo

# 检查 tkinter
if ! $PY -c "import tkinter" 2>/dev/null; then
    echo "[!] tkinter 缺失"
    echo
    echo "请先安装:"
    echo "  Ubuntu/Debian:  sudo apt install python3-tk"
    echo "  CentOS/RHEL:    sudo yum install python3-tkinter"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo
    exit 1
fi

# 调用 build 脚本
echo "[2/3] 调 build_portable_runtime.py ..."
echo
SCRIPT="$DIR/scripts/make_portable.sh"
if [ -f "$SCRIPT" ]; then
    bash "$SCRIPT"
else
    echo "[!] 未找到 scripts/make_portable.sh"
    exit 1
fi

echo
echo "[3/3] 验证 runtime ..."
RT_PY=""
for p in "$DIR/runtime/python/bin/python3" "$DIR/runtime/bin/python3" "$DIR/runtime/python"; do
    if [ -x "$p" ]; then RT_PY="$p"; break; fi
done

if [ -n "$RT_PY" ]; then
    if $RT_PY -c "import tkinter, paramiko, PIL, serial; print('[OK] all deps loaded')" 2>/dev/null; then
        echo "[OK] runtime 验证通过"
    else
        echo "[!] runtime 验证失败, 可能缺少依赖"
        echo "    尝试: $RT_PY -m pip install paramiko pillow pyserial"
    fi
fi

echo
echo "=========================================="
echo "  [OK] 部署完成!"
echo "=========================================="
echo
echo "启动方式: ./run.sh"
echo
