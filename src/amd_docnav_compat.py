#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
amd_docnav_compat.py — DocNav 多版本兼容层 (不修改原 amd_doc_downloader.py)
=====================================================================
解决: 不同版本 DocNav 的 xdocs.xml schema 不一样
  - 19.1 / 20.x: <webLocation> 是 PDF 直链, 没有 <downloadURL>
  - 25.2:        <downloadURL> 是 PDF 直链
  - 未来版本:    未知

工作原理 (双链路):
  链路1 (本地 xdocs.xml): 扫所有可能字段 (downloadURL / webLocation / attachment / file),
                          收集 URL, 按 .pdf 后缀判定 PDF
  链路2 (AMD khub 兜底):  当 xdocs.xml 解析不到任何 PDF, 或下载失败时,
                          自动转 AMD 官方 API  (docs.amd.com/api/khub/...)
                          按 Document_ID 查 maps, 再下载 attachments/content

设计原则:
  - 只新增文件, 不动 amd_doc_downloader.py
  - GUI 端可选切换: 用原版 (昨晚逻辑) 还是用兼容层
  - 默认走兼容层, 因为覆盖面更广

用法:
  from src.amd_docnav_compat import parse_xdocs_compat, search_docs_compat
  docs = parse_xdocs_compat()  # 替代原 parse_xdocs()
  results = search_docs_compat('can')
"""

import os
import sys
import json
import ssl
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ============== 配置 ==============
_KHUB_BASE = 'https://docs.amd.com'
_KHUB_TIMEOUT = 30
_DOWNLOAD_TIMEOUT = 120
_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.fpga_tool')
_KHUB_CACHE_FILE = os.path.join(_CACHE_DIR, 'amd_khub_maps_cache.json')
_KHUB_CACHE_TTL = 7 * 24 * 3600  # 7 天过期

# SSL 跳过校验
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


# ============== 链路1: 本地 xdocs.xml 多版本兼容 ==============

# 可能的 URL 字段名 (按优先级, 先到先得)
_URL_FIELDS = ('downloadURL', 'webLocation', 'attachment', 'file', 'url')


def _extract_url(doc):
    """
    从一个 <document> 节点提取最佳 PDF URL
    尝试所有可能的字段, 跳过明显是 HTML 页面的, 优先 PDF 直链
    """
    best = None
    for field in _URL_FIELDS:
        elem = doc.find(field)
        if elem is None or not elem.text:
            continue
        url = elem.text.strip()
        if not url.startswith(('http://', 'https://')):
            continue
        # 优先 PDF
        if url.lower().split('?')[0].endswith('.pdf'):
            return url
        # 备选非 PDF (但先记着, 万一都找不到 PDF)
        if best is None:
            best = url
    return best


def _is_pdf_url(url):
    """判定 URL 是否 PDF 直链"""
    if not url:
        return False
    return url.lower().split('?')[0].endswith('.pdf')


def parse_xdocs_compat(xml_path=None):
    """
    解析 xdocs.xml, 兼容 19.1/20.x/25.2/未来版本
    收集所有可能的 PDF URL, 忽略 schema 差异
    Returns: [{'docID', 'title', 'downloadURL' (主 URL), 'webLocation', 'url' (最佳), 'has_pdf', 'source'}, ...]
    """
    if xml_path is None:
        # 复用原版查找函数
        from src.amd_doc_downloader import find_xdocs_xml
        xml_path, _ = find_xdocs_xml()
    if not xml_path or not os.path.isfile(xml_path):
        return []

    docs = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f'[compat] parse error: {e}')
        return []

    for doc in root.iter('document'):
        doc_id_elem = doc.find('docID')
        if doc_id_elem is None:
            continue
        doc_id = (doc_id_elem.text or '').strip()
        if not doc_id:
            continue

        title_elem = doc.find('title')
        title = (title_elem.text or '').strip() if title_elem is not None and title_elem.text else ''

        # 提取所有可能 URL
        urls = {}
        for field in _URL_FIELDS:
            elem = doc.find(field)
            if elem is not None and elem.text:
                u = elem.text.strip()
                if u.startswith(('http://', 'https://')):
                    urls[field] = u

        if not urls:
            continue

        # 选最佳 URL: 优先 PDF
        best_url = None
        for u in urls.values():
            if _is_pdf_url(u):
                best_url = u
                break
        if not best_url:
            best_url = next(iter(urls.values()))

        docs.append({
            'docID': doc_id,
            'title': title,
            'downloadURL': urls.get('downloadURL', ''),
            'webLocation': urls.get('webLocation', ''),
            'url': best_url,
            'has_pdf': _is_pdf_url(best_url),
            'source': 'xdocs.xml',
        })

    return docs


def search_docs_compat(keyword, xml_path=None):
    """
    按关键词搜索 (兼容版) - 匹配 docID 或 title
    """
    docs = parse_xdocs_compat(xml_path)
    if not docs or not keyword or not keyword.strip():
        return docs

    kw = keyword.strip().upper()
    results = []
    for d in docs:
        if kw in d['docID'].upper() or kw in d['title'].upper():
            results.append(d)

    # 排序: 精确匹配 docID > startswith > 其它
    results.sort(key=lambda d: (
        0 if d['docID'].upper() == kw else
        1 if d['docID'].upper().startswith(kw) else
        2
    ))
    return results


# ============== 链路2: AMD khub API 兜底 ==============

def _http_get_json(url, timeout=_KHUB_TIMEOUT):
    """GET 一个 JSON 接口"""
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 Chrome/120.0'})
    resp = urlopen(req, context=_SSL_CTX, timeout=timeout)
    return json.loads(resp.read().decode('utf-8', errors='ignore'))


def _get_khub_maps(force_refresh=False):
    """
    拿 AMD khub 全量 maps (缓存到本地)
    14MB JSON, 首次下载后缓存 7 天
    """
    os.makedirs(_CACHE_DIR, exist_ok=True)

    # 读缓存
    if not force_refresh and os.path.isfile(_KHUB_CACHE_FILE):
        mtime = os.path.getmtime(_KHUB_CACHE_FILE)
        if time.time() - mtime < _KHUB_CACHE_TTL:
            try:
                with open(_KHUB_CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

    # 联网拉取
    url = f'{_KHUB_BASE}/api/khub/maps?size=10000'
    data = _http_get_json(url, timeout=60)

    # 写缓存
    try:
        with open(_KHUB_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

    return data


def _get_meta(d, key):
    for m in d.get('metadata', []):
        if m.get('key') == key:
            v = m.get('values') or ['']
            return v[0] if v else ''
    return ''


def search_khub(docid, force_refresh=False):
    """
    在 AMD khub 中按 Document_ID 查单个文档
    Returns: {
        'docID': 'pg096',
        'title': '...',
        'khub_id': 'xxx',
        'attachment_id': 'xxx',
        'pdf_url': 'https://docs.amd.com/api/khub/maps/.../attachments/.../content',
        'size': 844377,
        'filename': 'pg096-can-en-us-5.1.pdf',
    } 或 None
    """
    try:
        maps = _get_khub_maps(force_refresh=force_refresh)
    except Exception as e:
        print(f'[khub] maps fetch error: {e}')
        return None

    docid_lower = docid.lower()
    candidates = []
    for d in maps:
        did = _get_meta(d, 'Document_ID').lower()
        if did == docid_lower:
            candidates.append(d)
    if not candidates:
        return None

    # 优先 en-US, isLatest
    candidates.sort(key=lambda d: (
        0 if _get_meta(d, 'ft:locale') == 'en-US' else 1,
        0 if _get_meta(d, 'isLatest').lower() == 'true' else 1,
    ))
    best = candidates[0]

    _id = best.get('id')
    title = best.get('title', '')

    # 拉 attachments
    try:
        atts = _http_get_json(f'{_KHUB_BASE}/api/khub/maps/{_id}/attachments', timeout=15)
    except Exception as e:
        print(f'[khub] attachments error: {e}')
        return None

    pdf_att = next((a for a in atts if a.get('mimeType') == 'application/pdf'), None)
    if not pdf_att:
        return None

    att_id = pdf_att.get('id')
    return {
        'docID': docid,
        'title': title,
        'khub_id': _id,
        'attachment_id': att_id,
        'pdf_url': f'{_KHUB_BASE}/api/khub/maps/{_id}/attachments/{att_id}/content',
        'size': pdf_att.get('size', 0),
        'filename': pdf_att.get('file', f'{docid}.pdf'),
    }


# ============== 智能下载 (双链路) ==============

def download_pdf_smart(url, output_path, doc_id=None, force_khub=False, timeout=_DOWNLOAD_TIMEOUT):
    """
    智能下载: 优先用原 URL, 失败/无 PDF 时转 AMD khub 兜底
    url: 本地 xdocs.xml 里的 URL
    doc_id: 文档 ID (用于 khub 兜底), 必传
    """
    # 1) 如果 URL 明显不是 PDF, 直接走 khub
    if force_khub or not _is_pdf_url(url):
        return _download_via_khub(doc_id, output_path, timeout)

    # 2) 尝试直链下载
    ok, msg = _download_direct(url, output_path, timeout)
    if ok:
        return ok, msg

    # 3) 失败, 转 khub 兜底
    print(f'[compat] 直链失败 ({msg}), 转 khub 兜底: {doc_id}')
    return _download_via_khub(doc_id, output_path, timeout)


def _download_direct(url, output_path, timeout):
    """直链下载, 验证 Content-Type 必须是 PDF"""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        try:
            with open(output_path, 'rb') as _f:
                _h = _f.read(4)
            if _h == b'%PDF':
                _s = os.path.getsize(output_path)
                return True, f'已存在 ({_s/1024:.1f} KB)'
            os.remove(output_path)
        except OSError:
            pass

    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0',
            'Accept': 'application/pdf,*/*',
        })
        resp = urlopen(req, context=_SSL_CTX, timeout=timeout)
        ct = (resp.headers.get('Content-Type') or '').lower()

        # 关键校验: 服务器返回的必须真的是 PDF
        if 'pdf' not in ct and not _is_pdf_url(url):
            return False, f'非PDF内容 (CT={ct})'

        with open(output_path, 'wb') as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        size = os.path.getsize(output_path)
        if size < 1024:
            return False, f'文件太小 ({size}B), 可能不是 PDF'

        # 校验 PDF 头
        with open(output_path, 'rb') as f:
            head = f.read(4)
        if head != b'%PDF':
            try: os.remove(output_path)
            except OSError: pass
            return False, '文件头不是 %PDF (已删)'
            return False, '文件头不是 %PDF'

        return True, f'下载成功 ({size/1024:.1f} KB)'

    except HTTPError as e:
        return False, f'HTTP {e.code}'
    except URLError as e:
        return False, f'连接失败: {str(e.reason)[:40]}'
    except Exception as e:
        return False, str(e)[:80]


def _download_via_khub(doc_id, output_path, timeout):
    """通过 AMD khub API 下载"""
    if not doc_id:
        return False, 'doc_id 必传'

    info = search_khub(doc_id)
    if not info:
        return False, f'khub 中未找到 {doc_id}'

    return _download_direct(info['pdf_url'], output_path, timeout)


# ============== 批量下载 (兼容版) ==============

def batch_download_smart(docs, output_dir, progress_callback=None, use_khub_fallback=True):
    """
    批量下载 (智能版)
    docs: [{'docID', 'url'/'downloadURL'/'webLocation', ...}, ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    total = len(docs)

    for i, doc in enumerate(docs):
        doc_id = doc.get('docID', '')
        url = (doc.get('url') or doc.get('downloadURL') or doc.get('webLocation') or '')
        output_path = os.path.join(output_dir, f'{doc_id}.pdf')

        ok, msg = download_pdf_smart(url, output_path, doc_id=doc_id)
        results[doc_id] = (ok, msg)

        if progress_callback:
            progress_callback(i + 1, total, doc, ok, msg)

    return results


# ============== 统计 ==============

def get_compat_stats():
    """兼容层统计信息"""
    stats = {
        'xdocs_total': 0,
        'xdocs_pdf': 0,
        'xdocs_non_pdf': 0,
        'khub_cache_exists': os.path.isfile(_KHUB_CACHE_FILE),
        'khub_cache_age_days': 0,
    }

    docs = parse_xdocs_compat()
    stats['xdocs_total'] = len(docs)
    stats['xdocs_pdf'] = sum(1 for d in docs if d.get('has_pdf'))
    stats['xdocs_non_pdf'] = stats['xdocs_total'] - stats['xdocs_pdf']

    if stats['khub_cache_exists']:
        age = time.time() - os.path.getmtime(_KHUB_CACHE_FILE)
        stats['khub_cache_age_days'] = round(age / 86400, 1)

    return stats


if __name__ == '__main__':
    print('=== DocNav 兼容层测试 ===')
    stats = get_compat_stats()
    print(f'xdocs.xml: {stats["xdocs_total"]} 篇, PDF={stats["xdocs_pdf"]}, 非PDF={stats["xdocs_non_pdf"]}')
    print(f'khub 缓存: {"有" if stats["khub_cache_exists"] else "无"} ({"%.1f" % stats["khub_cache_age_days"]} 天)')

    kw = sys.argv[1] if len(sys.argv) > 1 else input('搜索关键词: ').strip() or 'can'
    print(f'\n--- 搜 "{kw}" (xdocs.xml) ---')
    results = search_docs_compat(kw)
    for d in results[:5]:
        kind = 'PDF' if d['has_pdf'] else 'WEB'
        print(f'  {d["docID"]:10s} [{kind}] {d["title"][:50]}')
        print(f'    -> {d["url"][:90]}')

    if results:
        first_id = results[0]['docID']
        print(f'\n--- khub 兜底查 {first_id} ---')
        info = search_khub(first_id)
        if info:
            print(f'  khub_id={info["khub_id"]}')
            print(f'  PDF URL: {info["pdf_url"]}')
            print(f'  文件名: {info["filename"]}, size: {info["size"]}')
        else:
            print(f'  khub 中未找到')
