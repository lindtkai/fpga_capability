"""测试修复后的发包流程 — 不加载 wpcap.dll 在 _t11_packet_init 中"""
import ctypes, re, struct, sys, io, subprocess as sp
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from ctypes import c_char_p, c_bool, c_void_p, c_ulong, byref, POINTER, Structure, c_int, c_uint

# ============ GUID MAP ============
_nic_guid_map = {}
def build_guid_map():
    global _nic_guid_map
    if _nic_guid_map: return _nic_guid_map
    _map = {}
    try:
        r = sp.run(['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True, encoding='gbk', errors='replace', timeout=10)
        wlan_name = ''
        for line in r.stdout.split('\n'):
            m = re.match(r'^\s*Name\s*:\s*(.+)', line)
            if m: wlan_name = m.group(1).strip()
            m = re.match(r'^\s*GUID\s*:\s*([0-9A-Fa-f\-]+)', line)
            if m and wlan_name: _map[wlan_name.lower()] = ('guid', m.group(1))
    except: pass
    try:
        r = sp.run(['netsh', 'interface', 'ip', 'show', 'config'],
                    capture_output=True, encoding='gbk', errors='replace', timeout=10)
        current_name = ''
        for line in r.stdout.split('\n'):
            m = re.match(r'^[^"]*"([^"]+)"', line)
            if m: current_name = m.group(1).strip()
            m = re.search(r'IP\s*(?:Address|地址)[^:]*:\s*(\d+\.\d+\.\d+\.\d+)', line)
            if m and current_name:
                ip = m.group(1)
                if not ip.startswith('127.'):
                    _map[ip] = ('name', current_name)
                    nl = current_name.lower()
                    if nl not in _map: _map[nl] = ('name', current_name)
    except: pass
    try:
        r = sp.run(['powershell', '-NoProfile', '-Command',
                     'Get-NetAdapter | Select-Object Name, InterfaceGuid | Format-List'],
                    capture_output=True, encoding='gbk', errors='replace', timeout=10)
        ps_name = ''
        for line in r.stdout.split('\n'):
            m = re.match(r'^Name\s*:\s*(.+)', line)
            if m: ps_name = m.group(1).strip()
            m = re.match(r'^InterfaceGuid\s*:\s*\{?([0-9A-Fa-f\-]{36})\}?', line)
            if m and ps_name:
                nl = ps_name.lower()
                if nl not in _map: _map[nl] = ('guid', m.group(1))
    except: pass
    _nic_guid_map = _map
    return _map

build_guid_map()

# ============ 修复后的 Packet.dll 初始化 (不加载 wpcap) ============
print('=== 修复后: Packet.dll 初始化 (不加载 wpcap.dll) ===')
packet_dll = ctypes.windll.LoadLibrary(r'C:\Windows\System32\Npcap\Packet.dll')
packet_dll.PacketGetAdapterNames.argtypes = [c_char_p, c_void_p]
packet_dll.PacketGetAdapterNames.restype = c_bool
packet_dll.PacketOpenAdapter.argtypes = [c_char_p]
packet_dll.PacketOpenAdapter.restype = c_void_p
packet_dll.PacketSendPacket.argtypes = [c_void_p, c_void_p, c_bool]
packet_dll.PacketSendPacket.restype = c_bool
packet_dll.PacketCloseAdapter.argtypes = [c_void_p]

buf = ctypes.create_string_buffer(8192)
ulen = c_ulong(8192)
packet_dll.PacketGetAdapterNames(buf, byref(ulen))

raw = buf.raw[:ulen.value]
parts = raw.split(b'\x00')
npf_names = []
friendly_candidates = []
in_friendly_section = False
for part in parts:
    s = part.decode('gbk', errors='replace').strip()
    if not s:
        in_friendly_section = True
        continue
    if not in_friendly_section:
        if s.startswith(r'\Device\NPF_') and 'Loopback' not in s:
            npf_names.append(s)
    else:
        if not s.startswith(r'\Device\NPF_') and not s.startswith('WAN ') and not s.startswith('Bluetooth'):
            friendly_candidates.append(s)

def _extract_guid(npf_name):
    m = re.search(r'\{([0-9A-Fa-f\-]{36})\}', npf_name)
    if m: return m.group(1).replace('-', '')
    m = re.search(r'_([0-9A-Fa-f\-]{36})$', npf_name)
    return m.group(1).replace('-', '') if m else ''

# 修复后的 guid→desc 映射 (使用 _nic_guid_map, 不加载 wpcap)
guid_to_desc = {}
for k, v in _nic_guid_map.items():
    if v[0] == 'guid':
        guid_lower = v[1].replace('-', '').lower()
        guid_to_desc[guid_lower] = k
for k, v in _nic_guid_map.items():
    if v[0] == 'name':
        raw_name = v[1]
        nl = raw_name.lower()
        if nl in _nic_guid_map and _nic_guid_map[nl][0] == 'guid':
            guid_lower = _nic_guid_map[nl][1].replace('-', '').lower()
            if guid_lower in guid_to_desc:
                guid_to_desc[guid_lower] = raw_name

print('guid_to_desc:')
for k, v in guid_to_desc.items():
    print(f'  {k} -> {v}')

packet_devices = []
for idx, name in enumerate(npf_names):
    guid = _extract_guid(name)
    desc = guid_to_desc.get(guid.lower(), '')
    if not desc and idx < len(friendly_candidates):
        desc = friendly_candidates[idx]
    packet_devices.append((name, desc))

print(f'\nPacket devices ({len(packet_devices)}):')
for name, desc in packet_devices:
    print(f'  {desc}')

# ============ 修复后: Npcap 初始化 (此时 wpcap 还没被加载过!) ============
print('\n=== 修复后: Npcap 初始化 (wpcap 尚未被调用) ===')

class pcap_if(Structure):
    pass
pcap_if._fields_ = [
    ('next', POINTER(pcap_if)),
    ('name', c_char_p),
    ('description', c_char_p),
    ('addresses', c_void_p),
    ('flags', c_uint),
]

npcap_wpcap = ctypes.windll.LoadLibrary('wpcap.dll')
npcap_wpcap.pcap_findalldevs.argtypes = [POINTER(POINTER(pcap_if)), c_char_p]
npcap_wpcap.pcap_findalldevs.restype = c_int
npcap_wpcap.pcap_open_live.argtypes = [c_char_p, c_int, c_int, c_int, c_char_p]
npcap_wpcap.pcap_open_live.restype = c_void_p
npcap_wpcap.pcap_sendpacket.argtypes = [c_void_p, c_void_p, c_int]
npcap_wpcap.pcap_sendpacket.restype = c_int
npcap_wpcap.pcap_close.argtypes = [c_void_p]
npcap_wpcap.pcap_freealldevs.argtypes = [POINTER(pcap_if)]

_VSKIP = ('wan miniport', 'loopback', 'bluetooth', 'vpn', 'wi-fi direct virtual', 'network monitor')
errbuf = ctypes.create_string_buffer(256)
alldevs = POINTER(pcap_if)()
npcap_wpcap.pcap_findalldevs(ctypes.byref(alldevs), errbuf)

dev = alldevs
raw_devs = []
print('Npcap 原始设备:')
while dev:
    name = dev.contents.name.decode('utf-8', errors='replace') if dev.contents.name else ''
    desc = dev.contents.description.decode('utf-8', errors='replace') if dev.contents.description else name
    dl = desc.lower()
    skip = any(k in dl for k in _VSKIP)
    print(f'  DESC={desc}  SKIP={skip}')
    if not skip:
        raw_devs.append((name, desc))
    dev = dev.contents.next
npcap_wpcap.pcap_freealldevs(alldevs)

# 排序 + 发包
nic_str = 'WLAN 2  —  192.168.31.116'
adapter_ip = '192.168.31.116'
adapter_name = 'WLAN 2'

target_guid = ''
if adapter_ip in _nic_guid_map:
    entry = _nic_guid_map[adapter_ip]
    if entry[0] == 'guid': target_guid = entry[1]
    elif entry[0] == 'name' and entry[1].lower() in _nic_guid_map:
        e2 = _nic_guid_map[entry[1].lower()]
        if e2[0] == 'guid': target_guid = e2[1]
if not target_guid and adapter_name.lower() in _nic_guid_map:
    entry = _nic_guid_map[adapter_name.lower()]
    if entry[0] == 'guid': target_guid = entry[1]

_norm_guid = target_guid.replace('-', '').lower()
al = adapter_name.lower()
want_wifi = any(k in al for k in ('wlan', 'wi-fi', 'wifi', 'wireless', '无线'))
want_eth = any(k in al for k in ('以太', 'ethernet', 'eth', '本地连接'))

def _sort_key(x):
    dl = x[1].lower()
    _dev_guid = x[0].lower().replace('-', '').replace('{', '').replace('}', '')
    if _norm_guid and _norm_guid in _dev_guid:
        return -2
    if adapter_name and adapter_name.lower() in dl:
        return -1
    if want_wifi and ('wi-fi' in dl or 'wireless' in dl): return 0
    if want_eth and ('ethernet' in dl or 'gbe' in dl or 'realtek' in dl or 'intel' in dl): return 1
    if 'vmware' in dl: return 2
    return 3

ordered = sorted(raw_devs, key=_sort_key)

print(f'\n排序后 (target_guid={target_guid}, norm={_norm_guid}):')
for i, (n, d) in enumerate(ordered):
    p = _sort_key((n, d))
    print(f'  [{i}] prio={p} {d}')

# 发包测试
import struct
test_pkt = bytes.fromhex(
    'ffffffffffff0011223344550800'
    '4500001c0001000040110000'
    'c0a81f74c0a81fff'
)
ip_part = test_pkt[14:]
s = 0
for i in range(0, 20, 2):
    w = (ip_part[i] << 8) + ip_part[i+1]
    s += w
s = (s >> 16) + (s & 0xffff)
s = ~s & 0xffff
test_pkt = test_pkt[:24] + struct.pack('!H', s) + test_pkt[26:]

print(f'\n发包测试:')
for name, desc in ordered:
    dev_name = name.encode('utf-8')
    errbuf2 = ctypes.create_string_buffer(256)
    handle = npcap_wpcap.pcap_open_live(dev_name, 65536, 0, 1, errbuf2)
    if not handle:
        print(f'  {desc}: OPEN FAIL')
        continue
    buf = ctypes.create_string_buffer(test_pkt, len(test_pkt))
    ret = npcap_wpcap.pcap_sendpacket(handle, buf, len(test_pkt))
    npcap_wpcap.pcap_close(handle)
    _dg = name.lower().replace('-', '').replace('{', '').replace('}', '')
    is_target = _norm_guid and _norm_guid in _dg
    status = 'OK (ret=0)' if ret == 0 else f'FAIL (ret={ret})'
    marker = ' <== WLAN2' if is_target else ''
    print(f'  {desc}{marker}: {status}')
    if ret == 0:
        if is_target:
            print(f'  >>> 成功！通过用户选中的 WLAN 2 (Wi-Fi) 发出！')
        else:
            print(f'  >>> 通过非目标网卡发出 (VMware)')
        break
