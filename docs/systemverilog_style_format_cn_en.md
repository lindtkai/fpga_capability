# SystemVerilog Style Format Guide (CN / EN)
# SystemVerilog 代码整理规范（中英双语）

> **Version / 版本**: v1.0  
> **Scope / 适用范围**: SystemVerilog IEEE 1800 (RTL / Testbench / Verification)  
> **Goal / 目标**: Unify code layout, improve readability, facilitate diff and code review  
> **目标**: 统一代码排版，提升可读性，便于 diff 与代码审查  
> **Note / 说明**: This document ONLY covers formatting — NOT functionality, synthesizability, or naming semantics.  
> **说明**: 本文档**仅**涉及排版格式 —— 不涉及功能正确性、可综合性或命名语义。

---

## Table of Contents / 目录

1. [Basic Layout Rules / 基础排版规则](#1-basic-layout-rules--基础排版规则-2)
2. [Declaration Block Layout / 声明区排版](#2-declaration-block-layout--声明区排版-2)
3. [Attribute Layout / 属性排版](#3-attribute-layout--属性排版-1)
4. [Logical Block Layout / 逻辑块排版](#4-logical-block-layout--逻辑块排版)
5. [Instantiation & Interface Layout / 实例化与接口排版](#5-instantiation--interface-layout--实例化与接口排版)
6. [Expression Layout / 表达式排版](#6-expression-layout--表达式排版)
7. [Enum, Struct & Typedef Layout / 枚举、结构体与类型定义排版](#7-enum-struct--typedef-layout--枚举结构体与类型定义排版)
8. [Package, Import & Attribute Layout / Package、Import 与属性排版](#8-package-import--attribute-layout--packageimport-与属性排版)
9. [Assertion & Constraint Layout / 断言与约束排版](#9-assertion--constraint-layout--断言与约束排版)
10. [Comment Layout / 注释排版](#10-comment-layout--注释排版)
11. [Formatting Before & After Comparison / 整理前后对照表](#11-formatting-before--after-comparison--整理前后对照表)
12. [Hard Rules (Red Lines) / 排版红线（禁止项）](#12-hard-rules-red-lines--排版红线禁止项)
13. [Recommended Tools / 推荐工具](#13-recommended-tools--推荐工具)

---

## 1. Basic Layout Rules / 基础排版规则

### 1.1 Indentation / 缩进

**EN**  
Use **2 spaces** for indentation. Tabs are strictly prohibited.

**中文**  
使用 **2 个空格** 缩进。严禁使用 Tab。

**Example / 示例**

```systemverilog
// ❌ Wrong / 错误
always_ff @(posedge clk) begin
    q <= d;
end

// ✅ Correct / 正确
always_ff @(posedge clk) begin
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

```systemverilog
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
| After `:` (in typedef) / `:` 后（typedef 中） | Must have space | 必须空格 |
| After `(` | No space | 无空格 |
| Before `)` | No space | 无空格 |
| After `,` | Must have space | 必须空格 |
| Around `->` / `->` 两侧 | Must have space | 必须空格 |

**Example / 示例**

```systemverilog
// ❌ Wrong / 错误
a=b+c;
always_ff@(posedge clk)begin

// ✅ Correct / 正确
a = b + c;
always_ff @(posedge clk) begin
```

---

### 1.4 Blank Line Rules / 空行规则

**EN**  
- Insert **1 blank line** between logical blocks.  
- Insert **2 blank lines** between `always_ff` / `always_comb` blocks.  
- Do NOT use consecutive blank lines (>2).

**中文**  
- 逻辑块之间插入 **1 个空行**。  
- `always_ff` / `always_comb` 块之间插入 **2 个空行**。  
- 禁止连续空行超过 2 行。

```systemverilog
// ✅ Correct / 正确
logic [7:0] cnt;

always_ff @(posedge clk) begin
  cnt <= cnt + 1;
end


always_comb begin
  dout = din;
end
```

---

## 2. Declaration Block Layout / 声明区排版

### 2.1 Module & Port Alignment / 模块与端口对齐

**EN**  
- `(` must be on its own line.  
- One port per line.  
- Align direction / type / bit-width / name vertically.  
- `);` must be on its own line.

**中文**  
- `(` 独占一行。  
- 每个端口独占一行。  
- 方向 / 类型 / 位宽 / 名称纵向对齐。  
- `);` 独占一行。

```systemverilog
// ❌ Wrong / 错误
module fifo(input logic clk,input logic rst_n,input logic [7:0]din,output logic [7:0]dout);

// ✅ Correct / 正确
module fifo (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [7:0]  din,
  output logic [7:0]  dout
);
```

---

### 2.2 Parameter Declaration / 参数声明

**EN**  
- `parameter` or `localparam` on its own line.  
- Align parameter names and default values.

**中文**  
- `parameter` 或 `localparam` 独占一行。  
- 参数名与默认值对齐。

```systemverilog
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

```systemverilog
// ❌ Wrong / 错误
logic [3:0] wr_ptr;logic [3:0] rd_ptr;logic full;logic empty;

// ✅ Correct / 正确
logic [3:0] wr_ptr;
logic [3:0] rd_ptr;
logic       full;
logic       empty;
```

---

## 3. Attribute Layout / 属性排版

### 3.1 Core Principle / 核心原则

**EN**  
Attributes belong to the declaration, not to the syntax.  
Always place attributes **above** the declaration they apply to.  
SystemVerilog uses the same `(* ... *)` syntax as Verilog-2001, but attributes may also appear on `interface`, `modport`, `class`, and `struct` members.

**中文**  
属性属于"被声明的对象"，而不是语法本身。  
属性应始终放在**被修饰对象的上方**，独占一行。  
SystemVerilog 使用与 Verilog-2001 相同的 `(* ... *)` 语法，但属性也可出现在 `interface`、`modport`、`class` 和 `struct` 成员上。

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

```systemverilog
// ❌ Wrong / 错误
module fifo #(
  parameter DW = 32
)(
  (* mark_debug = "true" *) input logic        clk,
  (* mark_debug = "true" *) input logic        valid,
                              output logic       ready
);
```

```systemverilog
// ✅ Correct / 正确
module fifo #(
  parameter int DW = 32
)(
  // Debug signals
  (* mark_debug = "true" *)
  input  logic        clk,

  (* mark_debug = "true" *)
  input  logic        valid,

  output logic       ready
);
```

---

### 3.3 Signal / Variable Attributes / 信号与变量属性

**EN**  
- Attribute must be placed **above** the signal declaration.  
- Left-align with the `logic` / `bit` / `var` keyword.  
- Add a comment above when the purpose is not obvious.

**中文**  
- 属性必须放在信号声明的**上方**。  
- 与 `logic` / `bit` / `var` 关键字左对齐。  
- 当目的不明显时，在属性上方加注释。

**Example / 示例**

```systemverilog
// ❌ Wrong / 错误
logic (* mark_debug="true"*) fsm_state;
wire  (* keep="true"*) critical_sig;
```

```systemverilog
// ✅ Correct / 正确
// FSM state (debug visible)
(* mark_debug = "true" *)
logic [1:0] fsm_state;

// Prevent synthesis optimization
(* keep = "true" *)
logic critical_sig;
```

---

### 3.4 Multiple Attributes / 多属性叠加

**EN**  
- One attribute per line.  
- Stack vertically in logical order:  
  `mark_debug` → `keep` → `max_fanout` / `dont_touch`.  
- Align attribute names (optional but recommended).

**中文**  
- 每行一个属性。  
- 按逻辑顺序纵向堆叠：  
  `mark_debug` → `keep` → `max_fanout` / `dont_touch`。  
- 属性名对齐（可选，但强烈推荐）。

**Example / 示例**

```systemverilog
// ❌ Wrong / 错误
(* mark_debug="true",keep="true"*)
logic dbg_signal;
```

```systemverilog
// ✅ Correct (basic) / 正确（基础版）
(* mark_debug = "true" *)
(* keep       = "true" *)
logic dbg_signal;
```

```systemverilog
// ✅ Correct (aligned) / 正确（对齐版，推荐）
(* mark_debug = "true" *)
(* keep       = "true" *)
(* max_fanout = 16      *)
logic dbg_signal;
```

---

### 3.5 Module / Interface / Program Attributes / 模块、接口、Program 属性

**EN**  
- Place before the `module` / `interface` / `program` keyword.  
- Left-align with the keyword.  
- Common for `keep_hierarchy`.

**中文**  
- 放在 `module` / `interface` / `program` 关键字之前。  
- 与关键字左对齐。  
- 常用于 `keep_hierarchy`。

**Example / 示例**

```systemverilog
// ❌ Wrong / 错误
(*keep_hierarchy="yes"*)interface axi_if #(parameter DW=32)();
```

```systemverilog
// ✅ Correct / 正确
(* keep_hierarchy = "yes" *)
interface axi_if #(
  parameter int DW = 32
)();
  logic [DW-1:0] data;
  logic          valid;
  logic          ready;
endinterface
```

---

### 3.6 Modport Attributes / Modport 属性

**EN**  
- Place attribute **before** the `modport` keyword.  
- One attribute per line.

**中文**  
- 将属性放在 `modport` 关键字**之前**。  
- 每行一个属性。

**Example / 示例**

```systemverilog
// ✅ Correct / 正确
(* mark_debug = "true" *)
modport master (
  output data,
  output valid,
  input  ready
);
```

---

### 3.7 Struct Member Attributes / 结构体成员属性

**EN**  
- Place attribute **before** the struct member declaration.  
- One attribute per line.  
- Left-align with the member type.

**中文**  
- 将属性放在结构体成员声明的**之前**。  
- 每行一个属性。  
- 与成员类型左对齐。

**Example / 示例**

```systemverilog
// ✅ Correct / 正确
typedef struct packed {
  // Debug this field
  (* mark_debug = "true" *)
  logic [31:0] addr;
  logic [31:0] data;
  logic         wr_en;
} bus_pkt_t;
```

---

### 3.8 Class Property Attributes / 类属性

**EN**  
- Place attribute **before** the property declaration.  
- One attribute per line.

**中文**  
- 将属性放在属性声明的**之前**。  
- 每行一个属性。

**Example / 示例**

```systemverilog
// ✅ Correct / 正确
class my_class;
  (* rand = "true" *)
  bit [31:0] data;

  function new();
    this.data = 0;
  endfunction
endclass
```

---

### 3.9 Common Attribute Reference / 常用属性速查

| Attribute / 属性 | Placement / 位置 | Purpose / 用途 |
|---|---|---|
| `(* mark_debug = "true" *)` | Port / Signal / 端口、信号 | Expose signal to Vivado Logic Analyzer / 暴露信号给 Vivado 逻辑分析仪 |
| `(* keep = "true" *)` | Signal / 信号 | Prevent optimization / 防止综合优化掉 |
| `(* keep_hierarchy = "yes" *)` | Module / Interface / 模块、接口 | Preserve hierarchy / 保留层次结构 |
| `(* max_fanout = N *)` | Signal / 信号 | Limit fanout / 限制扇出 |
| `(* dont_touch = "true" *)` | Module / Signal / 模块、信号 | Prevent any optimization / 禁止任何优化 |
| `(* ram_style = "block" *)` | Signal (memory) / 信号（存储器） | Force block RAM / 强制使用块 RAM |
| `(* rom_style = "block" *)` | Signal (ROM) / 信号（ROM） | Force block ROM / 强制使用块 ROM |
| `(* async_reg = "true" *)` | Signal / 信号 | Mark as asynchronous register / 标记为异步寄存器 |
| `(* shreg_extract = "no" *)` | Signal / 信号 | Prevent SRL extraction / 禁止 SRL 推断 |
| `(* mark_debug = "true" *)` | Modport / 结构体成员 | Debug visibility / 调试可见性 |

---

### 3.10 Formatting Before & After (Attribute Focused) / 属性整理前后对照

| Scenario / 场景 | Before / 整理前 | After / 整理后 |
|---|---|---|
| Port attribute / 端口属性 | `(*mark_debug="true"*)input logic clk` | `(* mark_debug = "true" *)\ninput logic clk` |
| Multi-attribute / 多属性 | `(*a=1,b=2*)logic x` | `(* a = 1 *)\n(* b = 2 *)\nlogic x` |
| Signal attribute / 信号属性 | `logic(*keep="true"*)a` | `(* keep = "true" *)\nlogic a` |
| Module attribute / 模块属性 | `(*keep*)module a` | `(* keep *)\nmodule a` |
| Interface attribute / 接口属性 | `(*keep*)interface a;` | `(* keep *)\ninterface a;` |
| Modport attribute / Modport 属性 | `(*mark_debug*)modport m(...)` | `(* mark_debug = "true" *)\nmodport m(...)` |
| Struct member attribute / 结构体成员属性 | `logic(*mark_debug*)a` | `(* mark_debug = "true" *)\nlogic a` |
| Class property attribute / 类属性 | `bit(*rand*)data` | `(* rand = "true" *)\nbit data` |
| Attribute spacing / 属性空格 | `(*mark_debug="true"*)` | `(* mark_debug = "true" *)` |
| Attribute grouping / 属性分组 | `(*a=1*)(*b=2*)logic x` | `(* a = 1 *)\n(* b = 2 *)\nlogic x` |

---

### 3.11 Hard Rules for Attributes / 属性排版红线

| # | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| 1 | Attribute must be on its own line | 属性必须独占一行 |
| 2 | Attribute must NOT be on the same line as the declaration | 属性不得与声明同行 |
| 3 | One attribute per line — never comma-separate | 每行一个属性 —— 严禁逗号分隔 |
| 4 | Space after `(` and before `)` in attribute | 属性内 `(` 后和 `)` 前必须有空格 |
| 5 | Space around `=` in attribute | 属性内 `=` 两侧必须有空格 |
| 6 | Attribute must be left-aligned with the keyword below | 属性必须与下方关键字左对齐 |
| 7 | No trailing whitespace after attribute closing `)` | 属性闭括号 `)` 后不得有空格 |
| 8 | Attribute must precede modport / struct member / class property | 属性必须在 modport / 结构体成员 / 类属性之前 |

---

## 4. Logical Block Layout / 逻辑块排版

### 4.1 always_ff Block / always_ff 块

**EN**  
- Use `always_ff` for sequential logic.  
- `begin / end` on separate lines.  
- `end` aligns with `always_ff`.

**中文**  
- 时序逻辑使用 `always_ff`。  
- `begin / end` 各占一行。  
- `end` 与 `always_ff` 对齐。

```systemverilog
// ❌ Wrong / 错误
always_ff @(posedge clk or negedge rst_n) begin if(!rst_n) cnt<='0; else cnt<=cnt+1; end

// ✅ Correct / 正确
always_ff @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    cnt <= '0;
  end else begin
    cnt <= cnt + 1'd1;
  end
end
```

---

### 4.2 always_comb Block / always_comb 块

**EN**  
- Use `always_comb` for combinational logic.  
- Same formatting as `always_ff`.

**中文**  
- 组合逻辑使用 `always_comb`。  
- 格式同 `always_ff`。

```systemverilog
// ✅ Correct / 正确
always_comb begin
  dout = din + cnt;
end
```

---

### 4.3 always_latch Block / always_latch 块

**EN**  
- Use `always_latch` for intentional latches.  
- Same formatting rules.

**中文**  
- 有意使用锁存器时用 `always_latch`。  
- 格式规则相同。

```systemverilog
// ✅ Correct / 正确
always_latch @(en) begin
  if (en) begin
    q <= d;
  end
end
```

---

### 4.4 if / else / if / else

**EN**  
- `if` condition must have a space after `if`.  
- `else` on its own line.

**中文**  
- `if` 条件后必须空格。  
- `else` 独占一行。

```systemverilog
// ✅ Correct / 正确
if (en) begin
  cnt <= cnt + 1'd1;
end else begin
  cnt <= cnt;
end
```

---

### 4.5 case / case

**EN**  
- `case (expr)` — space after `case`.  
- Each case item on its own line.  
- `default` must be present.

**中文**  
- `case (expr)` —— `case` 后空格。  
- 每个 case 项独占一行。  
- 必须有 `default`。

```systemverilog
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

### 4.6 for Loop / for 循环

**EN**  
- Loop variable declaration on its own line (use `int` or `var`).  
- `begin / end` on separate lines.

**中文**  
- 循环变量声明独占一行（使用 `int` 或 `var`）。  
- `begin / end` 各占一行。

```systemverilog
// ✅ Correct / 正确
for (int i = 0; i < 4; i = i + 1) begin
  mem[i] <= din[i];
end
```

---

### 4.7 foreach Loop / foreach 循环

**EN**  
- `foreach` on its own line.  
- Array name and index in parentheses.

**中文**  
- `foreach` 独占一行。  
- 数组名和索引在括号内。

```systemverilog
// ✅ Correct / 正确
foreach (mem[i]) begin
  mem[i] <= '0;
end
```

---

### 4.8 generate / generate

**EN**  
- `generate / endgenerate` on separate lines.  
- Label the generate block.

**中文**  
- `generate / endgenerate` 各占一行。  
- 给 generate 加标签。

```systemverilog
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

### 4.9 initial Block / initial 块

**EN**  
- Same formatting rules as `always_comb`.  
- Used in testbenches.

**中文**  
- 格式规则同 `always_comb`。  
- 用于 testbench。

```systemverilog
// ✅ Correct / 正确
initial begin
  clk = 0;
  rst_n = 0;
  #100 rst_n = 1;
end
```

---

### 4.10 final Block / final 块

**EN**  
- Same formatting rules.  
- Used for end-of-simulation tasks.

**中文**  
- 格式规则相同。  
- 用于仿真结束时的任务。

```systemverilog
// ✅ Correct / 正确
final begin
  $display("Simulation finished");
end
```

---

## 5. Instantiation & Interface Layout / 实例化与接口排版

### 5.1 Module Instantiation / 模块实例化

**EN**  
- Instance name on its own line.  
- Port connections: one per line, aligned.  
- Use `.port (signal)` format.

**中文**  
- 实例名独占一行。  
- 端口连接：每行一个，对齐。  
- 使用 `.port (signal)` 格式。

```systemverilog
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

```systemverilog
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

### 4.3 Interface Instantiation / 接口实例化

**EN**  
- Interface name on its own line.  
- Modport on its own line if specified.

**中文**  
- 接口名独占一行。  
- 如有 modport，独占一行。

```systemverilog
// ✅ Correct / 正确
axi_if #(
  .DW (32)
) u_axi_if (
  .clk   (clk),
  .rst_n (rst_n)
);
```

---

## 5. Expression Layout / 表达式排版

### 5.1 Arithmetic & Logical Expressions / 算术与逻辑表达式

**EN**  
- Space around operators.  
- Parentheses for clarity.

**中文**  
- 运算符两侧空格。  
- 括号增加可读性。

```systemverilog
// ❌ Wrong / 错误
if((a==b)&&(c!=d))begin

// ✅ Correct / 正确
if ((a == b) && (c != d)) begin
```

---

### 5.2 Concatenation / 拼接

**EN**  
- Short: `{}` with spaces after commas.  
- Long: one element per line.

**中文**  
- 短：使用 `{}`，逗号后空格。  
- 长：每个元素一行。

```systemverilog
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

### 5.3 Ternary Operator / 三目运算符

**EN**  
- Always wrap to multiple lines.  
- Align `?` and `:`.

**中文**  
- 始终换行书写。  
- `?` 与 `:` 对齐。

```systemverilog
// ✅ Correct / 正确
assign dout =
  (sel == 2'b00) ? a :
  (sel == 2'b01) ? b :
  (sel == 2'b10) ? c :
                   d;
```

---

### 5.4 Casting / 类型转换

**EN**  
- Cast type and expression separated by space.  
- Parentheses around the expression.

**中文**  
- 转换类型和表达式之间空格。  
- 表达式加括号。

```systemverilog
// ✅ Correct / 正确
int_val = int'(unsigned_val);
```

---

## 6. Enum, Struct & Typedef Layout / 枚举、结构体与类型定义排版

### 6.1 typedef enum / 枚举类型定义

**EN**  
- `typedef enum` on its own line.  
- One enum value per line.  
- Align assignment operators.

**中文**  
- `typedef enum` 独占一行。  
- 每行一个枚举值。  
- 赋值符号对齐。

```systemverilog
// ❌ Wrong / 错误
typedef enum logic[1:0]{IDLE=2'b00,LOAD=2'b01,RUN=2'b10}fsm_e;

// ✅ Correct / 正确
typedef enum logic [1:0] {
  IDLE = 2'b00,
  LOAD = 2'b01,
  RUN  = 2'b10
} fsm_e;
```

---

### 6.2 typedef struct / 结构体类型定义

**EN**  
- `typedef struct` on its own line.  
- One member per line.  
- Align types and names.

**中文**  
- `typedef struct` 独占一行。  
- 每行一个成员。  
- 类型和名称对齐。

```systemverilog
// ✅ Correct / 正确
typedef struct packed {
  logic [31:0] addr;
  logic [31:0] data;
  logic        wr_en;
  logic        rd_en;
} bus_pkt_t;
```

---

### 6.3 typedef (Simple) / 简单类型定义

**EN**  
- `typedef` on its own line.  
- Align original type and new type name.

**中文**  
- `typedef` 独占一行。  
- 原类型和新类型名对齐。

```systemverilog
// ✅ Correct / 正确
typedef logic [7:0]  byte_t;
typedef logic [31:0] word_t;
```

---

## 7. Package & Import Layout / Package 与 Import 排版

### 7.1 Package Declaration / 包声明

**EN**  
- `package / endpackage` on separate lines.  
- One declaration per line inside.

**中文**  
- `package / endpackage` 各占一行。  
- 内部每行一个声明。

```systemverilog
// ✅ Correct / 正确
package common_pkg;
  parameter int DATA_WIDTH = 32;
  typedef logic [DATA_WIDTH-1:0] data_t;
  typedef enum logic [1:0] {
    IDLE = 2'b00,
    RUN  = 2'b01
  } state_e;
endpackage
```

---

### 7.2 Import Statement / 导入语句

**EN**  
- One `import` per line.  
- Wildcard `::*` aligned.

**中文**  
- 每行一个 `import`。  
- 通配符 `::*` 对齐。

```systemverilog
// ❌ Wrong / 错误
import common_pkg::*;import axi_pkg::*;

// ✅ Correct / 正确
import common_pkg::*;
import axi_pkg::*;
```

---

## 8. Assertion & Constraint Layout / 断言与约束排版

### 8.1 Assertion / 断言

**EN**  
- `assert` on its own line.  
- Condition in parentheses, separated by space.

**中文**  
- `assert` 独占一行。  
- 条件在括号内，空格分隔。

```systemverilog
// ✅ Correct / 正确
assert (req |-> grant)
  else $error("Grant not asserted");
```

---

### 8.2 Constraint / 约束

**EN**  
- `constraint` block on its own line.  
- One constraint expression per line.

**中文**  
- `constraint` 块独占一行。  
- 每行一个约束表达式。

```systemverilog
// ✅ Correct / 正确
constraint addr_align_c {
  addr % 4 == 0;
  data inside {[0:255]};
}
```

---

## 9. Comment Layout / 注释排版

### 9.1 File Header / 文件头注释

**EN**  
- Mandatory for all files.  
- Format: centered banner with key info.

**中文**  
- 所有文件强制要求。  
- 格式：居中分隔线 + 关键信息。

```systemverilog
// ----------------------------------------------------------------------
// Module        : fifo
// Project       : SOC_CORE
// Author        : your_name
// Created       : 2026-01-15
// Description   : FIFO buffer
// ----------------------------------------------------------------------
```

---

### 9.2 Block Comments / 块注释

**EN**  
- Place above the code block.  
- One blank line before and after.

**中文**  
- 放在代码块上方。  
- 前后各空一行。

```systemverilog
// FSM state register
always_ff @(posedge clk) begin
  state <= next_state;
end
```

---

### 9.3 Inline Comments / 行尾注释

**EN**  
- Use sparingly.  
- Must align vertically if multiple inline comments are used.

**中文**  
- 谨慎使用。  
- 多个行尾注释必须纵向对齐。

```systemverilog
// ✅ Correct / 正确
logic [7:0] cnt;       // 8-bit counter
logic       wr_en;      // write enable
logic       rd_en;      // read enable
```

---

### 9.4 Multi-line Comments / 多行注释

**EN**  
- Use `/* */` for multi-line explanations.  
- Each line starts with ` *`.

**中文**  
- 多行说明使用 `/* */`。  
- 每行以 ` *` 开头。

```systemverilog
/*
 * State machine description:
 * IDLE -> WAIT -> RUN -> DONE
 */
```

---

## 10. Formatting Before & After Comparison / 整理前后对照表

| Syntax / 语法 | Before / 整理前 | After / 整理后 |
|---|---|---|
| module | `module a(b,c);` | `module a (\n  b,\n  c\n);` |
| always_ff | `always_ff@(posedge clk)begin` | `always_ff @(posedge clk) begin` |
| always_comb | `always_comb begin a=b+c;end` | `always_comb begin\n  a = b + c;\nend` |
| assign | `assign a=b+c;` | `assign a = b + c;` |
| if | `if(a)begin` | `if (a) begin` |
| case | `case(x)0:...` | `case (x)\n  0: begin\n  end\nendcase` |
| instance | `.a(a),.b(b)` | `.a (a),\n.b (b)` |
| parameter | `parameter DW=32,AW=8` | `parameter DW = 32,\nparameter AW = 8` |
| for | `for(i=0;i<4;i=i+1)begin` | `for (i = 0; i < 4; i = i + 1) begin` |
| typedef enum | `typedef enum{IDLE,LOAD}fsm_e;` | `typedef enum {\n  IDLE,\n  LOAD\n} fsm_e;` |
| typedef struct | `typedef struct{logic a;logic b;}t;` | `typedef struct packed {\n  logic a;\n  logic b;\n} t;` |
| package | `package p;...endpackage` | `package p;\n  ...\nendpackage` |
| import | `import p::*;import q::*;` | `import p::*;\nimport q::*;` |
| assertion | `assert(a|b)else$error;` | `assert (a |=> b)\n  else $error;` |
| ternary | `a?b:c` | `a ?\nb :\nc` |
| concatenation | `{a,b,c,d}` | `{\na,\nb,\nc,\nd\n}` |
| foreach | `foreach(mem[i])begin` | `foreach (mem[i]) begin` |
| generate | `generate for(i...` | `generate\n  for (i ...\nendgenerate` |
| interface | `axi_if u();` | `axi_if (\n  .clk (clk)\n);` |
| constraint | `constraint c{a==0;}` | `constraint c {\n  a == 0;\n}` |

---

## 11. Hard Rules (Red Lines) / 排版红线（禁止项）

| # | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| 1 | **No Tabs** — spaces only | **禁止 Tab** —— 仅使用空格 |
| 2 | **No multiple statements per line** | **一行只能有一条语句** |
| 3 | `begin` must be on its own line | `begin` 必须独占一行 |
| 4 | `end` must be on its own line | `end` 必须独占一行 |
| 5 | No misaligned parameters, ports, or typedef members | 参数、端口、typedef 成员必须对齐 |
| 6 | No trailing whitespace | 禁止行尾多余空格 |
| 7 | No comment obscuring code | 注释不得遮挡代码 |
| 8 | No inconsistent indentation | 缩进必须一致 |
| 9 | No spaces between `(` and first argument | `(` 后不能有空格 |
| 10 | No spaces before `)` | `)` 前不能有空格 |
| 11 | `always_ff` and `always_comb` must not be mixed in one block | `always_ff` 与 `always_comb` 不得混用 |
| 12 | Enum values must be on separate lines | 枚举值必须分行书写 |

---

## 12. Recommended Tools / 推荐工具

| Tool / 工具 | Purpose / 用途 | Language / 语言 |
|---|---|---|
| **Verible** | Auto-formatting / 自动格式化 | Verilog / SV |
| **Emacs `verilog-mode`** | Indentation / 缩进 | Verilog / SV |
| **VS Code + Verilog-HDL** | Editor support / 编辑器支持 | Verilog / SV |
| **Questa / VCS** | Simulation / 仿真 | SystemVerilog |

---

## Appendix A: Quick Reference Card / 附录 A：快速参考卡

```
Indent / 缩进:     2 spaces / 2 空格
Line width / 行宽: 100 columns / 100 列
Brackets / 括号:   begin/end on separate lines / begin/end 各占一行
Spacing / 空格:    Around all operators / 运算符两侧
Blank lines / 空行: 1 between blocks, 2 between always / 逻辑块间1行，always间2行
Comments / 注释:   // for single, /* */ for multi / 单行用//，多行用/* */
```

---

## Appendix B: always Block Selection Guide / 附录 B：always 块选择指南

| Usage / 用途 | Keyword / 关键字 | Description / 说明 |
|---|---|---|
| Sequential logic / 时序逻辑 | `always_ff` | Use for flip-flops / 用于触发器 |
| Combinational logic / 组合逻辑 | `always_comb` | Use for combinational / 用于组合逻辑 |
| Intentional latch / 有意锁存 | `always_latch` | Use when latch is intended / 明确需要锁存器时用 |

---

*End of Document / 文档结束*
