# VHDL Style Format Guide (CN / EN)
# VHDL 代码整理规范（中英双语）

> **Version / 版本**: v1.0  
> **Scope / 适用范围**: VHDL-2008 (RTL / Testbench)  
> **Goal / 目标**: Unify code layout, improve readability, facilitate diff and code review  
> **目标**: 统一代码排版，提升可读性，便于 diff 与代码审查  
> **Note / 说明**: This document ONLY covers formatting — NOT functionality, synthesizability, or naming semantics.  
> **说明**: 本文档**仅**涉及排版格式 —— 不涉及功能正确性、可综合性或命名语义。

---

## Table of Contents / 目录

1. [Basic Layout Rules / 基础排版规则](#1-basic-layout-rules--基础排版规则-1)
2. [Declaration Block Layout / 声明区排版](#2-declaration-block-layout--声明区排版-1)
3. [Attribute Layout / 属性排版](#3-attribute-layout--属性排版)
4. [Logical Block Layout / 逻辑块排版](#4-logical-block-layout--逻辑块排版)
5. [Instantiation Layout / 实例化排版](#5-instantiation-layout--实例化排版)
6. [Expression Layout / 表达式排版](#6-expression-layout--表达式排版)
7. [Package & Component Layout / Package 与 Component 排版](#7-package--component-layout--package-与-component-排版)
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

```vhdl
-- ❌ Wrong / 错误
process(clk)
begin
    if rising_edge(clk) then
        q <= d;
    end if;
end process;

-- ✅ Correct / 正确
process(clk)
begin
  if rising_edge(clk) then
    q <= d;
  end if;
end process;
```

---

### 1.2 Line Width / 行宽

**EN**  
Maximum line width is **100 columns**. Wrap lines with **+2 indentation**.

**中文**  
最大行宽为 **100 列**。换行后额外缩进 **2 空格**。

**Example / 示例**

```vhdl
-- ❌ Wrong / 错误
result <= (sel = "00") ? a : (sel = "01") ? b : (sel = "10") ? c : d;

-- ✅ Correct / 正确
result <=
  a when sel = "00" else
  b when sel = "01" else
  c when sel = "10" else
  d;
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
| Around `=>` in associations / 关联符号 `=>` 两侧 | Must have space | 必须空格 |

**Example / 示例**

```vhdl
-- ❌ Wrong / 错误
a<=b+c;
process(clk,rst_n)

-- ✅ Correct / 正确
a <= b + c;
process(clk, rst_n)
```

---

### 1.4 Blank Line Rules / 空行规则

**EN**  
- Insert **1 blank line** between logical blocks.  
- Insert **2 blank lines** between `process` blocks or component instances.  
- Do NOT use consecutive blank lines (>2).

**中文**  
- 逻辑块之间插入 **1 个空行**。  
- `process` 块之间或元件实例之间插入 **2 个空行**。  
- 禁止连续空行超过 2 行。

```vhdl
-- ✅ Correct / 正确
signal cnt : unsigned(7 downto 0);


begin

  process(clk)
  begin
    if rising_edge(clk) then
      q <= d;
    end if;
  end process;

end architecture;
```

---

## 2. Declaration Block Layout / 声明区排版

### 2.1 Entity & Port Alignment / 实体与端口对齐

**EN**  
- `(` must be on its own line.  
- One port per line.  
- Align direction / type / name vertically.  
- `);` must be on its own line.

**中文**  
- `(` 独占一行。  
- 每个端口独占一行。  
- 方向 / 类型 / 名称纵向对齐。  
- `);` 独占一行。

```vhdl
-- ❌ Wrong / 错误
entity fifo is port(clk:in std_logic;rst_n:in std_logic;din:in std_logic_vector(7 downto 0);dout:out std_logic_vector(7 downto 0));end entity;

-- ✅ Correct / 正确
entity fifo is
  port (
    clk   : in  std_logic;
    rst_n : in  std_logic;
    din   : in  std_logic_vector(7 downto 0);
    dout  : out std_logic_vector(7 downto 0)
  );
end entity;
```

---

### 2.2 Generic Declaration / 泛型声明

**EN**  
- `generic` keyword on its own line.  
- Align generic names and default values.

**中文**  
- `generic` 关键字独占一行。  
- 泛型名与默认值对齐。

```vhdl
-- ✅ Correct / 正确
entity fifo is
  generic (
    DEPTH : integer := 16;
    WIDTH : integer := 8
  );
  port (
    ...
  );
end entity;
```

---

### 2.3 Signal & Variable Declaration / 信号与变量声明

**EN**  
- One signal/variable per line.  
- Align types and widths.

**中文**  
- 每行一个信号/变量。  
- 类型和位宽对齐。

```vhdl
-- ❌ Wrong / 错误
signal wr_ptr:unsigned(3 downto 0);signal rd_ptr:unsigned(3 downto 0);signal full:std_logic;

-- ✅ Correct / 正确
signal wr_ptr  : unsigned(3 downto 0);
signal rd_ptr  : unsigned(3 downto 0);
signal full    : std_logic;
signal empty   : std_logic;
```

---

### 2.4 Constant Declaration / 常量声明

**EN**  
- One constant per line.  
- Align type and value.

**中文**  
- 每行一个常量。  
- 类型和值对齐。

```vhdl
-- ✅ Correct / 正确
constant MAX_DEPTH : integer := 16;
constant DATA_WIDTH : integer := 32;
```

---

## 3. Attribute Layout / 属性排版

### 3.1 Core Principle / 核心原则

**EN**  
In VHDL, attributes are declared separately from the signal/entity they apply to.  
Attribute declarations use `attribute <name> of <target> : <class> is <value>;` syntax.  
Always place the attribute declaration **before** the target declaration when possible, and group related attributes together.  
**One attribute per line. Never semicolon-chain.**

**中文**  
VHDL 中，属性声明与被修饰的信号/实体是分开的。  
属性使用 `attribute <name> of <target> : <class> is <value>;` 语法。  
尽可能将属性声明放在**目标声明之前**，并将相关属性分组放在一起。  
**每行一个属性，严禁分号连写。**

#### 3.1.1 VHDL Attribute Syntax Overview / 语法总览

**EN**  
VHDL attributes come in two forms: predefined and user-defined.  
Predefined attributes (like `'range`, `'left`, `'right`, `'length`) are built into the language and need no declaration.  
User-defined attributes must be **declared first** with `attribute <name> : <type>;`, then **assigned** with `attribute <name> of <target> : <class> is <value>;`.

**中文**  
VHDL 属性分为两种：预定义属性和用户自定义属性。  
预定义属性（如 `'range`、`'left`、`'right`、`'length`）是语言内置的，无需声明。  
用户自定义属性必须先**声明** `attribute <name> : <type>;`，再**赋值** `attribute <name> of <target> : <class> is <value>;`。

**Example / 示例**

```vhdl
-- Step 1: Declare the attribute (usually in package or architecture header)
-- 第一步：声明属性（通常在 package 或 architecture 头部）
attribute mark_debug : string;

-- Step 2: Assign the attribute to a target
-- 第二步：将属性赋值给目标
attribute mark_debug of clk : signal is "true";
```

#### 3.1.2 Attribute Classes / 属性分类

**EN**  
The `<class>` in an attribute assignment can be one of: `signal`, `entity`, `architecture`, `type`, `variable`, `component`, `function`, `procedure`.

**中文**  
属性赋值中的 `<class>` 可以是：`signal`、`entity`、`architecture`、`type`、`variable`、`component`、`function`、`procedure`。

```vhdl
attribute mark_debug of my_sig   : signal     is "true";   -- signal
attribute keep       of my_ent   : entity     is "yes";    -- entity
attribute keep       of rtl      : architecture is "true"; -- architecture
attribute ram_style  of mem_type : type       is "block";  -- type
attribute keep       of tmp_var  : variable   is "true";   -- variable
```

---

#### 3.1.3 Positioning Rules / 放置位置规则

**EN**  
Where you place the attribute declaration and assignment depends on the `<class>`:

| Class / 分类 | Declaration position / 声明位置 | Assignment position / 赋值位置 |
|---|---|---|
| `signal` | Architecture header / Architecture 头部 | Immediately before the signal declaration / 紧邻信号声明之前 |
| `entity` | Before `entity` keyword / `entity` 关键字之前 | Before `entity` / `entity` 之前 |
| `architecture` | After `architecture` name / `architecture` 名称之后 | Before `begin` / `begin` 之前 |
| `type` | Architecture header / Architecture 头部 | Before the `type` declaration / `type` 声明之前 |
| `variable` | Process declarative part / Process 声明区 | Before the `variable` declaration / `variable` 声明之前 |

**Chinese / 中文**  
属性的声明和赋值位置取决于 `<class>`：

| 分类 | 声明位置 | 赋值位置 |
|---|---|---|
| `signal` | Architecture 头部 | 紧邻信号声明之前 |
| `entity` | `entity` 关键字之前 | `entity` 之前 |
| `architecture` | `architecture` 名称之后 | `begin` 之前 |
| `type` | Architecture 头部 | `type` 声明之前 |
| `variable` | Process 声明区 | `variable` 声明之前 |

---

#### 3.1.4 Spacing Rules (Strict) / 空格规则（严格）

**EN**  
The keyword `attribute` must be followed by **one space**.  
The keyword `of` must have **one space before and after**.  
The colon `:` must have **one space after**.  
The keyword `is` must have **one space before and after**.  
The semicolon `;` must have **no space before**.

**中文**  
关键字 `attribute` 后必须有 **1 个空格**。  
关键字 `of` **前后各 1 个空格**。  
冒号 `:` 后必须有 **1 个空格**。  
关键字 `is` **前后各 1 个空格**。  
分号 `;` 前必须 **无空格**。

```vhdl
-- ❌ Wrong / 错误（各种空格问题）
attribute mark_debug of x:signal is"true";
attribute  mark_debug of x :signal is "true" ;
attribute mark_debug of x : signal is "true";  -- trailing space before ;

-- ✅ Correct / 正确
attribute mark_debug of x : signal is "true";
```

---

### 3.2 Signal Attributes / 信号属性

**EN**  
- Attribute declaration on its own line.  
- One attribute per line.  
- Place before the signal declaration it applies to.  
- Align the `of` keyword when multiple attributes apply to the same target.  
- Add a **block comment** above each attribute group to explain the purpose.

**中文**  
- 属性声明独占一行。  
- 每行一个属性。  
- 放在所修饰的信号声明之前。  
- 当多个属性作用于同一目标时，`of` 关键字对齐。  
- 每个属性组上方加**块注释**说明用途。

#### 3.2.1 Basic Layout / 基础排版

```vhdl
-- ❌ Wrong / 错误
signal wr_ptr : unsigned(3 downto 0);attribute mark_debug of wr_ptr : signal is "true";
signal rd_ptr : unsigned(3 downto 0);
```

```vhdl
-- ✅ Correct / 正确
-- FSM state (debug visible in Vivado)
attribute mark_debug of fsm_state : signal is "true";
signal fsm_state : unsigned(1 downto 0);

-- Prevent optimization during synthesis
attribute keep of critical_sig : signal is "true";
signal critical_sig : std_logic;
```

#### 3.2.2 Grouped Attributes (Same Target) / 同目标多属性分组

**EN**  
When multiple attributes apply to the **same signal**, place them **consecutively** with a single comment block above.

**中文**  
当多个属性作用于**同一信号**时，将它们**连续放置**，上方用一个注释块说明。

```vhdl
-- ❌ Wrong / 错误
attribute mark_debug of dbg_sig : signal is "true";
signal dbg_sig : std_logic;
attribute keep of dbg_sig : signal is "true";
```

```vhdl
-- ✅ Correct / 正确
-- dbg_sig: expose to ILA, prevent optimization
attribute mark_debug of dbg_sig : signal is "true";
attribute keep       of dbg_sig : signal is "true";
signal dbg_sig : std_logic;
```

#### 3.2.3 Advanced Alignment (Company-Grade) / 进阶对齐版（公司级）

**EN**  
When you have **many signals** with attributes, align `of`, `:`, and `is` columns separately for readability.

**中文**  
当**大量信号**带有属性时，分别对齐 `of`、`:`、`is` 三列，最大化可读性。

```vhdl
-- Debug signals for ILA core insertion
-- ILA 调试信号
attribute mark_debug of clk        : signal is "true";
attribute mark_debug of rst_n     : signal is "true";
attribute mark_debug of axis_tdata : signal is "true";
attribute mark_debug of axis_tvalid: signal is "true";
attribute mark_debug of axis_tready: signal is "true";

-- Critical signals: prevent synthesis optimization
-- 关键信号：防止综合优化
attribute keep of fsm_state  : signal is "true";
attribute keep of cnt_reg    : signal is "true";
attribute keep of mem_array  : signal is "true";
```

#### 3.2.4 Cross-Language Reference / 与 Verilog 对照

**EN**  
VHDL `attribute mark_debug of sig : signal is "true";` is the **exact equivalent** of Verilog `(* mark_debug = "true" *) signal sig;`.  
The VHDL form is **more verbose but more flexible** — it separates declaration from assignment.

**中文**  
VHDL 的 `attribute mark_debug of sig : signal is "true";` 完全等价于 Verilog 的 `(* mark_debug = "true" *) signal sig;`。  
VHDL 形式**更冗长但更灵活** —— 它将声明与赋值分离。

| Verilog / SystemVerilog | VHDL Equivalent | Note / 说明 |
|---|---|---|
| `(* mark_debug = "true" *) input clk;` | `attribute mark_debug of clk : signal is "true";` | Port / 端口 |
| `(* keep = "true" *) reg sig;` | `attribute keep of sig : signal is "true";` | Signal / 信号 |
| `(* max_fanout = 16 *) wire sig;` | `attribute max_fanout of sig : signal is 16;` | Fanout / 扇出 |
| `(* dont_touch = "true" *) wire sig;` | `attribute dont_touch of sig : signal is "true";` | Prevention / 禁止优化 |
| `(* ram_style = "block" *) reg [31:0] mem [0:15];` | `attribute ram_style of mem : signal is "block";` | RAM / 块RAM |

---

### 3.3 Entity Attributes / 实体属性

**EN**  
- Place **before** the `entity` declaration.  
- One attribute per line.  
- Common for `keep_hierarchy`, `dont_touch`.  
- If multiple entity attributes, group them with a comment block.

**中文**  
- 放在 `entity` 声明**之前**。  
- 每行一个属性。  
- 常用于 `keep_hierarchy`、`dont_touch`。  
- 多个实体属性时用注释块分组。

#### 3.3.1 Basic Layout / 基础排版

```vhdl
-- ❌ Wrong / 错误
attribute keep_hierarchy of fifo : entity is "yes";entity fifo is
```

```vhdl
-- ✅ Correct / 正确
-- Preserve hierarchy for debug
attribute keep_hierarchy of fifo : entity is "yes";
entity fifo is
  port (
    ...
  );
end entity fifo;
```

#### 3.3.2 Multiple Entity Attributes / 多实体属性

```vhdl
-- ❌ Wrong / 错误
attribute keep_hierarchy of fifo : entity is "yes";attribute dont_touch of fifo : entity is "true";
```

```vhdl
-- ✅ Correct / 正确
-- Entity-level attributes: preserve hierarchy and prevent touching
-- 实体级属性：保留层次结构，禁止触碰
attribute keep_hierarchy of fifo        : entity is "yes";
attribute dont_touch     of fifo        : entity is "true";
entity fifo is
  port (
    ...
  );
end entity fifo;
```

#### 3.3.3 Cross-Language Reference / 与 Verilog 对照

| Verilog / SystemVerilog | VHDL Equivalent | Note / 说明 |
|---|---|---|
| `(* keep_hierarchy = "yes" *) module fifo(...);` | `attribute keep_hierarchy of fifo : entity is "yes";` | Hierarchy / 层次结构 |
| `(* dont_touch = "true" *) module fifo(...);` | `attribute dont_touch of fifo : entity is "true";` | No optimization / 禁止优化 |

---

### 3.4 Architecture Attributes / 结构体属性

**EN**  
- Place **after** the `architecture` name, **before** the `begin`.  
- One attribute per line.  
- The `<class>` is always `architecture`.  
- Use a comment to explain why the architecture is being preserved.

**中文**  
- 放在 `architecture` 名称**之后**、`begin` **之前**。  
- 每行一个属性。  
- `<class>` 始终为 `architecture`。  
- 用注释说明为何要保留该结构体。

#### 3.4.1 Basic Layout / 基础排版

```vhdl
-- ✅ Correct / 正确
architecture rtl of fifo is
  -- Prevent synthesis optimization of this block
  attribute keep of rtl : architecture is "true";
  signal cnt : unsigned(7 downto 0);
begin
  ...
end architecture rtl;
```

#### 3.4.2 Architecture + Signal Attributes Combined / 结构体与信号属性共存

**EN**  
When an architecture has both its own attribute and signal attributes, place the **architecture attribute first**, then signal attributes, then signal declarations.

**中文**  
当结构体既有自身属性又有信号属性时，**先放结构体属性**，再放信号属性，最后放信号声明。

```vhdl
-- ❌ Wrong / 错误
architecture rtl of fifo is
  signal cnt : unsigned(7 downto 0);
  attribute keep of rtl : architecture is "true";
  attribute mark_debug of cnt : signal is "true";
begin
```

```vhdl
-- ✅ Correct / 正确
architecture rtl of fifo is
  -- Preserve this architecture during optimization
  attribute keep of rtl       : architecture is "true";

  -- Debug signals
  attribute mark_debug of cnt : signal is "true";
  signal cnt : unsigned(7 downto 0);

  attribute mark_debug of fsm_state : signal is "true";
  signal fsm_state : unsigned(1 downto 0);
begin
```

#### 3.4.3 Cross-Language Reference / 与 Verilog 对照

| Verilog / SystemVerilog | VHDL Equivalent | Note / 说明 |
|---|---|---|
| `(* keep = "true" *) module fifo(...);` | `attribute keep of rtl : architecture is "true";` | Note: VHDL applies to architecture name, not module name |
| `(* dont_touch = "true" *) module fifo(...);` | `attribute dont_touch of rtl : architecture is "true";` | Same note |

> **Important / 重要**: In VHDL, architecture attributes use the **architecture identifier** (e.g., `rtl`), not the entity name.

---

### 3.5 Type Attributes / 类型属性

**EN**  
- Place **before** the `type` declaration.  
- One attribute per line.  
- The `<class>` is `type` (not `signal`).  
- Commonly used for `ram_style`, `rom_style` to control synthesis inference.

**中文**  
- 放在 `type` 声明**之前**。  
- 每行一个属性。  
- `<class>` 为 `type`（不是 `signal`）。  
- 常用于 `ram_style`、`rom_style` 控制综合推断。

#### 3.5.1 Basic Layout / 基础排版

```vhdl
-- ✅ Correct / 正确
-- Force block RAM inference
attribute ram_style of mem_t : type is "block";
type mem_t is array (0 to 15) of std_logic_vector(31 downto 0);
signal mem : mem_t;
```

#### 3.5.2 RAM / ROM Style Attributes / RAM / ROM 风格属性

```vhdl
-- ❌ Wrong / 错误
attribute ram_style of mem : signal is "block";type mem_t is...  -- attribute on signal, not type
```

```vhdl
-- ✅ Correct / 正确 — Block RAM
-- Force block RAM inference
attribute ram_style of mem_t : type is "block";
type mem_t is array (0 to 255) of std_logic_vector(31 downto 0);
signal mem : mem_t;

-- Force block ROM inference
attribute rom_style of rom_t : type is "block";
type rom_t is array (0 to 127) of std_logic_vector(31 downto 0);
signal rom : rom_t;
```

#### 3.5.3 Cross-Language Reference / 与 Verilog 对照

| Verilog / SystemVerilog | VHDL Equivalent | Note / 说明 |
|---|---|---|
| `(* ram_style = "block" *) reg [31:0] mem [0:255];` | `attribute ram_style of mem_t : type is "block";` | Block RAM / 块 RAM |
| `(* rom_style = "block" *) reg [31:0] rom [0:127];` | `attribute rom_style of rom_t : type is "block";` | Block ROM / 块 ROM |

> **Note / 注意**: In VHDL, `ram_style` and `rom_style` attributes apply to the **type**, not the signal.

---

### 3.6 Common Attribute Reference / 常用属性速查

| Attribute / 属性 | Class / 分类 | Placement / 位置 | Format / 格式 | Purpose / 用途 |
|---|---|---|---|---|
| `mark_debug` | `signal` | Before signal / 信号之前 | `attribute mark_debug of <name> : signal is "true";` | Expose signal to Vivado Logic Analyzer / 暴露信号给 Vivado 逻辑分析仪 |
| `keep` (signal) | `signal` | Before signal / 信号之前 | `attribute keep of <name> : signal is "true";` | Prevent optimization / 防止综合优化掉 |
| `keep` (entity) | `entity` | Before entity / 实体之前 | `attribute keep of <name> : entity is "yes";` | Preserve hierarchy / 保留层次结构 |
| `keep` (arch) | `architecture` | After arch name, before begin / 结构体名后、begin 前 | `attribute keep of <arch> : architecture is "true";` | Prevent optimization of architecture / 防止结构体被优化 |
| `dont_touch` (entity) | `entity` | Before entity / 实体之前 | `attribute dont_touch of <name> : entity is "true";` | Prevent any optimization / 禁止任何优化 |
| `dont_touch` (signal) | `signal` | Before signal / 信号之前 | `attribute dont_touch of <name> : signal is "true";` | Prevent any optimization / 禁止任何优化 |
| `ram_style` | `type` | Before type / 类型之前 | `attribute ram_style of <type> : type is "block";` | Force block RAM / 强制使用块 RAM |
| `rom_style` | `type` | Before type / 类型之前 | `attribute rom_style of <type> : type is "block";` | Force block ROM / 强制使用块 ROM |
| `max_fanout` | `signal` | Before signal / 信号之前 | `attribute max_fanout of <name> : signal is N;` | Limit fanout / 限制扇出 |
| `parallel_case` | `signal` | Before signal / 信号之前 | `attribute parallel_case of <name> : signal is "true";` | Force parallel case / 强制并行 case |
| `full_case` | `signal` | Before signal / 信号之前 | `attribute full_case of <name> : signal is "true";` | Force full case / 强制完整 case |

---

### 3.7 Formatting Before & After (Attribute Focused) / 属性整理前后对照

| Scenario / 场景 | Before / 整理前 | After / 整理后 |
|---|---|---|
| Signal attribute / 信号属性 | `signal x:std_logic;attribute mark_debug of x:signal is "true";` | `attribute mark_debug of x : signal is "true";\nsignal x : std_logic;` |
| Multi-attribute same target / 同目标多属性 | `attribute mark_debug of x:s is "true";signal x:std_logic;attribute keep of x:s is "true";` | `attribute mark_debug of x : signal is "true";\nattribute keep of x : signal is "true";\nsignal x : std_logic;` |
| Entity attribute / 实体属性 | `attribute keep of e:entity is "yes";entity e is` | `attribute keep of e : entity is "yes";\nentity e is` |
| Architecture attribute / 结构体属性 | `architecture rtl of e is begin` | `architecture rtl of e is\n  attribute keep of rtl : architecture is "true";\nbegin` |
| Type attribute / 类型属性 | `attribute ram_style of m:type is "block";type t is...` | `attribute ram_style of m : type is "block";\ntype t is...` |
| Spacing / 空格 | `attribute mark_debug of x:signal is"true";` | `attribute mark_debug of x : signal is "true";` |
| Semicolon chain / 分号连写 | `attribute mark_debug of x:s is "true";attribute keep of x:s is "true";` | `attribute mark_debug of x : signal is "true";\nattribute keep of x : signal is "true";` |
| Attribute after signal / 属性在信号之后 | `signal x:std_logic;attribute mark_debug of x:signal is "true";` | `attribute mark_debug of x : signal is "true";\nsignal x : std_logic;` |
| Mixed attributes / 混合属性 | `attribute keep of rtl:architecture is "true";signal x:std_logic;attribute mark_debug of x:signal is "true";` | `attribute keep of rtl : architecture is "true";\n\nattribute mark_debug of x : signal is "true";\nsignal x : std_logic;` |

---

### 3.8 Hard Rules for Attributes / 属性排版红线

| # | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| 1 | Attribute must be on its own line | 属性必须独占一行 |
| 2 | No attribute on the same line as the target declaration | 属性不得与目标声明同行 |
| 3 | One attribute per line — never semicolon-chain | 每行一个属性 —— 严禁分号连写 |
| 4 | Space around `of`, `:`, `is` keywords | `of`、`:`、`is` 两侧必须有空格 |
| 5 | No space before `;` | `;` 前不得有空格 |
| 6 | Attribute must be placed before the target declaration | 属性必须放在目标声明之前 |
| 7 | No trailing whitespace | 不得有行尾空格 |
| 8 | Attribute class must match the target type | 属性分类必须匹配目标类型 |
| 9 | Multiple attributes on same target must be consecutive | 同一目标的多个属性必须连续放置 |
| 10 | Attribute declaration must precede attribute assignment | 属性声明必须先于属性赋值 |

#### 3.8.1 Rule 8 Detail / 规则 8 详解

**EN**  
The `<class>` in the attribute assignment must match the actual VHDL construct:  
- Use `signal` for `signal` declarations  
- Use `entity` for `entity` declarations  
- Use `architecture` for `architecture` names  
- Use `type` for `type` declarations  
- Use `variable` for `variable` declarations

**Chinese / 中文**  
属性赋值中的 `<class>` 必须与实际 VHDL 构造匹配：  
- `signal` 声明用 `signal`  
- `entity` 声明用 `entity`  
- `architecture` 名称用 `architecture`  
- `type` 声明用 `type`  
- `variable` 声明用 `variable`

```vhdl
-- ❌ Wrong / 错误 — class mismatch
attribute mark_debug of my_sig : entity is "true";  -- my_sig is a signal, not an entity!
attribute ram_style  of mem   : signal is "block";  -- ram_style applies to type, not signal!
```

```vhdl
-- ✅ Correct / 正确
attribute mark_debug of my_sig : signal is "true";
attribute ram_style  of mem_t  : type   is "block";
```

#### 3.8.2 Rule 9 Detail / 规则 9 详解

**EN**  
When a signal has multiple attributes, they must be placed **one after another** with **no other code** in between. A single comment block above the group explains the purpose.

**Chinese / 中文**  
当一个信号有多个属性时，它们必须**紧邻放置**，中间**不能插入其他代码**。在组上方用一个注释块说明用途。

```vhdl
-- ❌ Wrong / 错误 — attributes split by unrelated code
attribute mark_debug of dbg_sig : signal is "true";
signal tmp : std_logic;  -- ← unrelated signal in between!
attribute keep of dbg_sig : signal is "true";
```

```vhdl
-- ✅ Correct / 正确 — consecutive, with group comment
-- dbg_sig: expose to ILA + prevent optimization
attribute mark_debug of dbg_sig : signal is "true";
attribute keep       of dbg_sig : signal is "true";
```

#### 3.8.3 Rule 10 Detail / 规则 10 详解

**EN**  
Before you can assign an attribute with `attribute <name> of ... is ...;`, you **must first declare it** with `attribute <name> : <type>;`.  
The declaration typically goes in a `package` (shared) or at the top of the `architecture` (local).

**Chinese / 中文**  
在使用 `attribute <name> of ... is ...;` 赋值之前，**必须先声明** `attribute <name> : <type>;`。  
声明通常放在 `package`（共享）或 `architecture` 顶部（局部）。

```vhdl
-- ❌ Wrong / 错误 — assignment without declaration
attribute mark_debug of clk : signal is "true";  -- Error: attribute not declared!
```

```vhdl
-- ✅ Correct / 正确 — declare first, then assign
-- In package (shared across files)
package common_pkg is
  attribute mark_debug : string;
  attribute keep       : string;
end package common_pkg;

-- In architecture (local)
architecture rtl of fifo is
  attribute mark_debug of clk : signal is "true";  -- OK: declared in package
  signal clk : std_logic;
begin
```

---

### 3.9 Package-Centralized Attributes / Package 集中管理属性

**EN**  
For large projects, declare **all attributes in a shared package** (`common_pkg.vhd`) and `use` it in every RTL file.  
This avoids repeated declarations and ensures consistency.

**中文**  
大型项目中，将**所有属性声明放在一个共享 package**（`common_pkg.vhd`）中，每个 RTL 文件通过 `use` 引用。  
避免重复声明，保证一致性。

#### 3.9.1 Package Declaration Template / Package 声明模板

```vhdl
-- common_pkg.vhd
-- 共享属性声明包
package common_pkg is

  ---------------------------------------------------------------------------
  -- Attribute declarations (centralized)
  -- 属性声明（集中管理）
  ---------------------------------------------------------------------------
  attribute mark_debug   : string;
  attribute keep         : string;
  attribute dont_touch  : string;
  attribute ram_style    : string;
  attribute rom_style    : string;
  attribute max_fanout   : integer;
  attribute parallel_case : string;
  attribute full_case    : string;

  ---------------------------------------------------------------------------
  -- Other shared declarations
  -- 其他共享声明
  ---------------------------------------------------------------------------
  constant DATA_WIDTH : integer := 32;
  constant ADDR_WIDTH : integer := 16;

end package common_pkg;
```

#### 3.9.2 Usage in RTL Files / 在 RTL 中的使用

```vhdl
-- fifo.vhd
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.common_pkg.all;  -- Import shared attributes / 导入共享属性

entity fifo is
  port (
    clk   : in  std_logic;
    rst_n : in  std_logic;
    din   : in  std_logic_vector(31 downto 0);
    dout  : out std_logic_vector(31 downto 0)
  );
end entity fifo;

architecture rtl of fifo is
  -- Debug signals
  -- 调试信号
  attribute mark_debug of clk        : signal is "true";
  attribute mark_debug of din       : signal is "true";
  attribute mark_debug of dout      : signal is "true";

  -- Critical signals: prevent optimization
  -- 关键信号：防止优化
  attribute keep of fsm_state  : signal is "true";
  attribute keep of cnt_reg    : signal is "true";

  -- FSM state
  signal fsm_state : unsigned(1 downto 0);
  signal cnt_reg   : unsigned(7 downto 0);

begin
  ...
end architecture rtl;
```

#### 3.9.3 Formatting Rules / 排版规则

**EN**  
- Import the package with `use work.common_pkg.all;` **before** the entity.  
- Group attribute assignments by **purpose** (debug vs. optimization).  
- Leave **one blank line** between groups.  
- Align `of` and `is` within each group.

**中文**  
- 在 entity **之前**用 `use work.common_pkg.all;` 导入 package。  
- 按**用途**分组（调试 vs. 优化）。  
- 组之间留 **1 个空行**。  
- 组内对齐 `of` 和 `is`。

---

### 3.10 Generic-Controlled Conditional Attributes / Generic 控制的条件属性

**EN**  
Use `generic` to make attribute values **configurable at instantiation time**.  
The attribute assignment follows the same formatting rules — one per line, aligned.

**中文**  
通过 `generic` 让属性值在**实例化时可配置**。  
属性赋值遵循同样的排版规则 —— 每行一个，对齐。

#### 3.10.1 Basic Template / 基础模板

```vhdl
entity fifo is
  generic (
    DEBUG_EN : boolean := false;
    KEEP_EN  : boolean := false
  );
  port (
    clk   : in  std_logic;
    rst_n : in  std_logic;
    din   : in  std_logic_vector(31 downto 0);
    dout  : out std_logic_vector(31 downto 0)
  );
end entity fifo;

architecture rtl of fifo is
  -- Conditional attributes based on generics
  -- 基于泛型的条件属性
  attribute mark_debug of clk   : signal is "true" when DEBUG_EN else "false";
  attribute keep       of dout  : signal is "true" when KEEP_EN  else "false";

  signal internal_sig : std_logic_vector(31 downto 0);
begin
  ...
end architecture rtl;
```

#### 3.10.2 Formatting Rules / 排版规则

**EN**  
- The `when ... else ...` clause must be on the **same line** as the attribute assignment.  
- If the line exceeds 100 columns, wrap after `else` with **+2 indentation**.  
- Align the `when` and `else` keywords vertically across multiple attributes.

**中文**  
- `when ... else ...` 子句必须与属性赋值在**同一行**。  
- 超过 100 列时，在 `else` 后换行，额外缩进 **2 空格**。  
- 多个属性之间 `when` 和 `else` 纵向对齐。

```vhdl
-- ❌ Wrong / 错误 — when/else on separate lines
attribute mark_debug of long_signal_name_1 : signal is "true"
  when DEBUG_EN else "false";
```

```vhdl
-- ✅ Correct / 正确 — within line width
attribute mark_debug of long_signal_name_1 : signal is "true" when DEBUG_EN else "false";
attribute keep       of long_signal_name_2 : signal is "true" when KEEP_EN  else "false";
```

```vhdl
-- ✅ Correct / 正确 — wrap after else when line too long
attribute mark_debug of very_long_signal_name_that_exceeds_limit : signal is
    "true" when DEBUG_EN else "false";
```

---

### 3.11 Complete Worked Example / 完整综合示例

**EN**  
The following is a **complete, production-quality** example showing all attribute types in one file, properly formatted.

**中文**  
下面是一个**完整的、生产级**示例，展示一个文件中所有属性类型的正确排版。

```vhdl
---------------------------------------------------------------------------
-- Entity        : axi_stream_fifo
-- Project       : SOC_CORE
-- Author        : hdl_team
-- Created       : 2026-06-22
-- Description   : AXI-Stream FIFO with debug attributes
---------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.common_pkg.all;

-- Entity-level: preserve hierarchy
-- 实体级：保留层次结构
attribute keep_hierarchy of axi_stream_fifo : entity is "yes";

entity axi_stream_fifo is
  generic (
    DEPTH : integer := 16;
    WIDTH : integer := 32;
    DEBUG : boolean := true
  );
  port (
    -- AXI-Stream signals
    -- AXI-Stream 信号
    s_axis_aclk    : in  std_logic;
    s_axis_aresetn : in  std_logic;
    s_axis_tdata   : in  std_logic_vector(WIDTH-1 downto 0);
    s_axis_tvalid  : in  std_logic;
    s_axis_tready  : out std_logic;
    m_axis_tdata   : out std_logic_vector(WIDTH-1 downto 0);
    m_axis_tvalid  : out std_logic;
    m_axis_tready  : in  std_logic
  );
end entity axi_stream_fifo;

architecture rtl of axi_stream_fifo is

  -- Architecture-level: prevent optimization
  -- 结构体级：防止优化
  attribute keep of rtl : architecture is "true";

  --=========================================================================
  -- Debug signals (ILA insertion)
  -- 调试信号（ILA 插入）
  --=========================================================================
  attribute mark_debug of s_axis_aclk    : signal is "true";
  attribute mark_debug of s_axis_aresetn: signal is "true";
  attribute mark_debug of s_axis_tdata  : signal is "true" when DEBUG else "false";
  attribute mark_debug of s_axis_tvalid : signal is "true" when DEBUG else "false";
  attribute mark_debug of s_axis_tready : signal is "true" when DEBUG else "false";

  --=========================================================================
  -- Critical signals: prevent optimization
  -- 关键信号：防止优化
  --=========================================================================
  attribute keep of m_axis_tdata  : signal is "true";
  attribute keep of m_axis_tvalid : signal is "true";

  --=========================================================================
  -- Memory: force block RAM
  -- 存储器：强制块 RAM
  --=========================================================================
  attribute ram_style of mem_t : type is "block";

  --=========================================================================
  -- Signal declarations
  -- 信号声明
  --=========================================================================
  type mem_t is array (0 to DEPTH-1) of std_logic_vector(WIDTH-1 downto 0);
  signal mem        : mem_t;
  signal wr_ptr     : unsigned(3 downto 0) := (others => '0');
  signal rd_ptr     : unsigned(3 downto 0) := (others => '0');
  signal count      : unsigned(4 downto 0) := (others => '0');
  signal full       : std_logic := '0';
  signal empty      : std_logic := '1';

begin

  --=========================================================================
  -- Write pointer process
  -- 写指针进程
  --=========================================================================
  wr_proc : process(s_axis_aclk, s_axis_aresetn)
  begin
    if s_axis_aresetn = '0' then
      wr_ptr <= (others => '0');
    elsif rising_edge(s_axis_aclk) then
      if s_axis_tvalid = '1' and full = '0' then
        mem(to_integer(wr_ptr)) <= s_axis_tdata;
        wr_ptr <= wr_ptr + 1;
      end if;
    end if;
  end process wr_proc;

  --=========================================================================
  -- Read pointer process
  -- 读指针进程
  --=========================================================================
  rd_proc : process(s_axis_aclk, s_axis_aresetn)
  begin
    if s_axis_aresetn = '0' then
      rd_ptr <= (others => '0');
    elsif rising_edge(s_axis_aclk) then
      if m_axis_tready = '1' and empty = '0' then
        m_axis_tdata <= mem(to_integer(rd_ptr));
        rd_ptr <= rd_ptr + 1;
      end if;
    end if;
  end process rd_proc;

  --=========================================================================
  -- Status signals
  -- 状态信号
  --=========================================================================
  full  <= '1' when count = DEPTH else '0';
  empty <= '1' when count = 0      else '0';

end architecture rtl;
```

---

## 4. Logical Block Layout / 逻辑块排版

### 4.1 process Block / process 块

**EN**  
- `process` keyword, sensitivity list, `begin`, `end process` each on separate lines.  
- `end process` aligns with `process`.  
- Label the process.

**中文**  
- `process` 关键字、敏感列表、`begin`、`end process` 各占一行。  
- `end process` 与 `process` 对齐。  
- 给 process 加标签。

```vhdl
-- ❌ Wrong / 错误
process(clk,rst_n)begin if rst_n='0'then q<='0';elsif rising_edge(clk)then q<=d;end if;end process;

-- ✅ Correct / 正确
main_proc : process(clk, rst_n)
begin
  if rst_n = '0' then
    q <= '0';
  elsif rising_edge(clk) then
    q <= d;
  end if;
end process main_proc;
```

---

### 4.2 if / elsif / else / if / elsif / else

**EN**  
- `if` condition must have spaces.  
- `then` on the same line as the condition.  
- `else` / `elsif` on separate lines.

**中文**  
- `if` 条件必须空格。  
- `then` 与条件同行。  
- `else` / `elsif` 各占一行。

```vhdl
-- ✅ Correct / 正确
if en = '1' then
  cnt <= cnt + 1;
elsif clr = '1' then
  cnt <= (others => '0');
else
  cnt <= cnt;
end if;
```

---

### 4.3 case / when / case / when

**EN**  
- `case` expression on its own line.  
- Each `when` on its own line.  
- `when others` must be present.

**中文**  
- `case` 表达式独占一行。  
- 每个 `when` 独占一行。  
- 必须有 `when others`。

```vhdl
-- ✅ Correct / 正确
case state is
  when IDLE =>
    next_state <= RUN;
  when RUN =>
    next_state <= DONE;
  when others =>
    next_state <= IDLE;
end case;
```

---

### 4.4 for Loop / for 循环

**EN**  
- `for` on its own line.  
- `loop` on the same line as `for`.

**中文**  
- `for` 独占一行。  
- `loop` 与 `for` 同行。

```vhdl
-- ✅ Correct / 正确
for i in 0 to 3 loop
  mem(i) <= din(i);
end loop;
```

---

### 4.5 while Loop / while 循环

**EN**  
- `while` on its own line.  
- `loop` on the same line.

**中文**  
- `while` 独占一行。  
- `loop` 与 `while` 同行。

```vhdl
-- ✅ Correct / 正确
while i < 4 loop
  mem(i) <= din(i);
  i := i + 1;
end loop;
```

---

### 4.6 generate / generate

**EN**  
- `generate / end generate` on separate lines.  
- Label the generate block.

**中文**  
- `generate / end generate` 各占一行。  
- 给 generate 加标签。

```vhdl
-- ✅ Correct / 正确
gen_loop : for i in 0 to 3 generate
  u_ff : entity work.dff
    port map (
      clk => clk,
      d   => din(i),
      q   => dout(i)
    );
end generate gen_loop;
```

---

### 4.7 Concurrent Assignment / 并发赋值

**EN**  
- `when ... else` on separate lines for readability.  
- Align `when` keywords.

**中文**  
- `when ... else` 分行书写提高可读性。  
- `when` 关键字对齐。

```vhdl
-- ✅ Correct / 正确
ready <=
  '1' when (empty = '1' and full = '0') else
  '0';
```

---

## 5. Instantiation Layout / 实例化排版

### 5.1 Component Instantiation / 元件实例化

**EN**  
- Component name on its own line.  
- Port map: one association per line, aligned.

**中文**  
- 元件名独占一行。  
- 端口映射：每行一个关联，对齐。

```vhdl
-- ❌ Wrong / 错误
u_fifo: entity work.fifo port map(clk,rst_n,din,dout,full,empty);

-- ✅ Correct / 正确
u_fifo : entity work.fifo
  port map (
    clk   => clk,
    rst_n => rst_n,
    din   => din,
    dout  => dout,
    full  => full,
    empty => empty
  );
```

---

### 5.2 Instantiation with Generics / 带泛型实例化

**EN**  
- Generics before ports.  
- Align generic names and values.

**中文**  
- 泛型在前，端口在后。  
- 泛型名与值对齐。

```vhdl
-- ✅ Correct / 正确
u_fifo : entity work.fifo
  generic map (
    DEPTH => 16,
    WIDTH => 8
  )
  port map (
    clk   => clk,
    rst_n => rst_n,
    din   => din,
    dout  => dout
  );
```

---

## 6. Expression Layout / 表达式排版

### 6.1 Arithmetic & Logical Expressions / 算术与逻辑表达式

**EN**  
- Space around operators.  
- Parentheses for clarity.

**中文**  
- 运算符两侧空格。  
- 括号增加可读性。

```vhdl
-- ❌ Wrong / 错误
if((a=b)and(c/=d))then

-- ✅ Correct / 正确
if ((a = b) and (c /= d)) then
```

---

### 6.2 Concatenation / 拼接

**EN**  
- Short: `()` with spaces after commas.  
- Long: one element per line.

**中文**  
- 短：使用 `()`，逗号后空格。  
- 长：每个元素一行。

```vhdl
-- Short / 短
data <= (a, b, c);

-- Long / 长
data <= (
  a,
  b,
  c,
  d
);
```

---

### 6.3 Ternary (when ... else) / 三目（when ... else）

**EN**  
- Always wrap to multiple lines.  
- Align `when` and `else`.

**中文**  
- 始终换行书写。  
- `when` 与 `else` 对齐。

```vhdl
-- ✅ Correct / 正确
result <=
  a when sel = "00" else
  b when sel = "01" else
  c when sel = "10" else
  d;
```

---

## 7. Package & Component Layout / Package 与 Component 排版

### 7.1 Package Declaration / 包声明

**EN**  
- `package / end package` on separate lines.  
- One declaration per line inside.

**中文**  
- `package / end package` 各占一行。  
- 内部每行一个声明。

```vhdl
-- ✅ Correct / 正确
package common_pkg is
  constant DATA_WIDTH : integer := 32;
  type mem_t is array (0 to 15) of std_logic_vector(31 downto 0);
end package common_pkg;
```

---

### 7.2 Component Declaration / 元件声明

**EN**  
- `component / end component` on separate lines.  
- Port alignment same as entity.

**中文**  
- `component / end component` 各占一行。  
- 端口对齐同 entity。

```vhdl
-- ✅ Correct / 正确
component fifo
  port (
    clk   : in  std_logic;
    rst_n : in  std_logic;
    din   : in  std_logic_vector(7 downto 0);
    dout  : out std_logic_vector(7 downto 0)
  );
end component fifo;
```

---

### 7.3 Type & Subtype / 类型与子类型

**EN**  
- `type` declaration on its own line.  
- Align type names.

**中文**  
- `type` 声明独占一行。  
- 类型名对齐。

```vhdl
-- ✅ Correct / 正确
type state_t is (IDLE, LOAD, RUN, DONE);
type mem_t is array (0 to 15) of std_logic_vector(31 downto 0);
subtype byte_t is std_logic_vector(7 downto 0);
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

```vhdl
---------------------------------------------------------------------------
-- Entity        : fifo
-- Project       : SOC_CORE
-- Author        : your_name
-- Created       : 2026-01-15
-- Description   : FIFO buffer
---------------------------------------------------------------------------
```

---

### 8.2 Block Comments / 块注释

**EN**  
- Place above the code block.  
- One blank line before and after.

**中文**  
- 放在代码块上方。  
- 前后各空一行。

```vhdl
-- FSM state register
state_reg : process(clk)
begin
  if rising_edge(clk) then
    state <= next_state;
  end if;
end process state_reg;
```

---

### 8.3 Inline Comments / 行尾注释

**EN**  
- Use sparingly.  
- Must align vertically if multiple inline comments are used.

**中文**  
- 谨慎使用。  
- 多个行尾注释必须纵向对齐。

```vhdl
-- ✅ Correct / 正确
signal cnt   : unsigned(7 downto 0);  -- 8-bit counter
signal wr_en : std_logic;             -- write enable
signal rd_en : std_logic;             -- read enable
```

---

### 8.4 Multi-line Comments / 多行注释

**EN**  
- Each line starts with `--`.  
- Indent consistently.

**中文**  
- 每行以 `--` 开头。  
- 缩进一致。

```vhdl
-- State machine description:
-- IDLE -> WAIT -> RUN -> DONE
```

---

## 9. Formatting Before & After Comparison / 整理前后对照表

| Syntax / 语法 | Before / 整理前 | After / 整理后 |
|---|---|---|
| entity | `entity a is port(b:in std_logic;c:out std_logic);end entity;` | `entity a is\n  port (\n    b : in std_logic;\n    c : out std_logic\n  );\nend entity;` |
| process | `process(clk)begin if rising_edge(clk)then q<=d;end if;end process;` | `process(clk)\nbegin\n  if rising_edge(clk) then\n    q <= d;\n  end if;\nend process;` |
| if | `if(a='1')then` | `if (a = '1') then` |
| case | `case(x)when"0"=>...` | `case x is\n  when "0" =>\n    ...\n  when others =>\nend case;` |
| instance | `.a=>a,.b=>b` | `.a => a,\n.b => b` |
| generic | `generic(DEPTH:integer:=16;WIDTH:integer:=8)` | `generic (\n  DEPTH : integer := 16;\n  WIDTH : integer := 8\n);` |
| for | `for i in 0 to 3 loop` | `for i in 0 to 3 loop\n  ...\nend loop;` |
| concurrent | `a<=b when sel="0" else c;` | `a <= b when sel = "0" else\n  c;` |
| package | `package p is constant W:integer:=32;end package p;` | `package p is\n  constant W : integer := 32;\nend package p;` |
| component | `component c port(a:in std_logic;b:out std_logic);end component;` | `component c\n  port (\n    a : in std_logic;\n    b : out std_logic\n  );\nend component c;` |
| attr (signal) / 属性（信号） | `signal x:std_logic;attribute mark_debug of x:signal is "true";` | `attribute mark_debug of x : signal is "true";\nsignal x : std_logic;` |
| attr (signal, multi) / 属性（信号，多属性） | `attribute mark_debug of x:s is "true";signal x:std_logic;attribute keep of x:s is "true";` | `attribute mark_debug of x : signal is "true";\nattribute keep of x : signal is "true";\nsignal x : std_logic;` |
| attr (entity) / 属性（实体） | `attribute keep of e:entity is "yes";entity e is` | `attribute keep of e : entity is "yes";\nentity e is` |
| attr (entity, multi) / 属性（实体，多属性） | `attribute keep_hierarchy of e:e is "yes";attribute dont_touch of e:e is "true";entity e is` | `attribute keep_hierarchy of e : entity is "yes";\nattribute dont_touch of e : entity is "true";\nentity e is` |
| attr (arch) / 属性（结构体） | `architecture rtl of e is begin` | `architecture rtl of e is\n  attribute keep of rtl : architecture is "true";\nbegin` |
| attr (type) / 属性（类型） | `attribute ram_style of m:type is "block";type t is...` | `attribute ram_style of m : type is "block";\ntype t is...` |
| attr (generic-ctrl) / 属性（泛型控制） | `attribute mark_debug of x:s is "true"when G else"false";` | `attribute mark_debug of x : signal is "true" when G else "false";` |
| attr (package) / 属性（Package 集中管理） | `attribute mark_debug of x:s is "true";` (declared inline) | `package common_pkg is\n  attribute mark_debug : string;\nend package;\nuse work.common_pkg.all;\nattribute mark_debug of x : signal is "true";` |

---

## Attribute-Specific Quick Reference / 属性快速参考

| Attribute / 属性 | Class / 分类 | Placement / 位置 | Format / 格式 |
|---|---|---|---|
| `mark_debug` | `signal` | Before signal / 信号之前 | `attribute mark_debug of <name> : signal is "true";` |
| `keep` (signal) | `signal` | Before signal / 信号之前 | `attribute keep of <name> : signal is "true";` |
| `keep` (entity) | `entity` | Before entity / 实体之前 | `attribute keep of <name> : entity is "yes";` |
| `keep` (architecture) | `architecture` | After arch name, before begin / 结构体名后、begin 前 | `attribute keep of <arch_name> : architecture is "true";` |
| `dont_touch` (entity) | `entity` | Before entity / 实体之前 | `attribute dont_touch of <name> : entity is "true";` |
| `dont_touch` (signal) | `signal` | Before signal / 信号之前 | `attribute dont_touch of <name> : signal is "true";` |
| `ram_style` | `type` | Before type / 类型之前 | `attribute ram_style of <type> : type is "block";` |
| `rom_style` | `type` | Before type / 类型之前 | `attribute rom_style of <type> : type is "block";` |
| `max_fanout` | `signal` | Before signal / 信号之前 | `attribute max_fanout of <name> : signal is N;` |
| `parallel_case` | `signal` | Before signal / 信号之前 | `attribute parallel_case of <name> : signal is "true";` |
| `full_case` | `signal` | Before signal / 信号之前 | `attribute full_case of <name> : signal is "true";` |

---

## 10. Hard Rules (Red Lines) / 排版红线（禁止项）

| # | Rule / 规则 (EN) | 规则 (中文) |
|---|---|---|
| 1 | **No Tabs** — spaces only | **禁止 Tab** —— 仅使用空格 |
| 2 | **No multiple statements per line** | **一行只能有一条语句** |
| 3 | `then` must be on the same line as the condition | `then` 必须与条件同行 |
| 4 | `loop` must be on the same line as `for/while` | `loop` 必须与 `for/while` 同行 |
| 5 | No misaligned generics or ports | 泛型和端口必须对齐 |
| 6 | No trailing whitespace | 禁止行尾多余空格 |
| 7 | No comment obscuring code | 注释不得遮挡代码 |
| 8 | No inconsistent indentation | 缩进必须一致 |
| 9 | No spaces between `(` and first argument | `(` 后不能有空格 |
| 10 | No spaces before `)` | `)` 前不能有空格 |
| 11 | Attribute must be on its own line | 属性必须独占一行 |
| 12 | Attribute must precede the target declaration | 属性必须放在目标声明之前 |
| 13 | Space around `of`, `:`, `is` in attributes | 属性内 `of`、`:`、`is` 两侧必须有空格 |
| 14 | Attribute class must match the target type | 属性分类必须匹配目标类型 |
| 15 | Multiple attributes on same target must be consecutive | 同一目标的多个属性必须连续放置 |
| 16 | Attribute declaration must precede attribute assignment | 属性声明必须先于属性赋值 |
| 17 | No space before `;` in attribute assignments | 属性赋值中 `;` 前不得有空格 |
| 18 | `when ... else` must stay on same line as attribute | `when ... else` 必须与属性赋值同行 |

---

## 11. Recommended Tools / 推荐工具

| Tool / 工具 | Purpose / 用途 | Language / 语言 |
|---|---|---|
| **VSG (VHDL Style Guide)** | Auto-formatting / 自动格式化 | VHDL |
| **Emacs `vhdl-mode`** | Indentation / 缩进 | VHDL |
| **VS Code + VHDL** | Editor support / 编辑器支持 | VHDL |
| **GHDL** | Simulation / 仿真 | VHDL |

---

## Appendix: Quick Reference Card / 附录：快速参考卡

```
Indent / 缩进:     2 spaces / 2 空格
Line width / 行宽: 100 columns / 100 列
Brackets / 括号:   begin/end on separate lines / begin/end 各占一行
Spacing / 空格:    Around all operators / 运算符两侧
Blank lines / 空行: 1 between blocks, 2 between process / 逻辑块间1行，process间2行
Comments / 注释:   -- for single / 单行用 --
```

---

*End of Document / 文档结束*
