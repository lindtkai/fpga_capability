# CodeBuddy 自动化 Hooks

每次代码改动后, 自动清理工作区里的临时/调试文件。

## 安装 (三选一)

### 1) PowerShell 永久别名 (推荐)

把下面这一行加到你的 PowerShell profile 里:

```powershell
notepad $PROFILE
# 在打开的文件末尾加上:
. 'C:\Users\tasson\Desktop\tool\tool\.codebuddy\hooks\load-cleanup.ps1'
```

重启 PowerShell 后, 任意位置都可以直接打:

```powershell
cleanup-temp      # 清理
cct               # 短名
clean             # 同上
```

### 2) 临时一次性使用 (无需安装)

```powershell
pwsh -ExecutionPolicy Bypass -File "C:\Users\tasson\Desktop\tool\tool\.codebuddy\hooks\cleanup-temp.ps1"
```

### 3) 双击 .cmd

在文件管理器双击 `cleanup-temp.cmd`, 用默认工作区清理。

## 清理规则 (只删临时, 绝不碰正式文件)

| 规则 | 示例 |
|---|---|
| 以 `_test_` / `_tmp_` / `_debug_` 开头的文件/目录 | `_test_pins.xlsx`, `_tmp/`, `_debug.log` |
| `*.pyc` 缓存 (排除 runtime/_pyserial_lib) | `foo.pyc` |
| 根目录下的 `*.xlsx` / `*.csv` / `*.json` / `*.log` | 临时测试文件 |

## 保护目录 (绝不动)

`runtime`, `runtime_linux`, `_pyserial_lib`, `.git`, `.codebuddy`, `assets`, `docs`, `ip_docs`, `iperf3_bin`, `scripts`, `src`, `__pycache__`

## 自定义规则

编辑 `cleanup-temp.ps1`:
- `prefixPattern` / `prefixRegex` — 改前缀
- `tempExts` — 改临时扩展名
- `excludeDirs` — 加/删保护目录
