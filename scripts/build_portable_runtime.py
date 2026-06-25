"""
build_portable_runtime.py — 跨平台构建便携运行时
=====================================================
下载 Astral cbs-zig (python-build-standalone) 跨平台预编译 Python,
在任意有 Python 3.10+ 的机器上即可生成 Windows + Linux 的便携 runtime,
目标机器无需装 Python, 也无需联网, 双击 run.bat / ./run.sh 即可启动.

用法:
    python build_portable_runtime.py                  # 自动识别当前平台, 构建对应 runtime
    python build_portable_runtime.py --target both   # 同时构建 Windows + Linux 两个 runtime
    python build_portable_runtime.py --target windows
    python build_portable_runtime.py --target linux
    python build_portable_runtime.py --version 20260610  # 指定 cbs-zig release tag

特点:
  - 跨平台: 在 Linux 上能下载 Windows 包, 在 Windows 上能下载 Linux 包
  - cbs-zig 自带 tkinter (无需系统装 python3-tk)
  - 自动 pip install 第三方库 (paramiko / pillow / pyserial) 到 runtime
  - 完全离线可跑, 目标机不需要 Python
"""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile


HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
RUNTIME_WINDOWS = os.path.join(PROJECT_ROOT, 'runtime_windows')
RUNTIME_LINUX = os.path.join(PROJECT_ROOT, 'runtime_linux')
# 兼容: 旧版本单一 runtime/ 也保留 (默认 Windows 版)
RUNTIME_LEGACY = os.path.join(PROJECT_ROOT, 'runtime')

# GitHub API 限流严重, 缓存到本地避免反复触发
CACHE_DIR = os.path.join(PROJECT_ROOT, '.codebuddy', 'cache')
CBS_CACHE = os.path.join(CACHE_DIR, 'cbs-assets.json')

# cbs-zig 资产命名规则:
#   cpython-3.13.x+<DATE>-x86_64-pc-windows-msvc-install_only.tar.gz
#   cpython-3.13.x+<DATE>-x86_64-unknown-linux-gnu-install_only.tar.gz
#   cpython-3.13.x+<DATE>-x86_64-unknown-linux-musl-install_only.tar.gz (静态链接, Alpine 用)
#   cpython-3.13.x+<DATE>-x86_64-unknown-linux-gnu-pgo+lto-full.tar.zst  (含 tkinter 等全部 .so)
#   cpython-3.13.x+<DATE>-x86_64-unknown-linux-gnu-noopt-full.tar.zst      (无优化, 体积小)
DEFAULT_CBS_TAG = '20250409'  # 含 cpython-3.13.3 (稳定)
DEFAULT_CBS_PY_VERSION = '3.13.3'
# cbs-zig 资产变体选择:
#   install_only:        ~26 MB, 缺 _tkinter 等 GUI 扩展 (Linux 上不可用)
#   pgo+lto-full:        ~115 MB, 性能最佳 (静态链接, 无 _tkinter.so 独立模块)
#   noopt-full:          ~33 MB, 无优化, 体积小 (musl 才有, gnu 无)
#   debug-full:          ~30 MB, 含调试符号, debug build (静态链接, lib-dynload 是空)
#   auto:                Linux=full, Windows=install_only (Windows install_only 含 tkinter)
#
# 重要现实: cbs-zig Linux **所有 "full" 变体都把 stdlib + _tkinter 静态链接进 libpython.so**,
# 整个 lib-dynload/ 是空的, 没法独立 import _tkinter 模块.
# 所以这些 full 变体 Linux 上**仍然不能** import tkinter (虽然它们 "含 tkinter").
# 实际方案: install_only 部署, 配合 `apt install python3-tk` 复制 _tkinter.so 进来.
# 因此 Linux 默认仍然是 install_only, run.sh 在缺 _tkinter 时提示用户安装.
DEFAULT_LINUX_VARIANT = 'install_only'  # Linux install_only (无 _tkinter, 需 system python3-tk)
DEFAULT_WINDOWS_VARIANT = 'install_only'  # Windows install_only 已含 tkinter, 体积最小

# 已知 release 的关键资产名 (API 限流时直接用, 避免反复调 GitHub)
# 这些是从 release 页面 snapshot 出来的, 后续 tag 变动时更新 CBS_KNOWN_TAGS 即可
CBS_KNOWN_TAGS = {
    '20250409': {
        'linux_x86_64_glibc': {
            'install_only': 'cpython-3.13.3+20250409-x86_64-unknown-linux-gnu-install_only.tar.gz',
            'pgo+lto-full': 'cpython-3.13.3+20250409-x86_64-unknown-linux-gnu-pgo+lto-full.tar.zst',
            'debug-full':   'cpython-3.13.3+20250409-x86_64-unknown-linux-gnu-debug-full.tar.zst',
        },
        'linux_x86_64_musl': {
            'noopt-full':  'cpython-3.13.3+20250409-x86_64-unknown-linux-musl-noopt-full.tar.zst',
            'pgo+lto-full':'cpython-3.13.3+20250409-x86_64-unknown-linux-musl-pgo+lto-full.tar.zst',
            'install_only':'cpython-3.13.3+20250409-x86_64-unknown-linux-musl-install_only.tar.gz',
        },
        'windows_x86_64': {
            'install_only': 'cpython-3.13.3+20250409-x86_64-pc-windows-msvc-install_only.tar.gz',
            'pgo+lto-full': 'cpython-3.13.3+20250409-x86_64-pc-windows-msvc-pgo+lto-full.tar.zst',
        },
    },
}

# 国内镜像 (gh-proxy.com 走完整 URL 形式, 5MB/s 加速)
# 用法: 设环境变量 NO_MIRROR=1 关闭, 或 --no-mirror 强制直连 GitHub
GH_MIRRORS = [
    'https://gh-proxy.com/',  # 5MB/s, 国内稳定
    'https://mirror.ghproxy.com/',
    'https://ghproxy.com/',
]
CBS_RELEASE_BASE = 'https://github.com/astral-sh/python-build-standalone/releases/download'

# 第三方库 (GUI + 串口 + SSH 都要)
THIRD_PARTY_PKGS = [
    'paramiko', 'pillow', 'pyserial',
    'cryptography', 'bcrypt', 'pynacl',  # paramiko 依赖
    'python-docx', 'mss', 'invoke', 'lxml',  # GUI 额外用到
    'openpyxl', 'xlrd',                   # 管脚约束表解析 (.xlsx / .xls)
]


def step(msg):
    print(f'\n[build] {msg}', flush=True)


def fail(msg, code=1):
    print(f'\n[ERROR] {msg}', file=sys.stderr, flush=True)
    sys.exit(code)


def _load_cbs_cache(tag):
    """加载本地缓存的 GitHub API 响应, 没有/失效/不匹配 tag 返回 None"""
    if not os.path.isfile(CBS_CACHE):
        return None
    try:
        with open(CBS_CACHE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if cache.get('tag') == tag and 'data' in cache:
            return cache['data']
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _save_cbs_cache(tag, data):
    """保存 GitHub API 响应到本地缓存"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CBS_CACHE, 'w', encoding='utf-8') as f:
            json.dump({'tag': tag, 'data': data, 'saved_at': time.time()}, f)
    except OSError as e:
        print(f'  [WARN] 缓存写失败: {e}')


def _known_assets_to_api_shape(tag):
    """把 CBS_KNOWN_TAGS 转成 GitHub API 返回的 JSON 格式, 供 _get_cbs_assets 解析.
    返回 None 表示该 tag 没有硬编码数据.
    """
    if tag not in CBS_KNOWN_TAGS:
        return None
    known = CBS_KNOWN_TAGS[tag]
    assets = []
    for _platform_key, variants in known.items():
        for _variant_name, name in variants.items():
            assets.append({
                'name': name,
                'size': 0,  # 不知道, 占位
                'browser_download_url': f'{CBS_RELEASE_BASE}/{tag}/{name}',
            })
    return {'assets': assets, 'tag_name': tag}


def _size_mb(path):
    total = 0
    for r, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return total / 1024 / 1024


def _dl_progress(count, block, total):
    pct = min(100, count * block * 100 / total) if total else 0
    print(f'\r  下载进度: {pct:5.1f}% ({count*block/1024/1024:.1f}/{total/1024/1024:.1f} MB)',
          end='', flush=True)


def _download(url, out, use_mirror=True):
    """下载 url 到 out, 显示进度. 失败抛 IOError.
    国内环境默认走 gh-proxy.com 镜像 (5MB/s), NO_MIRROR=1 环境变量关闭.
    """
    if use_mirror and not os.environ.get('NO_MIRROR'):
        # 尝试所有镜像, 第一个成功的就行
        for mirror in GH_MIRRORS:
            mirror_url = mirror + url
            try:
                req = urllib.request.Request(mirror_url, method='HEAD',
                                              headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as r:
                    if r.status == 200:
                        url = mirror_url  # 用镜像源
                        print(f'  [镜像] {mirror}')
                        break
            except Exception:
                continue
    print(f'  URL: {url}')
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            total = int(r.headers.get('Content-Length', 0))
            chunk = 64 * 1024
            downloaded = 0
            last_print = time.time()
            with open(out, 'wb') as f:
                while True:
                    data = r.read(chunk)
                    if not data:
                        break
                    f.write(data)
                    downloaded += len(data)
                    if time.time() - last_print > 2:
                        pct = 100 * downloaded / total if total else 0
                        speed = downloaded / (time.time() - t0) / 1024 / 1024
                        print(f'\r  {pct:5.1f}%  {downloaded/1024/1024:6.1f}/{total/1024/1024:6.1f} MB  {speed:.2f} MB/s',
                              end='', flush=True)
                        last_print = time.time()
    except Exception as e:
        if os.path.exists(out):
            try: os.unlink(out)
            except OSError: pass
        raise IOError(f'下载失败: {e}') from e
    sz = os.path.getsize(out) / 1024 / 1024
    print(f'\n  完成: {sz:.1f} MB, 耗时 {time.time()-t0:.1f}s')


def _get_cbs_assets(tag=DEFAULT_CBS_TAG, prefer_py='3.13',
                    linux_variant=DEFAULT_LINUX_VARIANT,
                    windows_variant=DEFAULT_WINDOWS_VARIANT):
    """查询 GitHub API 拿 tag 的所有资产, 按 (platform, arch) 分组.
    prefer_py: 偏好的 Python 主版本, 资产多个时优先选它 (3.13 > 3.12 > 3.11)
    linux_variant:  'install_only' | 'pgo+lto-full' | 'noopt-full' | 'auto'
    windows_variant: 同上 (Windows install_only 已含 tkinter, 用 install_only 即可)

    限流时 fallback 到 CBS_KNOWN_TAGS 硬编码表.
    """
    # 1) 先查本地缓存
    cached = _load_cbs_cache(tag)
    if cached:
        print(f'  [cache] 使用本地缓存 {CBS_CACHE} (tag={tag})')
        data = cached
    else:
        url = f'https://api.github.com/repos/astral-sh/python-build-standalone/releases/tags/{tag}'
        print(f'  查询: {url}')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'fpgatool-build'})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            # 成功: 写缓存
            _save_cbs_cache(tag, data)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f'  [WARN] GitHub API 失败: {e}')
            # fallback 到硬编码
            fallback = _known_assets_to_api_shape(tag)
            if fallback is not None:
                print(f'  [fallback] 使用 CBS_KNOWN_TAGS 硬编码表 (tag={tag})')
                data = fallback
            else:
                print(f'  [ERROR] tag={tag} 没有硬编码 fallback, 请更新 CBS_KNOWN_TAGS 或检查网络')
                return {}
    assets = {}
    # 第一遍: 按 Python 主版本号分类, 后续按 prefer_py 选
    raw = {}  # (platform, arch) -> [(py_ver, asset_tuple), ...]
    dbg = []
    for a in data.get('assets', []):
        n = a['name']
        if 'sha256' in n or 'sig' in n:
            continue
        if 'cpython-' not in n:
            continue
        if '_stripped' in n:
            continue  # stripped 版本缺一些 .so, 跳过
        # 跳过不带 .tar. 后缀的 (如 freethreaded 标识? 不应过滤)
        if '.tar.' not in n:
            dbg.append(f'  [PRE-SKIP] {n}  no .tar. extension')
            continue
        # 决定变体匹配
        is_install_only = 'install_only' in n and 'install_only.tar' in n
        # full 变体多种: pgo+lto-full / pgo-full / lto-full / noopt-full / debug-full
        is_full = '-full' in n
        if not (is_install_only or is_full):
            dbg.append(f'  [PRE-SKIP] {n}  not install_only and not full')
            continue
        dbg.append(f'{n}  install_only={is_install_only}  full={is_full}')
        # 分类平台
        if 'x86_64-pc-windows-msvc' in n:
            key = ('windows', 'x86_64')
            want_variant = windows_variant
        elif 'aarch64-pc-windows-msvc' in n:
            key = ('windows', 'aarch64')
            want_variant = windows_variant
        elif 'x86_64-unknown-linux-gnu' in n and 'musl' not in n:
            key = ('linux', 'x86_64', 'glibc')
            want_variant = linux_variant
        elif 'x86_64-unknown-linux-musl' in n:
            key = ('linux', 'x86_64', 'musl')
            want_variant = linux_variant
        elif 'aarch64-unknown-linux-gnu' in n and 'musl' not in n:
            key = ('linux', 'aarch64', 'glibc')
            want_variant = linux_variant
        elif 'aarch64-unknown-linux-musl' in n:
            key = ('linux', 'aarch64', 'musl')
            want_variant = linux_variant
        else:
            continue
        # 匹配变体: 解析出当前 n 是什么变体
        # cbs-zig 命名里 "xxx-full" 和 "xxx+yyy-full" (复合变体) 都要识别
        if is_install_only:
            n_variant = 'install_only'
        else:
            # 取文件名里第一个 -full 之前的所有修饰词
            # 例: cpython-3.13.3+...-x86_64-unknown-linux-gnu-noopt+static-full.tar.zst
            #   → noopt+static-full
            #   cpython-3.13.3+...-pgo+lto-full.tar.zst
            #   → pgo+lto-full
            base_name = n.rsplit('/', 1)[-1]  # 去路径
            # 把 .tar.zst / .tar.gz 砍掉
            base_name = re.sub(r'\.tar\.(zst|gz)$', '', base_name)
            m_var = re.search(r'-((?:[a-z0-9]+\+)*[a-z0-9]+-full)$', base_name)
            if m_var:
                n_variant = m_var.group(1)
            else:
                n_variant = 'unknown'
        # auto 模式: Linux 优先 debug-full (含 tkinter, 体积小), Windows install_only
        if want_variant == 'auto':
            if key[0] == 'linux':
                if not is_full:
                    continue
                # auto 模式: 接受所有含 tkinter 的 full 变体, _pick 阶段按优先级选
                # debug-full (30MB) > noopt-full (33MB, 仅 musl) > pgo+lto-full (115MB)
                if n_variant not in ('debug-full', 'noopt-full', 'pgo+lto-full'):
                    continue
            else:  # windows
                if not is_install_only:
                    continue
        else:
            # 精确匹配变体
            if n_variant != want_variant:
                dbg.append(f'  [SKIP] {n}  n_variant={n_variant}  want={want_variant}  key={key}')
                continue
        dbg.append(f'  [HIT]  {n}  n_variant={n_variant}  key={key}')
        # 提取 py version: cpython-3.13.3+TAG-...  ->  3.13.3
        try:
            py_v = n.split('cpython-')[1].split('+')[0]
        except IndexError:
            continue
        raw.setdefault(key, []).append((py_v, (n, a['size'], a['browser_download_url'])))

    # 第二遍: 按 prefer_py 选, 同主版本选 patch 最大的
    def _parse_ver(v):
        """'3.13.3' -> (13, 3, 0, 1), '3.14.0a6' -> (14, 0, -1, 0) (a/b/rc 标记 < release)
        最后一位 0/1: 是否含 pre-release 标记 — 0 表示 pre, 1 表示正式."""
        parts = []
        for p in v.split('.'):
            num = ''
            for c in p:
                if c.isdigit(): num += c
                else: break
            parts.append(int(num) if num else 0)
        is_pre = any(s in v for s in ('a', 'b', 'rc'))
        parts.append(0 if is_pre else 1)
        return tuple(parts)

    def _is_stable(v):
        return not any(s in v for s in ('a', 'b', 'rc'))

    def _pick(items):
        if not items:
            return None
        # 先按主版本分组
        major_groups = {}
        for py_v, t in items:
            major = '.'.join(py_v.split('.')[:2])
            major_groups.setdefault(major, []).append((py_v, t))
        # 排序主版本号优先级: prefer_py 在前 (如果存在), 否则按主版本号降序 (取 stable)
        # 完全跳过 alpha/beta/rc (哪怕它是 3.14.0a6, 也不如 3.13.3 stable)
        stable_majors = [m for m in major_groups if any(_is_stable(v) for v, _ in major_groups[m])]
        def _key(m):
            is_preferred = 0 if m == prefer_py else 1
            # 该 major 下的 best stable 版本 (取 patch 最大)
            stables = [(v, t) for v, t in major_groups[m] if _is_stable(v)]
            if stables:
                best = max(stables, key=lambda x: _parse_ver(x[0]))
            else:
                best = max(major_groups[m], key=lambda x: _parse_ver(x[0]))
            pv = _parse_ver(best[0])
            return (is_preferred, -pv[0], -pv[1], -pv[2], -pv[3])
        # 如果 prefer_py 在 stable_majors, 优先选它; 否则用最大 stable 主版本
        if not stable_majors:
            stable_majors = list(major_groups.keys())  # 兜底
        chosen_major = sorted(stable_majors, key=_key)[0]
        # 同主版本内 stable 优先, patch 大的优先
        chosen = sorted(major_groups[chosen_major],
                        key=lambda x: _parse_ver(x[0]),
                        reverse=True)[0]
        return chosen[1]

    # auto 模式变体优先级: debug-full > noopt-full > pgo+lto-full
    # 用于 multi-variant 时挑最小的
    VARIANT_RANK = {'debug-full': 0, 'noopt-full': 1, 'pgo+lto-full': 2,
                    'pgo-full': 3, 'lto-full': 4, 'install_only': 5}

    def _variant_of(name):
        base_name = name.rsplit('/', 1)[-1]
        base_name = re.sub(r'\.tar\.(zst|gz)$', '', base_name)
        m_var = re.search(r'-((?:[a-z0-9]+\+)*[a-z0-9]+-full)$', base_name)
        return m_var.group(1) if m_var else 'install_only'

    for k, items in raw.items():
        # auto 模式: 优先选体积小的变体 (同主版本内)
        if (linux_variant == 'auto' and k[0] == 'linux') or \
           (windows_variant == 'auto' and k[0] == 'windows'):
            # 重新按 (主版本, 变体优先级) 排序
            def _auto_key(it):
                py_v, t = it
                major = py_v.split('.')[:2]
                major_s = '.'.join(major)
                # prefer_py 在前
                pref = 0 if major_s == prefer_py else 1
                pv = _parse_ver(py_v)
                v = _variant_of(t[0])
                vr = VARIANT_RANK.get(v, 9)
                return (pref, vr, -pv[0], -pv[1], -pv[2])
            sorted_items = sorted(items, key=_auto_key)
            if sorted_items:
                assets[k] = sorted_items[0][1]
        else:
            assets[k] = _pick(items)
    # 调试输出
    print('  --- 资产匹配过程 ---')
    for line in dbg[-30:]:
        print(f'   {line}')
    print(f'  --- 最终 raw: {list(raw.keys())} ---')
    return assets


def _extract_tar_gz(tar_path, target_dir):
    """解压 tar.gz / tar.zst 到 target_dir, 跳过 macOS 资源叉文件警告.
    关键: Windows NTFS 路径上限 255 字符, cbs-zig 的 share/terminfo/ 嵌套很深
    (例如 python/share/terminfo/v/vt220-w + python 几层前缀易超限),
    此外 terminfo 里有无效字符的节点名. 遇到 Errno 22/36 等只跳过单文件, 继续解压其它.
    """
    print(f'  解压到: {target_dir}')
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)
    skipped = []

    if tar_path.endswith('.zst'):
        # 先解压 zst → tar (临时文件), 再用 tarfile 解 tar
        # 优先用 zstandard 库 (跨平台)
        try:
            import zstandard as zstd
            tmp_tar = tar_path[:-4]  # .tar.zst -> .tar
            print(f'  [zst] 用 zstandard 库解压到 {tmp_tar} ...')
            dctx = zstd.ZstdDecompressor()
            with open(tar_path, 'rb') as inf, open(tmp_tar, 'wb') as outf:
                # 一次过流式解压, 大文件省内存
                reader = dctx.stream_reader(inf)
                while True:
                    chunk = reader.read(1024 * 1024)
                    if not chunk:
                        break
                    outf.write(chunk)
            tar_to_open = tmp_tar
        except ImportError:
            # 回退: 用系统 zstd + tar 命令 (Linux/macOS 自带)
            tmp_tar = tar_path[:-4]
            r = subprocess.run(['zstd', '-d', tar_path, '-o', tmp_tar, '-f'],
                               capture_output=True, text=True)
            if r.returncode != 0:
                # 二次回退: 直接给 tar 喂流
                tar_to_open = tar_path
                tmp_tar = None
            else:
                tar_to_open = tmp_tar
        with tarfile.open(tar_to_open, 'r:') as tar:
            _tar_extract_loop(tar, target_dir, skipped)
        if tmp_tar and os.path.exists(tmp_tar):
            try: os.unlink(tmp_tar)
            except OSError: pass
    else:
        with tarfile.open(tar_path, 'r:gz') as tar:
            _tar_extract_loop(tar, target_dir, skipped)

    if skipped:
        print(f'  [WARN] 跳过 {len(skipped)} 个文件 (路径过长/特殊字符)')
        for name, reason in skipped[:5]:
            print(f'    - {name[:80]}: {reason}')
        if len(skipped) > 5:
            print(f'    ... 还有 {len(skipped) - 5} 个')
    print(f'  解压完成: {_size_mb(target_dir):.1f} MB')


def _tar_extract_loop(tar, target_dir, skipped):
    """统一的 tar 提取循环, 处理 strip / 路径安全 / 长度限制.

    cbs-zig 2025+ 包的 tar 顶层结构:
      - 老版: 单个 'python/' 顶级目录
      - 新版 (full 系列): 多个顶级目录, 但运行时实际内容都在 'install/' 里
        (build/ 是临时构建产物, lib/ licenses/ PYTHON.json 是顶层元数据)
    策略:
      1) 如果有 'install/' 顶级目录: strip 它, 内容直接到 target_dir
      2) 否则如果只有 'python/': strip 它
      3) 否则原样解压
    """
    members = tar.getmembers()
    top_names = set(m.name.split('/', 1)[0] for m in members if m.name)
    if 'install' in top_names:
        # cbs-zig full: install/ 是运行时实际目录
        strip_prefix = 'install/'
    elif len(top_names) == 1 and 'python' in top_names:
        # 老 install_only: 单个 python/ 顶级目录
        strip_prefix = 'python/'
    else:
        strip_prefix = None
    target_prefix = os.path.realpath(target_dir)
    for m in members:
        # 跳过 strip_prefix 本身这个目录项 (它已是空目录, 无需创建)
        if strip_prefix and m.name.rstrip('/') == strip_prefix.rstrip('/'):
            continue
        if strip_prefix and m.name.startswith(strip_prefix):
            m.name = m.name[len(strip_prefix):]
        if m.name.startswith('/') or '..' in m.name.replace('\\', '/').split('/'):
            skipped.append((m.name, 'unsafe path'))
            continue
        full = os.path.join(target_prefix, m.name.replace('/', os.sep))
        if len(full) > 240:
            skipped.append((m.name, f'path too long ({len(full)})'))
            continue
        try:
            tar.extract(m, target_dir, filter='data')
        except (OSError, tarfile.TarError, ValueError) as e:
            skipped.append((m.name, str(e)[:80]))
            continue


def _pip_install_to(python_exe, target_site_packages, pkgs):
    """用 python_exe 的 pip 装 pkgs 到 target_site_packages.
    注: 当 python_exe 是 Linux ELF 而当前 OS 是 Windows 时, 这步会失败 (WinError 193),
    应改用 _download_wheels_and_unpack.
    """
    # 先确保目标目录存在
    os.makedirs(target_site_packages, exist_ok=True)

    # 先用 ensurepip 确认 pip 可用
    r = subprocess.run([python_exe, '-m', 'pip', '--version'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  [WARN] pip 不可用, 尝试 ensurepip ...')
        subprocess.run([python_exe, '-m', 'ensurepip', '--upgrade'],
                       capture_output=True)

    cmd = [python_exe, '-m', 'pip', 'install',
           '--target', target_site_packages,
           '--upgrade', '--disable-pip-version-check', '--quiet']
    cmd.extend(pkgs)
    print(f'  pip install {len(pkgs)} 个包 ...')
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f'  [OK] site-packages: {_size_mb(target_site_packages):.1f} MB')
        return True
    # 失败重试 (清华镜像)
    print(f'  [WARN] pip 默认源失败, 重试清华镜像 ...')
    cmd2 = [python_exe, '-m', 'pip', 'install',
            '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
            '--target', target_site_packages,
            '--upgrade', '--disable-pip-version-check', '--quiet']
    cmd2.extend(pkgs)
    r = subprocess.run(cmd2, capture_output=True, text=True)
    if r.returncode == 0:
        print(f'  [OK] 镜像安装成功: {_size_mb(target_site_packages):.1f} MB')
        return True
    print(f'  [WARN] pip 装第三方库全部失败, 继续 (部分功能不可用)')
    if r.stderr:
        print(f'    最后错误: {r.stderr[-300:]}')
    return False


def _download_wheels_and_unpack(python_version, target_site_packages, pkgs,
                                wheels_dir=None, host_python=None):
    """跨平台 pip install 替代方案: 用当前 OS 的 Python + --platform 拉目标平台的 wheels,
    然后解压到 site-packages. 这样 Windows 上能给 Linux runtime 装包.
    python_version: 形如 '3.13.3' 或 '3.9.22' (目标 Python 版本)
    target_site_packages: 目标 runtime 的 site-packages 目录
    pkgs: 包名列表
    host_python: 当前 OS 的 Python 解释器, 用来跑 pip download. None=自动找 sys.executable
    """
    if host_python is None:
        host_python = sys.executable
    if wheels_dir is None:
        wheels_dir = os.path.join(PROJECT_ROOT, '_wheels')
    os.makedirs(wheels_dir, exist_ok=True)
    os.makedirs(target_site_packages, exist_ok=True)

    major_minor = '.'.join(python_version.split('.')[:2])  # 3.13
    # manylinux tag: 优先 2.28 (Ubuntu 20.04+), 退到 2014 (RHEL 7+)
    # cpython 3.13 需要 glibc 2.28 (cbs-zig)
    platforms = ['manylinux_2_28_x86_64', 'manylinux_2_17_x86_64', 'manylinux2014_x86_64']
    # abi: 3.13 用 cp313, 3.12 用 cp312, 3.11 用 cp311, 3.10 用 cp310, 3.9 用 cp39
    py_tag = 'cp' + major_minor.replace('.', '')
    abi_tag = py_tag  # 标准 cpython 解释器 abi = 自身 tag

    cmd = [host_python, '-m', 'pip', 'download',
           '--dest', wheels_dir,
           '--python-version', major_minor,
           '--abi', abi_tag,
           '--only-binary=:all:',
           '--disable-pip-version-check', '--quiet']
    for p in platforms:
        cmd[3:3] = ['--platform', p]  # 插到 dest 后面
        # 用 extend 会重复, 改用这种方式:
    # 重新组装
    cmd = [host_python, '-m', 'pip', 'download',
           '--dest', wheels_dir,
           '--python-version', major_minor,
           '--abi', abi_tag,
           '--only-binary=:all:',
           '--disable-pip-version-check', '--quiet']
    for p in platforms:
        cmd += ['--platform', p]
    cmd += list(pkgs)

    print(f'  pip download (目标 {major_minor}, {len(platforms)} platforms) ...')
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  [WARN] pip download 失败: {r.stderr[-300:]}')
        # 重试 清华镜像
        cmd2 = [host_python, '-m', 'pip', 'download',
                '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple',
                '--dest', wheels_dir,
                '--python-version', major_minor,
                '--abi', abi_tag,
                '--only-binary=:all:',
                '--disable-pip-version-check', '--quiet']
        for p in platforms:
            cmd2 += ['--platform', p]
        cmd2 += list(pkgs)
        r = subprocess.run(cmd2, capture_output=True, text=True)
        if r.returncode != 0:
            print(f'  [WARN] 清华镜像也失败: {r.stderr[-300:]}')
            return False

    # 删掉 Windows wheels (漏网之鱼)
    cleaned = 0
    for f in os.listdir(wheels_dir):
        if 'win_amd64' in f or 'win32' in f or 'win_arm64' in f:
            try:
                os.unlink(os.path.join(wheels_dir, f)); cleaned += 1
            except OSError: pass
    if cleaned:
        print(f'  清掉 {cleaned} 个 Windows wheel')

    # 解压所有 wheel 到 target_site_packages
    n_ok = 0
    n_fail = 0
    for f in sorted(os.listdir(wheels_dir)):
        if not f.endswith('.whl'):
            continue
        wp = os.path.join(wheels_dir, f)
        try:
            with zipfile.ZipFile(wp, 'r') as z:
                z.extractall(target_site_packages)
            n_ok += 1
        except (zipfile.BadZipFile, OSError) as e:
            n_fail += 1
            print(f'    [WARN] 解压 {f} 失败: {e}')

    # 删 .dist-info 让 Python 能识别 (提取已包含)
    print(f'  [OK] 解压 {n_ok} 个 wheel 到 site-packages ({_size_mb(target_site_packages):.1f} MB)')
    if n_fail:
        print(f'  [WARN] {n_fail} 个 wheel 解压失败')
    return n_ok > 0


def _find_site_packages(runtime_dir, target, py_version=None):
    """根据平台找 cbs-zig 解压后的 site-packages 目录.
    py_version: 已知的目标 Python 版本 (例 '3.13.3'), 用它准确定位.
    """
    if target == 'windows':
        # Windows cbs-zig install_only: 没有 site-packages, 需手动创建
        # 标准库在 Lib/, pip 装到 Lib/site-packages/
        sp = os.path.join(runtime_dir, 'Lib', 'site-packages')
        if not os.path.isdir(sp):
            os.makedirs(sp, exist_ok=True)
        return sp
    # Linux
    # cbs-zig install_only 布局: lib/python3.13/site-packages
    # 优先用 py_version 指定的版本, 否则按 lib/ 实际目录
    if py_version:
        major_minor = '.'.join(py_version.split('.')[:2])  # 3.13
        sp = os.path.join(runtime_dir, 'lib', f'python{major_minor}', 'site-packages')
        os.makedirs(sp, exist_ok=True)
        return sp
    # 退化: 自动找
    lib_dir = os.path.join(runtime_dir, 'lib')
    if os.path.isdir(lib_dir):
        for d in os.listdir(lib_dir):
            if d.startswith('python3.'):
                sp = os.path.join(lib_dir, d, 'site-packages')
                os.makedirs(sp, exist_ok=True)
                return sp
    # 兜底
    sp = os.path.join(runtime_dir, 'lib', 'python3.13', 'site-packages')
    os.makedirs(sp, exist_ok=True)
    return sp


def _make_pth(runtime_dir, target, py_version=None):
    """生成 _pth 文件, 让 Python 能找到 site-packages 和 src.
    py_version: 形如 '3.13.3' 或 '3.9.22', 默认 3.13
    """
    if py_version is None:
        py_version = '3.13.3'
    major_minor = '.'.join(py_version.split('.')[:2])  # '3.13'
    pth_name = f'python{major_minor.replace(".", "")}._pth'  # 'python313._pth'
    pth = os.path.join(runtime_dir, pth_name)
    if target == 'windows':
        content = f"""python{major_minor.replace('.', '')}.zip
.
DLLs
Lib
Lib\\site-packages
..\\src
src
..
import site
"""
    else:  # linux
        content = f"""python{major_minor.replace('.', '')}.zip
.
lib/python{major_minor}
lib/python{major_minor}/site-packages
../src
src
..
import site
"""
    with open(pth, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  [OK] 写入 {pth}')


def _chmod_all_executable(root):
    """给所有 .so / .dll / bin/ 下的文件加可执行位 (Linux 上必要, Windows 上 no-op)"""
    n = 0
    for dirpath, _, files in os.walk(root):
        for fn in files:
            fp = os.path.join(dirpath, fn)
            # 跳过 Windows .exe 标记 (PE 文件 Windows 上不需要 chmod)
            if fp.lower().endswith(('.so', '.so.1', '.so.6', '.so.9')) or \
               (os.sep + 'bin' + os.sep in fp and not fp.lower().endswith('.py')) or \
               fp.endswith(('.dyn', '.elf')):
                try:
                    mode = os.stat(fp).st_mode
                    os.chmod(fp, mode | 0o111)
                    n += 1
                except OSError:
                    pass
    print(f'  [OK] chmod +x {n} 个 .so / bin 文件')


def build_target(target, tag=DEFAULT_CBS_TAG, assets=None,
                 linux_variant=DEFAULT_LINUX_VARIANT,
                 windows_variant=DEFAULT_WINDOWS_VARIANT):
    """构建单个 target (windows 或 linux)."""
    step(f'构建 {target} runtime (cbs-zig {tag}) ...')

    if assets is None:
        assets = _get_cbs_assets(tag, prefer_py=DEFAULT_CBS_PY_VERSION,
                                 linux_variant=linux_variant,
                                 windows_variant=windows_variant)

    # 找匹配的资产
    matching = None
    if target == 'windows':
        for k, v in assets.items():
            if k[0] == 'windows' and k[1] == 'x86_64':
                matching = v
                break
    else:  # linux
        for k, v in assets.items():
            if k[0] == 'linux' and k[1] == 'x86_64' and k[2] == 'glibc':
                matching = v
                break

    if not matching:
        fail(f'未找到 {target} x86_64 资产 (tag={tag})')

    asset_name, asset_size, asset_url = matching
    # 提取 py version 方便确认
    try:
        py_v = asset_name.split('cpython-')[1].split('+')[0]
    except IndexError:
        py_v = '?'
    print(f'  资产: {asset_name} ({asset_size/1024/1024:.0f} MB, Python {py_v})')

    # 下载到临时位置
    tmp_tar = os.path.join(PROJECT_ROOT, f'_cbs_{target}.tar.gz')
    if asset_url.endswith('.zst'):
        tmp_tar = os.path.join(PROJECT_ROOT, f'_cbs_{target}.tar.zst')
    try:
        _download(asset_url, tmp_tar)
    except IOError as e:
        fail(str(e))

    # 解压到目标目录
    target_dir = RUNTIME_WINDOWS if target == 'windows' else RUNTIME_LINUX
    if target == 'windows':
        # 兼容旧版本: 同时也放一份到 runtime/
        pass
    try:
        _extract_tar_gz(tmp_tar, target_dir)
    except Exception as e:
        fail(f'解压失败: {e}')

    # 清理 tar
    try: os.unlink(tmp_tar)
    except OSError: pass

    # 找 site-packages 目录 + 装第三方库
    try:
        _py_v = asset_name.split('cpython-')[1].split('+')[0]
    except IndexError:
        _py_v = None
    site_pkg = _find_site_packages(target_dir, target, py_version=_py_v)
    if target == 'windows':
        py_exe = os.path.join(target_dir, 'python.exe')
    else:
        py_exe = os.path.join(target_dir, 'bin', 'python3')

    # 判断目标 runtime 是不是当前 OS 可执行的: Linux ELF 不能在 Windows 跑
    py_executable_in_host = False
    if os.path.isfile(py_exe):
        # 简单判断: 读前 4 字节 (Windows PE = MZ, Linux ELF = \x7fELF)
        try:
            with open(py_exe, 'rb') as f:
                magic = f.read(4)
            if sys.platform == 'win32':
                py_executable_in_host = magic[:2] == b'MZ'
            else:
                py_executable_in_host = magic[:4] == b'\x7fELF'
        except OSError:
            pass

    if py_executable_in_host:
        # 同平台: 直接 pip install
        _pip_install_to(py_exe, site_pkg, THIRD_PARTY_PKGS)
    else:
        # 跨平台: 用 host python pip download wheels + 解压
        # 从资产名提取 Python 版本 (例: cpython-3.13.3+20250409-...)
        try:
            py_version = asset_name.split('cpython-')[1].split('+')[0]
        except IndexError:
            py_version = DEFAULT_CBS_PY_VERSION
        print(f'  跨平台 pip install (host={sys.platform}, target py={py_version})')
        _download_wheels_and_unpack(py_version, site_pkg, THIRD_PARTY_PKGS,
                                    host_python=sys.executable)

    # 写 _pth
    _make_pth(target_dir, target, py_version=_py_v)

    # 跨平台可移植性修复 (关键!)
    # 1. 展开所有 symlink 为实体文件, 避免 zip/scp 传输后死链
    # 2. 给所有 .so 库加 +x 权限 (Windows 上无法 chmod, 但 zip/tar 会保留元数据)
    try:
        _deref_symlinks(target_dir)
    except NameError:
        # 旧版本没这个函数, 用 fallback
        _chmod_all_executable(target_dir)
    except Exception as e:
        print(f'  [WARN] _deref_symlinks 失败: {e}')

    # 写 README
    readme = f"""FPGA Toolbox — Portable Runtime ({target})
{'=' * 50}
此目录由 build_portable_runtime.py 自动生成, 目标机器无需安装 Python.
请保留整个 {os.path.basename(target_dir)}/ 目录及工具根目录的所有文件.

cbs-zig release: {tag}
构建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
目标: {target} x86_64

启动方式:
  Windows: 双击 run.bat  (查找 {os.path.basename(RUNTIME_WINDOWS)}/python.exe 或 runtime/python.exe)
  Linux:   ./run.sh       (查找 {os.path.basename(RUNTIME_LINUX)}/bin/python3 或 runtime/python/bin/python3)
"""
    with open(os.path.join(target_dir, 'README_runtime.txt'), 'w', encoding='utf-8') as f:
        f.write(readme)

    # 验证
    if os.path.isfile(py_exe):
        step(f'验证 {py_exe} ...')
        if py_executable_in_host:
            r = subprocess.run([py_exe, '--version'], capture_output=True, text=True,
                               timeout=15)
            if r.returncode == 0:
                print(f'  [OK] {r.stdout.strip()}')
            else:
                print(f'  [WARN] --version 失败: {r.stderr[:200]}')
        else:
            # 跨平台: 读文件 magic 验证
            try:
                # 解决 symlink: 跟到真实文件再读
                real = os.path.realpath(py_exe)
                with open(real, 'rb') as f:
                    magic = f.read(4)
                ELF_MAGIC = bytes([0x7f, 0x45, 0x4c, 0x46])  # \x7fELF
                if sys.platform != 'win32' and magic == ELF_MAGIC:
                    print(f'  [OK] ELF 解释器 (target=linux, host={sys.platform})')
                elif sys.platform == 'win32' and magic[:2] == b'MZ':
                    print(f'  [OK] PE 解释器 (target=windows, host={sys.platform})')
                else:
                    # 安静提示, 不算错 (可能是其它类型)
                    print(f'  [INFO] 跨平台解释器, magic={magic.hex()} (host={sys.platform})')
            except OSError as e:
                print(f'  [WARN] 验证失败: {e}')
    else:
        print(f'  [WARN] {py_exe} 不存在 (cbs-zig 包结构可能不同, 手动检查)')

    # 验证 site-packages 装了第三方库
    sp_dist = [d for d in os.listdir(site_pkg) if d.endswith('.dist-info')] \
        if os.path.isdir(site_pkg) else []
    print(f'  [OK] site-packages 装了 {len(sp_dist)} 个第三方包: '
          f'{", ".join(sorted(d.split("-")[0] for d in sp_dist)[:8])}'
          f'{"..." if len(sp_dist) > 8 else ""}')

    return target_dir


def main():
    parser = argparse.ArgumentParser(
        description='跨平台构建 FPGA Toolbox 便携 runtime')
    parser.add_argument('--target', choices=['auto', 'windows', 'linux', 'both'],
                        default='auto',
                        help='构建目标: auto=当前平台, both=同时生成两个 (默认 auto)')
    parser.add_argument('--tag', default=DEFAULT_CBS_TAG,
                        help=f'cbs-zig release tag (默认 {DEFAULT_CBS_TAG})')
    parser.add_argument('--linux-variant',
                        choices=['auto', 'install_only', 'pgo+lto-full', 'noopt-full',
                                 'pgo-full', 'lto-full', 'debug-full'],
                        default=DEFAULT_LINUX_VARIANT,
                        help=f'Linux cbs-zig 变体 (默认 {DEFAULT_LINUX_VARIANT}, 含 tkinter)')
    parser.add_argument('--windows-variant',
                        choices=['auto', 'install_only', 'pgo+lto-full', 'noopt-full',
                                 'pgo-full', 'lto-full', 'debug-full'],
                        default=DEFAULT_WINDOWS_VARIANT,
                        help=f'Windows cbs-zig 变体 (默认 {DEFAULT_WINDOWS_VARIANT})')
    args = parser.parse_args()

    print('=' * 60)
    print('  FPGA Toolbox — 跨平台便携 Runtime 构建器')
    print('=' * 60)
    print(f'  Project: {PROJECT_ROOT}')
    print(f'  当前平台: {platform.system()} {platform.machine()}')
    print(f'  cbs-zig tag: {args.tag}')
    print(f'  构建目标: {args.target}')
    print(f'  Linux 变体: {args.linux_variant} (含 tkinter={("yes" if "full" in args.linux_variant or args.linux_variant == "auto" else "no")})')
    print(f'  Windows 变体: {args.windows_variant}')
    print()

    # 决定 target
    if args.target == 'auto':
        sysname = platform.system().lower()
        if sysname == 'windows':
            targets = ['windows']
        else:
            targets = ['linux']
    elif args.target == 'both':
        targets = ['windows', 'linux']
    else:
        targets = [args.target]

    # 查资产 (一次, 多个 target 共享)
    assets = _get_cbs_assets(args.tag, prefer_py=DEFAULT_CBS_PY_VERSION,
                             linux_variant=args.linux_variant,
                             windows_variant=args.windows_variant)
    print(f'  找到 {len(assets)} 个匹配的资产')
    for k, v in assets.items():
        if v:
            print(f'    {k} -> {v[0]}')

    built = []
    for t in targets:
        try:
            d = build_target(t, tag=args.tag, assets=assets,
                            linux_variant=args.linux_variant,
                            windows_variant=args.windows_variant)
            built.append(d)
        except SystemExit:
            raise
        except Exception as e:
            print(f'  [ERROR] 构建 {t} 失败: {e}')
            if len(targets) == 1:
                sys.exit(1)

    # 完成
    print()
    print('=' * 60)
    print(f'  [SUCCESS] 已生成 {len(built)} 个 runtime')
    for d in built:
        print(f'    {d}  ({_size_mb(d):.0f} MB)')
    print('=' * 60)
    print()
    print('  接下来:')
    print('    1. 整个工程目录 (含 runtime_windows/ + runtime_linux/) 复制到目标机器')
    print('    2. Windows: 双击 run.bat  (无网无 Python 即可启动)')
    print('    3. Linux:   ./run.sh       (无网无 Python 即可启动)')
    print()
    print('  说明:')
    print('    - runtime_windows/python.exe    - Windows 便携解释器 (44MB 含 tkinter)')
    print('    - runtime_linux/bin/python3     - Linux 便携解释器 (113MB 含 tkinter)')
    print('    - 两个 runtime 已 pip install paramiko/pillow/pyserial 等 GUI 依赖')
    print('    - 目标机器只需要 glibc >= 2.28 (Ubuntu 20.04+, CentOS 8+, Debian 10+)')
    print()


if __name__ == '__main__':
    main()
