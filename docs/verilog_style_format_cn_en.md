# Verilog Style Format Guide (CN / EN)
# Verilog 代码整理规范（中英双语）

> **Version / 版本**: v1.0  
> **Scope / 适用范围**: Verilog-2001 (RTL / Testbench)  
> **Goal / 目标**: Unify code layout, improve readability, facilitate diff and code review  
> **目标**: 统一代码排版，提升可读性，便于 diff 与代码审查  
> **Note / 说明**: This document ONLY covers formatting — NOT functionality, synthesizability, or naming semantics.  
> **说明**: 本文档**仅**涉及排版格式 —— 不涉及功能正确性、可综合性或命名语义。

---

## Table of Contents / 目录

1. [Basic Layout Rules / 基础排版规则](#1-basic-layout-rules--基础排版规则)
2. [Declaration Block Layout / 声明区排版](#2-declaration-block-layout--声明区排版)
3. [Attribute Layout / 属性排版](#3-attribute-layout--属性排版)
4. [Logical Block Layout / 逻辑块排版](#4-logical-block-layout--逻辑块排版)
5. [Instantiation Layout / 实例化排版](#5-instantiation-layout--实例化排版)
6. [Expression Layout / 表达式排版](#6-expression-layout--表达式排版)
7. [Macro & Conditional Compilation Layout / 宏与条件编译排版](#7-macro--conditional-compilation-layout--宏与条件编译排版)
8. [Comment Layout / 注释排版](#8-comment-layout--注释排版)
9. [Formatting Before & After Comparison / 整理前后对照表](#9-formatting-before--after-comparison--整理前后对照表)
10. [Hard Rules (Red Lines) / 排版红线（禁止项）](#10-hard-rules-red-lines--排版红线禁止项)
11. [Recommended Tools / 推荐工具](#11-recommended-tools--推荐工具)

---

## 1. Basic Layout Rules / 基础排版规则

### 1.1 Indentation / 缩进

**EN**  
Use **2 spaces** for indentation. Tabs are strictly prohibited.

**中文**  
使用 **2 个空格** 缩进。严禁使用 Tab。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
always @(posedge clk) begin
    q <= d;
end

// ✅ Correct / 正确
always @(posedge clk) begin
  q <= d;
end
```

---

### 1.2 Line Width / 行宽

**EN**  
Maximum line width is **100 columns**. Wrap lines with **+2 indentation**.

**中文**  
最大行宽为 **100 列**。换行后额外缩进 **2 空格**。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
assign data_out = (sel == 2'b00) ? a : (sel == 2'b01) ? b : (sel == 2'b10) ? c : d;

// ✅ Correct / 正确
assign data_out =
  (sel == 2'b00) ? a :
  (sel == 2'b01) ? b :
                   c;
```

---

### 1.3 Spacing Rules / 空格规则

| Position / 位置 | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| Around operators / 运算符左右 | Must have space | 必须空格 |
| After `;` | Must have space | 必须空格 |
| After `(` | No space | 无空格 |
| Before `)` | No space | 无空格 |
| After `,` | Must have space | 必须空格 |

**Example / 示例**

```verilog
// ❌ Wrong / 错误
a=b+c;
always@(posedge clk)begin

// ✅ Correct / 正确
a = b + c;
always @(posedge clk) begin
```

---

### 1.4 Blank Line Rules / 空行规则

**EN**  
- Insert **1 blank line** between logical blocks.  
- Insert **2 blank lines** between `always` blocks or module instances.  
- Do NOT use consecutive blank lines (>2).

**中文**  
- 逻辑块之间插入 **1 个空行**。  
- `always` 块之间或模块实例之间插入 **2 个空行**。  
- 禁止连续空行超过 2 行。

**Example / 示例**

```verilog
// ✅ Correct / 正确
reg [7:0] cnt;

always @(posedge clk) begin
  cnt <= cnt + 1;
end


always @(posedge clk) begin
  q <= d;
end
```

---

## 2. Declaration Block Layout / 声明区排版

### 2.1 Module & Port Alignment / 模块与端口对齐

**EN**  
- `(` must be on its own line.  
- One port per line.  
- Align direction / bit-width / name vertically.  
- `);` must be on its own line.

**中文**  
- `(` 独占一行。  
- 每个端口独占一行。  
- 方向 / 位宽 / 名称纵向对齐。  
- `);` 独占一行。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
module fifo(input clk,input rst_n,input [7:0]din,output [7:0]dout);

// ✅ Correct / 正确
module fifo (
  input        clk,
  input        rst_n,
  input  [7:0] din,
  output [7:0] dout
);
```

---

### 2.2 Parameter Declaration / 参数声明

**EN**  
- `parameter` keyword on its own line.  
- Align parameter names and default values.

**中文**  
- `parameter` 关键字独占一行。  
- 参数名与默认值对齐。

```verilog
// ✅ Correct / 正确
module fifo #(
  parameter int DEPTH = 16,
  parameter int WIDTH = 8
)(
  ...
);
```

---

### 2.3 Signal Declaration / 信号声明

**EN**  
- One signal per line.  
- Align types and widths.

**中文**  
- 每行一个信号。  
- 类型和位宽对齐。

```verilog
// ❌ Wrong / 错误
reg [3:0] wr_ptr;reg [3:0] rd_ptr;reg [7:0] mem[0:15];

// ✅ Correct / 正确
reg  [3:0] wr_ptr;
reg  [3:0] rd_ptr;
reg  [7:0] mem [0:15];
wire       full;
wire       empty;
```

---

## 3. Attribute Layout / 属性排版

### 3.1 Core Principle / 核心原则

**EN**  
Attributes belong to the declaration, not to the syntax.  
Always place attributes **above** the declaration they apply to.

**中文**  
属性属于"被声明的对象"，而不是语法本身。  
属性应始终放在**被修饰对象的上方**，独占一行。

---

### 3.2 Port Attributes / 端口属性

**EN**  
- Attribute on its own line, left-aligned with the port.  
- One blank line between ports.  
- Optional: group-related ports with a comment above.

**中文**  
- 属性独占一行，与端口左对齐。  
- 端口之间空一行。  
- 可选：用注释对一组相关端口分组。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
module fifo #(
  parameter DW = 32
)(
  (* mark_debug = "true" *) input        clk,
  (* mark_debug = "true" *) input        valid,
                              output reg ready
);
```

```verilog
// ✅ Correct / 正确
module fifo #(
  parameter int DW = 32
)(
  // Debug signals
  (* mark_debug = "true" *)
  input        clk,

  (* mark_debug = "true" *)
  input        valid,

  output reg   ready
);
```

---

### 3.3 Signal / Variable Attributes / 信号与变量属性

**EN**  
- Attribute must be placed **above** the signal declaration.  
- Left-align with the `reg` / `wire` keyword.  
- Add a comment above the attribute when the purpose is not obvious.

**中文**  
- 属性必须放在信号声明的**上方**。  
- 与 `reg` / `wire` 关键字左对齐。  
- 当目的不明显时，在属性上方加注释。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
reg (* mark_debug="true"*) fsm_state;
wire (* keep="true"*) critical_sig;
```

```verilog
// ✅ Correct / 正确
// FSM state (debug visible)
(* mark_debug = "true" *)
reg [1:0] fsm_state;

// Prevent synthesis optimization
(* keep = "true" *)
wire critical_sig;
```

---

### 3.4 Multiple Attributes / 多属性叠加

**EN**  
- One attribute per line.  
- Stack vertically in logical order (top → bottom):  
  `mark_debug` → `keep` → `max_fanout` / `dont_touch`.  
- Align attribute names (optional but recommended for readability).

**中文**  
- 每行一个属性。  
- 按逻辑顺序纵向堆叠：  
  `mark_debug` → `keep` → `max_fanout` / `dont_touch`。  
- 属性名对齐（可选，但强烈推荐）。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
(* mark_debug="true",keep="true"*)
reg dbg_signal;
```

```verilog
// ✅ Correct (basic) / 正确（基础版）
(* mark_debug = "true" *)
(* keep       = "true" *)
reg dbg_signal;
```

```verilog
// ✅ Correct (aligned) / 正确（对齐版，推荐）
(* mark_debug = "true" *)
(* keep       = "true" *)
(* max_fanout = 16      *)
reg dbg_signal;
```

---

### 3.5 Module-Level Attributes / 模块级属性

**EN**  
- Place before the `module` keyword.  
- Left-align with `module`.  
- Common for `keep_hierarchy`.

**中文**  
- 放在 `module` 关键字之前。  
- 与 `module` 左对齐。  
- 常用于 `keep_hierarchy`。

**Example / 示例**

```verilog
// ❌ Wrong / 错误
(*keep_hierarchy="yes"*)module axis_fifo #(
```

```verilog
// ✅ Correct / 正确
(* keep_hierarchy = "yes" *)
module axis_fifo #(
  parameter DW = 32
)(
  ...
);
```

---

### 3.6 Common Attribute Reference / 常用属性速查

| Attribute / 属性 | Placement / 位置 | Purpose / 用途 |
|---|---|---|
| `(* mark_debug = "true" *)` | Port / Signal / 端口、信号 | Expose signal to Vivado Logic Analyzer / 暴露信号给 Vivado 逻辑分析仪 |
| `(* keep = "true" *)` | Signal / 信号 | Prevent optimization / 防止综合优化掉 |
| `(* keep_hierarchy = "yes" *)` | Module / 模块 | Preserve hierarchy / 保留层次结构 |
| `(* max_fanout = N *)` | Signal / 信号 | Limit fanout / 限制扇出 |
| `(* dont_touch = "true" *)` | Module / Signal / 模块、信号 | Prevent any optimization / 禁止任何优化 |
| `(* ram_style = "block" *)` | Signal (memory) / 信号（存储器） | Force block RAM / 强制使用块 RAM |
| `(* rom_style = "block" *)` | Signal (ROM) / 信号（ROM） | Force block ROM / 强制使用块 ROM |

---

### 3.7 Formatting Before & After (Attribute Focused) / 属性整理前后对照

| Scenario / 场景 | Before / 整理前 | After / 整理后 |
|---|---|---|
| Port attribute / 端口属性 | `(*mark_debug="true"*)input clk` | `(* mark_debug = "true" *)\ninput clk` |
| Multi-attribute / 多属性 | `(*a=1,b=2*)reg x` | `(* a = 1 *)\n(* b = 2 *)\nreg x` |
| Signal attribute / 信号属性 | `wire(*keep="true"*)a` | `(* keep = "true" *)\nwire a` |
| Module attribute / 模块属性 | `(*keep*)module a` | `(* keep *)\nmodule a` |
| Attribute spacing / 属性空格 | `(*mark_debug="true"*)` | `(* mark_debug = "true" *)` |
| Attribute grouping / 属性分组 | `(*a=1*)(*b=2*)reg x` | `(* a = 1 *)\n(* b = 2 *)\nreg x` |

---

### 3.8 Hard Rules for Attributes / 属性排版红线

| # | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| 1 | Attribute must be on its own line | 属性必须独占一行 |
| 2 | Attribute must NOT be on the same line as the declaration | 属性不得与声明同行 |
| 3 | One attribute per line — never comma-separate | 每行一个属性 —— 严禁逗号分隔 |
| 4 | Space after `(` and before `)` in attribute | 属性内 `(` 后和 `)` 前必须有空格 |
| 5 | Space around `=` in attribute | 属性内 `=` 两侧必须有空格 |
| 6 | Attribute must be left-aligned with the keyword below | 属性必须与下方关键字左对齐 |
| 7 | No trailing whitespace after attribute closing `)` | 属性闭括号 `)` 后不得有空格 |

---

## 4. Logical Block Layout / 逻辑块排版

### 4.1 always Block / always 块

**EN**  
- `begin / end` on separate lines.  
- `end` aligns with `always`.  
- Nested `begin` adds 2 more spaces of indentation.

**中文**  
- `begin / end` 各占一行。  
- `end` 与 `always` 对齐。  
- 嵌套 `begin` 再缩进 2 空格。

```verilog
// ❌ Wrong / 错误
always @(posedge clk) begin if(rst) q<=0; else q<=d; end

// ✅ Correct / 正确
always @(posedge clk) begin
  if (rst) begin
    q <= 0;
  end else begin
    q <= d;
  end
end
```

---

### 4.2 if / else / if / else

**EN**  
- `if` condition must have a space after `if`.  
- `else` on its own line (or same line as `end`, but consistent).

**中文**  
- `if` 条件后必须空格。  
- `else` 独占一行（或与 `end` 同行，但全文件一致）。

```verilog
// ✅ Correct / 正确
if (en) begin
  cnt <= cnt + 1'b1;
end else begin
  cnt <= cnt;
end
```

---

### 4.3 case / case

**EN**  
- `case (expr)` — space after `case`.  
- Each case item on its own line.  
- `default` must be present.

**中文**  
- `case (expr)` —— `case` 后空格。  
- 每个 case 项独占一行。  
- 必须有 `default`。

```verilog
// ✅ Correct / 正确
case (state)
  IDLE: begin
    next_state = RUN;
  end
  RUN: begin
    next_state = DONE;
  end
  default: begin
    next_state = IDLE;
  end
endcase
```

---

### 4.4 for Loop / for 循环

**EN**  
- Loop variable declaration on its own line.  
- `begin / end` on separate lines.

**中文**  
- 循环变量声明独占一行。  
- `begin / end` 各占一行。

```verilog
// ✅ Correct / 正确
integer i;
always @(posedge clk) begin
  for (i = 0; i < 4; i = i + 1) begin
    mem[i] <= din[i];
  end
end
```

---

### 4.5 generate / generate

**EN**  
- `generate / endgenerate` on separate lines.  
- `for` inside `generate` follows the same rules as above.

**中文**  
- `generate / endgenerate` 各占一行。  
- 内部 `for` 遵循上述规则。

```verilog
// ✅ Correct / 正确
genvar i;
generate
  for (i = 0; i < 4; i = i + 1) begin : GEN_FF
    dff u_dff (
      .clk (clk),
      .d   (din[i]),
      .q   (dout[i])
    );
  end
endgenerate
```

---

### 4.6 initial Block / initial 块

**EN**  
- Same formatting rules as `always`.  
- Used in testbenches.

**中文**  
- 格式规则同 `always`。  
- 用于 testbench。

```verilog
// ✅ Correct / 正确
initial begin
  clk = 0;
  rst_n = 0;
  #100 rst_n = 1;
end
```

---

## 5. Instantiation Layout / 实例化排版

### 5.1 Module Instantiation / 模块实例化

**EN**  
- Instance name on its own line.  
- Port connections: one per line, aligned.

**中文**  
- 实例名独占一行。  
- 端口连接：每行一个，对齐。

```verilog
// ❌ Wrong / 错误
fifo u_fifo(clk,rst_n,din,dout,full,empty);

// ✅ Correct / 正确
fifo u_fifo (
  .clk   (clk),
  .rst_n (rst_n),
  .din   (din),
  .dout  (dout),
  .full  (full),
  .empty (empty)
);
```

---

### 5.2 Parameterized Instantiation / 带参数实例化

**EN**  
- Parameters before ports.  
- Align parameter names and values.

**中文**  
- 参数在前，端口在后。  
- 参数名与值对齐。

```verilog
// ✅ Correct / 正确
fifo #(
  .DEPTH (16),
  .WIDTH (8)
) u_fifo (
  .clk   (clk),
  .rst_n (rst_n),
  .din   (din),
  .dout  (dout)
);
```

---

## 6. Expression Layout / 表达式排版

### 6.1 Arithmetic & Logical Expressions / 算术与逻辑表达式

**EN**  
- Space around operators.  
- Parentheses for clarity — no penalty.

**中文**  
- 运算符两侧空格。  
- 括号增加可读性 —— 无惩罚。

```verilog
// ❌ Wrong / 错误
if((a==b)&&(c!=d))begin

// ✅ Correct / 正确
if ((a == b) && (c != d)) begin
```

---

### 6.2 Concatenation / 拼接

**EN**  
- Short: `{}` with spaces after commas.  
- Long: one element per line.

**中文**  
- 短：使用 `{}`，逗号后空格。  
- 长：每个元素一行。

```verilog
// Short / 短
data <= {a, b, c};

// Long / 长
data <= {
  a,
  b,
  c,
  d
};
```

---

### 6.3 Ternary Operator / 三目运算符

**EN**  
- Always wrap to multiple lines for readability.  
- Align `?` and `:`.

**中文**  
- 始终换行书写以提高可读性。  
- `?` 与 `:` 对齐。

```verilog
// ✅ Correct / 正确
assign dout =
  (sel == 2'b00) ? a :
  (sel == 2'b01) ? b :
  (sel == 2'b10) ? c :
                   d;
```

---

## 7. Macro & Conditional Compilation Layout / 宏与条件编译排版

### 7.1 `ifdef / `endif / `ifdef / `endif

**EN**  
- `` `ifdef `` and `` `endif `` on separate lines.  
- Indent content inside.

**中文**  
- `` `ifdef `` 与 `` `endif `` 各占一行。  
- 内部内容缩进。

```verilog
// ✅ Correct / 正确
`ifdef SIMULATION
  initial begin
    $display("Simulation mode");
  end
`endif
```

---

### 7.2 `define / `define

**EN**  
- One macro per line.  
- Parentheses around arguments.

**中文**  
- 每行一个宏。  
- 参数加括号。

```verilog
// ❌ Wrong / 错误
`define MAX(a,b) a>b?a:b

// ✅ Correct / 正确
`define MAX(a, b) ((a) > (b) ? (a) : (b))
```

---

## 8. Comment Layout / 注释排版

### 8.1 File Header / 文件头注释

**EN**  
- Mandatory for all files.  
- Format: centered banner with key info.

**中文**  
- 所有文件强制要求。  
- 格式：居中分隔线 + 关键信息。

```verilog
// ----------------------------------------------------------------------
// Module        : fifo
// Project       : SOC_CORE
// Author        : your_name
// Created       : 2026-01-15
// Description   : FIFO buffer
// ----------------------------------------------------------------------
```

---

### 8.2 Block Comments / 块注释

**EN**  
- Place above the code block.  
- One blank line before and after.

**中文**  
- 放在代码块上方。  
- 前后各空一行。

```verilog
// FSM state register
always @(posedge clk) begin
  state <= next_state;
end
```

---

### 8.3 Inline Comments / 行尾注释

**EN**  
- Use sparingly.  
- Must align vertically if multiple inline comments are used.

**中文**  
- 谨慎使用。  
- 多个行尾注释必须纵向对齐。

```verilog
// ✅ Correct / 正确
reg [7:0] cnt;     // 8-bit counter
reg       wr_en;    // write enable
reg       rd_en;    // read enable
```

---

### 8.4 Multi-line Comments / 多行注释

**EN**  
- Use `/* */` for multi-line explanations.  
- Each line starts with ` *`.

**中文**  
- 多行说明使用 `/* */`。  
- 每行以 ` *` 开头。

```verilog
/*
 * State machine description:
 * IDLE -> WAIT -> RUN -> DONE
 */
```

---

## 9. Formatting Before & After Comparison / 整理前后对照表

| Syntax / 语法 | Before / 整理前 | After / 整理后 |
|---|---|---|
| module | `module a(b,c);` | `module a (\n  b,\n  c\n);` |
| always | `always@(posedge clk)begin` | `always @(posedge clk) begin` |
| assign | `assign a=b+c;` | `assign a = b + c;` |
| if | `if(a)begin` | `if (a) begin` |
| case | `case(x)0:...` | `case (x)\n  0: begin\n  end\nendcase` |
| instance | `.a(a),.b(b)` | `.a (a),\n.b (b)` |
| parameter | `parameter DW=32,AW=8` | `parameter DW = 32,\nparameter AW = 8` |
| for | `for(i=0;i<4;i=i+1)begin` | `for (i = 0; i < 4; i = i + 1) begin` |
| ternary | `a?b:c` | `a ?\nb :\nc` |
| concatenation | `{a,b,c,d}` | `{\na,\nb,\nc,\nd\n}` |
| `ifdef | `` `ifdef SIM\ncode\n`endif `` | `` `ifdef SIM\n  code\n`endif `` |
| initial | `initial clk=0;rst_n=0;` | `initial begin\n  clk = 0;\n  rst_n = 0;\nend` |
| attribute (port) / 属性（端口） | `(*mark_debug="true"*)input clk` | `(* mark_debug = "true" *)\ninput clk` |
| attribute (signal) / 属性（信号） | `reg(*mark_debug="true"*)x` | `(* mark_debug = "true" *)\nreg x` |
| attribute (multi) / 属性（多属性） | `(*a=1,b=2*)reg x` | `(* a = 1 *)\n(* b = 2 *)\nreg x` |
| attribute (module) / 属性（模块） | `(*keep*)module a` | `(* keep *)\nmodule a` |

---

## 10. Hard Rules (Red Lines) / 排版红线（禁止项）

| # | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| 1 | **No Tabs** — spaces only | **禁止 Tab** —— 仅使用空格 |
| 2 | **No multiple statements per line** | **一行只能有一条语句** |
| 3 | `begin` must be on its own line | `begin` 必须独占一行 |
| 4 | `end` must be on its own line | `end` 必须独占一行 |
| 5 | No misaligned parameters or ports | 参数和端口必须对齐 |
| 6 | No trailing whitespace | 禁止行尾多余空格 |
| 7 | No comment obscuring code | 注释不得遮挡代码 |
| 8 | No inconsistent indentation | 缩进必须一致 |
| 9 | No spaces between `(` and first argument | `(` 后不能有空格 |
| 10 | No spaces before `)` | `)` 前不能有空格 |
| 11 | Attribute must be on its own line, not inline | 属性必须独占一行，不得内联 |
| 12 | No comma-separated attributes — one per line | 属性不得逗号分隔，每行一个 |
| 13 | Space around `=` in attribute expressions | 属性内 `=` 两侧必须有空格 |

---

## 11. Recommended Tools / 推荐工具

| Tool / 工具 | Purpose / 用途 | Language / 语言 |
|---|---|---|
| **Verible** | Auto-formatting / 自动格式化 | Verilog / SV |
| **Emacs `verilog-mode`** | Indentation / 缩进 | Verilog |
| **VS Code + Verilog-HDL** | Editor support / 编辑器支持 | Verilog / SV |
| **Icarus Verilog** | Simulation / 仿真 | Verilog |

---

## Appendix: Quick Reference Card / 附录：快速参考卡

```
Indent / 缩进:     2 spaces / 2 空格
Line width / 行宽: 100 columns / 100 列
Brackets / 括号:   begin/end on separate lines / begin/end 各占一行
Spacing / 空格:    Around all operators / 运算符两侧
Blank lines / 空行: 1 between blocks, 2 between always / 逻辑块间1行，always间2行
Comments / 注释:   // for single, /* */ for multi / 单行用//，多行用/* */
```

---

*End of Document / 文档结束*
