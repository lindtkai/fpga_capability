# FPGA 工具箱 — 功能 / 能力 / 使用说明

> 工具位置：`C:\Users\Administrator\Desktop\tool\tool`
> 入口脚本：`run.bat`（Windows 双击启动）/ `run.sh`（Linux/macOS）
> 主代码：`src/gen_gui.py`（16 个 Tab）+ `src/gen_inst.py`（后端算法）+ `src/app_config.py`（全局配置）
> 主题：ttkbootstrap 现代化卡片式 UI
> 语言：中文 / English（UI 文案全中文）

---

## 目录

1. [运行方式](#运行方式)
2. [Tab 总览](#tab-总览)
3. [Tab 1 — ⚡ 例化模板](#tab-1--例化模板)
4. [Tab 2 — 工程压缩](#tab-2--工程压缩)
5. [Tab 3 — 🔀 Git 提交](#tab-3--git-提交)
6. [Tab 4 — 🇨🇳 国产化](#tab-4--国产化)
7. [Tab 5 — 代码整理](#tab-5--代码整理)
8. [Tab 6 — 📚 IP 文档](#tab-6--ip-文档)
9. [Tab 7 — 🧮 计算器](#tab-7--计算器)
10. [Tab 8 — 🔌 约束生成](#tab-8--约束生成)
11. [Tab 9 — 分析辅助](#tab-9--分析辅助)
12. [Tab 10 — 串口助手](#tab-10--串口助手)
13. [Tab 11 — 🌐 网络助手](#tab-11--网络助手)
14. [Tab 12 — QCI 测试图](#tab-12--qci-测试图)
15. [Tab 13 — 📡 iperf3](#tab-13--iperf3)
16. [Tab 14 — 🔐 SSH/SFTP](#tab-14--sshsftp)
17. [Tab 15 — 🧪 仿真自动化](#tab-15--仿真自动化)
18. [Tab 16 — ⚙ 设置](#tab-16--设置)
19. [通用 FAQ](#通用-faq)

---

## 运行方式

```bat
:: Windows: 双击或命令行
cd /d C:\Users\Administrator\Desktop\tool\tool
run.bat
```

```bash
# Linux / macOS
cd /path/to/tool
./run.sh
```

启动后界面是 16 个 Tab 的 Notebook（ttkbootstrap 主题）。无外部依赖，Python 3.8+ 即可。

---

## Tab 总览

| #  | Tab         | 主要用途                  | 关键后端模块           |
| -- | ----------- | ------------------------- | ---------------------- |
| 1  | ⚡ 例化模板 | Verilog/SV 模板生成       | `gen_inst.parse_file` / `generate_templates` |
| 2  | 工程压缩    | Vivado 工程打包 / 归档    | `gen_inst.compress_project` / `archive_project` |
| 3  | 🔀 Git 提交 | 仓库初始化 / 提交 / 推送  | `subprocess.run(git ...)`（安全重试 WinError 32）|
| 4  | 🇨🇳 国产化  | Vivado → 国产 FPGA 厂商   | `t4_execute()`（IP 重打包 / tcl 改写）|
| 5  | 代码整理    | Verilog/SV 风格规范化     | `gen_inst.format_fpga_code` |
| 6  | 📚 IP 文档  | 离线 PDF 检索 + DocNav 在线下载 | `os.walk(ip_docs/)` + `amd_doc_downloader`（解析 xdocs.xml）|
| 7  | 🧮 计算器  | FPGA 专用计算            | 纯 Python 算法          |
| 8  | 🔌 约束生成 | XDC / 端口 / 时序约束     | `_get_vcco` / `xdc_writer` |
| 9  | 分析辅助    | CDC / 时序 / Log 诊断     | `_CDC_SCENARIOS` / `_WARN_TYPES` |
| 10 | 串口助手    | XCOM/SSCOM 风格串口调试   | `pyserial` (3 种加载路径自动回退) |
| 11 | 🌐 网络助手 | TCP/UDP 客户端/服务器     | `socket` + 网卡枚举     |
| 12 | QCI 测试图  | 流程图显示 / 缩放 / 导出  | `PIL.ImageTk`           |
| 13 | 📡 iperf3  | 网络打流（多版本）        | `iperf3_bin/*` 自动选最优 |
| 14 | 🔐 SSH/SFTP | 类 WinSCP 双栏文件管理    | `paramiko` + Tk Canvas |
| 15 | 🧪 仿真自动化 | Vivado → ModelSim 一键跑 | `tcl + do + f` 三件套生成 |
| 16 | ⚙ 设置     | Vivado / DocNav 全局路径管理 | `app_config`（统一持久化 `~/.fpga_tool/app_config.json`）|

---

## Tab 1 — ⚡ 例化模板

### 功能
自动解析 Verilog / SystemVerilog / VHDL 源文件，提取模块端口和参数，生成三种常用模板：
1. **Verilog 例化模板**：`module_name u_name (.port1(val1), .port2(val2));`
2. **Verilog header 模板**：`wire / reg` 声明块
3. **parameter 模板**：`defparam` 或 `instance#(.X(...))` 重写块

### 能力
- 支持 `.v` / `.sv` / `.vhd` / `.vhdl` 四种 HDL
- 端口自动按 `input` / `output` / `inout` 分组排序
- 端口名 / 位宽 / 方向全部提取
- 一键多例化（设置 `例化个数` N，生成 `u_name_0 … u_name_N-1`）
- F5 刷新 / Ctrl+C 复制 / Ctrl+S 保存

### 怎么用
1. 切换到「⚡ 例化模板」Tab
2. 点击「📂 选择文件」选 `.v` / `.sv` / `.vhd`（也支持拖拽进窗口）
3. 解析完后下方显示「✔ 文件名 | 模块名 (语言) | 端口:N 参数:M」
4. 设「例化个数」+ / −
5. 代码预览区两个 Tab：「Verilog」「Header」分别显示模板
6. 选中代码 → `Ctrl+C` 复制 → 粘到目标工程
7. `Ctrl+S` 可直接保存为 `.v` 文件

---

## Tab 2 — 工程压缩

### 功能
把 Vivado 工程目录（源码 + 约束 + IP + 工程文件）压缩成一份归档，体积通常是原工程的 1/10 到 1/50，方便备份 / 移交 / 上传 Git。

### 能力
- 一键 7z 压缩（自动排除 `.Xil/`、`.log`、`.jou`、`.cache/`、`synth_1/`、`impl_1/`）
- 输出文件名带时间戳：`vivado_xxx_20260624_1820.7z`
- 「压缩」 vs 「归档」两种模式：
  - **压缩**：体积最小，但解压后需 Vivado 重新生成 .Xil 缓存
  - **归档**：保留完整 Vivado 元数据，开箱即用
- 干跑预览（`dry_run`）：先列出会被压缩的文件清单 + 预估大小
- **可选自动 Export Hardware**：压缩前自动跑一次 Vivado `export_simulation / export_hardware`
- 自动生成 `.gitignore`（FPGA 工程专用）

### 怎么用
1. 「工程压缩」Tab → 选 Vivado 工程根目录（含 `.xpr` 文件的目录）
2. 选压缩模式：「压缩」或「归档」
3. 勾选「干跑预览」先看清单（不勾 = 直接出 `.7z`）
4. Vivado 路径和版本自动从 ⚙设置 Tab 读取为下拉
6. 完成后日志显示「✔ 文件数 1234，压缩后 12.3 MB（节省 87%）」

---

## Tab 3 — 🔀 Git 提交

### 功能
简化 Git 日常使用：登录、初始化、提交、推送，尤其针对内网 GitLab / 临时账户。

### 能力
- **Git 账户管理**：登录/切换/登出；自动注入 `user.name` / `user.email`
  - 优先写入 `repo/.git/config`（`--local`），避免抢占 `~/.gitconfig` 文件锁
  - 全局写入失败时冷却重试 1 次
- **SSH host key 自动跳过**（内网 IP 常见问题）
  - 自动注入 `GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=accept-new'`
- **WinError 32 自动重试**：内网环境下 `git config` / `ssh` 偶发「另一个程序正在使用此文件」错误，自动重试 3 次间隔 200ms
- **多 remote 支持**：可一键 push 到 `origin` / `backup` 等
- 智能 `.gitignore`（Vivado + ISE + Quartus + Verilog 通用模板）

### 怎么用
1. 「🔀 Git 提交」Tab
2. 顶部「Git 账户」状态栏：显示当前 `已登录: 张三 <zhangsan@xx.com>`
3. 点「登录」填 Name / Email → 自动写 local config
4. 中部输入「远程 URL」（如 `git@gitlab.xxx.com:fpga/aaa.git`）或选本地已克隆目录
5. 点「克隆」或「初始化」→ 仓库准备
6. 写 commit message（默认带时间戳）→ 点「提交并推送」
7. 日志区显示每步操作结果，失败会标红并自动重试

---

## Tab 4 — 🇨🇳 国产化

### 功能
把 Vivado（Xilinx）工程导出为国产 FPGA 厂商所需的全部文件。

### 能力
- **Zynq 检测**：从 `.xpr` XML 自动识别器件类型（`xc7z*` / `xcz*`）
- **BD 检测**：递归扫描 `.bd` 文件，有 BD 则导出
- **四文件导出**（按需）：
  | 文件 | 条件 | 来源 |
  |------|------|------|
  | `.bd` | 有 BD | 直接复制原始文件 |
  | `.hdf` | 有 BD | 8.3 → `write_hwdef`，≥2020 → `write_hw_platform` + `write_hwdef` |
  | `.bit` | 总是 | 搜 `{工程}.runs/` 目录 |
  | Zynq XCI | 是 Zynq | 搜 `processing_system*` `.xci` 直接复制 |
- **智能备份**：导出前将工程复制到临时目录，Vivado 操作在副本上执行，源工程完全不受影响
- **多版本兼容**：18.3 生成 `.hdf`，25.2 同步生成 `.xsa` + `.hdf`
- 支持递归找 `.xpr`（给粗略目录自动向下查找）
- 导出路径用户自定义
- 版本号从全局设置的 Vivado 路径自动提取为 Combobox

### 怎么用
1. 「🇨🇳 国产化」Tab
2. 「工程路径」选 Vivado 工程根目录（支持粗略路径，自动递归找 `.xpr`）
3. 「导出路径」选输出目录
4. 「国产平台」下拉选厂商
5. 「Vivado 版本」从全局路径自动提取为下拉
6. 点「▶ 执行导出」

> ⚠️ 部分 IP 可能因 Xilinx 特有功能（如 GTP/PCIe）需要手动调整。

---

## Tab 5 — 代码整理

### 功能
批量规范化 Verilog / SystemVerilog 代码风格（缩进、参数对齐、注释、空格、模块头）。

### 能力
- 缩进统一（Tab ↔ 空格，空格数可选：2/4）
- 参数对齐（`parameter A = 8` / `parameter AB = 16` 自动等宽）
- 模块头模板注入（自动添加 `// === Module : xxx === // Purpose:` 注释）
- 注释规范化（`/* ... */` ↔ `// ...`）
- 去除尾随空格、规范化空行
- 自动备份（生成 `*.bak`）
- 单文件/整目录批量处理
- 干跑预览：先看 diff，再决定是否真的改

### 怎么用
1. 「代码整理」Tab
2. 「浏览」选目录 或 「➕ 添加文件」选多个 `.v`/`.sv`
3. 路径列表显示待整理文件
4. 勾选整理项：缩进 / 参数对齐 / 头注释 / 注释规范 / 去除空格
5. 选「干跑预览」先看差异（推荐先预览）
6. 点「开始整理」
7. 日志区显示每个文件的旧/新字节数 + 改动行数
8. 不满意？删除 `*.bak` 即可回滚

---

## Tab 6 — 📚 IP 文档

### 功能
IP 文档一站式管理：离线 PDF 搜索 + DocNav 在线搜索下载，通过可拖拽分隔线分成上下两区。

### 能力

#### 离线 PDF 搜索（上区，可拖拽面板）
- 每次搜索实时重新扫描 `ip_docs/` 目录（含子目录）下所有 `.pdf`
- 智能搜索：关键词匹配 文件名 + 标题（`_meta.json`）+ **IP 映射表反向匹配**（搜 `CAN` 也能找到 `PG096.pdf`）
- 显示 `CAN LogiCORE IP Product Guide (PG096)` 格式标题
- 双击 PDF 用系统默认阅读器打开
- **Ctrl 多选删除**：选中多个 → 批量删除
- 「刷新」按钮手动重新扫描

#### DocNav 在线搜索下载（下区，可拖拽面板）
- **原理**：解析 DocNav 本地数据库 `resources/xdocs.xml`（~2000+ 篇文档）
- **智能搜索**：输入关键词 → IP 映射表自动扩展 docID → 合并搜索结果
- **显示格式**：`CAN LogiCORE IP Product Guide (PG096)`
- **下载**：勾选后点"下载选中"或"下载全部"，直链下载到 `ip_docs/docnav/`
- **标题持久化**：下载时保存 `_meta.json`，离线区也能显示完整标题
- **双击**：已下载的自动打开，未下载的自动触发下载
- DocNav 路径在顶部状态栏显示（✔ 已配置 / ✘ 未配置 + ⚙打开设置按钮），切回 IP文档 Tab 自动刷新

#### 上下区可拖拽
- 中间分隔线可上下拖拽，调整离线区和下载区比例

### 怎么用
1. 到 ⚙设置 Tab 添加 DocNav 安装目录
2. 「📚 IP 文档」Tab → 上方搜索框搜离线 PDF
3. 下方输入关键词 → 搜索结果 → 勾选 → 下载
4. 下载完成后切回上方可搜到
5. 不需要的 PDF：Ctrl 多选 → 「删除」

> DocNav 下载的文档统一存到 `ip_docs/docnav/`。IP 映射表覆盖 CAN/Ethernet/PCIe/DMA/DDR/FIFO/UART/I2C/SPI/GPIO/AXI/Zynq 等 60+ 常用 IP。

---

## Tab 7 — 🧮 计算器

### 功能
FPGA 专用计算器，含多个子页。

### 能力（子页）

#### FIFO 深度计算
- 输入：写时钟频率、读时钟频率、写位宽、读位宽、突发长度
- 输出：所需最小 FIFO 深度（含 / 不含 backpressure）

#### 时序 / 资源估算
- BRAM / LUT / FF 用量预估
- 跨时钟域路径数

#### 波特率计算
- 输入：系统时钟 + 目标波特率
- 输出：分频比整数/小数表示 + 实际波特率误差 %

#### 位宽截位
- 输入：源位宽 N、目标位宽 M、舍入方式
- 输出：截位代码模板

#### 进制转换
- BIN / HEX / DEC 互转
- 二进制补码、反码转换

### 怎么用
1. 「🧮 计算器」Tab → 上方子页 Notebook 选「FIFO 深度」/「时序」/...
2. 填输入参数（带单位提示：MHz、bit 等）
3. 结果实时显示在右侧（蓝色加粗）
4. 某些子页提供「复制代码」按钮，直接粘到 RTL

---

## Tab 8 — 🔌 约束生成

### 功能
从 Excel / CSV 表格批量生成 XDC 约束，避免手敲错管脚号。

### 能力
- 子页 1：**管脚约束** — 读 CSV/Excel（port, pin, io_std, drive, slew...）→ 生成 XDC
  - 自动识别列名别名（`port/signal/name`/`信号名` 都认）
  - 7 系列 I/O 标准 → VCCO 电压自动校验
  - Bank 电压检查（混电压会警告）
  - 支持差分对自动配 `DIFF_*` 标准
  - 预览生成结果 + 复制 + 保存
- 子页 2：**时序约束** — 模板化生成 `create_clock` / `set_input_delay` / `set_false_path`
- 子页 3：**其他约束** — 调试探针 (`mark_debug`)、`dont_touch` 等

### 怎么用（管脚约束）
1. 「🔌 约束生成」Tab → 「📌 管脚约束」子页
2. 「📂 加载 Excel/CSV」选你的管脚表
3. 工具自动识别列：信号名 / 管脚 / 电平标准
4. 检查「电压/电平」列是否有冲突（红色标记）
5. 右侧实时预览生成的 XDC
6. 「💾 保存 XDC」→ 选目录 → 输出 `xxx.xdc`

示例 CSV：
```csv
port,pin,io_std,drive
clk_p,E3,LVDS,
clk_n,D3,LVDS,
led[0],A14,LVCMOS33,8
led[1],A15,LVCMOS33,8
```

---

## Tab 9 — 分析辅助

### 功能
综合/实现日志分析、CDC 路径提示、时序违例分类、Debug 屏蔽、仿真报告。

### 能力

#### 子页 1 — CDC 检查
- 内置 CDC 场景库（单 bit 慢→快 / 快→慢 / 多 bit / FIFO 握手 / 异步复位）
- 输入源域/目的域时钟关系 + 信号类型 → 推荐同步方案
- 给 Verilog / VHDL 两套参考代码

#### 子页 2 — 时序报告
- Vivado 路径来自全局设置，选版本对应不同 Vivado
- 读 `vivado.rpt` / `vivado_impl.rpt`
- 解析 WNS/TNS/WHS/THS
- 按 path group 分类最差路径

#### 子页 3 — Log 解析
- 拖入 `vivado.log` / `synth_1/*.log`
- 自动分类 warning（latch / undriven / multi-driven / 组合环 / 未连接端口）
- Vivado 路径来自全局设置，按版本自动匹配

#### 子页 6 — Debug 屏蔽
- 选工程路径 → 递归扫描 `*.vhd` / `*.vhdl`
- 自动注释掉调试属性（加 `--` 前缀）：`mark_debug` / `dont_touch` / `keep` / `syn_keep` / `debug`
- 日志逐文件显示屏蔽行数

### 怎么用
1. 「分析辅助」Tab → 选子页
2. 工程路径支持粗略输入（自动递归找 `.xpr`）
3. Vivado 版本自动从全局设置提取为下拉

---

## Tab 10 — 串口助手

### 功能
XCOM / SSCOM 风格的串口调试终端，单窗口显示收发。

### 能力
- 串口枚举 + 插拔自动检测
- 波特率：110 ~ 921600（支持自定义）
- 数据位 / 停止位 / 校验位全配置
- HEX / ASCII 双显示
- HEX 发送：支持空格分隔（如 `AA BB CC`）或不带空格
- 时间戳：每行前缀 `HH:MM:SS.mmm`
- 自动换行 / 转义字符（`\r\n` `\t`）
- 定时发送：周期 1ms ~ 60s
- 流量统计：Tx 字节 / Rx 字节 / 错误帧数
- DTR / RTS 手动控制（用于复位/进入 Bootloader）
- 单数据框（顶 Tx/Rx 混排，加 `[Tx]` `[Rx]` 前缀区分）

### 怎么用
1. 工具 → 「串口助手」Tab
2. 点底部右「⚙ 串口设置」按钮（弹窗）
3. 选 COM 口、波特率（如 115200）→ 确认
4. 主界面点「打开串口」→ 状态变绿
5. 接收区显示收到的所有数据
6. 发送区输入文字（或 HEX），点「发送」
7. 勾选「HEX 显示」看原始字节
8. 勾选「定时发送」+ 周期（如 1000ms）+ 发送内容 → 自动循环

> 离线/便携：自动从 `_pyserial_lib/` 或 `runtime/Lib/site-packages/` 加载 pyserial，无需 pip 装。

---

## Tab 11 — 🌐 网络助手

### 功能
TCP/UDP 调试工具，类 `socat` / `hercules` / `TcpView`。

### 能力
- 自动枚举本机网卡（Windows 解析 ipconfig / Linux 解析 ip addr）
- 绑定指定网卡
- TCP 客户端 / TCP 服务器 / UDP 三种模式
- 十六进制收发（HEX 输入框 + HEX 显示）
- 心跳包（自定义内容 + 周期）
- 自定义端口扫描（1-65535 批量）
- 收发日志带时间戳
- 连接状态实时刷新

### 怎么用
1. 「🌐 网络助手」Tab
2. 选「网卡」下拉（如 `以太网 — 192.168.1.100`）
3. 选模式：
   - **TCP 客户端**：填远端 IP + 端口 → 「连接」
   - **TCP 服务器**：填监听端口 → 「监听」
   - **UDP**：填远端 IP + 端口 → 「连接」（UDP 实际是 bind）
4. 收发区输入文字/HEX → 「发送」
5. 心跳：勾「启用心跳」+ 内容 + 周期 → 自动发
6. 端口扫描：选「扫描」Tab → 填 IP + 端口范围 → 「开始」

---

## Tab 12 — QCI 测试图

### 功能
显示内置的 QCI 功能测试流程图（assets/qci_flow.png），支持缩放 / 平移 / 导出。

### 能力
- 加载 `assets/qci_flow.png`（带透明度合成到白底）
- 鼠标右键拖动平移
- 滚轮缩放（10% ~ 800%）
- 缩放比例实时显示
- 「重置视图」按钮回到 100%
- 「导出 PNG」保存当前视图到任意目录

### 怎么用
1. 「QCI 测试图」Tab → 自动加载图
2. 右键拖动平移、滚轮缩放
3. 点「🔍+」「🔍-」按钮精确缩放
4. 点「↺ 重置」回 100%
5. 点「💾 导出 PNG」保存到 `doc/`

---

## Tab 13 — 📡 iperf3

### 功能
图形化 iperf3 网络打流工具，自动选最优版本。

### 能力
- **自动扫描多版本**：`iperf3_bin/iperf3.11_64bit/`、`iperf3.13/`... 自动列出
- 兼容 PATH 里的 `iperf3`（标为 `iperf3 (PATH)`）
- 模式：客户端 / 服务端 / 自定义命令
- 客户端：填服务器 IP + 端口 + 时长 + 并发数 + 协议（TCP/UDP）+ 窗口
- 服务端：填监听端口 + 一键启动
- 实时显示：带宽 / 抖动 / 丢包率（折线图）
- 原始 log 窗口（带 stderr 颜色高亮）
- 常见错误自动诊断（无法连接 / 端口占用 / 版本不兼容）

### 怎么用（测速场景）
1. PC A：工具 → 「📡 iperf3」→ 选「服务端」→ 监听 5201 → 「启动」
2. PC B：工具 → 「📡 iperf3」→ 选「客户端」
   - 填 PC A 的 IP + 端口 5201
   - 时长 10s、并发 4
   - 协议 TCP → 「启动」
3. 进度条 + 实时带宽曲线显示
4. 完成后汇总：avg=940 Mbps, jitter=0.05 ms, loss=0%

### 怎么用（多版本）
1. 把 `iperf3.11` 二进制放到 `iperf3_bin/iperf3.11/iperf3.exe`
2. 把 `iperf3.13` 放到 `iperf3_bin/iperf3.13/iperf3.exe`
3. 重启工具 → 「iperf3 可执行文件」下拉出现两个版本
4. 切换版本测试兼容性（旧服务端 + 新客户端 等）

---

## Tab 14 — 🔐 SSH/SFTP

### 功能
类 WinSCP 的双栏 SFTP 文件管理器 + 集成 SSH 终端。

### 能力
- **SSH 连接**：
  - 主机 / 端口 / 用户名 / 密码 / 私钥
  - 私钥支持 `id_rsa` / `id_ed25519` / `.pem` 三种格式
  - 10s TCP / 15s Auth 超时（防卡死）
  - 连接状态：未连接 / 连接中 / 已连接 user@host:22
- **SFTP 文件管理**（双栏布局）：
  - 左边 = 本地、 右边 = 远程
  - Treeview 显示文件 / 大小 / 修改时间 / 权限
  - 操作：刷新 / 选文件夹 / 删除 / 重命名 / 新建目录
  - **拖拽上传/下载**：本地文件拖到远程 → 上传；远程拖到本地 → 下载
  - **双击文件** 在内置编辑器打开（HEX + 文本）
  - 上传/下载支持单文件 + 整目录
- **SSH 终端**：
  - 模式切换：[📁 SFTP] / [🖥 终端]
  - 终端模式：交互式 shell，支持 ANSI 转义
- **账号库**：
  - 「💾 保存账号」：把当前 host/port/user/pwd 存到本地 base64 加密
  - 「📚 账号库」：列出已保存账号，单击查看密码，双击快速填入
  - 文件存到 `~/.config/fpga_tool/accounts.json`

### 怎么用
1. 「🔐 SSH/SFTP」Tab
2. 顶部「SSH 连接」栏填：
   - 主机：192.168.1.100
   - 端口：22
   - 用户名：root
   - 密码：xxx（或选私钥）
3. 点「💾 保存账号」（下次不用重输）
4. 点「[连接]」→ 状态变 `● 已连接 root@192.168.1.100:22`
5. 双栏文件管理器激活：
   - 左栏浏览本地 → 点「[选文件夹]」
   - 右栏浏览远程 → 默认显示 `/`
   - 拖拽文件跨栏传输
6. 切到「🖥 终端」模式 → 跑 `ls /` `uname -a` 等命令

---

## Tab 15 — 🧪 仿真自动化

### 功能
Vivado 工程 → 一键生成 ModelSim / Questa 仿真脚本（tcl + do + f）并跑。

### 能力
- **自动扫描工程**：
  - 找 Vivado 工程根目录（含 `.xpr`）
  - 扫描 `*.v` / `*.sv` / `*.vhd` 源文件
  - 扫描 IP 目录 → 推断库映射（`xil_defaultlib`、`unisim`、`secureip`）
  - 自动选顶层模块（优先级：用户指定 > sim_1 set > 第一个 module）
- **生成三件套**：
  - `*.do` — ModelSim 命令脚本（`vlib` `vlog` `vsim` `run` `wave`）
  - `*.tcl` — 编译+仿真合一 tcl
  - `*.f` — 文件列表（`-f` 编译模式）
- **库映射**：
  - Vivado IP 库自动映射：`work` / `xil_defaultlib` / `unisims_ver` / `secureip`
  - 支持用户自定义库（如 `xpm`）
- **仿真参数**：
  - `run 时间`（默认 200ns）
  - `仿真分辨率`（默认 1ps）
  - 选择生成哪几种产物（do / tcl / f）
- **执行仿真**：
  - 自动找 `vsim.exe`（PATH / 手动指定）
  - 弹窗显示 ModelSim 实时输出
  - 错误自动捕获，输出红字 + 上下文

### 怎么用
1. 「🧪 仿真自动化」Tab
2. 「工程根」填 Vivado 工程路径 → 「浏览」/「🔄 重新扫描」
3. 「vsim.exe」路径可留空（用 PATH 里第一个）
4. 中间「仿真配置」：
   - 「顶层模块」下拉选 / 手动输入
   - 库映射行可加/删（默认 `work` → 工程目录）
5. 「生成产物」勾 `do` `tcl` `f` 至少一种
6. 右侧文件列表勾/取消个别文件
7. 「run 时间」填 `200ns` 或 `10us`
8. 「▶ 生成并运行」→ 等待弹窗

生成后你会得到：
- `sim_top.do` — ModelSim 主脚本
- `compile.tcl` — Modelsim Tcl 编译入口
- `files.f` — 编译文件列表

---

## Tab 16 — ⚙ 设置

### 功能
全局管理 Vivado 和 DocNav 安装路径，供所有 Tab 统一读取，不再需要在每个 Tab 里单独配置。

### 能力

#### Vivado 路径管理
- 添加/删除 Vivado 路径（支持粗略路径，自动递归查找 `bin/` 目录）
- 智能识别：`vivado.exe` / `vivado.bat` / `vivado`（`vitis` 仅用于路径验证，不用于批量命令）
- 自动校验有效路径标 ✔ 绿色，无效标 ✘ 红色
- 支持多版本并存（如 2018.3 + 2025.2），版本号自动提取到各 Tab 的版本下拉框
- 支持 `Ctrl` 多选批量删除
- 供：工程压缩 / 国产化 / 分析辅助（时序报告/Log清洗）等 Tab 使用
- 切回对应 Tab 自动刷新路径状态

#### DocNav 路径管理
- 添加/删除 DocNav 路径（支持粗略路径，自动递归查找 `resources/xdocs.xml`）
- 自动校验有效路径
- 支持 `Ctrl` 多选批量删除
- 供：IP文档 Tab 的 DocNav 搜索下载功能使用
- 切回 IP文档 Tab 自动刷新路径状态

#### 全局路径汇总
- 底部面板列出所有有效路径
- 显示配置文件位置：`~/.fpga_tool/app_config.json`
- 每次增删立即持久化

#### 自动迁移
首次启动时自动从旧的分散配置文件迁移到统一配置。

### 怎么用
1. 切换到「⚙ 设置」Tab
2. **添加 Vivado**：点「➕ 添加路径」→ 选 Vivado 安装的 `bin/` 目录 → 自动校验通过
3. **添加 DocNav**：点「➕ 添加路径」→ 选 DocNav 安装目录 → 自动校验 `resources/xdocs.xml`
4. 列表显示所有路径及其有效性（✔/✘）
5. 不需要的路径：选中 → 「➖ 删除选中」
6. 其他 Tab（IP文档/工程压缩/仿真等）自动读取设置好的路径

> 提示：所有路径保存在 `~/.fpga_tool/app_config.json`，工具跨版本升级后依然可用。

---

## 通用 FAQ

**Q1：Tab 闪退 / 卡死？**
看 `gen_gui.py` 顶部 `print` 输出（启动时终端窗口）。常见原因：Python < 3.8、缺少 ttkbootstrap（工具已内置，无此问题）。

**Q2：pyserial / paramiko 加载失败？**
工具自动从三条路径找：
1. `_pyserial_lib/` (仓库自带)
2. `runtime/Lib/site-packages/` (便携 runtime)
3. `pip install` (兜底，可能无网)
如仍失败，参考 `setup_offline.bat` 重装离线 whl。

**Q3：Vivado 工程扫描不到 .xpr？**
确认工程根目录下有 `.xpr` 文件（不是 `.runs` / `.cache` / `ip_repo` 那些子目录）。

**Q4：Tab 12 QCI 图不显示？**
确认 `assets/qci_flow.png` 存在（可替换成自己的图）。

**Q5：Tab 14 SSH 连不上？**
- 防火墙：板卡 22 端口开放
- 私钥权限：Linux 下 `chmod 600 id_rsa`
- 网络：先 `ping` 主机
- 工具「🌐 网络助手」可先 TCP 测试端口通不通

**Q6：Tab 15 仿真报 `vsim not found`？**
填 ModelSim/Questa 完整 `vsim.exe` 路径（如 `D:\modeltech_2023.4\win64\vsim.exe`）。

---

## 联系 / 反馈

工程 owner：`C:\Users\Administrator\Desktop\tool\tool\docs\`
更多截图：见各子目录 `README.md`。
