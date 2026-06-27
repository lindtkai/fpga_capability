@echo off
rem ── 一键清理临时文件 ──
rem 用法:  cleanup-temp.cmd           (清理默认工作区)
rem       cleanup-temp.cmd  <path>   (清理指定工作区)

setlocal
set "ROOT=%~dp0..\.."
if "%~1" neq "" set "ROOT=%~1"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cleanup-temp.ps1" -Root "%ROOT%"
endlocal
