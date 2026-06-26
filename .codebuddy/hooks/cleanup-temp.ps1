<#
.SYNOPSIS
  清理工作区内的临时/调试文件 (一键)

.DESCRIPTION
  删除规则 (仅工作区根目录, 递归最多 3 层, 不删 src/runtime/runtime_linux 等正式目录):
    - 以 _test_ 或 _tmp_ 或 _debug_ 开头的文件/目录
    - 以 _test_ 或 _tmp_ 或 _debug_ 开头的 .py/.xlsx/.csv/.log/.txt
    - *.pyc  (Python 缓存, 不在 runtime/ 下)
    - 临时 xlsx/csv/json/pickle (在根目录或 _test/ 子目录)

.PARAMETER Root
  工作区根目录, 默认从脚本所在目录向上找

.EXAMPLE
  pwsh -ExecutionPolicy Bypass -File .codebuddy/hooks/cleanup-temp.ps1
  # 或
  . .codebuddy/hooks/cleanup-temp.ps1 ; Invoke-CleanupTemp
#>

[CmdletBinding()]
param(
    [string]$Root
)

$ErrorActionPreference = 'Stop'

# 1) 定位工作区根
if (-not $Root) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Root = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
}
if (-not (Test-Path $Root)) {
    Write-Host "[cleanup-temp] Root not found: $Root" -ForegroundColor Red
    exit 1
}

Write-Host "[cleanup-temp] Workspace: $Root" -ForegroundColor Cyan

# 2) 规则: 匹配 _test_ / _tmp_ / _debug_ 前缀 (任意扩展名或无扩展名)
$prefixPattern = '^_?(test|tmp|debug)_'
$prefixRegex   = '^(test|tmp|debug)_'

# 3) 临时扩展名
$tempExts = @('.pyc', '.tmp', '.bak', '.orig', '.swp', '.swo')

# 4) 排除的目录 (绝不能碰)
$excludeDirs = @(
    'runtime', 'runtime_linux', '_pyserial_lib',
    '.git', '.codebuddy', '.venv', 'node_modules', '__pycache__',
    'assets', 'docs', 'ip_docs', 'iperf3_bin', 'scripts', 'src'
)

function Test-ExcludedPath {
    param([string]$FullPath, [string]$RootPath)
    $rel = $FullPath.Substring($RootPath.Length).TrimStart('\','/')
    $first = ($rel -split '[\\/]')[0]
    return $excludeDirs -contains $first
}

$removed = 0
$kept   = 0

# ── 阶段 A: 扫根目录 + 第一层子目录的临时文件/目录 (快捷删除) ──
Get-ChildItem -LiteralPath $Root -Depth 2 -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $full = $_.FullName
    if (Test-ExcludedPath -FullPath $full -RootPath $Root) { $kept++; return }

    $name = $_.Name
    $isDir = $_.PSIsContainer
    $shouldRemove = $false
    $reason = ''

    # 前缀规则
    if ($name -match $prefixPattern) {
        $shouldRemove = $true; $reason = "prefix match ($name)"
    }
    # 临时扩展名 (但要排除 runtime/_pyserial_lib 等, 已通过 excludeDirs 处理)
    elseif (-not $isDir -and ($tempExts -contains $_.Extension.ToLower())) {
        $shouldRemove = $true; $reason = "temp ext ($($_.Extension))"
    }
    # 根目录下的 .xlsx/.csv/.json (用户工程正式文件通常在子目录)
    elseif (-not $isDir -and $_.DirectoryName -eq $Root) {
        $ext = $_.Extension.ToLower()
        if ($ext -in @('.xlsx','.xls','.csv','.json','.pickle','.pkl','.log')) {
            # 仅当文件名前缀匹配 test/tmp/debug, 或者 名字本身是 _test_xxx.xlsx 这种
            if ($name -match '^_?(test|tmp|debug)_' -or $name -match $prefixRegex) {
                $shouldRemove = $true; $reason = "root temp file ($name)"
            }
        }
    }

    if ($shouldRemove) {
        try {
            if ($isDir) { Remove-Item -LiteralPath $full -Recurse -Force }
            else        { Remove-Item -LiteralPath $full -Force }
            Write-Host "  [RM] $reason`n       $full" -ForegroundColor DarkYellow
            $script:removed++
        } catch {
            Write-Host "  [!!] Failed: $full`n       $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        $script:kept++
    }
}

Write-Host ""
Write-Host "[cleanup-temp] removed: $removed   kept: $kept" -ForegroundColor Green
