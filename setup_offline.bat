@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ========================================
echo   FPGA Toolbox - 离线部署向导 (Windows)
echo ========================================
echo.
echo 当前目录: %cd%
echo.

:: ============================================================
:: Step 1: 检查 runtime 是否已完整
:: ============================================================
if exist "runtime\python.exe" (
    if exist "runtime\Lib\site-packages\paramiko" (
        if exist "runtime\Lib\site-packages\PIL" (
            echo [√] runtime 已就绪！可以直接使用。
            echo.
            echo 双击 run.bat 启动 FPGA Toolbox
            goto :done
        )
    )
)

echo [!] runtime 不完整或不存在，需要补全
echo.

:: ============================================================
:: Step 2: 优先尝试用 build_portable_runtime.py (推荐, 完整含 tkinter)
:: ============================================================
where python >nul 2>&1
if %errorlevel% neq 0 goto :no_python

echo [→] 找到系统 Python，准备调 build_portable_runtime.py ...
echo.

python --version
echo.
echo    该脚本会自动:
echo      1. 复制 Python 解释器 + tkinter + 标准库到 runtime\
echo      2. 用 pip 安装 paramiko / pillow / pyserial 到 runtime\Lib\site-packages\
echo      3. 验证所有依赖可加载
echo.

python "%~dp0scripts\build_portable_runtime.py"
if %errorlevel% neq 0 (
    echo.
    echo [×] 构建失败，请检查上面的错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [√] 部署完成!
echo ========================================
echo.
echo 启动方式: 双击 run.bat
echo.
goto :done

:: ============================================================
:: Step 3: 系统中没 Python, 给出提示
:: ============================================================
:no_python
echo.
echo ========================================
echo   [×] 未找到 Python 3.13
echo ========================================
echo.
echo 当前电脑没有 Python, 但有 2 种解决方案:
echo.
echo 方案 A: 在任意有 Python 3.10+ 的电脑上跑 build_portable_runtime.py
echo   1. 把整个 tool\ 目录复制到该电脑
echo   2. python scripts\build_portable_runtime.py
echo   3. 把生成的 runtime\ 目录复制回原电脑
echo.
echo 方案 B: 下载 Python 3.13 官方安装包
echo   1. 访问 https://www.python.org/downloads/release/python-3135/
echo   2. 下载 "Windows installer (64-bit)"
echo   3. 安装时勾选 "Add Python to PATH" 和 "tcl/tk and IDLE"
echo   4. 安装后重新运行 setup_offline.bat
echo.
pause
exit /b 1

:done
echo.
echo 启动方式:
echo   Windows: 双击 run.bat
echo.
pause
exit /b 0
