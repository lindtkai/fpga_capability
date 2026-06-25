#!/usr/bin/env python3
"""
gen_inst.py — Verilog/VHDL 例化模板生成工具 (跨平台)
=====================================================
解析 .v/.sv/.vhd/.vhdl 文件，自动生成带方向注释的例化模板。
同时输出 Verilog 和 VHDL 两种格式，自动生成 wire/signal 信号定义。
多例化时信号名自动加 _reg_1, _reg_2 ... 后缀。

用法:
    python3 gen_inst.py                          # GUI 模式 (tkinter)
    python3 gen_inst.py foo.v                    # CLI 单例化
    python3 gen_inst.py foo.v -n 3               # CLI 多例化
    python3 gen_inst.py bar.vhd -n 2 -o out_dir  # 指定输出目录

依赖: Python 3.7+, 标准库 (tkinter 用于 GUI)
日期: 2026-06-18
版本: 2.0
"""

import re
import sys
import os
import json
import argparse
import subprocess

# 确保项目根目录在 sys.path 中
# gen_inst.py 在 src/ 子目录, 项目根是它的上级
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 确保 _pyserial_lib (离线串口库) 在 sys.path 中
_pyserial_dir = os.path.join(_project_root, '_pyserial_lib')
if os.path.isdir(_pyserial_dir) and _pyserial_dir not in sys.path:
    sys.path.insert(0, _pyserial_dir)
import fnmatch
import shutil
from pathlib import Path

# ============================================================================
# 数据结构
# ============================================================================

class Port:
    """端口信息"""
    def __init__(self, name, direction, width=None, vhdl_type=None):
        self.name = name
        self.direction = direction  # 'input'|'output'|'inout'
        self.width = width          # e.g. '[7:0]' or None
        self.vhdl_type = vhdl_type  # original VHDL type string

class Param:
    """参数/泛型信息"""
    def __init__(self, name, default=None, vhdl_type=None):
        self.name = name
        self.default = default
        self.vhdl_type = vhdl_type

class ModuleInfo:
    """模块/实体信息"""
    def __init__(self, name, ports, params, lang):
        self.name = name
        self.ports = ports      # list[Port]
        self.params = params    # list[Param]
        self.lang = lang        # 'verilog'|'vhdl'


# ============================================================================
# 通用工具
# ============================================================================

def remove_verilog_comments(text):
    """去除 Verilog 注释: // 和 /* */"""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
    return text

def remove_vhdl_comments(text):
    """去除 VHDL 注释: --"""
    return re.sub(r'--.*$', '', text, flags=re.MULTILINE)

def extract_balanced_parens(text, start_pos):
    """从 start_pos ( '(' 的位置 ) 提取匹配括号内容"""
    depth = 0
    for i in range(start_pos, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return text[start_pos + 1:i]
    return text[start_pos + 1:]

def split_by_comma_top_level(text):
    """按逗号分割，忽略方括号 [] 内的逗号"""
    parts = []
    current = ""
    depth = 0
    for ch in text:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        elif ch == ',' and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += ch
    if current.strip():
        parts.append(current.strip())
    return parts


# ============================================================================
# Verilog 解析器
# ============================================================================

def parse_verilog(text):
    """解析 Verilog module 声明 (支持参数块嵌套括号)"""
    clean = remove_verilog_comments(text)

    # 查找 module 关键字
    m = re.search(r'module\s+(\w+)', clean)
    if not m:
        raise ValueError("未找到 Verilog module 声明")

    module_name = m.group(1)
    after_name = clean[m.end():]

    # 跳过空白，找 # 或 (
    pos = 0
    has_params = False
    while pos < len(after_name) and after_name[pos] in ' \t\n\r':
        pos += 1

    if pos < len(after_name) and after_name[pos] == '#':
        has_params = True
        # 找到 # 后的 (
        p = pos + 1
        while p < len(after_name) and after_name[p] in ' \t\n\r':
            p += 1
        if p < len(after_name) and after_name[p] == '(':
            param_block = extract_balanced_parens(after_name, p)
            pos = p + len(param_block) + 2  # 跳过 ')' 到下一个字符

    # 找端口列表的 (
    while pos < len(after_name) and after_name[pos] in ' \t\n\r':
        pos += 1

    if pos >= len(after_name) or after_name[pos] != '(':
        raise ValueError("未找到 Verilog module 的端口列表 '('")

    port_text = extract_balanced_parens(after_name, pos)

    # 判断 ANSI 风格
    is_ansi = bool(re.search(r'\b(input|output|inout)\b', port_text, re.IGNORECASE))

    if is_ansi:
        ports = _parse_verilog_ansi_ports(port_text)
    else:
        ports = _parse_verilog_non_ansi_ports(clean, port_text)

    # 始终调用参数解析: 它会先尝试 module #(...) 头, 再尝试 body 内 parameter
    # (即使 module 头没写 #(), body 内也可能有 parameter 声明)
    params = _parse_verilog_params(clean)

    return ModuleInfo(module_name, ports, params, 'verilog')

def _parse_verilog_ansi_ports(port_text):
    """解析 ANSI 风格端口"""
    ports = []
    parts = split_by_comma_top_level(port_text)

    cur_direction = ""
    cur_width = None

    for part in parts:
        if not part:
            continue

        # 去除 Verilog-2001 属性 (* ... *)
        part = re.sub(r'\(\s*\*.*?\*\s*\)', '', part)

        # 检查方向关键字
        dir_match = re.match(r'\s*(input|output|inout)\b', part, re.IGNORECASE)
        if dir_match:
            cur_direction = dir_match.group(1).lower()
            remaining = part[dir_match.end():]

            # 去除数据类型修饰
            remaining = re.sub(r'^\s+(wire|reg|logic|tri|wand|wor|supply0|supply1|tri0|tri1|triand|trior|trireg)\b',
                               '', remaining)
            remaining = re.sub(r'^\s+(signed|unsigned)\b', '', remaining)

            # 检查位宽
            width_match = re.match(r'^\s*(\[[^\]]+\](?:\s*\[[^\]]+\])*)', remaining)
            if width_match:
                cur_width = width_match.group(1).strip()
                remaining = remaining[width_match.end():]
            else:
                cur_width = None

            remaining = remaining.strip()
        else:
            remaining = part.strip()

        # 可能有逗号分隔的多个名字
        names = [n.strip() for n in remaining.split(',') if n.strip()]
        for name in names:
            if name:
                ports.append(Port(name, cur_direction, cur_width))

    return ports

def _parse_verilog_non_ansi_ports(text, port_text):
    """解析非 ANSI 风格端口"""
    ports = []
    port_names = split_by_comma_top_level(port_text)

    for pname in port_names:
        pname = pname.strip()
        if not pname:
            continue

        # 查找声明: (input|output|inout) [width] name ;
        escaped = re.escape(pname)
        pattern = rf'(input|output|inout)(?:\s+(?:wire|reg|logic|tri))?\s*(\[[^\]]*\])?\s+{escaped}\s*;'
        m = re.search(pattern, text, re.IGNORECASE)

        if m:
            ports.append(Port(
                name=pname,
                direction=m.group(1).lower(),
                width=m.group(2)
            ))
        else:
            ports.append(Port(pname, 'input'))  # 默认 input

    return ports

def _parse_verilog_params(text):
    """解析 Verilog parameter (支持 SystemVerilog 类型: parameter integer name = val)"""
    params = []

    # 提取所有参数声明: 方式1 #(...) 或 方式2 body 内
    param_block = re.search(r'module\s+\w+\s*#\s*\(', text, re.IGNORECASE)
    if param_block:
        block = extract_balanced_parens(text, param_block.end() - 1)
        # 方式1: 参数在 #() 内, 按顶层逗号分割
        parts = split_by_comma_top_level(block)
    else:
        # 方式2: body 内 parameter, 先找 parameter 声明, 按 ; 分割
        # 提取所有以 parameter 开头到 ; 之间的内容
        parts = re.findall(
            r'parameter\s+(?:[^;]|"[^"]*")+;',
            text, re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not re.match(r'parameter\b', part, re.IGNORECASE):
            continue

        # 拆解单条声明: parameter [type] [range] NAME [= default]
        m = re.match(r'^\s*parameter\s+(.+)', part, re.IGNORECASE)
        if not m:
            continue
        decl = m.group(1).strip().rstrip(',;')

        # 去掉 optional [range]
        decl = re.sub(r'\[[^\]]*\]\s*', '', decl, count=1)

        # 查找 '=' 位置
        eq = decl.find('=')
        if eq >= 0:
            before_eq = decl[:eq].strip()
            default = decl[eq + 1:].strip()
        else:
            before_eq = decl.strip()
            default = None

        # name = before_eq 的最后一个 token
        tokens = before_eq.split()
        if tokens:
            name = tokens[-1]
            if name.lower() != 'parameter':
                params.append(Param(name, default))

    return params


# ============================================================================
# VHDL 解析器
# ============================================================================

def parse_vhdl(text):
    """解析 VHDL entity 声明"""
    clean = remove_vhdl_comments(text)

    m = re.search(r'entity\s+(\w+)\s+is\b', clean, re.IGNORECASE)
    if not m:
        raise ValueError("未找到 VHDL entity 声明")

    entity_name = m.group(1)
    body_start = m.end()

    # 提取 entity body (到 end)
    end_m = re.search(r'\bend\b(?:\s+entity)?(?:\s+\w+)?\s*;', clean, re.IGNORECASE)
    if end_m:
        body = clean[body_start:end_m.start()]
    else:
        body = clean[body_start:]

    # 解析 generic
    params = []
    gen_m = re.search(r'generic\s*\(', body, re.IGNORECASE)
    if gen_m:
        gen_text = extract_balanced_parens(body, gen_m.end() - 1)
        params = _parse_vhdl_generics(gen_text)

    # 解析 port
    ports = []
    port_m = re.search(r'port\s*\(', body, re.IGNORECASE)
    if port_m:
        port_text = extract_balanced_parens(body, port_m.end() - 1)
        ports = _parse_vhdl_ports(port_text)

    return ModuleInfo(entity_name, ports, params, 'vhdl')

def _parse_vhdl_generics(text):
    """解析 VHDL generic (处理字符串内的 ; 和括号嵌套)"""
    params = []
    decls = [d.strip() for d in _split_vhdl_decls(text) if d.strip()]

    for decl in decls:
        m = re.match(r'^\s*(.+?)\s*:\s*(\w+)(?:\s*:=\s*(.+))?$', decl)
        if m:
            names_str = m.group(1)
            vhdl_type = m.group(2)
            default = m.group(3).strip() if m.group(3) else None

            names = [n.strip() for n in names_str.split(',') if n.strip()]
            for n in names:
                params.append(Param(n, default, vhdl_type))

    return params

def _split_vhdl_decls(text):
    """按顶层 ; 分割 VHDL 声明, 忽略字符串 "" 和括号内的 ;
    通用工具, 给 generic / port 解析用"""
    decls = []
    cur = []
    in_str = False
    paren_depth = 0
    bracket_depth = 0
    for ch in text:
        if in_str:
            cur.append(ch)
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            cur.append(ch)
            continue
        if ch == '(':
            paren_depth += 1
        elif ch == ')':
            paren_depth -= 1
        elif ch == '[':
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1
        elif ch == ';' and paren_depth == 0 and bracket_depth == 0:
            decls.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    if cur:
        decls.append(''.join(cur))
    return decls


def _parse_vhdl_ports(text):
    """解析 VHDL port"""
    ports = []
    declarations = [d.strip() for d in _split_vhdl_decls(text) if d.strip()]

    for decl in declarations:
        m = re.match(r'^\s*(.+?)\s*:\s*(in|out|inout|buffer)\s+(.+)$', decl, re.IGNORECASE)
        if m:
            names_str = m.group(1)
            direction = m.group(2).lower()
            type_str = m.group(3).strip()

            # buffer → output
            if direction == 'buffer':
                direction = 'output'

            # 提取位宽
            width = None
            vec_m = re.search(r'(?:std_logic_vector|unsigned|signed)\s*\(([^)]+)\)',
                              type_str, re.IGNORECASE)
            if vec_m:
                w = vec_m.group(1).strip()
                w = re.sub(r'\s*downto\s*', ':', w)
                w = re.sub(r'\s*to\s*', ':', w)
                w = re.sub(r'\s+', '', w)
                width = f'[{w}]'

            names = [n.strip() for n in names_str.split(',') if n.strip()]
            for n in names:
                ports.append(Port(n, direction, width, type_str))

    return ports


# ============================================================================
# 文件解析入口
# ============================================================================

def parse_file(filepath):
    """根据扩展名自动选择解析器"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    ext = path.suffix.lower()
    content = path.read_text(encoding='utf-8', errors='replace')

    if ext in ('.v', '.sv'):
        return parse_verilog(content)
    elif ext in ('.vhd', '.vhdl'):
        return parse_vhdl(content)
    else:
        raise ValueError(f"不支持的文件类型: {ext}\n支持: .v, .sv, .vhd, .vhdl")


# ============================================================================
# 生成器 — Verilog 信号定义
# ============================================================================

def gen_verilog_signal_defs(module, suffix=""):
    """生成 wire 声明"""
    lines = []
    if not module.ports:
        return ""

    max_width_len = max((len(p.width) if p.width else 0) for p in module.ports)
    max_name_len = max(len(p.name + suffix) for p in module.ports)

    for p in module.ports:
        sig_name = p.name + suffix
        sig_width = p.width if p.width else ""
        pad_width = ' ' * (max_width_len - len(sig_width))
        pad_name = ' ' * (max_name_len - len(sig_name))
        lines.append(f"wire {pad_width}{sig_width} {sig_name}{pad_name};")

    return '\n'.join(lines)


# ============================================================================
# 生成器 — Verilog 例化
# ============================================================================

def gen_verilog_instantiation(module, inst_name, suffix=""):
    """生成 Verilog 例化模板"""
    lines = []

    # 模块名 + 参数
    if module.params:
        lines.append(f"{module.name} #(")
        max_name = max(len(p.name) for p in module.params)
        max_default = max((len(p.default) if p.default else 0) for p in module.params)
        for i, p in enumerate(module.params):
            pad_name = ' ' * (max_name - len(p.name))
            default = p.default if p.default else ""
            pad_default = ' ' * (max_default - len(default))
            comma = ',' if i < len(module.params) - 1 else ' '
            lines.append(f"    .{p.name}{pad_name} ({default}{pad_default}){comma} // parameter")
        lines.append(f") {inst_name} (")
    else:
        lines.append(f"{module.name} {inst_name} (")

    # 端口连接
    if module.ports:
        max_port = max(len(p.name) for p in module.ports)
        max_sig = max(len(p.name + suffix) for p in module.ports)

        for i, p in enumerate(module.ports):
            sig_name = p.name + suffix
            port_pad = ' ' * (max_port - len(p.name))
            sig_pad = ' ' * (max_sig - len(sig_name))

            # 方向注释
            dir_map = {'in': 'input', 'out': 'output',
                       'input': 'input', 'output': 'output', 'inout': 'inout'}
            dir_comment = dir_map.get(p.direction, p.direction)
            width_comment = f" {p.width}" if p.width else ""
            comma = ',' if i < len(module.ports) - 1 else ' '

            lines.append(f"    .{p.name}{port_pad} ({sig_name}{sig_pad}){comma} // {dir_comment}{width_comment}")

    lines.append(");")
    return '\n'.join(lines)


# ============================================================================
# 生成器 — VHDL Component 声明
# ============================================================================

def gen_vhdl_component(module):
    """生成 VHDL component 声明"""
    lines = [f"component {module.name} is"]

    # Generic
    if module.params:
        lines.append("    generic (")
        max_name = max(len(p.name) for p in module.params)
        for i, p in enumerate(module.params):
            pad_name = ' ' * (max_name - len(p.name))
            vhdl_type = p.vhdl_type if p.vhdl_type else "integer"
            default = f" := {p.default}" if p.default else ""
            semi = ';' if i < len(module.params) - 1 else ''
            lines.append(f"        {p.name}{pad_name} : {vhdl_type}{default}{semi}")
        lines.append("    );")

    # Port
    lines.append("    port (")
    if module.ports:
        max_port = max(len(p.name) for p in module.ports)
        for i, p in enumerate(module.ports):
            pad_name = ' ' * (max_port - len(p.name))

            # VHDL 类型
            if p.vhdl_type:
                vhdl_type = p.vhdl_type
            elif p.width:
                w = p.width.replace('[', '').replace(']', '').replace(':', ' downto ')
                vhdl_type = f"std_logic_vector({w})"
            else:
                vhdl_type = "std_logic"

            # VHDL 方向
            dir_map = {'input': 'in', 'output': 'out', 'inout': 'inout',
                       'in': 'in', 'out': 'out'}
            vhdl_dir = dir_map.get(p.direction, p.direction)

            semi = ';' if i < len(module.ports) - 1 else ''
            lines.append(f"        {p.name}{pad_name} : {vhdl_dir} {vhdl_type}{semi}")

    lines.append("    );")
    lines.append(f"end component {module.name};")
    return '\n'.join(lines)


# ============================================================================
# 生成器 — VHDL 信号定义
# ============================================================================

def gen_vhdl_signal_defs(module, suffix=""):
    """生成 VHDL signal 声明"""
    lines = []
    if not module.ports:
        return ""

    # 预先计算类型和最大宽度
    type_list = []
    max_name_len = 0
    max_type_len = 0

    for p in module.ports:
        sig_name = p.name + suffix
        max_name_len = max(max_name_len, len(sig_name))

        if p.vhdl_type:
            t = p.vhdl_type
        elif p.width:
            w = p.width.replace('[', '').replace(']', '').replace(':', ' downto ')
            t = f"std_logic_vector({w})"
        else:
            t = "std_logic"

        type_list.append(t)
        max_type_len = max(max_type_len, len(t))

    for i, p in enumerate(module.ports):
        sig_name = p.name + suffix
        pad_name = ' ' * (max_name_len - len(sig_name))
        vhdl_type = type_list[i]
        pad_type = ' ' * (max_type_len - len(vhdl_type))
        lines.append(f"signal {sig_name}{pad_name} : {vhdl_type}{pad_type};")

    return '\n'.join(lines)


# ============================================================================
# 生成器 — VHDL 例化
# ============================================================================

def gen_vhdl_instantiation(module, inst_name, suffix=""):
    """生成 VHDL 例化模板"""
    lines = [f"{inst_name} : entity work.{module.name}"]

    # Generic map
    if module.params:
        lines.append("    generic map (")
        max_name = max(len(p.name) for p in module.params)
        max_default = max((len(p.default) if p.default else 0) for p in module.params)
        for i, p in enumerate(module.params):
            pad_name = ' ' * (max_name - len(p.name))
            default = p.default if p.default else ""
            pad_default = ' ' * (max_default - len(default))
            comma = ',' if i < len(module.params) - 1 else ' '
            lines.append(f"        {p.name}{pad_name} => {default}{pad_default}{comma} -- generic")
        lines.append("    )")

    # Port map
    lines.append("    port map (")
    if module.ports:
        max_port = max(len(p.name) for p in module.ports)
        max_sig = max(len(p.name + suffix) for p in module.ports)

        for i, p in enumerate(module.ports):
            sig_name = p.name + suffix
            port_pad = ' ' * (max_port - len(p.name))
            sig_pad = ' ' * (max_sig - len(sig_name))

            dir_map = {'input': 'in', 'output': 'out', 'inout': 'inout',
                       'in': 'in', 'out': 'out'}
            dir_comment = dir_map.get(p.direction, p.direction)
            width_comment = f" {p.width}" if p.width else ""
            comma = ',' if i < len(module.ports) - 1 else ' '

            lines.append(f"        {p.name}{port_pad} => {sig_name}{sig_pad}{comma} -- {dir_comment}{width_comment}")

    lines.append("    );")
    return '\n'.join(lines)


# ============================================================================
# 主控: 生成完整模板
# ============================================================================

def generate_templates(module, count=1):
    """
    生成完整例化模板 (Verilog + VHDL)
    返回 (verilog_code, vhdl_code)
    """
    if count < 1:
        count = 1

    vcompo = gen_vhdl_component(module)

    verilog_parts = []
    vhdl_parts = []

    # VHDL: component 声明置顶
    vhdl_parts.append(vcompo)
    vhdl_parts.append("")

    if count == 1:
        # 单实例: 信号定义 + 例化
        inst_name = f"{module.name}_inst"

        verilog_parts.append(gen_verilog_signal_defs(module))
        verilog_parts.append("")
        verilog_parts.append(gen_verilog_instantiation(module, inst_name))

        vhdl_parts.append(gen_vhdl_signal_defs(module))
        vhdl_parts.append("")
        vhdl_parts.append(gen_vhdl_instantiation(module, inst_name))
    else:
        # 多实例: 先生成所有信号定义, 再生成例化
        for i in range(1, count + 1):
            suffix = f"_reg_{i}"
            verilog_parts.append(f"// ======== Signals for instance {i} ========")
            verilog_parts.append(gen_verilog_signal_defs(module, suffix))
            verilog_parts.append("")

            vhdl_parts.append(f"-- ======== Signals for instance {i} ========")
            vhdl_parts.append(gen_vhdl_signal_defs(module, suffix))
            vhdl_parts.append("")

        for i in range(1, count + 1):
            inst_name = f"{module.name}_inst_{i}"
            suffix = f"_reg_{i}"

            verilog_parts.append(f"// ======== Instance {i}: {inst_name} ========")
            verilog_parts.append(gen_verilog_instantiation(module, inst_name, suffix))
            verilog_parts.append("")

            vhdl_parts.append(f"-- ======== Instance {i}: {inst_name} ========")
            vhdl_parts.append(gen_vhdl_instantiation(module, inst_name, suffix))
            vhdl_parts.append("")

    return '\n'.join(verilog_parts), '\n'.join(vhdl_parts)


# ============================================================================
# CLI 模式
# ============================================================================

def run_cli(filepath, count=1, output_dir=None):
    """命令行模式"""
    print("\033[36m========================================\033[0m")
    print("\033[36m  Verilog/VHDL 例化模板生成器\033[0m")
    print("\033[36m========================================\033[0m")
    print()

    try:
        # 解析
        print(f"\033[33m[1/3] 正在解析: {filepath}\033[0m")
        abs_path = os.path.abspath(filepath)
        module = parse_file(abs_path)
        print(f"\033[32m       模块名: {module.name}\033[0m")
        print(f"\033[32m       语言:   {module.lang}\033[0m")
        print(f"\033[32m       端口数: {len(module.ports)}\033[0m")
        print(f"\033[32m       参数数: {len(module.params)}\033[0m")
        print()

        # 生成
        print(f"\033[33m[2/3] 正在生成例化模板 (实例数: {count})...\033[0m")
        verilog_code, vhdl_code = generate_templates(module, count)
        print("\033[32m       生成完成!\033[0m")
        print()

        # 保存
        print("\033[33m[3/3] 正在保存文件...\033[0m")
        dir_path = output_dir if output_dir else os.path.dirname(abs_path)
        base_name = os.path.splitext(os.path.basename(abs_path))[0]

        v_path = os.path.join(dir_path, f"{base_name}_inst.v")
        vhdl_path = os.path.join(dir_path, f"{base_name}_inst.vhd")

        with open(v_path, 'w', encoding='utf-8') as f:
            f.write(verilog_code)
        print(f"\033[32m       已保存: {v_path}\033[0m")

        with open(vhdl_path, 'w', encoding='utf-8') as f:
            f.write(vhdl_code)
        print(f"\033[32m       已保存: {vhdl_path}\033[0m")
        print()

        print("\033[36m========================================\033[0m")
        print("\033[32m  生成完毕!\033[0m")
        print("\033[36m========================================\033[0m")

        # 预览
        print()
        print("\033[36m--- Verilog 例化预览 ---\033[0m")
        print(verilog_code)
        print()
        print("\033[36m--- VHDL 例化预览 ---\033[0m")
        print(vhdl_code)

    except Exception as e:
        print(f"\033[31m错误: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# 配置持久化 — Vivado 路径等用户设置
# ============================================================================

_CONFIG_PATH = Path.home() / '.fpga_toolbox_config.json'

def _load_config():
    """加载持久化配置, 文件不存在则返回默认值"""
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        'vivado_bin_paths': [],
        'last_vivado_ver': '',
        'last_compress_path': '',
    }

def _save_config(cfg):
    """保存配置到文件"""
    try:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # 静默失败, 下次启动恢复默认


# ============================================================================
# FPGA 工程压缩 — 按 GitLab 管理规范清理 Vivado 生成文件
# ============================================================================

# 需要删除的目录（递归）
_COMPRESS_DEL_DIRS = [
    '.runs', '.srcs', '.sdk', '.sim', '.cache', '.hw', '.gen', '.tmp',
    'ip_user_files', 'ip_project',
]

# 需要删除的文件（glob 模式，匹配文件名）
_COMPRESS_DEL_FILES = [
    '*.jou', '*.log', '*.str', '*.xpe',
    '*.bit', '*.mcs', '*.prm', '*.bin', '*.rpt', '*.dcp', '*.ltx',
    '*.hdf', '*.sysdef', '*.xpr.lock', '*.xpr.user', '*hwdef',
    '*.xcix',  # Vivado 新版 IP 中间文件
]

# 白名单：即使匹配删除规则也不删（安全检查）
_COMPRESS_WHITELIST_EXT = {
    '.v', '.vhd', '.sv', '.xdc', '.tcl', '.xci', '.xml',
    '.md', '.pdf', '.doc', '.docx', '.xlsx', '.txt',
    '.gitignore', '.gitattributes', '.xpr', '.elf',
}


def auto_export_vivado(root_dir, vivado_bin=None):
    """
    从 Vivado 工程(.xpr)自动导出源码文件:
      - Block Design Tcl 脚本
      - 硬件平台定义 (.hdf / .xsa)
      - IP 状态报告

    参数:
        root_dir: 工程根目录
        vivado_bin: Vivado bin 目录路径 (如 C:/Xilinx/Vivado/2019.1/bin),
                    None=使用系统 PATH 中的 vivado

    返回: (生成文件路径列表, 日志字符串)
    """
    root = os.path.abspath(root_dir)

    # 确定 vivado 可执行文件
    if vivado_bin:
        vivado_exe = os.path.join(vivado_bin, 'vivado')
        if not os.path.isfile(vivado_exe) and not os.path.isfile(vivado_exe + '.bat'):
            # 尝试 Windows / Linux
            if os.path.isfile(vivado_exe + '.bat'):
                vivado_exe += '.bat'
            else:
                return [], f"指定路径下未找到 vivado: {vivado_bin}"
    else:
        vivado_exe = 'vivado'

    # 查找 .xpr 文件(排除 lock / user 后缀)
    xpr_files = []
    try:
        for f in os.listdir(root):
            if f.endswith('.xpr') and not f.endswith('.xpr.lock') and not f.endswith('.xpr.user'):
                xpr_files.append(os.path.join(root, f))
    except OSError:
        return [], "无法读取工程目录"

    if not xpr_files:
        return [], "未找到 Vivado 工程文件 (.xpr)，跳过自动导出"

    xpr_path = xpr_files[0]
    proj_name = os.path.splitext(os.path.basename(xpr_path))[0]

    # 检查 Vivado 是否可用
    try:
        r = subprocess.run([vivado_exe, '-version'],
                           capture_output=True, text=True, timeout=10)
        vivado_ver = (r.stdout.strip().split('\n')[0]
                      if r.stdout and r.stdout.strip() else 'unknown')
    except FileNotFoundError:
        return [], "Vivado 未安装或未加入 PATH，跳过自动导出"
    except Exception as e:
        return [], f"检测 Vivado 失败: {e}，跳过自动导出"

    # 生成临时导出 Tcl
    tcl_path = os.path.join(root, '_auto_export.tcl')
    tcl_content = f'''# Auto-generated by gen_inst.py — Vivado 工程自动导出
set proj_name {{{proj_name}}}
set xpr_path  {{{xpr_path}}}
set out_dir   {{{root}}}

puts ">>> Opening project: $proj_name"
open_project $xpr_path

# ---- Block Design Tcl ----
set bd_files [get_files -filter {{FILE_TYPE == "Block Designs"}}]
if {{[llength $bd_files] > 0}} {{
    foreach bd $bd_files {{
        set bd_name [file rootname [file tail $bd]]
        set bd_tcl [file join $out_dir "${{bd_name}}.tcl"]
        puts ">>> Exporting BD Tcl: ${{bd_name}} → ${{bd_tcl}}"
        if {{[catch {{write_bd_tcl -force $bd_tcl}} err]}} {{
            puts "WARNING: write_bd_tcl failed: $err"
        }}
    }}
}} else {{
    puts ">>> No Block Design found, skip"
}}

# ---- Hardware Platform Definition ----
catch {{
    write_hw_platform -fixed -force -file [file join $out_dir "${{proj_name}}.xsa"]
    puts ">>> Exported HW platform: ${{proj_name}}.xsa (XSA)"
}}
catch {{
    write_hwdef -force -file [file join $out_dir "${{proj_name}}.hdf"]
    puts ">>> Exported HW definition: ${{proj_name}}.hdf (HDF)"
}}

# ---- IP Status Report ----
catch {{
    report_ip_status -file [file join $out_dir "${{proj_name}}_ip_status.txt"]
    puts ">>> IP status report: ${{proj_name}}_ip_status.txt"
}}

close_project
puts ">>> Vivado export done."
'''

    try:
        with open(tcl_path, 'w', encoding='utf-8') as fh:
            fh.write(tcl_content)
    except OSError as e:
        return [], f"无法写入临时 Tcl 脚本: {e}"

    # 运行 Vivado 批处理
    try:
        subprocess.run(
            [vivado_exe, '-mode', 'batch', '-source', tcl_path, '-notrace'],
            capture_output=True, text=True, timeout=300, cwd=root,
            env={**os.environ})
    except subprocess.TimeoutExpired:
        return [], "Vivado 执行超时 (5 分钟限制)，请检查工程是否正常"
    except Exception as e:
        return [], f"运行 Vivado 失败: {e}"

    # 收集生成文件
    generated = []
    for f in os.listdir(root):
        fp = os.path.join(root, f)
        if not os.path.isfile(fp):
            continue
        if f == '_auto_export.tcl':
            continue
        # BD Tcl
        if f.endswith('.tcl'):
            generated.append(fp)
        # 硬件定义
        if f.endswith(('.hdf', '.xsa')) and proj_name.lower() in f.lower():
            generated.append(fp)
        # IP 状态报告
        if f.endswith('_ip_status.txt'):
            generated.append(fp)

    # 清理中间脚本
    try:
        os.unlink(tcl_path)
    except OSError:
        pass

    # 更新白名单: 自动加入本次导出的扩展名, 防止被后续 clean 误删
    for fp in generated:
        ext = os.path.splitext(fp)[1].lower()
        if ext and ext not in _COMPRESS_WHITELIST_EXT:
            _COMPRESS_WHITELIST_EXT.add(ext)

    log_lines = [f"Vivado ({vivado_ver}) 导出 {len(generated)} 个文件"]
    for g in generated:
        log_lines.append(f"  + {os.path.basename(g)}")
    if not generated:
        log_lines.append("  (未生成新文件 — 工程可能已是最新)")

    return generated, '\n'.join(log_lines)


# ════════════════════════════════════════════════════════════════════════
#  BD Tcl 检查与补全 (基于 FPGA_GIT_GUIDE.md 规范)
# ════════════════════════════════════════════════════════════════════════
def _parse_vivado_ver(ver_str):
    """从 'Vivado v2023.2 ...' 解析出版本号元组 (2023, 2)"""
    if not ver_str:
        return (0, 0)
    m = re.search(r'(\d{4})\.(\d+)', ver_str)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (0, 0)


def _scan_bd_files(root_dir):
    """扫描工程目录及 project/ 子目录, 返回所有 .bd 文件路径列表"""
    root = os.path.abspath(root_dir)
    bd_files = []
    # 优先看 project/ 子目录
    candidates = [root]
    proj_dir = os.path.join(root, 'project')
    if os.path.isdir(proj_dir):
        candidates.append(proj_dir)
    # 也扫描 bd/ 子目录 (FPGA_GIT_GUIDE.md 第6章规定)
    bd_dir = os.path.join(root, 'bd')
    if os.path.isdir(bd_dir):
        candidates.append(bd_dir)
    for cdir in candidates:
        try:
            for entry in os.scandir(cdir):
                if entry.is_file() and entry.name.endswith('.bd'):
                    bd_files.append(entry.path)
        except OSError:
            pass
    return bd_files


def _supplement_recreate_block_design_tcl(tcl_path, bd_name, vivado_ver_str,
                                            src_bd_path=None):
    """按 FPGA_GIT_GUIDE.md 第 5.1/7.1 节规则, 生成 recreate_block_design.tcl 骨架
    当 Vivado 不可用 / 版本不匹配时使用.
    不同 Vivado 版本的 API 差异 (简化处理, 用 set_param 兼容大部分):
      - 2014.1+: write_bd_tcl
      - 2018.1+: make_wrapper -files
      - 2020.1+: create_bd_design
    """
    major, minor = _parse_vivado_ver(vivado_ver_str)
    ver_tag = f'{major}.{minor}' if major else 'unknown'
    # 构造标准 tcl 骨架 (与 Vivado write_bd_tcl 输出一致, 但 IP 列表为空)
    tcl = f'''# ════════════════════════════════════════════════════════════════
# recreate_block_design.tcl — Auto-generated by gen_inst.py
# Block Design 重建脚本 (依据 FPGA_GIT_GUIDE.md 第 5 章)
# BD 名: {bd_name}
# Vivado 版本: {ver_tag}
# 注意: 本脚本为骨架模板, 需要根据实际 .bd 内容补充 IP 列表
# ════════════════════════════════════════════════════════════════

# 切换到工程根目录
set origin_dir [file dirname [file dirname [file normalize [info script]]]]
puts ">>> recreate_block_design.tcl 起点: $origin_dir"

'''
    if src_bd_path and os.path.isfile(src_bd_path):
        # .bd 是 IP-XACT XML, 解析出 IP 列表
        try:
            with open(src_bd_path, 'r', encoding='utf-8') as fh:
                bd_xml = fh.read()
            # 提取 <xd:componentRef id="xxx"> 和 <bd:property name="component_name" value="..."/>
            ip_pattern = re.compile(
                r'<xd:componentRef\s+id="([^"]+)"[^/]*/>', re.S)
            names_pattern = re.compile(
                r'<bd:property\s+[^/]*name="component_name"[^/]*value="([^"]+)"',
                re.S)
            ip_ids = ip_pattern.findall(bd_xml)
            ip_names = names_pattern.findall(bd_xml)
            tcl += f'# 从 {os.path.basename(src_bd_path)} 解析到 {len(ip_ids)} 个 IP 实例\n\n'
        except Exception:
            ip_ids = []
            ip_names = []
    else:
        ip_ids = []
        ip_names = []

    tcl += f'''# 创建/打开 Block Design
set bd_name "{bd_name}"
puts ">>> 创建/打开 Block Design: $bd_name"

# 注: 若 .bd 已在工程中, 优先 open_bd_design; 否则 create_bd_design
# Vivado 2019.1+ 推荐的写法:
if {{[catch {{create_bd_design $bd_name}} err]}} {{
    puts "create_bd_design failed (可能已存在): $err"
    open_bd_design [get_files *$bd_name.bd]
}}

# ═══ 此处插入 IP 创建语句 ═══
# 骨架中 IP 列表为空, 需要在 Vivado 中打开 BD 后, 用:
#   write_bd_tcl -force [info script]
# 重新生成完整脚本
'''
    if ip_ids:
        tcl += '\n# 从 .bd XML 中检测到的 IP 组件 (需要 verify):\n'
        for i, ipid in enumerate(ip_ids[:20]):
            name = ip_names[i] if i < len(ip_names) else f'ip_{i}'
            tcl += f'#   - {name}  ({ipid})\n'
        tcl += '\n# 参考 Vivado write_bd_tcl 输出, 在此处插入:\n'
        tcl += '# create_bd_cell -type ip -vlnv <vlnv> [get_bd_cells /<ip_name>]\n'
        tcl += '# create_bd_intf_pin / ...\n'
        tcl += '# connect_bd_intf_net / ...\n'

    tcl += '''
# 保存设计
save_bd_design
puts ">>> Block Design 重建完成: $bd_name"

# 生成 wrapper (顶层 Verilog/VHDL)
if {[llength [get_files *$bd_name.bd]] > 0} {
    make_wrapper -files [get_files *$bd_name.bd] -top
    puts ">>> 已生成 wrapper: ${bd_name}_wrapper.v"
}
'''
    try:
        os.makedirs(os.path.dirname(tcl_path), exist_ok=True)
        with open(tcl_path, 'w', encoding='utf-8') as fh:
            fh.write(tcl)
        return True, tcl_path
    except OSError as e:
        return False, str(e)


def _supplement_recreate_project_tcl(tcl_path, proj_name, part_name,
                                       vivado_ver_str, bd_name):
    """按 FPGA_GIT_GUIDE.md 第 7.1 节规则, 生成 recreate_project.tcl 骨架"""
    major, minor = _parse_vivado_ver(vivado_ver_str)
    ver_tag = f'{major}.{minor}' if major else 'unknown'
    tcl = f'''# ════════════════════════════════════════════════════════════════
# recreate_project.tcl — Auto-generated by gen_inst.py
# 工程重建脚本 (依据 FPGA_GIT_GUIDE.md 第 6/7 章)
# 工程名: {proj_name}
# 器件:   {part_name or 'UNKNOWN (需在 Vivado 中确认)'}
# Vivado 版本: {ver_tag}
# ════════════════════════════════════════════════════════════════

# 0. 设置变量
set origin_dir [file dirname [file normalize [info script]]]
puts ">>> recreate_project.tcl 起点: $origin_dir"

# 1. 创建 Vivado 工程
#    注意: -part 参数需根据实际 FPGA 型号修改
set proj_name "{proj_name}"
set proj_part "{part_name or 'xc7a100tcsg324-1'}"
set proj_dir "$origin_dir/../project"
file mkdir $proj_dir
create_project $proj_name $proj_dir -part $proj_part

# 2. 添加自定义 IP 库 (若工程有 ip_repo/ 目录)
if {{[file exists "$origin_dir/../ip_repo"]}} {{
    set_property ip_repo_paths "$origin_dir/../ip_repo" [current_project]
    update_ip_catalog
    puts ">>> 已添加 IP 库: $origin_dir/../ip_repo"
}}

# 3. 刷新文件顺序
update_compile_order -fileset sources_1

# 4. 重建 Block Design (调用独立的 BD 脚本)
set bd_tcl "$origin_dir/recreate_block_design.tcl"
if {{[file exists $bd_tcl]}} {{
    source $bd_tcl
    puts ">>> 已加载 BD 重建脚本: $bd_tcl"
}} else {{
    puts "WARNING: 未找到 BD 重建脚本 $bd_tcl, 跳过 BD 重建"
}}

# 5. 添加约束文件 (xdc/)
set xdc_dir "$origin_dir/../xdc"
if {{[file exists $xdc_dir]}} {{
    set xdc_files [glob -nocomplain "$xdc_dir/*.xdc"]
    if {{[llength $xdc_files] > 0}} {{
        add_files -norecurse $xdc_files
        puts ">>> 已添加 XDC 约束: [llength $xdc_files] 个"
    }}
}}

# 6. 添加应用文件 (app/)
set app_dir "$origin_dir/../app"
if {{[file exists $app_dir]}} {{
    set app_files [glob -nocomplain [concat \\
        [glob -nocomplain "$app_dir/*.elf"] \\
        [glob -nocomplain "$app_dir/*.hdf"] \\
        [glob -nocomplain "$app_dir/*.xsa"]]]
    if {{[llength $app_files] > 0}} {{
        add_files -norecurse $app_files
        puts ">>> 已添加应用文件: [llength $app_files] 个"
    }}
}}

puts ">>> 工程重建完成: $proj_name"
'''
    try:
        os.makedirs(os.path.dirname(tcl_path), exist_ok=True)
        with open(tcl_path, 'w', encoding='utf-8') as fh:
            fh.write(tcl)
        return True, tcl_path
    except OSError as e:
        return False, str(e)


# ════════════════════════════════════════════════════════════════════════
#  工程目录补全 (依据 FPGA_GIT_GUIDE.md 第 3.1 / 4.2 / 7.1 节)
# ════════════════════════════════════════════════════════════════════════
def _supplement_package_project_tcl(tcl_path, proj_name, part_name, vivado_ver_str):
    """按 FPGA_GIT_GUIDE.md 第 7.1 节生成 package_project.tcl
    该脚本在 Vivado 中 source 后, 自动生成 recreate_block_design.tcl 和 recreate_project.tcl"""
    major, minor = _parse_vivado_ver(vivado_ver_str)
    ver_tag = f'{major}.{minor}' if major else 'unknown'
    tcl = f'''# ════════════════════════════════════════════════════════════════
# package_project.tcl — Auto-generated by gen_inst.py
# 工程归档脚本 (依据 FPGA_GIT_GUIDE.md 第 7.1 节)
# 工程名: {proj_name}
# 器件:   {part_name or 'UNKNOWN'}
# Vivado 版本: {ver_tag}
# ════════════════════════════════════════════════════════════════

set tcl_obj [current_project]
set proj_name [file tail [get_property name $tcl_obj]]
set proj_dir [get_property directory $tcl_obj]
set part_name [get_property part $tcl_obj]

# 设置路径 (假设脚本位于 tcl/ 目录)
set origin_dir ".."
puts ">>> 开始归档: $proj_name ($part_name)"

# 1. 生成 Block Design 重建脚本
if {{[llength [get_bd_designs]] > 0}} {{
    set bd_tcl_path [file join $origin_dir "tcl" "recreate_block_design.tcl"]
    write_bd_tcl -force $bd_tcl_path
    puts ">>> 已生成: $bd_tcl_path"
}} else {{
    puts ">>> 工程无 Block Design, 跳过 BD 脚本生成"
}}

# 2. 生成 Vivado 工程重建脚本
set proj_tcl_path [file join $origin_dir "tcl" "recreate_project.tcl"]
set fileId [open $proj_tcl_path "w"]
puts $fileId "create_project $proj_name $origin_dir/project -part $part_name"
puts $fileId "set_property ip_repo_paths $origin_dir/ip_repo \\\\\\[current_project\\\\\\]"
puts $fileId "update_ip_catalog"
puts $fileId "update_compile_order -fileset sources_1"
puts $fileId "source $origin_dir/tcl/recreate_block_design.tcl"
puts $fileId "set bdname \\\\\\[get_bd_designs\\\\\\]"
puts $fileId "make_wrapper -files \\\\\\[get_files $origin_dir/project/bd/\\\\\\$bdname/\\\\\\$bdname.bd\\\\\\] -top"
puts $fileId "add_files -norecurse $origin_dir/tcl/bd/\\\\\\$bdname/hdl/\\\\\\$bdname\\\\_wrapper.v"
close $fileId
puts ">>> 已生成: $proj_tcl_path"

puts ">>> 归档完成. 提交以下文件到 Git:"
puts "    - tcl/recreate_block_design.tcl"
puts "    - tcl/recreate_project.tcl"
puts "    - ip_repo/ (自定义 IP)"
puts "    - xdc/ (约束文件)"
puts "    - app/ (应用文件: .elf / .hdf / .xsa)"
'''
    try:
        os.makedirs(os.path.dirname(tcl_path), exist_ok=True)
        with open(tcl_path, 'w', encoding='utf-8') as fh:
            fh.write(tcl)
        return True, tcl_path
    except OSError as e:
        return False, str(e)


def _supplement_readme_md(readme_path, proj_name, vivado_ver_str,
                            bd_names, has_ip_repo):
    """生成 README.md 模板 (依据 FPGA_GIT_GUIDE.md 3.1 节末 "README.md 须有功能/版本/更新记录")"""
    major, minor = _parse_vivado_ver(vivado_ver_str)
    ver_tag = f'{major}.{minor}' if major else 'unknown'
    today = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    bd_section = ''
    if bd_names:
        bd_section = '\n## Block Design\n\n'
        for n in bd_names:
            bd_section += f'- `{n}` (重建脚本: `tcl/recreate_block_design.tcl`)\n'
    ip_section = ''
    if has_ip_repo:
        ip_section = '\n## 自定义 IP 核\n\n详见 `ip_repo/` 目录下各 IP 核的 README.\n'
    md = f'''# {proj_name}

> FPGA 工程 (Vivado {ver_tag})

## 目录结构

```
{proj_name}/
├── project/        # Vivado 工程目录 (被 .gitignore 过滤)
├── tcl/            # 重建脚本 (必须版本控制)
│   ├── package_project.tcl
│   ├── recreate_block_design.tcl
│   └── recreate_project.tcl
├── ip_repo/        # 自定义 IP 库
├── xdc/            # 约束文件
├── app/            # 应用文件 (.elf / .hdf / .xsa)
├── release/        # 固件 (用 Git LFS 跟踪)
├── .gitignore
└── README.md (本文件)
```
{bd_section}{ip_section}
## 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1.0 | {today} | 初始版本 |

## 重建方法

1. 在 Vivado 中 source 重建脚本:
   ```tcl
   source tcl/recreate_project.tcl
   ```
2. 或命令行:
   ```bash
   vivado -source tcl/recreate_project.tcl
   ```

## 归档方法

在 Vivado 中:
```tcl
source tcl/package_project.tcl
```

## 维护说明

- 所有 Vivado 自动生成文件 (`.runs/`, `.cache/`, `.gen/` 等) 已通过 `.gitignore` 过滤
- IP 核和 BD 必须通过 tcl 脚本重建, 不直接版本控制生成文件
- 详细规则见 `FPGA_GIT_GUIDE.md`

## 更新记录

- {today}: 项目初始化
'''
    try:
        with open(readme_path, 'w', encoding='utf-8') as fh:
            fh.write(md)
        return True, readme_path
    except OSError as e:
        return False, str(e)


def _supplement_gitkeep(dir_path, note=''):
    """在空目录中放 .gitkeep 占位, 让 git 跟踪空目录"""
    try:
        os.makedirs(dir_path, exist_ok=True)
        gitkeep = os.path.join(dir_path, '.gitkeep')
        if not os.path.isfile(gitkeep):
            with open(gitkeep, 'w', encoding='utf-8') as fh:
                if note:
                    fh.write(f'# {note}\n')
            return True, gitkeep
        return False, '已存在'
    except OSError as e:
        return False, str(e)


def _scan_xdc_files(root_dir):
    """扫描工程目录及 project/ 子目录的 .xdc 文件"""
    root = os.path.abspath(root_dir)
    xdc_files = []
    candidates = [root, os.path.join(root, 'project'),
                  os.path.join(root, 'src'), os.path.join(root, 'hdl'),
                  os.path.join(root, 'constraints')]
    for cdir in candidates:
        if not os.path.isdir(cdir):
            continue
        try:
            for entry in os.scandir(cdir):
                if entry.is_file() and entry.name.lower().endswith('.xdc'):
                    xdc_files.append(entry.path)
        except OSError:
            pass
    return xdc_files


def _scan_app_files(root_dir):
    """扫描工程目录的 app 文件 (.elf / .hdf / .xsa)"""
    root = os.path.abspath(root_dir)
    app_files = []
    candidates = [root, os.path.join(root, 'project'),
                  os.path.join(root, 'release'), os.path.join(root, 'app')]
    for cdir in candidates:
        if not os.path.isdir(cdir):
            continue
        try:
            for entry in os.scandir(cdir):
                if entry.is_file() and entry.name.lower().endswith(
                        ('.elf', '.hdf', '.xsa')):
                    app_files.append(entry.path)
        except OSError:
            pass
    return app_files


def _try_vivado_export_bd_tcl(bd_path, tcl_out, vivado_bin=None, xpr_path=None):
    """调用 Vivado 生成 BD tcl, 失败时返回 (False, error_msg)"""
    if not vivado_bin:
        vivado_exe = 'vivado'
    else:
        vivado_exe = os.path.join(vivado_bin, 'vivado')
        if not os.path.isfile(vivado_exe) and not os.path.isfile(vivado_exe + '.bat'):
            return False, f'未找到 vivado: {vivado_bin}'

    bd_name = os.path.splitext(os.path.basename(bd_path))[0]
    if xpr_path and os.path.isfile(xpr_path):
        # 通过 .xpr 打开工程, 再导出 BD
        tcl = (f'open_project {{{xpr_path}}}\n'
               f'set bd_files [get_files -filter {{FILE_TYPE == "Block Designs"}}]\n'
               f'foreach bd $bd_files {{\n'
               f'  set name [file rootname [file tail $bd]]\n'
               f'  set out  [file join [file dirname [info script]] "${{name}}.tcl"]\n'
               f'  write_bd_tcl -force $out\n'
               f'  puts "Exported: $out"\n'
               f'}}\n'
               f'close_project\n')
        try:
            r = subprocess.run([vivado_exe, '-mode', 'batch', '-source', '-'],
                               input=tcl, capture_output=True, text=True,
                               timeout=180)
            return r.returncode == 0, r.stderr or r.stdout
        except Exception as e:
            return False, str(e)
    return False, '未提供 .xpr 路径, 无法用 Vivado 导出'


# ════════════════════════════════════════════════════════════════════════
#  审核工程 (不修改文件, 只生成清单)
# ════════════════════════════════════════════════════════════════════════
# 清单项数据结构:
#   {
#     'key':        str  唯一标识 (用户勾选时使用),
#     'group':      str  类别: '目录' / 'tcl 脚本' / 'IP 脚本' / '文档' / '配置',
#     'name':       str  显示名称 (相对路径),
#     'desc':       str  规则说明 (依据哪一节),
#     'status':     str  '存在' / '缺失',
#     'exists':     bool 目录/文件是否已存在,
#     'default':    bool 默认勾选 (True=勾上, False=不勾),
#     'target':     str  绝对路径 (要创建/已存在的),
#     'note':       str  额外说明 (如: 需 Vivado 导出 / BD 工程必须),
#     'reason_skip': str  为什么默认不勾 (默认空)
#   }

def audit_project(root_dir, vivado_bin=None, vivado_ver_str='', project_part=None):
    """
    审核 FPGA 工程, **只读不写**, 返回按 FPGA_GIT_GUIDE.md 规则需要补全的清单.

    清单项 'default' 字段表示默认是否勾选:
      - 缺失的目录 / 文档 / .gitignore  → 默认 True (强烈建议补全)
      - 缺失的 BD tcl (有 .bd)            → 默认 True (BD 工程必须)
      - 缺失的 recreate_project.tcl       → 默认 True
      - 缺失的 package_project.tcl        → 默认 True
      - 缺失的 IP tcl (有自定义 IP)        → 默认 True
      - 重复项 / Vivado 不在                → 默认 False (谨慎)

    返回: (items: list[dict], summary: dict)
    """
    root = os.path.abspath(root_dir)
    summary = {
        'root': root, 'proj_name': os.path.basename(root),
        'has_xpr': False, 'bd_count': 0, 'xdc_count': 0,
        'app_count': 0, 'ip_count': 0,
        'vivado_ver': vivado_ver_str or '', 'vivado_bin': vivado_bin or '',
    }
    if not os.path.isdir(root):
        return [], summary

    # ── 探测工程基本信息 ──
    xpr_files = []
    try:
        for f in os.listdir(root):
            if f.endswith('.xpr') and not f.endswith(('.lock', '.user')):
                xpr_files.append(os.path.join(root, f))
    except OSError:
        pass
    proj_dir = os.path.join(root, 'project')
    if not xpr_files and os.path.isdir(proj_dir):
        try:
            for f in os.listdir(proj_dir):
                if f.endswith('.xpr') and not f.endswith(('.lock', '.user')):
                    xpr_files.append(os.path.join(proj_dir, f))
        except OSError:
            pass
    xpr_path = xpr_files[0] if xpr_files else None
    proj_name = (os.path.splitext(os.path.basename(xpr_path))[0]
                 if xpr_path else os.path.basename(root))
    summary['has_xpr'] = bool(xpr_path)
    summary['proj_name'] = proj_name

    bd_files = _scan_bd_files(root)
    xdc_files = _scan_xdc_files(root)
    app_files = _scan_app_files(root)
    has_ip_repo = os.path.isdir(os.path.join(root, 'ip_repo'))
    custom_ip_dirs = []
    for parent in [os.path.join(root, 'ip_repo'), root]:
        if not os.path.isdir(parent):
            continue
        try:
            for d in os.listdir(parent):
                dp = os.path.join(parent, d)
                if (os.path.isdir(dp)
                        and os.path.isfile(os.path.join(dp, 'component.xml'))):
                    custom_ip_dirs.append(dp)
        except OSError:
            pass
    summary['bd_count'] = len(bd_files)
    summary['xdc_count'] = len(xdc_files)
    summary['app_count'] = len(app_files)
    summary['ip_count'] = len(custom_ip_dirs)

    items = []

    def _add(group, name, desc, target, exists, default, note='', reason_skip=''):
        items.append({
            'key': f'{group}|{name}',
            'group': group,
            'name': name,
            'desc': desc,
            'status': '存在' if exists else '缺失',
            'exists': exists,
            'default': bool(default) and not exists,
            'target': target,
            'note': note,
            'reason_skip': reason_skip,
        })

    # ── 1. 必选目录 (依据 3.1 节) ──
    required_dirs = [
        ('tcl',     '重建脚本目录 (依据 3.1/5.1/6/7 节)'),
        ('xdc',     '约束文件目录 (依据 3.1 节)'),
        ('app',     '应用文件目录 (.elf/.hdf/.xsa, 依据 3.1 节)'),
        ('ip_repo', '自定义 IP 库 (依据 3.1/4.2 节)'),
        ('release', '固件目录 (LFS 跟踪, 依据 3.1/7.2 节)'),
    ]
    for dname, desc in required_dirs:
        dp = os.path.join(root, dname)
        _add('目录', f'{dname}/', desc, dp, os.path.isdir(dp), True)

    # ── 2. tcl 脚本 ──
    tcl_dir = os.path.join(root, 'tcl')
    first_bd = (os.path.splitext(os.path.basename(bd_files[0]))[0]
                if bd_files else 'design_1')

    # 2.1 recreate_block_design.tcl (BD 工程才需要)
    bd_tcl = os.path.join(tcl_dir, 'recreate_block_design.tcl')
    if bd_files:
        if os.path.isfile(bd_tcl):
            _add('tcl 脚本', 'tcl/recreate_block_design.tcl',
                 'BD 重建脚本 (依据 5.1/7.1 节)', bd_tcl, True, True)
        else:
            # Vivado 可用 → 优先导出真实 tcl (默认勾选)
            # Vivado 不可用 → 用骨架, 也默认勾选, 提示需在 Vivado 中重新生成
            note = ('需 Vivado write_bd_tcl 导出, 失败时用骨架'
                    if not vivado_bin else
                    f'将用 Vivado ({os.path.basename(vivado_bin)}) 导出')
            _add('tcl 脚本', 'tcl/recreate_block_design.tcl',
                 f'BD 重建脚本 (BD 工程必须, 依据 5.1/7.1 节)',
                 bd_tcl, False, True, note=note)
    else:
        # 非 BD 工程 → 也报告, 但默认不勾 (用户可选)
        _add('tcl 脚本', 'tcl/recreate_block_design.tcl',
             'BD 重建脚本 (非 BD 工程, 依据 5.1/7.1 节)',
             bd_tcl, os.path.isfile(bd_tcl), False,
             note='非 BD 工程, 可不勾',
             reason_skip='非 BD 工程')

    # 2.2 recreate_project.tcl
    proj_tcl = os.path.join(tcl_dir, 'recreate_project.tcl')
    _add('tcl 脚本', 'tcl/recreate_project.tcl',
         '工程重建脚本 (依据 6/7.1 节)',
         proj_tcl, os.path.isfile(proj_tcl), True)

    # 2.3 package_project.tcl
    pkg_tcl = os.path.join(tcl_dir, 'package_project.tcl')
    _add('tcl 脚本', 'tcl/package_project.tcl',
         '工程归档脚本 (依据 7.1 节)',
         pkg_tcl, os.path.isfile(pkg_tcl), True)

    # 2.4 每个自定义 IP 一条
    for ip_dir in custom_ip_dirs:
        ip_name = os.path.basename(ip_dir)
        ip_tcl = os.path.join(ip_dir, 'tcl', 'recreate_ip.tcl')
        _add('IP 脚本', f'ip_repo/{ip_name}/tcl/recreate_ip.tcl',
             f'自定义 IP "{ip_name}" 重建脚本 (依据 4.4 节)',
             ip_tcl, os.path.isfile(ip_tcl), True)

    # ── 3. 文档 ──
    readme_path = os.path.join(root, 'README.md')
    _add('文档', 'README.md', '工程说明 (依据 3.1 节末)',
         readme_path, os.path.isfile(readme_path), True)

    # ── 4. 配置 ──
    gitignore_path = os.path.join(root, '.gitignore')
    _add('配置', '.gitignore', '过滤 Vivado 自动生成文件 (依据 3.2 节)',
         gitignore_path, os.path.isfile(gitignore_path), True)

    return items, summary


def check_and_supplement_bd_tcl(root_dir, vivado_bin=None, vivado_ver_str='',
                                  project_part=None, skip_keys=None):
    """
    检查工程目录并按 FPGA_GIT_GUIDE.md 规则补全缺失的必须版本控制文件:

    检查项 (依据 3.1 / 3.2 / 4.2 / 5.1 / 6 / 7.1 节):
      - 必选目录: tcl/, xdc/, app/, ip_repo/, release/
      - 必选 tcl: tcl/recreate_block_design.tcl, tcl/recreate_project.tcl,
                  tcl/package_project.tcl
      - 必选文档: README.md
      - 必选配置: .gitignore (3.2 节)
      - BD 工程额外需要: tcl/recreate_block_design.tcl
      - 自定义 IP 额外需要: tcl/recreate_ip.tcl (per IP)

    补全策略:
      1) 优先用 Vivado write_bd_tcl 导出真实 tcl (如果 Vivado 可用)
      2) 否则按版本规则生成最小可用骨架 tcl
      3) 缺失目录自动创建 + .gitkeep 占位

    skip_keys: 可选 set/list, 包含要**跳过**的 audit 项目 key (如 '目录|tcl/'),
               跳过的项只 log "用户跳过", 不创建/不修改.

    返回: (补全文件列表, 日志字符串)
    """
    skip_keys = set(skip_keys or [])
    root = os.path.abspath(root_dir)
    if not os.path.isdir(root):
        return [], f'目录不存在: {root}'

    def _skipped(key):
        """判断某 audit key 是否在跳过列表中"""
        return key in skip_keys

    log_lines = ['[工程目录完整性检查] (依据 FPGA_GIT_GUIDE.md)']
    generated = []

    # ────────── 0. 探测工程基本信息 ──────────
    xpr_files = []
    try:
        for f in os.listdir(root):
            if f.endswith('.xpr') and not f.endswith(('.lock', '.user')):
                xpr_files.append(os.path.join(root, f))
    except OSError:
        pass
    proj_dir = os.path.join(root, 'project')
    if not xpr_files and os.path.isdir(proj_dir):
        try:
            for f in os.listdir(proj_dir):
                if f.endswith('.xpr') and not f.endswith(('.lock', '.user')):
                    xpr_files.append(os.path.join(proj_dir, f))
        except OSError:
            pass
    xpr_path = xpr_files[0] if xpr_files else None
    proj_name = (os.path.splitext(os.path.basename(xpr_path))[0]
                 if xpr_path else os.path.basename(root))

    # 扫描工程内容
    bd_files = _scan_bd_files(root)
    xdc_files = _scan_xdc_files(root)
    app_files = _scan_app_files(root)
    has_ip_repo = os.path.isdir(os.path.join(root, 'ip_repo'))
    # 检测自定义 IP (有 packaged_ip/component.xml)
    custom_ip_dirs = []
    for parent in [os.path.join(root, 'ip_repo'), root]:
        if not os.path.isdir(parent):
            continue
        try:
            for d in os.listdir(parent):
                dp = os.path.join(parent, d)
                if (os.path.isdir(dp)
                        and os.path.isfile(os.path.join(dp, 'component.xml'))):
                    custom_ip_dirs.append(dp)
        except OSError:
            pass

    log_lines.append(f'  工程: {proj_name}' + (' (BD 工程)' if bd_files else ''))
    log_lines.append(f'  .xpr: {"有" if xpr_path else "无"}  '
                     f'.bd: {len(bd_files)}  .xdc: {len(xdc_files)}  '
                     f'app: {len(app_files)}  IP: {len(custom_ip_dirs)}')

    # ────────── 1. 必选目录补全 (3.1 节) ──────────
    log_lines.append('  ── 必选目录检查 ──')
    required_dirs = [
        ('tcl',     '重建脚本目录 (依据 3.1/5.1/6/7 节)'),
        ('xdc',     '约束文件目录 (依据 3.1 节)'),
        ('app',     '应用文件目录 (.elf/.hdf/.xsa, 依据 3.1 节)'),
        ('ip_repo', '自定义 IP 库 (依据 3.1/4.2 节)'),
        ('release', '固件目录 (LFS 跟踪, 依据 3.1/7.2 节)'),
    ]
    for dname, desc in required_dirs:
        dpath = os.path.join(root, dname)
        if os.path.isdir(dpath):
            log_lines.append(f'  ✓ {dname}/  {desc}')
        elif _skipped(f'目录|{dname}/'):
            log_lines.append(f'  · 用户跳过: {dname}/  ({desc})')
        else:
            try:
                os.makedirs(dpath, exist_ok=True)
                # 在空目录放 .gitkeep 让 git 跟踪
                gitkeep = os.path.join(dpath, '.gitkeep')
                with open(gitkeep, 'w', encoding='utf-8') as fh:
                    fh.write(f'# {desc}\n')
                log_lines.append(f'  [新建] {dname}/  ({desc})')
                generated.append(gitkeep)
            except OSError as e:
                log_lines.append(f'  ✗ {dname}/  创建失败: {e}')

    tcl_dir = os.path.join(root, 'tcl')

    # ────────── 2. tcl 脚本补全 ──────────
    log_lines.append('  ── tcl 脚本检查 ──')

    # 2.1 recreate_block_design.tcl (BD 工程)
    bd_tcl = os.path.join(tcl_dir, 'recreate_block_design.tcl')
    first_bd = (os.path.splitext(os.path.basename(bd_files[0]))[0]
                if bd_files else 'design_1')
    if os.path.isfile(bd_tcl):
        log_lines.append(f'  ✓ tcl/recreate_block_design.tcl')
    elif _skipped('tcl 脚本|tcl/recreate_block_design.tcl'):
        log_lines.append(f'  · 用户跳过: tcl/recreate_block_design.tcl')
    elif bd_files:
        log_lines.append(f'  ✗ 缺少: tcl/recreate_block_design.tcl (BD 工程必须)')
        success = False
        if xpr_path and vivado_bin:
            log_lines.append(f'    [尝试] 用 Vivado 导出 BD tcl ...')
            ok, msg = _try_vivado_export_bd_tcl(
                bd_files[0], bd_tcl, vivado_bin, xpr_path)
            if ok and os.path.isfile(bd_tcl):
                log_lines.append(f'    [成功] Vivado 导出完成')
                generated.append(bd_tcl)
                success = True
            else:
                log_lines.append(f'    [失败] Vivado 导出失败, 改用规则补全')
                log_lines.append(f'            {str(msg)[:200]}')
        if not success:
            ok, result = _supplement_recreate_block_design_tcl(
                bd_tcl, first_bd, vivado_ver_str, src_bd_path=bd_files[0])
            if ok:
                size = os.path.getsize(bd_tcl)
                log_lines.append(f'    [骨架] 已按 FPGA_GIT_GUIDE.md 第 5 章规则生成')
                log_lines.append(f'            路径: tcl/recreate_block_design.tcl')
                log_lines.append(f'            大小: {size} 字节')
                log_lines.append(f'    [提示] 骨架中 IP 列表为空, 需在 Vivado 中用 '
                                 f'write_bd_tcl 重新生成完整版')
                generated.append(result)
            else:
                log_lines.append(f'    [失败] {result}')
    else:
        log_lines.append(f'  · 跳过: tcl/recreate_block_design.tcl (非 BD 工程)')

    # 2.2 recreate_project.tcl
    proj_tcl = os.path.join(tcl_dir, 'recreate_project.tcl')
    if os.path.isfile(proj_tcl):
        log_lines.append(f'  ✓ tcl/recreate_project.tcl')
    elif _skipped('tcl 脚本|tcl/recreate_project.tcl'):
        log_lines.append(f'  · 用户跳过: tcl/recreate_project.tcl')
    else:
        log_lines.append(f'  ✗ 缺少: tcl/recreate_project.tcl')
        ok, result = _supplement_recreate_project_tcl(
            proj_tcl, proj_name, project_part, vivado_ver_str, first_bd)
        if ok:
            size = os.path.getsize(proj_tcl)
            log_lines.append(f'    [骨架] 已按 FPGA_GIT_GUIDE.md 第 6/7 章规则生成')
            log_lines.append(f'            路径: tcl/recreate_project.tcl')
            log_lines.append(f'            大小: {size} 字节')
            generated.append(result)
        else:
            log_lines.append(f'    [失败] {result}')

    # 2.3 package_project.tcl
    pkg_tcl = os.path.join(tcl_dir, 'package_project.tcl')
    if os.path.isfile(pkg_tcl):
        log_lines.append(f'  ✓ tcl/package_project.tcl')
    elif _skipped('tcl 脚本|tcl/package_project.tcl'):
        log_lines.append(f'  · 用户跳过: tcl/package_project.tcl')
    else:
        log_lines.append(f'  ✗ 缺少: tcl/package_project.tcl')
        ok, result = _supplement_package_project_tcl(
            pkg_tcl, proj_name, project_part, vivado_ver_str)
        if ok:
            size = os.path.getsize(pkg_tcl)
            log_lines.append(f'    [骨架] 已按 FPGA_GIT_GUIDE.md 第 7.1 节规则生成')
            log_lines.append(f'            路径: tcl/package_project.tcl')
            log_lines.append(f'            大小: {size} 字节')
            generated.append(result)
        else:
            log_lines.append(f'    [失败] {result}')

    # 2.4 自定义 IP 的 recreate_ip.tcl
    for ip_dir in custom_ip_dirs:
        ip_name = os.path.basename(ip_dir)
        ip_tcl = os.path.join(ip_dir, 'tcl', 'recreate_ip.tcl')
        if os.path.isfile(ip_tcl):
            log_lines.append(f'  ✓ ip_repo/{ip_name}/tcl/recreate_ip.tcl')
        elif _skipped(f'IP 脚本|ip_repo/{ip_name}/tcl/recreate_ip.tcl'):
            log_lines.append(f'  · 用户跳过: ip_repo/{ip_name}/tcl/recreate_ip.tcl')
        else:
            log_lines.append(f'  ✗ 缺少: ip_repo/{ip_name}/tcl/recreate_ip.tcl')
            # 为该 IP 创建 tcl/ 目录 + 骨架
            os.makedirs(os.path.dirname(ip_tcl), exist_ok=True)
            tpl = f'''# ════════════════════════════════════════════════════════════════
# recreate_ip.tcl — Auto-generated by gen_inst.py
# 自定义 IP "{ip_name}" 重建脚本 (依据 FPGA_GIT_GUIDE.md 第 4.4 节)
# Vivado 版本: {vivado_ver_str or 'unknown'}
# ════════════════════════════════════════════════════════════════

set origin_dir [file dirname [file dirname [file normalize [info script]]]]
set ip_name "{ip_name}"
set ip_project_dir "$origin_dir/ip_project"

puts ">>> 重建自定义 IP: $ip_name"

# 1. 创建 IP 工程 (如不存在)
if {{![file exists $ip_project_dir]}} {{
    file mkdir $ip_project_dir
    create_project $ip_name $ip_project_dir -part xc7a100tcsg324-1
}}

# 2. 打开 IP 工程
open_project [file join $ip_project_dir "$ip_name.xpr"]

# 3. 重新封装 IP
update_ip_catalog -rebuild
ipx::open_ipxact_file [file join $origin_dir "packaged_ip" "component.xml"]
ipx::update_ipxact_file component.xml
ipx::save_ipxact [file join $origin_dir "packaged_ip" "component.xml"]

puts ">>> IP 重建完成: $ip_name"
'''
            try:
                with open(ip_tcl, 'w', encoding='utf-8') as fh:
                    fh.write(tpl)
                log_lines.append(f'    [骨架] 已生成 ip_repo/{ip_name}/tcl/recreate_ip.tcl')
                generated.append(ip_tcl)
            except OSError as e:
                log_lines.append(f'    [失败] {e}')

    # ────────── 3. README.md 补全 ──────────
    log_lines.append('  ── 文档检查 ──')
    readme_path = os.path.join(root, 'README.md')
    if os.path.isfile(readme_path):
        log_lines.append(f'  ✓ README.md')
    elif _skipped('文档|README.md'):
        log_lines.append(f'  · 用户跳过: README.md')
    else:
        log_lines.append(f'  ✗ 缺少: README.md (依据 3.1 节末)')
        bd_names = [os.path.splitext(os.path.basename(b))[0] for b in bd_files]
        ok, result = _supplement_readme_md(
            readme_path, proj_name, vivado_ver_str, bd_names, has_ip_repo)
        if ok:
            size = os.path.getsize(readme_path)
            log_lines.append(f'    [新建] README.md  (含目录结构/版本/重建方法, {size} 字节)')
            generated.append(result)
        else:
            log_lines.append(f'    [失败] {result}')

    # ────────── 4. .gitignore 补全 ──────────
    gitignore_path = os.path.join(root, '.gitignore')
    if os.path.isfile(gitignore_path):
        log_lines.append(f'  ✓ .gitignore')
    elif _skipped('配置|.gitignore'):
        log_lines.append(f'  · 用户跳过: .gitignore')
    else:
        log_lines.append(f'  ✗ 缺少: .gitignore (依据 3.2 节)')
        gi = '''# FPGA Toolbox 推荐的 Vivado .gitignore (依据 FPGA_GIT_GUIDE.md 3.2 节)
# Vivado 自动生成的文件和目录
project/
ip_project/
*.jou
*.log
*.str
*.xpe
.cache/
.hw
.sim/
*ip_user_files/
.gen
.runs/
.srcs/
.sdk/
.tmp
*hwdef
*.xpr.lock
*xpr.ip_user_files/

# 编译结果和中间文件
*.bit
*.mcs
*.prn
*.bin
*.rpt
*.dcp
*.ltx
*.hdf
*.sysdef
*.xsa

# IP 产生的文件
*.xcix
.*/ip/*
.*/bd/*/ip/*

# 检查点文件 (除非必要)
*.dcp

# 排除 Vivado 工程设置
.xpr.user
'''
        try:
            with open(gitignore_path, 'w', encoding='utf-8') as fh:
                fh.write(gi)
            log_lines.append(f'    [新建] .gitignore (按 FPGA_GIT_GUIDE.md 3.2 节)')
            generated.append(gitignore_path)
        except OSError as e:
            log_lines.append(f'    [失败] {e}')

    # ────────── 5. xdc/ 目录约束文件检查 (提示) ──────────
    if xdc_files and not os.path.isdir(os.path.join(root, 'xdc')):
        log_lines.append(f'  · 提示: 发现 {len(xdc_files)} 个 .xdc 文件, '
                         f'但 xdc/ 目录不存在, 建议移动到 xdc/')

    # ────────── 6. app/ 目录应用文件检查 (提示) ──────────
    if app_files and not os.path.isdir(os.path.join(root, 'app')):
        log_lines.append(f'  · 提示: 发现 {len(app_files)} 个 app 文件 '
                         f'(.elf/.hdf/.xsa), 但 app/ 目录不存在, 建议移动到 app/')

    log_lines.append(f'  ── 总结: 共补全 {len(generated)} 项 ──')
    return generated, '\n'.join(log_lines)


# ════════════════════════════════════════════════════════════════════════
#  整理为 Git 工程 (新建文件夹, 不破坏原工程, 依据 FPGA_GIT_GUIDE.md)
# ════════════════════════════════════════════════════════════════════════
def organize_project_to_git(src_dir, dst_name=None, vivado_bin=None,
                              vivado_ver='', project_part=None,
                              copy_files=True, auto_export=True,
                              skip_keys=None):
    """
    将 FPGA 工程整理为符合 FPGA_GIT_GUIDE.md 规范的 Git 工程,
    **不破坏原工程**, 而是创建一个新文件夹 <src>/<proj>_git/,
    按规范重组原工程中的:
      - .xpr 工程文件       → <new>/project/
      - .bd 文件             → <new>/project/bd/<name>/
      - .xdc 约束            → <new>/xdc/
      - .elf/.hdf/.xsa       → <new>/app/
      - 自定义 IP 目录        → <new>/ip_repo/<name>/
      - HDL 源码 (.v/.vhd)   → <new>/src/
      - Vivado tcl 脚本      → <new>/tcl/

    然后调 check_and_supplement_bd_tcl 补全 tcl/README/.gitignore.

    返回: (新目录路径, 日志字符串)
    """
    src = os.path.abspath(src_dir)
    if not os.path.isdir(src):
        raise ValueError(f'源目录不存在: {src}')

    # 1. 探测工程名 (从 .xpr 推)
    src_name = os.path.basename(src.rstrip('/\\'))
    xpr_files = []
    for f in os.listdir(src):
        if f.endswith('.xpr') and not f.endswith(('.lock', '.user')):
            xpr_files.append(os.path.join(src, f))
    proj_dir_src = os.path.join(src, 'project')
    if not xpr_files and os.path.isdir(proj_dir_src):
        for f in os.listdir(proj_dir_src):
            if f.endswith('.xpr') and not f.endswith(('.lock', '.user')):
                xpr_files.append(os.path.join(proj_dir_src, f))
    if xpr_files:
        proj_name = os.path.splitext(os.path.basename(xpr_files[0]))[0]
    else:
        proj_name = dst_name or src_name

    # 2. 目标目录: <src>/<proj_name>_git/
    suffix = dst_name if dst_name else f'{proj_name}_git'
    dst = os.path.join(os.path.dirname(src), suffix)
    if os.path.abspath(dst) == os.path.abspath(src):
        dst = os.path.join(os.path.dirname(src), f'{proj_name}_git_git')
    # 已存在则加 _1 _2 ...
    if os.path.exists(dst):
        i = 1
        while os.path.exists(f'{dst}_{i}'):
            i += 1
        dst = f'{dst}_{i}'

    log = [f'[整理为 Git 工程]  原: {src}', f'                新: {dst}']

    def _ignore_filter(src_path, names):
        """过滤 Vivado 自动生成目录, 不复制"""
        ignore_set = {
            '.runs', '.cache', '.gen', '.sdk', '.tmp', '.hw', '.sim',
            '.srcs', 'ip_user_files', 'ip_project', 'project',
            'incremental_db', 'ip', 'hls', '.Xil',
        }
        # .git 也忽略
        if os.path.basename(src_path) == '.git':
            return ['.']
        # vivado 生成目录
        return [n for n in names if n in ignore_set or n.startswith('.')]

    if copy_files:
        # 创建目标 + 复制
        try:
            shutil.copytree(src, dst, ignore=_ignore_filter)
            log.append(f'  ✓ 已复制原工程到新目录 (过滤 vivado 自动生成目录)')
        except Exception as e:
            log.append(f'  ✗ 复制失败: {e}')
            return None, '\n'.join(log)
    else:
        os.makedirs(dst, exist_ok=True)
        log.append(f'  ✓ 已创建新目录')

    # 3. 移动 / 重命名分类文件
    # 3.1 找所有 .bd / .xdc / .elf / .hdf / .xsa / .v / .vhd / .sv / .tcl
    def _scan_dir_for_ext(root, exts):
        results = []
        try:
            for dp, dns, fns in os.walk(root):
                # 跳过 .git, 自动生成目录
                dns[:] = [d for d in dns
                          if d not in {'.git', '.runs', '.cache', '.gen',
                                       '.sdk', '.tmp', '.hw', '.sim', 'ip_user_files',
                                       '.Xil', 'ip', 'hls'}]
                for fn in fns:
                    if fn.lower().endswith(exts):
                        results.append(os.path.join(dp, fn))
        except OSError:
            pass
        return results

    moves = []  # (src_file, dst_dir_in_dst)

    # .bd → project/bd/
    for f in _scan_dir_for_ext(dst, '.bd'):
        bd_name = os.path.splitext(os.path.basename(f))[0]
        target_dir = os.path.join(dst, 'project', 'bd', bd_name)
        moves.append((f, target_dir))

    # .xdc → xdc/
    for f in _scan_dir_for_ext(dst, '.xdc'):
        moves.append((f, os.path.join(dst, 'xdc')))

    # .elf / .hdf / .xsa → app/
    for f in _scan_dir_for_ext(dst, ('.elf', '.hdf', '.xsa')):
        moves.append((f, os.path.join(dst, 'app')))

    # .v / .sv / .vhd / .vhdl → src/  (跳过 Vivado 内部生成目录)
    for f in _scan_dir_for_ext(dst, ('.v', '.sv', '.vhd', '.vhdl')):
        if any(seg in f for seg in ('/project/', '/ip_repo/')):
            # 已经分类过的, 跳过
            continue
        if '/.gen/' in f or '/.runs/' in f or '/.sim/' in f or '/hls/' in f:
            continue
        moves.append((f, os.path.join(dst, 'src')))

    # .tcl (用户的) → tcl/
    for f in _scan_dir_for_ext(dst, '.tcl'):
        if '/.gen/' in f or '/.runs/' in f or '/.cache/' in f:
            continue
        moves.append((f, os.path.join(dst, 'tcl')))

    # 执行移动
    moved = 0
    for src_f, dst_dir in moves:
        try:
            os.makedirs(dst_dir, exist_ok=True)
            dst_f = os.path.join(dst_dir, os.path.basename(src_f))
            # 已存在同名 → 加 _1 _2
            if os.path.exists(dst_f):
                base, ext = os.path.splitext(os.path.basename(src_f))
                i = 1
                while os.path.exists(os.path.join(dst_dir, f'{base}_{i}{ext}')):
                    i += 1
                dst_f = os.path.join(dst_dir, f'{base}_{i}{ext}')
            shutil.move(src_f, dst_f)
            moved += 1
        except Exception as e:
            log.append(f'  · 移动失败 {os.path.basename(src_f)}: {e}')

    log.append(f'  ✓ 重组 {moved} 个文件 (按规范分类到对应目录)')

    # 4. 调 check_and_supplement_bd_tcl 补全
    log.append(f'  ── 调 check_and_supplement_bd_tcl 补全缺失文件 ──')
    gen_files, gen_log = check_and_supplement_bd_tcl(
        dst, vivado_bin=vivado_bin, vivado_ver_str=vivado_ver,
        project_part=project_part, skip_keys=skip_keys)
    for line in gen_log.split('\n'):
        log.append('  ' + line)

    log.append(f'\n  ✔ 整理完成: {dst}')
    log.append(f'    下一步: 在 {dst} 目录下 git init / add / commit / push')

    return dst, '\n'.join(log)


def compress_project(root_dir, dry_run=True, no_interactive=False, auto_export=True,
                    vivado_bin=None, vivado_ver=''):
    """
    压缩 FPGA 工程：删除所有 Vivado 生成文件，只保留源码+脚本+配置。

    参数:
        root_dir: 工程根目录
        dry_run: True=仅预览不删除, False=执行删除
        no_interactive: 跳过交互式确认 (GUI 模式使用)
        auto_export: 自动从 .xpr 导出 BD Tcl / HDF / XSA 等文件
        vivado_bin: Vivado bin 目录路径
        vivado_ver: Vivado 版本字符串 (如 "Vivado v2023.2" 或 "2023.2"),
                    用于 BD tcl 补全时按版本规则生成

    返回: (删除文件数, 释放字节数)
    """
    root = os.path.abspath(root_dir)
    if not os.path.isdir(root):
        raise ValueError(f"目录不存在: {root}")

    # ==== Step 0: 自动导出 (可选) ====
    if auto_export:
        gen_files, gen_log = auto_export_vivado(root, vivado_bin)
        if gen_files:
            print(f"\033[36m[自动导出] {gen_log}\033[0m")
        elif '未找到 Vivado 工程文件' not in gen_log:
            print(f"\033[33m[自动导出] {gen_log}\033[0m")

        # ==== Step 0.5: BD Tcl 检查与补全 (依据 FPGA_GIT_GUIDE.md) ====
        # 若工程是 BD 工程但缺少 tcl/recreate_block_design.tcl 等,
        # 优先用 Vivado 导出, 失败时按版本规则生成最小骨架
        # 优先用调用方传入的 vivado_ver, 否则从 log 第一行取
        vivado_ver_str = vivado_ver or (gen_log.split('\n')[0] if gen_log else '')
        bd_files, bd_log = check_and_supplement_bd_tcl(
            root, vivado_bin=vivado_bin, vivado_ver_str=vivado_ver_str)
        if bd_files or '未发现' not in bd_log:
            # 无论是否真的补全, 只要检测到 .bd 就输出日志
            print(f"\033[35m{bd_log}\033[0m")

    to_delete = []  # (path, is_dir, size_bytes)

    def _size(path):
        """递归计算文件/目录大小"""
        total = 0
        if os.path.isfile(path):
            try:
                total = os.path.getsize(path)
            except OSError:
                pass
        elif os.path.isdir(path):
            try:
                for entry in os.scandir(path):
                    if entry.is_file(follow_symlinks=False):
                        try:
                            total += entry.stat().st_size
                        except OSError:
                            pass
                    elif entry.is_dir(follow_symlinks=False):
                        total += _size(entry.path)
            except OSError:
                pass
        return total

    # 递归扫描
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        rel_dir = os.path.relpath(dirpath, root)

        # 跳过已标记删除的目录
        dirnames[:] = [d for d in dirnames if os.path.join(dirpath, d) not in
                       {p for p, is_d, _ in to_delete if is_d}]

        # 检查目录名
        for d in dirnames[:]:
            if d in _COMPRESS_DEL_DIRS or d.endswith('_ip_user_files'):
                full = os.path.join(dirpath, d)
                to_delete.append((full, True, _size(full)))
                dirnames.remove(d)

        # 检查文件名
        for f in filenames:
            full = os.path.join(dirpath, f)
            ext = os.path.splitext(f)[1].lower()
            base = f.lower()

            # 白名单检查：不过滤源码、配置、文档
            if ext in _COMPRESS_WHITELIST_EXT:
                continue
            if base in ('component.xml', '.gitignore', '.gitattributes',
                        'makefile', 'readme.md'):
                continue

            # 匹配删除模式
            import fnmatch
            for pattern in _COMPRESS_DEL_FILES:
                if fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch(base, pattern):
                    to_delete.append((full, False, _size(full)))
                    break

    # 统计
    total_files = sum(1 for _, is_d, _ in to_delete if not is_d)
    total_dirs = sum(1 for _, is_d, _ in to_delete if is_d)
    total_size = sum(sz for _, _, sz in to_delete)

    # 显示预览
    print()
    print(f"\033[36m扫描: {root}\033[0m")
    print(f"  将删除 {total_files} 个文件 + {total_dirs} 个目录, "
          f"释放约 {_fmt_size(total_size)}")
    print()

    if total_files + total_dirs == 0:
        print("\033[32m  工程已是最精简状态，无需清理。\033[0m")
        return 0, 0

    # 按路径排序显示
    to_delete.sort(key=lambda x: x[0])
    max_show = 80
    for i, (path, is_dir, sz) in enumerate(to_delete):
        if i >= max_show:
            print(f"  ... 还有 {len(to_delete) - max_show} 项 (省略)")
            break
        tag = "\033[33m[目录]\033[0m" if is_dir else "\033[37m[文件]\033[0m"
        rel = os.path.relpath(path, root)
        print(f"  {tag} {rel}  ({_fmt_size(sz)})")

    print()

    if dry_run:
        print("\033[33m[Dry-Run 模式] 未实际删除。\033[0m")
        return len(to_delete), total_size

    # 确认 (非交互模式跳过)
    if not no_interactive:
        print(f"\033[31m确认删除以上 {len(to_delete)} 项 (释放 {_fmt_size(total_size)})? [y/N]\033[0m")
        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消。")
            return 0, 0
        if answer not in ('y', 'yes'):
            print("已取消。")
            return 0, 0

    # 执行删除（先删文件再删目录）
    import shutil
    deleted = 0
    freed = 0
    for path, is_dir, sz in to_delete:
        try:
            if is_dir:
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.unlink(path)
            deleted += 1
            freed += sz
        except OSError as e:
            print(f"\033[31m  删除失败: {path} ({e})\033[0m")

    print()
    print(f"\033[32m  压缩完成! 删除 {deleted} 项, 释放 {_fmt_size(freed)}\033[0m")
    return deleted, freed


def archive_project(src_dir, dst_dir, dry_run=True, auto_export=True, vivado_bin=None,
                    vivado_ver=''):
    """
    归档 FPGA 工程：复制必要文件到新目录，源文件不动。

    参数:
        src_dir: 源工程根目录
        dst_dir: 目标目录 (将创建)
        dry_run: True=仅预览, False=执行复制
        auto_export: 自动从 .xpr 导出 BD Tcl / HDF / XSA
        vivado_ver: Vivado 版本 (用于 BD tcl 补全)

    返回: (复制文件数, 总大小字节数)
    """
    import fnmatch, shutil
    src = os.path.abspath(src_dir)
    dst = os.path.abspath(dst_dir)

    if not os.path.isdir(src):
        raise ValueError(f"源目录不存在: {src}")
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError("目标目录不能与源目录相同")

    # ==== Step 0: 自动导出 (可选) ====
    if auto_export:
        gen_files, gen_log = auto_export_vivado(src, vivado_bin)
        if gen_files:
            print(f"\033[36m[自动导出] {gen_log}\033[0m")
        elif '未找到 Vivado 工程文件' not in gen_log:
            print(f"\033[33m[自动导出] {gen_log}\033[0m")

        # ==== Step 0.5: BD Tcl 检查与补全 (依据 FPGA_GIT_GUIDE.md) ====
        vivado_ver_str = vivado_ver or (gen_log.split('\n')[0] if gen_log else '')
        bd_files, bd_log = check_and_supplement_bd_tcl(
            src, vivado_bin=vivado_bin, vivado_ver_str=vivado_ver_str)
        if bd_files or '未发现' not in bd_log:
            print(f"\033[35m{bd_log}\033[0m")

    to_copy = []  # (src_path, dst_path, size)

    def _should_skip(name, is_dir):
        """检查文件/目录是否在黑名单中"""
        if is_dir:
            if name in _COMPRESS_DEL_DIRS or name.endswith('_ip_user_files'):
                return True
            return False
        ext = os.path.splitext(name)[1].lower()
        if ext in _COMPRESS_WHITELIST_EXT:
            return False
        if name.lower() in ('component.xml', '.gitignore', '.gitattributes',
                            'makefile', 'readme.md'):
            return False
        for pattern in _COMPRESS_DEL_FILES:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    for dirpath, dirnames, filenames in os.walk(src, topdown=True):
        rel = os.path.relpath(dirpath, src)
        # 过滤目录
        dirnames[:] = [d for d in dirnames if not _should_skip(d, True)]
        # 过滤文件
        for f in filenames:
            if not _should_skip(f, False):
                sp = os.path.join(dirpath, f)
                dp = os.path.join(dst, rel, f) if rel != '.' else os.path.join(dst, f)
                sz = os.path.getsize(sp) if os.path.isfile(sp) else 0
                to_copy.append((sp, dp, sz))

    total = sum(sz for _, _, sz in to_copy)
    print(f"\n\033[36m归档: {src}\033[0m")
    print(f"\033[36m  -> {dst}\033[0m")
    print(f"  将复制 {len(to_copy)} 个文件, 总计 {_fmt_size(total)}")
    print()

    for sp, dp, sz in to_copy[:50]:
        print(f"  \033[37m[复制]\033[0m {os.path.relpath(dp, dst)}  ({_fmt_size(sz)})")
    if len(to_copy) > 50:
        print(f"  ... 还有 {len(to_copy) - 50} 个文件 (省略)")

    if dry_run:
        print(f"\n\033[33m[Dry-Run 模式] 未实际复制。\033[0m")
        return len(to_copy), total

    # 执行复制
    copied = 0
    for sp, dp, sz in to_copy:
        try:
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.copy2(sp, dp)
            copied += 1
        except OSError as e:
            print(f"\033[31m  复制失败: {sp} ({e})\033[0m")

    print(f"\n\033[32m  归档完成! 复制 {copied} 个文件, {_fmt_size(total)}\033[0m")
    return copied, total


def _fmt_size(size_bytes):
    """人类可读的文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# ============================================================================
# GUI 模式 (tkinter)
# ============================================================================





def _generate_fpga_gitignore():
    """返回 FPGA 工程标准 .gitignore 内容 (对齐文档规范)"""
    return """# Vivado 自动生成的文件和目录
project/
ip_project/
*.jou
*.log
*.str
*.xpe
.cache/
.hw
.sim/
*ip_user_files/
.gen
.runs/
.srcs/
.sdk/
.tmp
*hwdef
*.xpr.lock
*xpr.ip_user_files/

# 编译结果和中间文件
*.bit
*.mcs
*.prm
*.bin
*.rpt
*.dcp
*.ltx
*.hdf
*.sysdef

# IP 产生的文件
*.xcix
.*/ip/*
.*/bd/*/ip/*

# 检查点文件
*.dcp

# Vivado 工程设置
.xpr.user
"""






# ── GUI (delegated to gen_gui.py) ──
# 惰性导入：仅在 GUI 模式下加载，避免 CLI 模式因缺少 tkinter 而崩溃
def _run_gui():
    import sys as _sys
    try:
        from gen_gui import run_gui
    except ImportError:
        # PyInstaller 打包后路径不同
        if getattr(_sys, 'frozen', False):
            _sys.path.insert(0, _sys._MEIPASS)
            from gen_gui import run_gui
        else:
            raise
    run_gui()


def format_fpga_code(filepath, dry_run=False):
    """
    整理 FPGA 代码排版 (Verilog/SystemVerilog/VHDL)
    - 统一缩进 (tab/4空格)
    - begin-end 对齐
    - wire/reg/assign 对齐
    - 添加注释头 (如缺失)
    - 去除多余空行

    返回: (原文件大小, 新文件大小, 改动数, 日志列表)
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ('.v', '.sv', '.vhd', '.vhdl'):
        return 0, 0, 0, [f'  跳过: 不支持的文件类型 {ext}']

    # 兼容 Windows (GBK) 和 Linux (UTF-8)
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                original = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        original = open(filepath, 'r', errors='replace').read()

    if ext in ('.v', '.sv'):
        formatted = _format_verilog(original, filepath)
    else:
        formatted = _format_vhdl(original, filepath)

    changed = (original != formatted)

    if dry_run or not changed:
        return len(original), len(formatted), 1 if changed else 0, []

    with open(filepath, 'w', encoding=enc, newline='') as f:
        f.write(formatted)

    return len(original), len(formatted), 1, []


def _format_verilog(code, filepath):
    """Verilog/SystemVerilog 格式化 (依据 docs/verilog_style_format_cn_en.md)"""
    import datetime

    lines = code.split('\n')
    result = []
    indent = 0
    INDENT = '  '  # 2 空格 (规范 1.1)
    prev_blank = False
    paren_stack = []  # 跟踪 '(' 缩进
    # 块头关键字栈: case/for/if/while/always 自身 -1 进入, 弹出时 +1 恢复.
    # 这样嵌套 for 内 if 会自动多缩进一级. case 后无 begin 也生效.
    block_stack = []

    # ── 规范第 1.3 节: 关键字后空格 ──
    def _normalize_spacing(s):
        """归一化关键字间距, 去掉行尾空格"""
        # always@ → always @
        s = re.sub(r'\b(always|always_ff|always_comb|always_latch|initial|final)\s*@',
                   r'\1 @', s)
        # if( → if (, case( → case (, for( → for (, while( → while (, foreach( → foreach (
        s = re.sub(r'\b(if|case|for|while|foreach|task|function)\s*\(', r'\1 (', s)
        s = s.rstrip()
        return s

    # 跟踪"上一行非空代码行的 indent", 用于注释行继承.
    # Xilinx 模板里"上注释 + 下端口"的风格, 注释与端口同缩进.
    last_code_indent = 0

    # 块头关键字识别: 以这些关键字开头的行, 块内容多缩进一级.
    # 注意: 这些关键字"自身不再 +1" (避免缩进累积), 但块内容靠 block_stack 维护.
    BLOCK_KW = r'\b(case|casex|casez|for|while|foreach|always|always_ff|always_comb|always_latch|initial|if|else|elsif)\b'

    for i, raw in enumerate(lines):
        stripped = raw.strip()

        # 跳过空行（保留最多 1 个）
        if not stripped:
            if not prev_blank and result:
                result.append('')
                prev_blank = True
            continue
        prev_blank = False

        # 应用间距归一化
        stripped = _normalize_spacing(stripped)

        # ── 判断是否是纯注释行 (规范 §8) ──
        is_comment_line = stripped.startswith('//') or stripped.startswith('/*')

        # ── 缩进计算 (注释行不影响 indent, 不修改栈) ──
        # 内联注释 // ... 不能含 begin/end 等关键字干扰 indent
        code_for_kw = stripped.split('//')[0].rstrip() if not is_comment_line else stripped
        if not is_comment_line:
            # ① 减少缩进: end 行 (仅看代码部分, 忽略内联注释)
            has_end = bool(re.search(r'\bend\b', code_for_kw)) or re.match(r'^\bendcase\b', code_for_kw)
            if has_end:
                if re.match(r'^\bendmodule\b', code_for_kw):
                    indent = 0
                    paren_stack.clear()
                    block_stack.clear()
                elif re.match(r'^\bendcase\b', code_for_kw):
                    for i in range(len(block_stack) - 1, -1, -1):
                        if block_stack[i] in ('case', 'casex', 'casez'):
                            del block_stack[i]
                            break
                    indent = max(0, indent - 1)
                elif re.match(r'^\b(endfunction|endtask|endgenerate|endpackage|'
                              r'endinterface|endclass|endspecify|endprimitive|'
                              r'endconfig|endclocking|endproperty|endsequence|'
                              r'endchecker)\b', code_for_kw):
                    if block_stack:
                        block_stack.pop()
                    indent = max(0, indent - 1)
                else:
                    for i in range(len(block_stack) - 1, -1, -1):
                        if block_stack[i] == 'begin':
                            del block_stack[i:]
                            break
                    indent = max(0, indent - 1)

            # ①.b 清掉 case 内部的 if/for/while 隐式块
            is_case_item = bool(re.match(
                r"^\s*([A-Za-z_]\w*|\d+\s*'[bhdBHD]?\s*[0-9a-fA-FxXzZ?]+|default)\s*:",
                code_for_kw))
            is_endcase_line = bool(re.match(r'^\bendcase\b', code_for_kw))
            if is_case_item or is_endcase_line:
                while block_stack and block_stack[-1] in ('if', 'for', 'while', 'foreach'):
                    block_stack.pop()
                    indent = max(0, indent - 1)

            # ② endmodule
            if re.match(r'^\bendmodule\b', code_for_kw):
                indent = 0
                paren_stack.clear()
                block_stack.clear()

            # ③ 闭括号
            while paren_stack and re.match(r'^\s*\)', code_for_kw):
                indent = paren_stack.pop()

            # ④ else/elsif
            is_else = bool(re.match(r'^\b(else|elsif)\b', code_for_kw))
            if is_else and block_stack:
                indent = max(0, indent - 1)

        cur_indent = indent if not is_comment_line else last_code_indent

        result.append(INDENT * cur_indent + stripped)

        # 记录"上一行非空代码行 indent" (仅对非注释行更新, 让注释行继承)
        if not is_comment_line:
            last_code_indent = cur_indent

        # ── 下一行缩进计算 (仅非注释行, 关键字检测用 code_for_kw 避免内联注释干扰) ──
        if not is_comment_line:
            # else/elsif 临时减的 1 恢复
            if is_else:
                indent += 1

            # begin 块: 多缩进一级, 入 block_stack
            if re.search(r'\bbegin\b', code_for_kw):
                indent += 1
                block_stack.append('begin')

            # 块头关键字 (case/for/if/while/always) 块内多缩进一级.
            is_case = bool(re.match(r'^\b(case|casex|casez)\b', code_for_kw))
            is_always = bool(re.match(r'^\b(always|always_ff|always_comb|always_latch|initial)\b', code_for_kw))
            is_for_while = bool(re.search(r'\b(for|while|foreach)\b', code_for_kw))
            is_if = bool(re.search(r'\bif\b', code_for_kw))
            has_begin_inline = bool(re.search(r'\bbegin\b(\s*;|\s*:|\s*$)', code_for_kw))
            is_single_stmt = code_for_kw.endswith(';') and not has_begin_inline

            if (is_case or is_always) and not has_begin_inline:
                indent += 1
                block_stack.append(code_for_kw.split()[0])
            elif is_for_while and not is_single_stmt and not has_begin_inline:
                indent += 1
                block_stack.append('for')
            elif is_if and not is_single_stmt and not has_begin_inline and not is_else:
                indent += 1
                block_stack.append('if')

            # module / generate 后必须跟 begin 或语句
            if re.match(r'^\b(module|generate)\b', code_for_kw) and not re.search(r'\bbegin\b', code_for_kw):
                indent += 1





    # 对齐 wire/reg/assign（后处理）
    result = _align_declarations(result, INDENT)

    # 对齐例化端口
    result = _align_instantiations(result)

    # 短注释 (≤2 行) 合并为行尾 inline 注释
    result = _merge_short_comments(result)

    # 清理 + 对齐行尾注释
    for i in range(len(result)):
        result[i] = re.sub(r'(\w)\s+([,;])(?=\s*(?://|--|$))', r'\1\2', result[i])
    result = _align_inline_comments(result)

    # ── 注释头: 有旧头 → 换成新头, 无头 → 插入新头 ──
    result = _rewrite_header(result, filepath, False)

    return '\n'.join(result)


def _format_vhdl(code, filepath):
    """VHDL 格式化 — entity/architecture/process 缩进 + 声明对齐"""
    import datetime

    lines = code.split('\n')
    result = []
    indent = 0
    INDENT = '  '
    prev_blank = False

    def _vhdl_normalize(s):
        """VHDL 关键字后空格 + 行尾去空格"""
        # if( → if (, case( → case (, for( → for (, while( → while (
        s = re.sub(r'\b(if|case|for|while|when|with)\s*\(', r'\1 (', s)
        # elsif / else 后空格
        s = re.sub(r'\b(elsif|else)\s+', r'\1 ', s)
        return s.rstrip()

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            if not prev_blank and result:
                result.append('')
                prev_blank = True
            continue
        prev_blank = False

        stripped = _vhdl_normalize(stripped)
        lower = stripped.lower()

        # elsif/else 应与其对应的 if 同级
        is_elsif_else = bool(re.match(r'^\b(elsif|else)\b', stripped, re.IGNORECASE))
        if is_elsif_else:
            indent = max(0, indent - 1)  # 临时回到 if 层级

        # 减少缩进 (end 系列)
        if re.match(r'^\b(end|end\s+entity|end\s+architecture|'
                    r'end\s+component|end\s+process|end\s+generate|'
                    r'end\s+if|end\s+case|end\s+loop|end\s+block)\b',
                    stripped, re.IGNORECASE):
            indent = max(0, indent - 1)

        result.append(INDENT * indent + stripped)

        # 增加缩进 — 块开头关键字
        if re.match(r'^\b(entity|architecture|component|process|'
                    r'if\b|case\b|for\b|while\b|'
                    r'generate\b|loop\b|block\b)\b',
                    stripped, re.IGNORECASE):
            if 'begin' in lower or 'then' in lower or not stripped.endswith(';'):
                indent += 1

        # begin 关键字 — 仅当在 process/if/for 等块内时才缩进
        if re.match(r'^\bbegin\b', stripped, re.IGNORECASE):
            # 看上一行是否有块关键字
            prev_nonblank = ''
            for rl in reversed(result[:-1]):
                if rl.strip():
                    prev_nonblank = rl.strip().lower()
                    break
            if any(kw in prev_nonblank for kw in
                   ('process', 'then', 'else', 'generate', 'loop',
                    'block', 'is', 'begin')):
                indent += 1

        # elsif/else 之后恢复缩进（其内部块需要多一级）
        if is_elsif_else:
            indent += 1


    # 对齐 signal/port/generic 声明
    result = _align_vhdl_declarations(result, INDENT)

    # 对齐例化端口
    result = _align_instantiations(result)

    # 短注释 (≤2 行) 合并为行尾 inline 注释
    result = _merge_short_comments(result)

    # 清理 + 对齐行尾注释
    for i in range(len(result)):
        result[i] = re.sub(r'(\w)\s+([,;])(?=\s*(?://|--|$))', r'\1\2', result[i])
    result = _align_inline_comments(result)

    # ── 注释头: 有旧头 → 换成新头, 无头 → 插入新头 ──
    result = _rewrite_header(result, filepath, True)

    return '\n'.join(result)


def _align_vhdl_declarations(lines, indent_str):
    """对齐 VHDL signal/variable/constant 声明 — 跨前缀共享名字列宽 + 关键字列宽"""
    import re
    # ── 全局扫描 ──
    ALL_VHDL_KW = ('signal', 'variable', 'constant', 'shared variable')
    all_decls = {}

    for prefix in ALL_VHDL_KW:
        decls = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(rf'^{prefix}\s+\w+', stripped, re.IGNORECASE):
                m = re.match(rf'({prefix}\s+)(\w+)', stripped, re.IGNORECASE)
                if m:
                    decls.append((i, m.group(1), m.group(2)))
        if decls:
            all_decls[prefix] = decls

    # 全局 max_name / max_prefix (关键字+尾部空格)
    global_max_name = 0
    global_max_pre = 0
    for decls in all_decls.values():
        for _, pre, name in decls:
            global_max_name = max(global_max_name, len(name))
            global_max_pre = max(global_max_pre, len(pre))

    # ── 重构 ──
    for prefix, decls in all_decls.items():
        for i, pre, name in decls:
            stripped = lines[i].strip()
            m = re.match(rf'({prefix}\s+)(\w+)(.*)', stripped, re.IGNORECASE)
            if m:
                rest = m.group(3)
                name_pad = ' ' * (global_max_name - len(name))
                pre_pad = ' ' * (global_max_pre - len(pre))
                il = (len(lines[i]) - len(lines[i].lstrip())) // len(indent_str)
                lines[i] = indent_str * il + pre + pre_pad + name + name_pad + rest
    return lines


def _align_instantiations(lines):
    """对齐例化端口 (Verilog: .port(sig), VHDL: name=>sig).
    同时确保例化块前有空行. 从下往上扫描, 避免索引偏移.
    """
    # Verilog: .port_name (signal_name),
    VL_RE = re.compile(r'^\s*\.(\w+)\s*\((.+?)\)\s*(,?)\s*$')
    # VHDL: port_name => signal_name,
    VHDL_RE = re.compile(r'^\s*(\w+)\s*=>\s*(.+?)\s*(,?)\s*$')

    i = len(lines) - 1
    while i >= 0:
        stripped = lines[i].strip()
        m = VL_RE.match(stripped)
        is_vhdl = False
        if not m:
            m = VHDL_RE.match(stripped)
            is_vhdl = True
        if not m:
            i -= 1
            continue

        # 根据格式选择正则
        RE = VHDL_RE if is_vhdl else VL_RE

        # 找到连续例化行块 (向上扩展)
        block_end = i + 1
        block_start = i
        while block_start > 0:
            s = lines[block_start - 1].strip()
            if RE.match(s):
                block_start -= 1
            else:
                break

        if block_end - block_start < 2:
            i = block_start - 1
            continue

        # 计算列宽
        max_port = 0
        max_sig = 0
        decls = []
        for j in range(block_start, block_end):
            m = RE.match(lines[j].strip())
            if m:
                pname = m.group(1)
                sig = m.group(2).strip()
                decls.append((j, pname, sig, m.group(3) if not is_vhdl else m.group(3)))
                max_port = max(max_port, len(pname))
                max_sig = max(max_sig, len(sig))

        # 重构
        for j, pname, sig, comma in decls:
            port_pad = ' ' * (max_port - len(pname))
            sig_pad = ' ' * (max_sig - len(sig))
            indent = len(lines[j]) - len(lines[j].lstrip())
            if is_vhdl:
                lines[j] = f'{" " * indent}{pname}{port_pad} => {sig}{sig_pad}{comma}'
            else:
                lines[j] = f'{" " * indent}.{pname}{port_pad} ({sig}{sig_pad}){comma}'

        # 例化块内部清理: 删掉 opener 和 .port 之间的空行
        if block_start > 0:
            prev_idx = block_start - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            if prev_idx >= 0:
                prev = lines[prev_idx].strip()
                is_inst_open = (prev.startswith('#') or
                                re.match(r'\)\s*\w+\s*\(|.+?#\s*\(', prev))
                if is_inst_open:
                    while block_start > 0 and not lines[block_start - 1].strip():
                        del lines[block_start - 1]
                        block_start -= 1
        i = block_start - 1

    # ── 第二遍: 例化块前加空行 (跳过 ) name ( 这种例化内部行) ──
    INST_OPEN_RE = re.compile(r'^\s*(?:#\s*\(|.+?#\s*\(|\)\s*\w+\s*\()')
    DOT_PORT_RE = re.compile(r'^\s*\.\w+\s*\(')
    for j in range(len(lines) - 1, -1, -1):
        stripped = lines[j].strip()
        if not INST_OPEN_RE.match(stripped):
            continue
        if j == 0:
            continue
        # 找上面第一个非空行
        k = j - 1
        while k >= 0 and not lines[k].strip():
            k -= 1
        if k < 0:
            continue
        # 如果上是 .port( 行, 不插入空行 (这是例化内部)
        if DOT_PORT_RE.match(lines[k].strip()):
            continue
        if j - k <= 1:
            lines.insert(j, '')

    return lines


def _align_inline_comments(lines):
    """对齐连续行内的行尾分隔符 , ; 和 // 注释.
    1. 对齐 , / ; 到同一列
    2. 对齐 // 到同一列
    只处理"代码后跟的注释" (非顶格注释).
    """
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith('//') or stripped.startswith('--'):
            i += 1
            continue

        # 必须有行尾注释 或 行尾 , 才参与对齐
        cmt_pos = stripped.find('//')
        has_comma = stripped.endswith(',')
        if (cmt_pos == -1 or cmt_pos < 10) and not has_comma:
            i += 1
            continue
        if cmt_pos == -1:
            cmt_pos = len(stripped)  # 虚拟位置 (无注释)

        # 收集连续有行尾注释或端口声明的行
        block = [i]
        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if s and not s.startswith('//') and not s.startswith('--'):
                cp = s.find('//')
                if cp >= 10:
                    block.append(j)
                    j += 1
                elif s.endswith(',') and cp == -1:
                    block.append(j)  # 无注释端口声明
                    j += 1
                else:
                    break
            elif not s:
                block.append(j)
                j += 1
            else:
                break

        # 过滤纯空行的块
        code_lines = [(x, lines[x].strip()) for x in block
                      if lines[x].strip() and not lines[x].strip().startswith('//')]

        if len(code_lines) <= 1:
            i = j
            continue

        # 找 // 和 ,/; 的最右位置
        max_comma = 0
        max_cmt = 0
        for idx, s in code_lines:
            # 找到最后一个 , 或 ; (在 // 之前)
            cc = s.find('//')
            before_cmt = s[:cc] if cc >= 0 else s
            comma_pos = -1
            for delim in (',', ';'):
                p = before_cmt.rfind(delim)
                if p > comma_pos:
                    comma_pos = p
            if comma_pos >= 0:
                max_comma = max(max_comma, comma_pos + 1)  # 位置: 分隔符 + 1 空格
            if cc >= 10:
                max_cmt = max(max_cmt, cc)

        # 对齐: 先对齐 ,/;, 再对齐 //
        for idx, s in code_lines:
            indent = len(lines[idx]) - len(lines[idx].lstrip())
            cc = s.find('//')
            before_cmt = s[:cc] if cc >= 0 else s
            cmt = s[cc:] if cc >= 0 else ''

            # 找到分隔符位置
            comma_pos = -1
            comma_char = ''
            for delim in (',', ';'):
                p = before_cmt.rfind(delim)
                if p > comma_pos:
                    comma_pos = p
                    comma_char = delim

            if comma_pos >= 0 and max_comma > 0:
                # 重建: code_before_comma + pad_to_max_comma + comma + pad_to_cmt + comment
                before = before_cmt[:comma_pos].rstrip()
                pad1 = ' ' * (max_comma - 1 - len(before))
                if max_cmt > max_comma:
                    pad2 = ' ' * (max_cmt - max_comma)
                else:
                    pad2 = ''
                new_s = before + pad1 + comma_char + pad2 + cmt
                # 如果没注释, 不要尾随空格
                if not cmt:
                    new_s = new_s.rstrip()
                lines[idx] = ' ' * indent + new_s
            elif cc >= 10 and cc < max_cmt:
                before = before_cmt.rstrip()
                lines[idx] = ' ' * indent + before + ' ' * (max_cmt - cc) + cmt

        i = j

    return lines


def _merge_short_comments(lines):
    """短注释 (≤2 行) 合并为行尾 inline 注释.
    参数/端口列表内的注释无论多长都合并 inline.
    其他声明和代码上的长注释 (≥3 行) 保持原样不动.
    """
    DECL_OR_ASSIGN = re.compile(
        r'^\s*(?:parameter|localparam|wire|reg|logic|integer|real|time|realtime|'
        r'event|tri|input|output|inout|assign|signal|variable|constant|shared\s+variable)\b',
        re.IGNORECASE)
    # VHDL 端口/generic 项: name : type/dir ... ;  (不以 signal 等开头)
    VHDL_PORT_ITEM = re.compile(
        r'^\s*(\w+)\s*:\s*(?:in|out|inout|buffer|\w+)', re.IGNORECASE)
    # VHDL 常规声明 (signal/variable/constant) — 不在端口列表内
    VHDL_REGULAR = re.compile(
        r'^\s*(?:signal|variable|constant|shared\s+variable)\b', re.IGNORECASE)

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        is_comment = stripped.startswith('//') or stripped.startswith('--')
        if not is_comment:
            i += 1
            continue

        # 根据注释前缀判断语言
        is_vhdl = stripped.startswith('--')
        cmt_prefix = '--' if is_vhdl else '//'

        # 收集连续的注释行 (跳过中间空行)
        comment_block = [lines[i]]
        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if s.startswith('//') or s.startswith('--'):
                comment_block.append(lines[j])
                j += 1
            elif not s:
                j += 1
            else:
                break

        if j >= len(lines) or not lines[j].strip():
            i = j
            continue

        target_line = lines[j].strip()
        is_decl = bool(DECL_OR_ASSIGN.match(target_line))

        if is_vhdl:
            # VHDL 端口/generic 列表: 不以 signal/variable 开头的声明项
            is_vhdl_decl = is_decl or bool(VHDL_PORT_ITEM.match(target_line))
            in_list = is_vhdl_decl and not VHDL_REGULAR.match(target_line)
        else:
            # Verilog/SV: 以 , 结尾, 或后面紧跟 ) / );
            in_list = is_decl and (
                target_line.endswith(',')
                or any(lines[k].strip().startswith(')')
                       for k in range(j + 1, min(j + 4, len(lines)))
                       if lines[k].strip()))

        if len(comment_block) <= 2 or in_list:
            # 短注释 或 列表内声明 → 合并到代码行尾部
            comments = []
            for cl in comment_block:
                ct = cl.strip()
                if ct.startswith('//'):
                    ct = ct[2:].strip()
                elif ct.startswith('--'):
                    ct = ct[2:].strip()
                comments.append(ct)
            inline = f' {cmt_prefix} ' + ' '.join(comments)
            del lines[i:j]
            target_idx = i
            if target_idx < len(lines):
                lines[target_idx] = lines[target_idx].rstrip() + inline
            i = target_idx + 1
        else:
            # ≥3 行长注释 + 非列表声明 → 保持原样不动
            i = j

    return lines


def _rewrite_header(lines, filepath, is_vhdl):
    """统一注释头: 检测旧头并替换, 无头则插入"""
    if not lines:
        return lines

    c = '--' if is_vhdl else '//'
    # 分隔线模式: 行首可选注释符, 然后是 30+ 个 '-'
    sep_re = re.compile(r'^\s*(' + re.escape(c) + r'?\s*-{30,})\s*$')

    # ── 在文件开头找分隔线围起来的 header 块 ──
    search_range = min(12, len(lines))
    sep_positions = []
    for i in range(search_range):
        if sep_re.match(lines[i]):
            sep_positions.append(i)

    # 至少找到两处分隔线 (上 + 下), 中间就是 header
    old_header = None
    if len(sep_positions) >= 2:
        start, end = sep_positions[0], sep_positions[-1]
        between = ''.join(lines[start + 1:end]).lower()
        if any(kw in between for kw in
               ('module', 'entity', 'project', 'author', 'created',
                'description', 'file', 'date', 'copyright')):
            # 找到旧头: 切掉从第一个分隔线到最后一个分隔线 + 前面空行
            old_header = True
            while start > 0 and not lines[start - 1].strip():
                start -= 1
            del lines[start:end + 1]
    elif not lines[0].strip().startswith(c):
        # 开头没有注释行, 也没有分隔线 → 无头
        old_header = False
    else:
        # 有注释行但不是分隔线格式, 检查是否包含 header 关键字
        first_lines = ''.join(lines[:8]).lower()
        has_header_kw = bool(re.search(
            r'(?://|--)\s*(?:module|entity|author|created|description|date|copyright|file)\s*:',
            first_lines, re.IGNORECASE))
        if has_header_kw:
            # 有旧头但无分隔线 → 切掉所有前导注释行
            old_header = True
            cut = 0
            for i, ln in enumerate(lines):
                stripped = ln.strip()
                if not stripped:
                    cut = i + 1
                elif stripped.startswith(c):
                    cut = i + 1
                else:
                    break
            # 同时切掉尾部空行
            while cut > 0 and not lines[cut - 1].strip():
                cut -= 1
            if cut > 0:
                del lines[:cut]
        else:
            old_header = False

    # ── 插入新头 ──
    header = _gen_header(filepath)
    if old_header is None:
        old_header = False  # 未识别出旧头, 按无头处理

    lines.insert(0, header)
    lines.insert(1, '')

    return lines


def _gen_header(filepath):
    """生成统一注释头 (规范 §8.1 / §9.1):
    Verilog/SV: // Module/Project/Author/Created/Description, : 对齐
    VHDL:       -- Entity/Project/Author/Created/Description, : 对齐
    """
    import datetime
    fname = os.path.basename(filepath)
    today = datetime.date.today().isoformat()
    ext = os.path.splitext(filepath)[1].lower()
    module_name = os.path.splitext(fname)[0]

    if ext in ('.vhd', '.vhdl'):
        sep = '-' * 75
        lines = [
            sep,
            f'-- {"Entity":<14}: {module_name}',
            '-- ' + 'Project'.ljust(14) + ': ',
            '-- ' + 'Author'.ljust(14) + ': ',
            f'-- {"Created":<14}: {today}',
            '-- ' + 'Description'.ljust(14) + ': ',
            sep,
        ]
    else:
        sep = '// ' + '-' * 70
        lines = [
            sep,
            f'// {"Module":<14}: {module_name}',
            '// ' + 'Project'.ljust(14) + ': ',
            '// ' + 'Author'.ljust(14) + ': ',
            f'// {"Created":<14}: {today}',
            '// ' + 'Description'.ljust(14) + ': ',
            sep,
        ]
    return '\n'.join(lines)


def _align_declarations(lines, indent_str):
    """对齐 wire/reg/assign: 位宽列 + 信号名列 + ; 列, 无位宽的行也留空位.

    规则 (依据 docs/verilog_style_format_cn_en.md §2.3):
      - wire/reg/assign 关键字左对齐
      - 位宽列对齐
      - 信号名列对齐
      - 不破坏原行内容 (assign 后面的 = expr; 完整保留, 不再吃掉 expr)
      - 红线 1: 严禁 Tab, 位宽 / 关键字 / 名字之间的多个空白 (含 Tab) 一律折成 1 空格
    """
    import re

    # ── 第 0 步: 去除 Tab ──
    # 只对 indent 之后的内容做处理, 否则 indent 中的 2 空格也会被破坏
    for i in range(len(lines)):
        line = lines[i]
        # 跳过前导缩进 (已经是 2 空格, 不含 tab)
        stripped_lead = len(line) - len(line.lstrip(' '))
        lead = line[:stripped_lead]
        rest = line[stripped_lead:]
        # rest 里: tab→1空格, 连续 2 空格以上 → 1 空格
        rest = rest.replace('\t', ' ')
        rest = re.sub(r'  +', ' ', rest)
        lines[i] = lead + rest

    # ── 第 1 步: 压缩位宽括号内多余空格, 统一为 "N : M" ──
    def _normalize_range(line):
        # 处理 [N : M] / [N: M] / [N :M] / [N-1 : 0] / [C_S_AXI_DATA_WIDTH-1 : 0] 等
        line = re.sub(r'\[(\S+)\s*:\s*(\S+)\]', r'[\1 : \2]', line)
        return line

    for i in range(len(lines)):
        lines[i] = _normalize_range(lines[i])

    # ── 第 2 步: 对齐 ──
    # 三组关键字:
    #   DECL_KW  : wire / reg / integer / real / time / realtime / event  (可带位宽)
    #   PORT_KW  : input / output / inout  (端口方向, 可带后续 wire/reg 类型)
    #   ASSIGN_KW: assign  (无位宽)
    # 共享: range 列宽 / name 列宽. 不共享: kw 列宽 (每组独立).
    DECL_KW   = ('wire', 'reg', 'integer', 'real', 'time', 'realtime', 'event', 'logic', 'tri')
    PORT_KW   = ('input', 'output', 'inout')
    ASSIGN_KW = ('assign',)

    # ── 第 2a 步: 全局扫描 ──
    all_decls = {}
    for prefix, is_port in [(kw, True) for kw in PORT_KW] + \
                            [(kw, False) for kw in DECL_KW + ASSIGN_KW]:
        decls = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not re.match(rf'^{prefix}\s+', stripped):
                continue
            if is_port:
                # 端口: "input wire [range] name" or "input [range] name"
                m = re.match(
                    rf'({prefix})(\s+wire|\s+reg|\s+logic)?( +\[[^\]]+\])?( +)(\w+)(.*)',
                    stripped, re.DOTALL)
                if not m:
                    continue
                kw = m.group(1) + (m.group(2) or '')  # "input wire" or "input"
                rng = (m.group(3) or '').strip()
                nm = m.group(5)
                tail = m.group(6).rstrip()
            else:
                m = re.match(
                    rf'({prefix})( +\[[^\]]+\])?( +)(\w+)(.*)',
                    stripped, re.DOTALL)
                if not m:
                    continue
                kw = m.group(1)
                rng = (m.group(2) or '').strip()
                nm = m.group(4)
                tail = m.group(5).rstrip()
            decls.append((i, kw, rng, nm, tail))
        if decls:
            group_id = 'port' if is_port else ('assign' if prefix == 'assign' else 'decl')
            all_decls.setdefault(group_id, {})[prefix] = decls

    # 全局 max_name, max_range, max_kw (跨所有组)
    global_max_name = 0
    global_max_range = 0
    global_max_kw = 0
    for group in all_decls.values():
        for decls in group.values():
            for _, kw, rng, nm, _ in decls:
                global_max_name = max(global_max_name, len(nm))
                global_max_range = max(global_max_range, len(rng))
                global_max_kw = max(global_max_kw, len(kw))

    # ── 第 2b 步: 各组用全局 kw/range/name 列宽重构 ──
    for group_id, group in all_decls.items():
        # assign 组 range=0, 其他组用全局 range
        my_max_range = 0 if group_id == 'assign' else global_max_range

        for prefix, decls in group.items():
            for i, kw, rng, nm, tail in decls:
                nm_pad = ' ' * (global_max_name - len(nm))
                kw_pad = ' ' * (global_max_kw - len(kw))
                if my_max_range:
                    rng_pad = (rng or '').ljust(my_max_range)
                    mid = f' {rng_pad} '
                else:
                    mid = ' '
                new_stripped = f'{kw}{kw_pad}{mid}{nm}{nm_pad}{tail}'.rstrip()
                indent_level = (len(lines[i]) - len(lines[i].lstrip())) // len(indent_str)
                lines[i] = indent_str * indent_level + new_stripped

    return lines


def main():
    parser = argparse.ArgumentParser(description='FPGA 工具箱 (跨平台)')
    parser.add_argument('file', nargs='?', default=None)
    parser.add_argument('-n', '--count', type=int, default=1)
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('--compress', type=str, default=None, metavar='DIR')
    parser.add_argument('--dry-run', action='store_true', default=False)
    parser.add_argument('--no-auto-export', action='store_true', default=False,
                        help='压缩时跳过 Vivado 自动导出 (默认自动导出)')
    parser.add_argument('--git-init', type=str, default=None, metavar='DIR')
    args = parser.parse_args()
    if args.compress:
        compress_project(args.compress, dry_run=args.dry_run,
                         auto_export=not args.no_auto_export)
    elif args.git_init:
        from pathlib import Path
        (Path(args.git_init) / '.gitignore').write_text(
            _generate_fpga_gitignore(), encoding='utf-8')
        print(f'已生成: {Path(args.git_init) / ".gitignore"}')
    elif args.file:
        run_cli(args.file, args.count, args.output)
    else:
        _run_gui()


if __name__ == '__main__':
    main()
