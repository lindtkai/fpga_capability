# FPGA Capability Tool — 问题总结

> 本文档记录项目开发与调试过程中遇到的所有问题、根因分析与解决方案。

---

## 1. Windows Raw Packet 发送失败 (核心问题)

### 问题描述
GUI 的原始发包功能 (`_t11_raw_send`) 在 Windows 上无法通过物理网卡发送自定义 MAC 地址的以太网帧。用户明确指出"小兵以太网"可以做到，要求自行测试验证。

### 子问题 1.1: Packet.dll 策略全部失败

**现象**: `PacketOpenAdapter` + `PacketSendPacket` 对所有设备均返回 `False`。

**根因**: Packet.dll (WinPcap/Npcap 底层 NDIS 驱动接口) 在现代 Windows 10/11 上对物理网卡的 raw injection 支持极其有限。`PacketSendPacket` 虽然在 API 层面可用，但 NDIS 驱动层拒绝通过物理网卡发送自定义以太网帧。

**尝试过的方案** (均失败):
- `PacketSendPacket(h, buf, True)` — 返回 False
- `PacketSendPacket(h, buf, False)` — 返回 False
- 直接构造 NDIS_PACKET 结构体 — 返回 False
- 遍历所有设备逐个尝试 — 全部 False

**结论**: Packet.dll 在此环境下不可用于物理网卡 raw send，保留作为策略1但不可靠。

### 子问题 1.2: Npcap pcap_inject 函数不存在

**现象**: `_t11_npcap_init()` 加载 wpcap.dll 时报错找不到 `pcap_inject`。

**根因**: 代码中错误地引用了 `pcap_inject` 函数（来自 libpcap 1.0+ 但仅限 Unix），Windows 的 wpcap.dll 中不包含此函数。

```python
# 错误代码 (已删除):
_npcap_wpcap.pcap_inject.argtypes = [c_void_p, c_void_p, c_int]
_npcap_wpcap.pcap_inject.restype = c_int
```

**修复**: 删除这两行，只使用 `pcap_sendpacket`。

### 子问题 1.3: pcap_sendpacket 返回 -1 (关键发现)

**现象**: `pcap_sendpacket` 对物理网卡 (Intel Wi-Fi 6E AX211, Realtek Gaming 2.5GbE) 返回 -1。

**根因**: `pcap_open_live(dev, 65536, 1, 1000, ...)` 使用 `promisc=1` (混杂模式) + `timeout=1000`，物理网卡驱动拒绝在此模式下注入数据包。

**验证过程**: 编写 `test_pcap_all_modes.py` 对所有网卡测试所有参数组合:
| promisc | timeout | Intel Wi-Fi | Realtek 2.5GbE | VMware VMnet |
|---------|---------|-------------|----------------|--------------|
| 1       | 1000    | -1 ❌       | -1 ❌          | 0 ✅         |
| 1       | 1       | -1 ❌       | -1 ❌          | 0 ✅         |
| 0       | 1000    | 0 ✅        | 0 ✅           | 0 ✅         |
| 0       | 1       | 0 ✅        | 0 ✅           | 0 ✅         |

**修复**: 将 `pcap_open_live` 参数改为 `promisc=0, timeout=1`:
```python
# 修复后:
handle = _npcap_wpcap.pcap_open_live(dev_name, 65536, 0, 1, errbuf)
```

**最终验证**: `test_auto_gui_send.py` 自动化测试所有设备，全部返回 SUCCESS:
- Realtek Gaming 2.5GbE Family Controller: OK (ret=0)
- VMware Virtual Ethernet Adapter for VMnet1: OK (ret=0)
- VMware Virtual Ethernet Adapter for VMnet8: OK (ret=0)
- Intel Wi-Fi 6E AX211: OK (ret=0)

### 子问题 1.4: 设备优先级排序不合理

**现象**: 之前代码将 VMware 虚拟网卡排在物理网卡前面，因为认为物理网卡不支持 raw injection。

**修复**: 恢复物理网卡优先排序:
```python
def _dev_rank(x):
    d = x[1].lower()
    if 'wi-fi' in d or 'wireless' in d: return 0      # Wi-Fi 最高优先
    if 'ethernet' in d or 'gbe' in d or 'realtek' in d or 'intel' in d: return 1  # 有线次之
    if 'vmware' in d: return 2                          # VMware 最后
    return 3
```

---

## 2. 测试脚本中文编码问题

### 问题描述
编写测试脚本 (`test_pcap_all_modes.py`, `test_auto_gui_send.py` 等) 时，PowerShell 输出中文字符导致 `UnicodeEncodeError`。

### 根因
Windows PowerShell 默认使用 GBK 编码，而 Python 脚本使用 UTF-8 字符串。

### 修复
在测试脚本中添加:
```python
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

---

## 3. AMD 文档下载 — 死代码问题

### 问题描述
`src/amd_docnav_compat.py` 第 350-351 行存在不可达代码。

```python
# 第 347-351 行:
if head != b'%PDF':
    try: os.remove(output_path)
    except OSError: pass
    return False, '文件头不是 %PDF (已删)'    # 第 350 行: 返回
    return False, '文件头不是 %PDF'           # 第 351 行: 永远执行不到
```

### 影响
无功能影响（第 351 行永远不会执行），但属于代码质量缺陷。

### 状态
待修复。

---

## 4. AMD 账户/Playwright 功能未实现

### 背景
用户记忆中描述了 AMD 文档下载的 4 路方案，包括:
1. 直链下载 (`amd_pdf_direct.py`, 15 个常用 PDF)
2. Playwright 搜 AMD 官方
3. Playwright cookie 静默登录
4. Xilinx 官方 IP 文档导航

### 实际状态
项目代码中以下文件和功能**不存在**:
- `src/amd_account.py` — AMD 账号管理 + Playwright 自动化
- `src/amd_search_cache.py` — 24h 搜索缓存
- `src/amd_pdf_direct.py` — 15 个直链 PDF
- Playwright 集成 — 任何文件中均无
- AMD 账户登录/密码管理 — 不存在

当前项目使用纯 `urllib` + AMD khub API (`docs.amd.com/api/khub/maps`)，该 API 无需认证。

### 状态
这些功能在设计规划中但尚未实现。如需实现需要:
1. 安装 Playwright (`playwright==1.60.0`)
2. 安装 chromium-headless-shell
3. 创建 `src/amd_account.py` (账号管理 + Playwright 自动登录)
4. 创建 `src/amd_search_cache.py` (搜索缓存)
5. 创建 `src/amd_pdf_direct.py` (直链下载)
6. 修改 `gen_gui.py` 集成到 IP 文档 Tab

---

## 5. SSL 证书校验全局跳过

### 问题描述
`amd_docnav_compat.py` 和 `amd_doc_downloader.py` 中全局禁用了 SSL 证书校验:
```python
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE
```

### 影响
虽然适合内网/自签名证书环境，但在公网使用时有安全风险（中间人攻击）。

### 建议
可改为仅对特定域名跳过，或添加用户可配置的选项。

---

## 6. 配置迁移兼容性

### 问题描述
`app_config.py` 需要从多个旧配置文件迁移到统一配置:
- `~/.fpga_tool/docnav_config.json` → `app_config.json`
- `~/.fpga_tool/vivado_paths.json` → `app_config.json`
- `~/.fpga_toolbox_config.json` → `app_config.json`

### 处理
`_migrate_old_configs()` 自动处理迁移，JSON 解析失败时静默降级。

### 风险
静默降级可能掩盖用户配置丢失问题，建议添加日志提示。

---

### 子问题 1.5: PacketGetAdapterNames 污染 Npcap 驱动状态 (2026-06-27)

**现象**: 用户选择 WLAN 2 (Intel Wi-Fi 6E AX211) 发送报文，实际却通过 VMware VMnet1 发出。

**根因**: `_t11_packet_init` 中调用 `PacketGetAdapterNames`（Packet.dll）会改变 Npcap 驱动的内部状态。之后 `_t11_npcap_init` 调用 `pcap_findalldevs` 时，Wi-Fi 设备的描述从 "Microsoft" 变为 "Intel(R) Wi-Fi 6E AX211 160MHz"（更准确），但同时 `pcap_sendpacket` 对物理网卡（Wi-Fi 和 Realtek 2.5GbE）全部返回 -1。只有 VMware 虚拟网卡仍能发送成功，导致 fallback 到 VMware。

**验证过程**:
- 直接 Npcap（不碰 Packet.dll）: Wi-Fi desc="Microsoft", pcap_sendpacket ret=0 ✅
- Packet.dll 后再 Npcap: Wi-Fi desc="Intel(R) Wi-Fi 6E AX211 160MHz", pcap_sendpacket ret=-1 ❌
- 仅调用 PacketGetAdapterNames（不加载 wpcap）也触发同样问题

**修复** (2 处修改):
1. `_t11_packet_init`: 移除 wpcap.dll 加载（`_tmp_wpcap.pcap_findalldevs`），改用 `_nic_guid_map` 构建 GUID→描述映射
2. `_t11_raw_send`: 在调用 `_t11_packet_send` 之前先调用 `_t11_npcap_init()` 预热，让 Npcap 在 Packet.dll 之前缓存设备列表（此时驱动状态干净，Wi-Fi 可正常发包）

**最终验证**: 预热 Npcap → Packet.dll 失败 → Npcap 用缓存列表发送 → Wi-Fi (desc="Microsoft") pcap_sendpacket ret=0，成功通过用户选中的 WLAN 2 发出。

---

## 7. 代码规模问题

### 问题描述
`src/gen_gui.py` 单个文件 **15018 行 / 664 KB**，包含 GUI、网络发包、IP 文档、Vivado 集成、Git 管理等所有功能。

### 影响
- 难以维护和定位问题
- 修改容易引入新 bug
- 代码审查困难

### 建议
按功能模块拆分为多个文件:
- `gui_main.py` — 主窗口框架
- `gui_ip_docs.py` — IP 文档 Tab
- `gui_settings.py` — 设置 Tab
- `network_send.py` — 网络发包核心

---

## 问题汇总表

| # | 问题 | 严重度 | 状态 |
|---|------|--------|------|
| 1.1 | Packet.dll 物理网卡发送全部失败 | 高 | 已分析(不可用) |
| 1.2 | `pcap_inject` 函数不存在导致 DLL 加载失败 | 高 | ✅ 已修复 |
| 1.3 | `pcap_sendpacket` promisc=1 导致物理网卡返回 -1 | 高 | ✅ 已修复 |
| 1.4 | 设备优先级排序不合理 | 中 | ✅ 已修复 |
| 1.5 | PacketGetAdapterNames 污染 Npcap 驱动状态 | 高 | ✅ 已修复 |
| 2 | 测试脚本中文编码问题 | 低 | ✅ 已修复 |
| 3 | `amd_docnav_compat.py` 死代码 | 低 | 待修复 |
| 4 | AMD 账户/Playwright 功能未实现 | 中 | 待实现 |
| 5 | SSL 证书校验全局跳过 | 低 | 待优化 |
| 6 | 配置迁移静默降级 | 低 | 待优化 |
| 7 | gen_gui.py 单文件过大 (15K行) | 中 | 待重构 |
