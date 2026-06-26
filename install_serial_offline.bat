@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ========================================
echo   串口助手 - 安装 pyserial (离线)
echo ========================================
echo.

set "SRC=%~dp0_pyserial_lib\serial"
set "DST=%~dp0runtime\Lib\site-packages\serial"

if not exist "%SRC%" (
    echo [X] 找不到源: %SRC%
    echo     请确认 _pyserial_lib\serial\ 目录存在
    pause
    exit /b 1
)

if not exist "%~dp0runtime\Lib\site-packages" (
    echo [i] 创建 runtime\Lib\site-packages\ ...
    mkdir "%~dp0runtime\Lib\site-packages" 2>nul
)

if exist "%DST%" (
    echo [i] 已存在 %DST% , 先删除...
    rmdir /s /q "%DST%"
)

echo [i] 复制 %SRC% -^> %DST% ...
xcopy /e /i /y /q "%SRC%" "%DST%" >nul
if errorlevel 1 (
    echo [X] 复制失败
    pause
    exit /b 1
)

:: 顺便复制 dist-info (让 pip list 能看到)
if exist "%~dp0_pyserial_lib\pyserial-3.5.dist-info" (
    if exist "%~dp0runtime\Lib\site-packages\pyserial-3.5.dist-info" (
        rmdir /s /q "%~dp0runtime\Lib\site-packages\pyserial-3.5.dist-info"
    )
    xcopy /e /i /y /q "%~dp0_pyserial_lib\pyserial-3.5.dist-info" "%~dp0runtime\Lib\site-packages\pyserial-3.5.dist-info" >nul
)

echo.
echo [V] pyserial 离线安装完成!
echo     双击 run.bat 启动, 串口助手即可使用
echo.
pause
