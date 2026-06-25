@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM ============================================================
REM  FPGA Toolbox 启动器 (Windows)
REM  查找顺序:
REM    1. runtime_windows\python.exe       (新格式, cbs-zig install_only)
REM    2. runtime\python.exe               (旧格式, 兼容)
REM    3. 系统 python (where)
REM    4. py launcher (py -3)
REM    5. 常见安装路径
REM  任何失败都会 pause, 不会再闪退
REM ============================================================

set "SCRIPT_DIR=%~dp0"

REM ── 1. 优先使用便携 runtime_windows/ (新格式) ──
if exist "%SCRIPT_DIR%runtime_windows\python.exe" (
    echo [run.bat] 使用便携 Python: %SCRIPT_DIR%runtime_windows\python.exe
    "%SCRIPT_DIR%runtime_windows\python.exe" "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" (
        echo.
        echo [×] 程序异常退出, 返回码 %RC%
    )
    pause
    exit /b %RC%
)

REM ── 2. 兼容旧格式 runtime/ ──
if exist "%SCRIPT_DIR%runtime\python.exe" (
    echo [run.bat] 使用便携 Python: %SCRIPT_DIR%runtime\python.exe
    "%SCRIPT_DIR%runtime\python.exe" "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" (
        echo.
        echo [×] 程序异常退出, 返回码 %RC%
    )
    pause
    exit /b %RC%
)

REM ── 3. 检测残缺 runtime/ (有 python 子目录但无 python.exe) ──
if exist "%SCRIPT_DIR%runtime\python" (
    if not exist "%SCRIPT_DIR%runtime\python.exe" (
        echo.
        echo [×] runtime\ 目录是 Linux 版本 (缺少 python.exe)
        echo     当前电脑是 Windows, 需要重新生成 Windows 版本的 runtime
        echo.
        echo     解决方案 A: 在有 Python 3.13 的机器上跑
        echo                 python scripts\build_portable_runtime.py --target both
        echo                 会同时生成 runtime_windows\ 和 runtime_linux\
        echo     解决方案 B: 访问 https://www.python.org/downloads/
        echo                 安装 Python 3.13 (勾选 Add to PATH 和 tcl/tk and IDLE)
        echo.
        pause
        exit /b 1
    )
)

REM ── 4. 尝试系统 python (where) ──
where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" (
        echo.
        echo [×] 程序异常退出, 返回码 %RC%
    )
    pause
    exit /b %RC%
)

REM ── 5. 尝试 py launcher (Python 3.13 默认可用) ──
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" (
        echo.
        echo [×] 程序异常退出, 返回码 %RC%
    )
    pause
    exit /b %RC%
)

REM ── 6. 尝试常见安装路径 (兜底) ──
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
    "%LocalAppData%\Programs\Python\Python313\python.exe" "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" echo. & echo [×] 程序异常退出, 返回码 %RC%
    pause
    exit /b %RC%
)
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" echo. & echo [×] 程序异常退出, 返回码 %RC%
    pause
    exit /b %RC%
)
if exist "C:\Python313\python.exe" (
    "C:\Python313\python.exe" "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" echo. & echo [×] 程序异常退出, 返回码 %RC%
    pause
    exit /b %RC%
)
if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" "%SCRIPT_DIR%src\gen_inst.py" %*
    set RC=%errorlevel%
    if not "%RC%"=="0" echo. & echo [×] 程序异常退出, 返回码 %RC%
    pause
    exit /b %RC%
)

REM ── 7. 全部失败, 提示用户 ──
echo.
echo [×] 未找到 Python 运行环境。
echo.
echo 此工具需要 Python 3 运行时, 当前电脑没有可用的 Python,
echo 且 runtime_windows\ 和 runtime\ 中都没有便携版 Python。
echo.
echo 解决方法 A: 在有 Python 3.10+ 的电脑上跑:
echo            python scripts\build_portable_runtime.py --target both
echo            同时生成 Windows + Linux 两个 runtime, 拷到目标机器即可
echo 解决方法 B: 访问 https://www.python.org/downloads/
echo            安装 Python 3.13 (勾选 Add to PATH 和 tcl/tk and IDLE)
echo.
echo 详细说明见 docs\README_SETUP.txt
echo.
pause
exit /b 1
