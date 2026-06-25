# ── FPGA Toolbox: 自动清理临时文件 ──
# 在 PowerShell profile 里 dot-source 此文件即可启用 `cleanup-temp` 命令
# 安装:  Add-Content $PROFILE "`n. '$PSScriptRoot\load-cleanup.ps1'"

$script:CleanupScript = Join-Path $PSScriptRoot 'cleanup-temp.ps1'

function cleanup-temp {
<#
.SYNOPSIS
  清理工作区内的临时/调试文件

.DESCRIPTION
  删除以 _test_/_tmp_/_debug_ 开头的文件/目录, 以及根目录的临时 xlsx/csv/log。
  安全: 不碰 src/runtime/runtime_linux/scripts/docs 等正式目录。

.EXAMPLE
  cleanup-temp
  cleanup-temp -Root 'D:\proj\foo'
#>
    [CmdletBinding()]
    param(
        [string]$Root
    )
    if (-not $Root) {
        $Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    }
    & $script:CleanupScript -Root $Root
}

# 别名 (短名)
Set-Alias -Name cct -Value cleanup-temp -Force -Scope Global
Set-Alias -Name clean -Value cleanup-temp -Force -Scope Global

Write-Host "[load-cleanup] cleanup-temp / cct / clean 已注册" -ForegroundColor DarkCyan
