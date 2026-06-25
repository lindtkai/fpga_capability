#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMD/Xilinx 文档下载器 — 基于 DocNav 本地 xdocs.xml 数据库
工作原理:
  1. 解析 DocNav 的 xdocs.xml, 提取 {docID, title, downloadURL}
  2. 按关键词搜索 (匹配 docID 或 title)
  3. 通过 downloadURL 直链下载 PDF 到 ip_docs/
"""

import os
import sys
import json
import ssl
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ====== 配置持久化路径 ======
_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.fpga_tool')
_CONFIG_FILE = os.path.join(_CONFIG_DIR, 'docnav_config.json')

# ====== DocNav 常见安装路径 (按优先级排序) ======
_DOCNAV_CANDIDATE_PATHS = [
    r'D:\software\xilinx\DocNav',
    r'D:\Xilinx\DocNav',
    r'C:\Xilinx\DocNav',
    r'C:\software\xilinx\DocNav',
    r'D:\AMD\DocNav',
    r'C:\AMD\DocNav',
]

# ====== 搜索缓存 ======
_cache = None          # list of {'docID': str, 'title': str, 'downloadURL': str}
_cache_xml_path = None


def _load_config():
    """加载 DocNav 路径配置"""
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_config(config):
    """保存 DocNav 路径配置"""
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def find_xdocs_xml(docnav_dir=None):
    """
    自动查找 xdocs.xml 文件路径
    返回 (path, is_auto_detected)
    """
    # 1) 从配置文件读取
    if docnav_dir is None:
        config = _load_config()
        if config.get('docnav_dir'):
            docnav_dir = config['docnav_dir']

    # 2) 尝试已知目录
    if docnav_dir:
        xml_path = os.path.join(docnav_dir, 'resources', 'xdocs.xml')
        if os.path.isfile(xml_path):
            return xml_path, False

    # 3) 自动探测常见安装路径
    for base in _DOCNAV_CANDIDATE_PATHS:
        xml_path = os.path.join(base, 'resources', 'xdocs.xml')
        if os.path.isfile(xml_path):
            _save_config({'docnav_dir': base})
            return xml_path, True

    return None, False


def set_docnav_dir(docnav_dir):
    """手动设置 DocNav 安装目录并持久化"""
    config = _load_config()
    config['docnav_dir'] = docnav_dir
    _save_config(config)


def get_docnav_dir():
    """获取已配置的 DocNav 目录"""
    config = _load_config()
    return config.get('docnav_dir', None)


def parse_xdocs(xml_path=None):
    """
    解析 xdocs.xml，返回文档列表
    Returns: [(docID, title, downloadURL), ...]
    """
    global _cache, _cache_xml_path

    if xml_path is None:
        xml_path, _auto = find_xdocs_xml()
    if xml_path is None:
        return []
    if not os.path.isfile(xml_path):
        return []

    # 使用缓存 (同一个 xml 文件)
    if _cache is not None and _cache_xml_path == xml_path:
        return _cache

    docs = []
    tree = ET.parse(xml_path)
    root = tree.getroot()

    for doc in root.iter('document'):
        doc_id_elem = doc.find('docID')
        url_elem = doc.find('downloadURL')
        title_elem = doc.find('title')

        if doc_id_elem is None or url_elem is None:
            continue

        doc_id = (doc_id_elem.text or '').strip()
        url = (url_elem.text or '').strip()
        title = (title_elem.text or '').strip() if title_elem is not None else ''

        if not doc_id or not url:
            continue

        docs.append({
            'docID': doc_id,
            'title': title,
            'downloadURL': url,
        })

    _cache = docs
    _cache_xml_path = xml_path
    return docs


def search_docs(keyword, xml_path=None):
    """
    按关键词搜索文档
    keyword: 搜索关键词 (如 'CAN', 'GTX', 'AXI', 'UG476')
    Returns: [{'docID': ..., 'title': ..., 'downloadURL': ...}, ...]
    匹配规则: keyword (大小写不敏感) 出现在 docID 或 title 中
    """
    docs = parse_xdocs(xml_path)
    if not docs or not keyword or not keyword.strip():
        return docs

    kw = keyword.strip().upper()
    results = []
    for doc in docs:
        if kw in doc['docID'].upper() or kw in doc['title'].upper():
            results.append(doc)

    # 优先按 docID 精确匹配排前面
    results.sort(key=lambda d: (
        0 if d['docID'].upper() == kw else
        1 if d['docID'].upper().startswith(kw) else
        2
    ))

    return results


# ====== SSL 上下文 (跳过证书验证, 兼容内网/自签名) ======
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def download_pdf(url, output_path, timeout=120):
    """
    下载单个 PDF (纯标准库 urllib)
    Returns: (success: bool, message: str)
    """
    try:
        # 如果已经存在且大小>0，跳过
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            size_kb = os.path.getsize(output_path) / 1024
            return True, f'已存在 ({size_kb:.1f} KB)'

        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,*/*',
        })
        resp = urlopen(req, context=_SSL_CTX, timeout=timeout)
        if resp.status != 200:
            return False, f'HTTP {resp.status}'

        with open(output_path, 'wb') as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        size_kb = os.path.getsize(output_path) / 1024
        return True, f'下载成功 ({size_kb:.1f} KB)'
    except HTTPError as e:
        return False, f'HTTP {e.code}'
    except URLError as e:
        return False, f'连接失败: {str(e.reason)[:40]}'
    except OSError as e:
        return False, f'超时' if 'timed out' in str(e).lower() else str(e)[:60]
    except Exception as e:
        return False, str(e)[:80]


def batch_download(docs, output_dir, progress_callback=None):
    """
    批量下载文档
    docs: [{'docID': ..., 'downloadURL': ...}, ...]
    output_dir: 输出目录 (如 ip_docs/)
    progress_callback: 可选, progress_callback(current, total, doc, status)
    Returns: {docID: (success, message), ...}
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    total = len(docs)

    for i, doc in enumerate(docs):
        doc_id = doc['docID']
        url = doc['downloadURL']
        output_path = os.path.join(output_dir, f'{doc_id}.pdf')

        ok, msg = download_pdf(url, output_path)

        results[doc_id] = (ok, msg)

        if progress_callback:
            progress_callback(i + 1, total, doc, ok, msg)

    return results


def get_docnav_stats():
    """获取 DocNav 数据库统计信息"""
    docs = parse_xdocs()
    if not docs:
        return {'total': 0, 'xml_path': None}
    return {
        'total': len(docs),
        'xml_path': _cache_xml_path,
    }


if __name__ == '__main__':
    # 命令行测试
    print('=== AMD DocNav 文档下载器 ===')
    xml_path, auto = find_xdocs_xml()
    if xml_path:
        print(f'xdocs.xml 路径: {xml_path}  (自动检测: {auto})')
    else:
        print('未找到 DocNav 安装, 请设置 DOCNAV_DIR 环境变量')

    stats = get_docnav_stats()
    print(f'文档总数: {stats["total"]}')

    if len(sys.argv) > 1:
        kw = sys.argv[1]
    else:
        kw = input('输入搜索关键词: ').strip() or 'CAN'

    results = search_docs(kw)
    print(f'\n搜索 "{kw}" 找到 {len(results)} 个文档:')
    for doc in results:
        print(f'  {doc["docID"]:10s}  {doc["title"][:70]}')
        print(f'           → {doc["downloadURL"][:90]}')
