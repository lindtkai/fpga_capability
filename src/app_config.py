#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_config.py — 全局应用配置 (设置 Tab 共享)
管理 Vivado 路径 和 DocNav 路径，持久化到 ~/.fpga_tool/app_config.json
所有 Tab 通过此模块读写路径，无需各自硬编码。
"""

import os
import json

_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.fpga_tool')
_CONFIG_FILE = os.path.join(_CONFIG_DIR, 'app_config.json')

# ====== 内部缓存 ======
_config_cache = None


def _ensure_config_dir():
    os.makedirs(_CONFIG_DIR, exist_ok=True)


def _load_raw():
    """从磁盘加载原始配置 dict"""
    global _config_cache
    _ensure_config_dir()
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
                _config_cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _config_cache = {}
    else:
        _config_cache = {}

    # 确保基本键存在
    _config_cache.setdefault('vivado_paths', [])
    _config_cache.setdefault('docnav_paths', [])
    return _config_cache


def _save():
    """保存配置到磁盘"""
    global _config_cache
    if _config_cache is None:
        return
    _ensure_config_dir()
    with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(_config_cache, f, indent=2, ensure_ascii=False)


def reload():
    """强制从磁盘重新加载（供外部配置变更后同步）"""
    return _load_raw()


# ==================== Vivado 路径管理 ====================

def get_vivado_paths():
    """
    获取所有已配置的 Vivado bin 目录路径列表。
    Returns: list[str]  每个路径指向 Vivado 的 bin/ 目录
    """
    cfg = _load_raw()
    return list(cfg.get('vivado_paths', []))


def add_vivado_path(path):
    """
    添加一个 Vivado 路径（自动探测 bin 子目录）
    path: Vivado 安装目录或 bin/ 目录
    Returns: (True/False, resolved_path_or_error_msg)
    """
    # 自动探测 bin 目录
    resolved = resolve_vivado_bin(path)
    if not resolved:
        return False, '该目录下未找到 vivado.exe'
    path = os.path.normpath(resolved).rstrip(os.sep)
    cfg = _load_raw()
    paths = cfg.setdefault('vivado_paths', [])
    if path in paths:
        return False, '已存在'
    paths.append(path)
    _save()
    return True, path


def remove_vivado_path(path):
    """
    删除一个 Vivado bin 目录路径
    Returns: True=删除成功, False=未找到
    """
    path = os.path.normpath(path).rstrip(os.sep)
    cfg = _load_raw()
    paths = cfg.get('vivado_paths', [])
    if path not in paths:
        return False
    paths.remove(path)
    _save()
    return True


def get_vivado_exe():
    """
    获取 vivado 可执行文件完整路径（优先第一个配置）
    Returns: path 或 None
    """
    for p in get_vivado_paths():
        for exe in _VIVADO_EXES:
            full = os.path.join(p, exe)
            if os.path.isfile(full):
                return full
    return None


def get_vivado_bin_dirs():
    """
    获取所有有效的 Vivado bin 目录 (仅 vivado 可执行文件, 排除 vitis)
    """
    valid = []
    for p in get_vivado_paths():
        for exe in _VIVADO_EXES:
            if os.path.isfile(os.path.join(p, exe)):
                valid.append(p)
                break
    return valid


# ==================== DocNav 路径管理 ====================

def get_docnav_paths():
    """
    获取所有已配置的 DocNav 安装目录路径列表。
    Returns: list[str]  每个路径指向包含 resources/xdocs.xml 的 DocNav 目录
    """
    cfg = _load_raw()
    return list(cfg.get('docnav_paths', []))


def add_docnav_path(path):
    """
    添加一个 DocNav 路径（自动递归查找 resources/xdocs.xml）
    Returns: (True/False, resolved_path_or_error_msg)
    """
    path = os.path.normpath(path).rstrip(os.sep)
    # 先直接检查
    if not validate_docnav_dir(path):
        # 递归查找
        found = _find_docnav_recursive(path)
        if found:
            path = os.path.normpath(found).rstrip(os.sep)
        else:
            return False, '未找到 resources/xdocs.xml (已递归查找子目录)'
    cfg = _load_raw()
    paths = cfg.setdefault('docnav_paths', [])
    if path in paths:
        return False, '已存在'
    paths.append(path)
    _save()
    return True, path


def remove_docnav_path(path):
    """
    删除一个 DocNav 安装目录路径
    Returns: True=删除成功, False=未找到
    """
    path = os.path.normpath(path).rstrip(os.sep)
    cfg = _load_raw()
    paths = cfg.get('docnav_paths', [])
    if path not in paths:
        return False
    paths.remove(path)
    _save()
    return True


def get_xdocs_xml_path():
    """
    获取 xdocs.xml 文件路径（优先第一个配置的 DocNav）
    Returns: path 或 None
    """
    paths = get_docnav_paths()
    for p in paths:
        xml_path = os.path.join(p, 'resources', 'xdocs.xml')
        if os.path.isfile(xml_path):
            return xml_path
    return None


def get_valid_docnav_dirs():
    """获取所有有效（包含 resources/xdocs.xml）的 DocNav 目录"""
    valid = []
    for p in get_docnav_paths():
        xml_path = os.path.join(p, 'resources', 'xdocs.xml')
        if os.path.isfile(xml_path):
            valid.append(p)
    return valid


# ==================== 工具方法 ====================

_VIVADO_EXES = ['vivado.exe', 'vivado.bat', 'vivado'] if os.name == 'nt' else ['vivado']  # 仅 vivado (支持 -mode batch)
_VITIS_EXES = ['vitis.exe', 'vitis.bat', 'vitis'] if os.name == 'nt' else ['vitis']      # vitis (不支持 -mode batch)
_DOCNAV_MARKERS = ['resources/xdocs.xml']


def _find_vivado_exe(path):
    """在路径内智能查找 vivado, 返回 bin 目录路径或 None"""
    # 候选 bin 子目录
    sub_dirs = ['.', 'bin', 'bin/unwrapped/win64.o']
    for sub in sub_dirs:
        for exe in _VIVADO_EXES:
            test_path = os.path.join(path, sub, exe) if sub != '.' else os.path.join(path, exe)
            test_path = os.path.normpath(test_path)
            if os.path.isfile(test_path):
                if sub == '.':
                    return os.path.normpath(path)
                else:
                    return os.path.normpath(os.path.join(path, sub))
    return None


def _find_vivado_recursive(path, max_depth=4):
    """递归查找 Vivado, 返回 bin 目录路径或 None"""
    # 1) 直接尝试当前路径
    result = _find_vivado_exe(path)
    if result:
        return result
    # 2) 递归子目录
    if max_depth <= 0:
        return None
    try:
        for item in os.listdir(path):
            sub = os.path.join(path, item)
            if os.path.isdir(sub) and not item.startswith('.') and item not in ('Windows', '$Recycle.Bin'):
                result = _find_vivado_recursive(sub, max_depth - 1)
                if result:
                    return result
    except (OSError, PermissionError):
        pass
    return None


def _find_docnav_recursive(path, max_depth=3):
    """递归查找 DocNav (resources/xdocs.xml), 返回 DocNav 安装目录或 None"""
    # 1) 直接检查
    xml = os.path.join(path, 'resources', 'xdocs.xml')
    if os.path.isfile(xml):
        return os.path.normpath(path)
    # 2) 递归子目录
    if max_depth <= 0:
        return None
    try:
        for item in os.listdir(path):
            sub = os.path.join(path, item)
            if os.path.isdir(sub) and not item.startswith('.') and item not in ('Windows', '$Recycle.Bin'):
                result = _find_docnav_recursive(sub, max_depth - 1)
                if result:
                    return result
    except (OSError, PermissionError):
        pass
    return None


def validate_vivado_bin(path):
    """验证路径是否包含 Vivado/Vitis (自动探测子目录 + 递归)"""
    if not path or not os.path.isdir(path):
        return False
    # 先检查 vivado
    if _find_vivado_exe(path) is not None or _find_vivado_recursive(path) is not None:
        return True
    # 再检查 vitis (用于验证路径存在, 但不会用于 -mode batch)
    for exe in _VITIS_EXES:
        if os.path.isfile(os.path.join(path, exe)):
            return True
    return False


def resolve_vivado_bin(path):
    """解析路径为真正的 Vivado bin 目录 (自动探测 + 递归)"""
    if not path or not os.path.isdir(path):
        return None
    return _find_vivado_exe(path) or _find_vivado_recursive(path)


def validate_docnav_dir(path):
    """验证路径是否包含 DocNav (自动探测子目录 + 递归)"""
    if not path or not os.path.isdir(path):
        return False
    xml = os.path.join(path, 'resources', 'xdocs.xml')
    if os.path.isfile(xml):
        return True
    return _find_docnav_recursive(path) is not None


# ==================== 初始化时自动迁移旧配置 ====================

def _migrate_old_configs():
    """将旧的分散配置文件迁移到统一配置"""
    cfg = _load_raw()
    changed = False

    # 迁移旧的 vivado_paths.json (TAB 9 用的)
    old_vivado = os.path.join(_CONFIG_DIR, 'vivado_paths.json')
    if os.path.exists(old_vivado) and not cfg.get('vivado_paths'):
        try:
            with open(old_vivado, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            if isinstance(old_data, list):
                for p in old_data:
                    if validate_vivado_bin(p):
                        add_vivado_path(p)
                        changed = True
        except Exception:
            pass

    # 迁移旧的 docnav_config.json (TAB 6 用的)
    old_docnav = os.path.join(_CONFIG_DIR, 'docnav_config.json')
    if os.path.exists(old_docnav) and not cfg.get('docnav_paths'):
        try:
            with open(old_docnav, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            if isinstance(old_data, dict) and old_data.get('docnav_dir'):
                p = old_data['docnav_dir']
                if validate_docnav_dir(p):
                    add_docnav_path(p)
                    changed = True
        except Exception:
            pass

    # 迁移旧的 ~/.fpga_toolbox_config.json (TAB 2 用的 vivado_bin_paths)
    old_toolbox = os.path.join(os.path.expanduser('~'), '.fpga_toolbox_config.json')
    if os.path.exists(old_toolbox):
        try:
            with open(old_toolbox, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            if isinstance(old_data, dict) and old_data.get('vivado_bin_paths'):
                for p in old_data['vivado_bin_paths']:
                    if validate_vivado_bin(p) and p not in cfg.get('vivado_paths', []):
                        add_vivado_path(p)
                        changed = True
        except Exception:
            pass

    return changed


# 模块加载时执行一次迁移
_migrate_old_configs()
