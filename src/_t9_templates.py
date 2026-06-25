# -*- coding: utf-8 -*-
"""
TAB 9 - 代码模板 (子页 4)
提供 11 个常用 HDL 代码模板, 每个都有 Verilog + VHDL 两个版本
"""

_TB_VERILOG = '''\
// Module  : tb_basic
// Created : auto-generated
// 功能    : 标准 Testbench 模板 — 含时钟、复位、任务封装

`timescale 1ns / 1ps

module tb_basic ();

  parameter CLK_PERIOD = 10;

  reg        clk;
  reg        rst_n;
  wire [7:0] led;

  initial clk = 1'b0;
  always #(CLK_PERIOD/2) clk = ~clk;

  initial begin
    rst_n = 1'b0;
    #(CLK_PERIOD * 10);
    rst_n = 1'b1;
  end

  initial begin
    #(CLK_PERIOD * 1000);
    $display("[TB] Simulation finished at %t", $time);
    $finish;
  end

  initial begin
    $dumpfile("tb_basic.vcd");
    $dumpvars(0, tb_basic);
  end

  task automatic check(input [255:0] tag, input actual, input expected);
    if (actual === expected)
      $display("[PASS] %0s: 0x%h", tag, actual);
    else
      $display("[FAIL] %0s: actual=0x%h expected=0x%h",
               tag, actual, expected);
  endtask

endmodule
'''

_TB_VHDL = '''\
-- Module  : tb_basic
-- Created : auto-generated
-- 功能    : 标准 Testbench 模板

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_basic is
end entity tb_basic;

architecture sim of tb_basic is
  constant CLK_PERIOD : time := 10 ns;
  signal clk   : std_logic := '0';
  signal rst_n : std_logic := '0';
  signal led   : std_logic_vector(7 downto 0);
begin
  clk <= not clk after CLK_PERIOD / 2;

  process
  begin
    rst_n <= '0';
    wait for CLK_PERIOD * 10;
    rst_n <= '1';
    wait;
  end process;

  process(clk)
  begin
    if rising_edge(clk) then
      assert rst_n = '1'
        report "[TB] Reset released" severity note;
    end if;
  end process;

  process
  begin
    wait for CLK_PERIOD * 1000;
    report "[TB] Simulation finished" severity note;
    std.env.stop;
  end process;

end architecture sim;
'''


_GMII2RGMII_VERILOG = '''\
// Module  : gmii2rgmii
// Created : auto-generated
// 功能    : GMII (8bit@125MHz) -> RGMII (4bit DDR@125MHz)

module gmii2rgmii (
    input              clk_125m,
    input              rst_n,
    input  [7:0]       gmii_txd,
    input              gmii_tx_en,
    input              gmii_tx_er,
    output [7:0]       gmii_rxd,
    output             gmii_rx_dv,
    output             gmii_rx_er,
    output             gmii_rx_clk,
    output [3:0]       rgmii_txd,
    output             rgmii_tx_ctl,
    output             rgmii_txc,
    input  [3:0]       rgmii_rxd,
    input              rgmii_rx_ctl,
    input              rgmii_rxc
);

    ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) oddr_txd [3:0] (
        .Q (rgmii_txd), .C (clk_125m), .CE(1'b1),
        .D1(gmii_txd[3:0]), .D2(gmii_txd[7:4]), .R(1'b0));

    ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) oddr_tx_ctl (
        .Q (rgmii_tx_ctl), .C (clk_125m), .CE(1'b1),
        .D1(gmii_tx_en), .D2(gmii_tx_er), .R(1'b0));

    ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) oddr_txc (
        .Q (rgmii_txc), .C (clk_125m), .CE(1'b1),
        .D1(1'b1), .D2(1'b0), .R(1'b0));

    IDDR #(.DDR_CLK_EDGE("SAME_EDGE_PIPELINED")) iddr_rxd [3:0] (
        .Q1(gmii_rxd[3:0]), .Q2(gmii_rxd[7:4]),
        .C (rgmii_rxc), .CE(1'b1), .D(rgmii_rxd), .R(1'b0));

    IDDR #(.DDR_CLK_EDGE("SAME_EDGE_PIPELINED")) iddr_rx_ctl (
        .Q1(gmii_rx_dv), .Q2(gmii_rx_er),
        .C (rgmii_rxc), .CE(1'b1), .D(rgmii_rx_ctl), .R(1'b0));

    assign gmii_rx_clk = rgmii_rxc;

endmodule
'''

_GMII2RGMII_VHDL = '''\
-- Module  : gmii2rgmii
-- Created : auto-generated
-- 功能    : GMII -> RGMII 转换 (Xilinx 原语示例)

library ieee;
use ieee.std_logic_1164.all;

entity gmii2rgmii is
  port (
    clk_125m      : in  std_logic;
    rst_n         : in  std_logic;
    gmii_txd      : in  std_logic_vector(7 downto 0);
    gmii_tx_en    : in  std_logic;
    gmii_tx_er    : in  std_logic;
    gmii_rxd      : out std_logic_vector(7 downto 0);
    gmii_rx_dv    : out std_logic;
    gmii_rx_er    : out std_logic;
    gmii_rx_clk   : out std_logic;
    rgmii_txd     : out std_logic_vector(3 downto 0);
    rgmii_tx_ctl  : out std_logic;
    rgmii_txc     : out std_logic;
    rgmii_rxd     : in  std_logic_vector(3 downto 0);
    rgmii_rx_ctl  : in  std_logic;
    rgmii_rxc     : in  std_logic
  );
end entity gmii2rgmii;

architecture rtl of gmii2rgmii is
  component ODDR is
    generic (DDR_CLK_EDGE : string);
    port (Q: out std_logic; C, CE, D1, D2, R: in std_logic);
  end component;
  component IDDR is
    generic (DDR_CLK_EDGE : string);
    port (Q1, Q2: out std_logic; C, CE, D, R: in std_logic);
  end component;
begin
  TX_GEN : for i in 0 to 3 generate
    oddr_t : ODDR generic map (DDR_CLK_EDGE => "SAME_EDGE")
      port map (Q=>rgmii_txd(i), C=>clk_125m, CE=>'1',
                D1=>gmii_txd(i), D2=>gmii_txd(i+4), R=>'0');
  end generate;
  oddr_ctl : ODDR generic map (DDR_CLK_EDGE => "SAME_EDGE")
    port map (Q=>rgmii_tx_ctl, C=>clk_125m, CE=>'1',
              D1=>gmii_tx_en, D2=>gmii_tx_er, R=>'0');
  oddr_clk : ODDR generic map (DDR_CLK_EDGE => "SAME_EDGE")
    port map (Q=>rgmii_txc, C=>clk_125m, CE=>'1',
              D1=>'1', D2=>'0', R=>'0');
  gmii_rx_clk <= rgmii_rxc;
end architecture rtl;
'''


_UART_VERILOG = '''\
// Module  : uart_top
// Created : auto-generated
// 功能    : 简易 UART 收发器 (115200, 8N1, 无流控)

module uart_top #(
    parameter CLK_FREQ  = 50_000_000,
    parameter BAUD_RATE = 115200
) (
    input        clk, rst_n, rx,
    output       tx,
    input  [7:0] tx_data,
    input        tx_start,
    output       tx_busy,
    output [7:0] rx_data,
    output       rx_ready
);

    localparam BAUD_DIV = CLK_FREQ / BAUD_RATE;

    reg [15:0] rx_cnt;
    reg [3:0]  rx_bit;
    reg [7:0]  rx_shift;
    reg        rx_done;
    reg [1:0]  rx_sync;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync <= 2'b11; rx_cnt <= 0; rx_bit <= 0;
            rx_shift <= 0; rx_done <= 0;
        end else begin
            rx_sync <= {rx_sync[0], rx};
            case (rx_bit)
                0: if (rx_sync == 2'b10) begin
                    rx_cnt <= BAUD_DIV/2; rx_bit <= 1;
                end
                1: if (rx_cnt == 0) begin
                    rx_shift[0] <= rx_sync[1];
                    rx_cnt <= BAUD_DIV; rx_bit <= 2;
                end else rx_cnt <= rx_cnt - 1;
                2,3,4,5,6,7,8: if (rx_cnt == 0) begin
                    rx_shift <= {rx_sync[1], rx_shift[7:1]};
                    rx_cnt <= BAUD_DIV; rx_bit <= rx_bit + 1;
                end else rx_cnt <= rx_cnt - 1;
                9: if (rx_cnt == 0) begin
                    rx_done <= 1; rx_bit <= 0;
                end else rx_cnt <= rx_cnt - 1;
            endcase
            if (rx_done) rx_done <= 0;
        end
    end

    assign rx_data = rx_shift; assign rx_ready = rx_done;

    reg [15:0] tx_cnt;
    reg [3:0]  tx_bit;
    reg [7:0]  tx_shift;
    reg        tx_reg, tx_run;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_cnt <= 0; tx_bit <= 0; tx_reg <= 1; tx_run <= 0;
        end else if (tx_start && !tx_run) begin
            tx_run <= 1; tx_shift <= tx_data;
            tx_bit <= 0; tx_reg <= 0; tx_cnt <= BAUD_DIV;
        end else if (tx_run) begin
            if (tx_cnt == 0) begin
                tx_cnt <= BAUD_DIV;
                if (tx_bit < 8) begin
                    tx_reg <= tx_shift[0];
                    tx_shift <= tx_shift >> 1;
                    tx_bit <= tx_bit + 1;
                end else if (tx_bit == 8) begin
                    tx_reg <= 1; tx_bit <= tx_bit + 1;
                end else tx_run <= 0;
            end else tx_cnt <= tx_cnt - 1;
        end
    end

    assign tx = tx_reg; assign tx_busy = tx_run;
endmodule
'''

_UART_VHDL = '''\
-- Module  : uart_top
-- Created : auto-generated
-- 功能    : 简易 UART 收发器 (115200, 8N1)

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_top is
  generic (CLK_FREQ:integer:=50_000_000; BAUD_RATE:integer:=115200);
  port (
    clk: in std_logic; rst_n: in std_logic;
    rx: in std_logic; tx: out std_logic;
    tx_data: in std_logic_vector(7 downto 0);
    tx_start: in std_logic; tx_busy: out std_logic;
    rx_data: out std_logic_vector(7 downto 0);
    rx_ready: out std_logic
  );
end entity uart_top;

architecture rtl of uart_top is
  constant BAUD_DIV : integer := CLK_FREQ / BAUD_RATE;
  signal rx_cnt, tx_cnt : integer range 0 to BAUD_DIV;
  signal rx_bit, tx_bit : integer range 0 to 10 := 0;
  signal rx_shift, tx_shift : std_logic_vector(7 downto 0);
  signal rx_done, tx_run : std_logic := '0';
  signal rx_sync : std_logic_vector(1 downto 0) := "11";
  signal tx_reg : std_logic := '1';
begin
  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then
        rx_sync <= "11"; rx_bit <= 0; rx_done <= '0';
      else
        rx_sync <= rx_sync(0) & rx;
        if rx_bit=0 and rx_sync="10" then
          rx_bit <= 1; rx_cnt <= BAUD_DIV/2;
        elsif rx_bit>0 and rx_cnt=0 then
          if rx_bit<9 then
            rx_shift(rx_bit-1) <= rx_sync(1);
            rx_bit <= rx_bit+1; rx_cnt <= BAUD_DIV;
          else rx_done <= '1'; rx_bit <= 0;
          end if;
        elsif rx_cnt>0 then rx_cnt <= rx_cnt-1;
        end if;
        if rx_done='1' then rx_done <= '0'; end if;
      end if;
    end if;
  end process;
  rx_data <= rx_shift; rx_ready <= rx_done;

  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then
        tx_reg <= '1'; tx_run <= '0'; tx_bit <= 0;
      elsif tx_start='1' and tx_run='0' then
        tx_run <= '1'; tx_shift <= tx_data;
        tx_reg <= '0'; tx_bit <= 0; tx_cnt <= BAUD_DIV;
      elsif tx_run='1' then
        if tx_cnt=0 then
          tx_cnt <= BAUD_DIV;
          if tx_bit<8 then
            tx_reg <= tx_shift(0);
            tx_shift <= '0' & tx_shift(7 downto 1);
            tx_bit <= tx_bit+1;
          elsif tx_bit=8 then tx_reg <= '1'; tx_bit <= tx_bit+1;
          else tx_run <= '0';
          end if;
        else tx_cnt <= tx_cnt-1;
        end if;
      end if;
    end if;
  end process;
  tx <= tx_reg; tx_busy <= tx_run;
end architecture rtl;
'''

_IIC_VERILOG = '''\
// Module  : iic_master
// Created : auto-generated
// 功能    : 简易 I2C 主控 (100kHz / 400kHz)

module iic_master #(
    parameter CLK_FREQ = 50_000_000,
    parameter SCL_FREQ = 100_000
) (
    input        clk, rst_n,
    output       scl, inout sda,
    input  [6:0] slave_addr,
    input        rw,
    input  [7:0] wr_data,
    output [7:0] rd_data,
    output       done, err,
    input        start
);

    localparam SCL_DIV = CLK_FREQ / (SCL_FREQ * 2);
    localparam S_IDLE  = 0, S_START = 1, S_ADDR = 2, S_ACK1 = 3;
    localparam S_WR    = 4, S_ACK2  = 5, S_RD    = 6, S_ACK3 = 7;
    localparam S_STOP  = 8, S_DONE  = 9;

    reg [3:0]  state = S_IDLE;
    reg [15:0] div_cnt = 0;
    reg        scl_reg = 1, sda_reg = 1, sda_oe = 0;
    reg [3:0]  bit_cnt = 0;
    reg [7:0]  shift = 0;

    assign scl = scl_reg;
    assign sda = sda_oe ? sda_reg : 1'bz;
    assign done = (state == S_DONE) && !err;
    assign err  = (state == S_DONE) && sda_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; div_cnt <= 0;
            scl_reg <= 1; sda_reg <= 1;
            sda_oe <= 0; bit_cnt <= 0;
        end else begin
            case (state)
                S_IDLE: if (start) begin
                    state <= S_START; sda_reg <= 0;
                    sda_oe <= 1; div_cnt <= SCL_DIV;
                end
                S_START: if (div_cnt == 0) begin
                    scl_reg <= 0; shift <= {slave_addr, rw};
                    bit_cnt <= 8; state <= S_ADDR;
                end else div_cnt <= div_cnt - 1;
                S_ADDR: if (div_cnt == 0) begin
                    if (bit_cnt > 0) begin
                        sda_reg <= shift[7];
                        shift <= {shift[6:0], 1'b0};
                        bit_cnt <= bit_cnt - 1;
                        div_cnt <= SCL_DIV;
                    end else begin
                        sda_oe <= 0; state <= S_ACK1;
                        div_cnt <= SCL_DIV;
                    end
                end else div_cnt <= div_cnt - 1;
                S_ACK1: if (div_cnt == 0) begin
                    sda_oe <= 1; sda_reg <= wr_data[7];
                    bit_cnt <= 8; state <= S_WR;
                end else div_cnt <= div_cnt - 1;
                S_WR:  state <= S_STOP;
                S_STOP: begin sda_reg <= 0; state <= S_DONE; end
                S_DONE: state <= S_IDLE;
            endcase
        end
    end
endmodule
'''


_IIC_VHDL = '''\
-- Module  : iic_master
-- Created : auto-generated
-- 功能    : 简易 I2C 主控

library ieee;
use ieee.std_logic_1164.all;

entity iic_master is
  generic (CLK_FREQ:integer:=50_000_000; SCL_FREQ:integer:=100_000);
  port (
    clk: in std_logic; rst_n: in std_logic;
    scl: out std_logic; sda: inout std_logic;
    slave_addr: in std_logic_vector(6 downto 0);
    rw: in std_logic; wr_data: in std_logic_vector(7 downto 0);
    rd_data: out std_logic_vector(7 downto 0);
    done: out std_logic; err: out std_logic;
    start: in std_logic
  );
end entity iic_master;

architecture rtl of iic_master is
  constant SCL_DIV : integer := CLK_FREQ / (SCL_FREQ * 2);
  signal state   : integer range 0 to 9 := 0;
  signal scl_reg : std_logic := '1';
  signal sda_reg : std_logic := '1';
begin
  scl <= scl_reg;
  sda <= sda_reg when state /= 3 else 'Z';
  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then
        state <= 0; scl_reg <= '1'; sda_reg <= '1';
      elsif start = '1' and state = 0 then
        state <= 1; sda_reg <= '0';
      elsif state = 1 then scl_reg <= '0'; state <= 8;
      elsif state = 8 then sda_reg <= '0'; state <= 9;
      elsif state = 9 then state <= 0;
      end if;
    end if;
  end process;
  done <= '1' when state = 9 else '0';
  err  <= '0';
end architecture rtl;
'''


_DEBUG_VERILOG = '''\
// Module  : debug_demo
// Created : auto-generated
// 功能    : Vivado ILA 调试示例

module debug_demo (
    input        clk, rst_n,
    input  [7:0] data_in,
    input        data_valid,
    output [7:0] data_out,
    output       data_ready
);

    (* mark_debug = "true" *) wire        dbg_valid;
    (* mark_debug = "true" *) wire [7:0]  dbg_data;
    (* mark_debug = "true" *) wire [3:0]  dbg_state;

    reg [3:0]  state = 0;
    reg [7:0]  data_buf = 0;
    reg        ready = 0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 0; data_buf <= 0; ready <= 0;
        end else begin
            case (state)
                0: if (data_valid) begin
                    data_buf <= data_in; state <= 1;
                end
                1: state <= 2;
                2: begin ready <= 1; state <= 3; end
                3: begin ready <= 0; state <= 0; end
            endcase
        end
    end

    assign data_out   = data_buf;
    assign data_ready = ready;
    assign dbg_valid  = data_valid;
    assign dbg_data   = data_buf;
    assign dbg_state  = state;
endmodule
'''


_DEBUG_VHDL = '''\
-- Module  : debug_demo
-- Created : auto-generated
-- 功能    : Vivado ILA 调试示例 (VHDL)

library ieee;
use ieee.std_logic_1164.all;

entity debug_demo is
  port (
    clk: in std_logic; rst_n: in std_logic;
    data_in: in std_logic_vector(7 downto 0);
    data_valid: in std_logic;
    data_out: out std_logic_vector(7 downto 0);
    data_ready: out std_logic
  );
end entity debug_demo;

architecture rtl of debug_demo is
  signal state : integer range 0 to 3 := 0;
  signal data_buf : std_logic_vector(7 downto 0) := (others => '0');
  signal ready : std_logic := '0';
  attribute mark_debug : boolean;
  attribute mark_debug of data_valid : signal is true;
  attribute mark_debug of data_buf   : signal is true;
  attribute mark_debug of state      : signal is true;
begin
  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then
        state <= 0; data_buf <= (others => '0'); ready <= '0';
      else
        case state is
          when 0 => if data_valid = '1' then
                      data_buf <= data_in; state <= 1; end if;
          when 1 => state <= 2;
          when 2 => ready <= '1'; state <= 3;
          when 3 => ready <= '0'; state <= 0;
        end case;
      end if;
    end if;
  end process;
  data_out   <= data_buf;
  data_ready <= ready;
end architecture rtl;
'''


_FSM_VERILOG = '''\
// Module  : fsm_3stage
// Created : auto-generated
// 功能    : 标准三段式状态机 (现态/次态/输出分离)

module fsm_3stage #(
    parameter [1:0] S_IDLE = 2'd0, S_RUN = 2'd1, S_DONE = 2'd2
) (
    input        clk, rst_n,
    input        trig, done_tick,
    output reg   busy, done
);

    reg [1:0] curr_state, next_state;

    // 第 1 段
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) curr_state <= S_IDLE;
        else        curr_state <= next_state;
    end

    // 第 2 段
    always @(*) begin
        case (curr_state)
            S_IDLE: next_state = trig      ? S_RUN  : S_IDLE;
            S_RUN : next_state = done_tick ? S_DONE : S_RUN;
            S_DONE: next_state = S_IDLE;
            default: next_state = S_IDLE;
        endcase
    end

    // 第 3 段
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin busy <= 0; done <= 0; end
        else begin
            busy <= (curr_state == S_RUN) || (next_state == S_RUN);
            done <= (curr_state == S_DONE);
        end
    end
endmodule
'''


_FSM_VHDL = '''\
-- Module  : fsm_3stage
-- Created : auto-generated
-- 功能    : 标准三段式状态机

library ieee;
use ieee.std_logic_1164.all;

entity fsm_3stage is
  port (
    clk: in std_logic; rst_n: in std_logic;
    trig: in std_logic; done_tick: in std_logic;
    busy: out std_logic; done: out std_logic
  );
end entity fsm_3stage;

architecture rtl of fsm_3stage is
  type state_t is (S_IDLE, S_RUN, S_DONE);
  signal curr_state : state_t := S_IDLE;
  signal next_state : state_t;
begin
  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then curr_state <= S_IDLE;
      else curr_state <= next_state;
      end if;
    end if;
  end process;
  process(curr_state, trig, done_tick) begin
    case curr_state is
      when S_IDLE => next_state <= S_RUN  when trig      = '1' else S_IDLE;
      when S_RUN  => next_state <= S_DONE when done_tick = '1' else S_RUN;
      when S_DONE => next_state <= S_IDLE;
    end case;
  end process;
  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then busy <= '0'; done <= '0';
      else
        busy <= '1' when curr_state = S_RUN or next_state = S_RUN else '0';
        done <= '1' when curr_state = S_DONE else '0';
      end if;
    end if;
  end process;
end architecture rtl;
'''


_WDT_VERILOG = '''\
// Module  : watchdog
// Created : auto-generated
// 功能    : 看门狗定时器 - 超时未喂狗则复位

module watchdog #(
    parameter CLK_FREQ   = 50_000_000,
    parameter TIMEOUT_US = 1_000_000
) (
    input        clk, rst_n, feed,
    output reg   wdt_reset
);

    localparam [31:0] CNT_MAX = (CLK_FREQ / 1_000_000) * TIMEOUT_US;
    reg [31:0] cnt = 0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 0; wdt_reset <= 0;
        end else begin
            if (feed) begin
                cnt <= 0; wdt_reset <= 0;
            end else if (cnt >= CNT_MAX - 1) begin
                wdt_reset <= 1;
            end else cnt <= cnt + 1;
        end
    end
endmodule
'''


_WDT_VHDL = '''\
-- Module  : watchdog
-- Created : auto-generated
-- 功能    : 看门狗定时器

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity watchdog is
  generic (CLK_FREQ:integer:=50_000_000; TIMEOUT_US:integer:=1_000_000);
  port (
    clk: in std_logic; rst_n: in std_logic;
    feed: in std_logic; wdt_reset: out std_logic
  );
end entity watchdog;

architecture rtl of watchdog is
  constant CNT_MAX : integer := (CLK_FREQ / 1_000_000) * TIMEOUT_US;
  signal cnt : integer range 0 to CNT_MAX := 0;
begin
  process(clk) begin
    if rising_edge(clk) then
      if rst_n = '0' then cnt <= 0; wdt_reset <= '0';
      elsif feed = '1' then cnt <= 0; wdt_reset <= '0';
      elsif cnt >= CNT_MAX - 1 then wdt_reset <= '1';
      else cnt <= cnt + 1;
      end if;
    end if;
  end process;
end architecture rtl;
'''


# ═══════════════════════════════════════════════════════════════
# 模板数据库
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
# 8. AXI-Lite 寄存器读写 (fork..join 并行握手)
# ═══════════════════════════════════════════════════════════════
_AXILITE_WR_VERILOG = '''\
// Module  : tb_axilite
// Created : auto-generated
// 功能    : AXI-Lite 寄存器读写 task 模板
//           适用于 Zynq PS-PL 寄存器交互 / 自定义 IP 验证

`timescale 1ns / 1ps

module tb_axilite ();

  reg         sys_clk = 0;
  reg         sys_rstn = 0;
  always #5 sys_clk = ~sys_clk;  // 100MHz

  // AXI-Lite Write Address
  reg  [31:0]  s_axil_awaddr  = 0;
  reg          s_axil_awvalid = 0;
  wire         s_axil_awready;
  // AXI-Lite Write Data
  reg  [31:0]  s_axil_wdata   = 0;
  reg  [3:0]   s_axil_wstrb   = 0;
  reg          s_axil_wvalid  = 0;
  wire         s_axil_wready;
  // AXI-Lite Write Response
  wire [1:0]   s_axil_bresp;
  wire         s_axil_bvalid;
  reg          s_axil_bready  = 0;
  // AXI-Lite Read Address
  reg  [31:0]  s_axil_araddr  = 0;
  reg          s_axil_arvalid = 0;
  wire         s_axil_arready;
  // AXI-Lite Read Data
  wire [31:0]  s_axil_rdata;
  wire [1:0]   s_axil_rresp;
  wire         s_axil_rvalid;
  reg          s_axil_rready  = 0;

  // ── 写寄存器 task ──
  task AXILITE_WR_reg;
    input  [31:0] address;
    input  [31:0] datain;
  begin
    @(posedge sys_clk);
    s_axil_awaddr  = address;
    s_axil_wdata   = datain;
    s_axil_wstrb   = 4'hF;
    s_axil_awvalid = 1'b1;
    s_axil_wvalid  = 1'b1;

    fork
      // 写地址通道
      begin
        @(negedge s_axil_awready);
        s_axil_awaddr  = 32'h00000000;
        s_axil_awvalid = 1'b0;
      end

      // 写数据通道
      begin
        @(negedge s_axil_wready);
        s_axil_wdata   = 32'h00000000;
        s_axil_wvalid  = 1'b0;
        s_axil_wstrb   = 4'h0;
      end

      // 写响应通道
      begin
        @(posedge s_axil_bvalid);
        s_axil_bready = 1'b1;
        @(posedge sys_clk);
        @(posedge sys_clk);
        s_axil_bready = 1'b0;
      end
    join

    $display("The AXILITE_WR_reg write address = 32'h%h, data = 32'h%h",
             address, datain);
    repeat(3) @(posedge sys_clk);
  end
  endtask

  // ── 读寄存器 task ──
  task AXILITE_RD_reg;
    input  [31:0]  address;
    output [31:0]  rd_dout;
  begin
    @(posedge sys_clk);
    s_axil_araddr  = address;
    s_axil_arvalid = 1'b1;
    s_axil_rready  = 1'b1;

    fork
      // 读地址通道
      begin
        @(negedge s_axil_arready);
        s_axil_araddr  = 32'h00000000;
        s_axil_arvalid = 1'b0;
      end

      // 读数据通道 (拉低 rready)
      begin
        @(negedge s_axil_rvalid);
        s_axil_rready = 1'b0;
      end

      // 采样数据
      begin
        @(posedge s_axil_rvalid);
        rd_dout = s_axil_rdata;
        $display("The AXILITE_RD_reg read address = 32'h%h, data = 32'h%h",
                 address, s_axil_rdata);
      end
    join

    repeat(3) @(posedge sys_clk);
  end
  endtask

  reg [31:0] rd_data;
  initial begin
    sys_rstn = 0;
    repeat(10) @(posedge sys_clk);
    sys_rstn = 1;
    repeat(5)  @(posedge sys_clk);

    AXILITE_WR_reg(32'h0000_0004, 32'hA5A5_A5A5);
    AXILITE_RD_reg(32'h0000_0004, rd_data);
    AXILITE_WR_reg(32'h0000_0008, 32'h1234_5678);
    AXILITE_RD_reg(32'h0000_0008, rd_data);

    repeat(20) @(posedge sys_clk);
    $finish;
  end

  initial begin
    $dumpfile("tb_axilite.vcd");
    $dumpvars(0, tb_axilite);
  end

endmodule
'''

_AXILITE_WR_VHDL = '''\
-- Module  : tb_axilite
-- Created : auto-generated
-- 功能    : AXI-Lite 寄存器读写模板 (VHDL 完整版, 含 procedure)
--           VHDL 没有 fork..join, 用并发 process 模拟
--           适用于 Zynq PS-PL 寄存器交互 / 自定义 IP 验证
--           完整 Slave 建议用 Vivado/Quartus 自动生成

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_axilite is
end entity tb_axilite;

architecture sim of tb_axilite is

  signal sys_clk : std_logic := '0';
  signal sys_rstn : std_logic := '0';

  -- AXI-Lite Write Address
  signal s_axil_awaddr  : std_logic_vector(31 downto 0) := (others => '0');
  signal s_axil_awvalid : std_logic := '0';
  signal s_axil_awready : std_logic := '0';
  -- AXI-Lite Write Data
  signal s_axil_wdata   : std_logic_vector(31 downto 0) := (others => '0');
  signal s_axil_wstrb   : std_logic_vector(3 downto 0)  := (others => '0');
  signal s_axil_wvalid  : std_logic := '0';
  signal s_axil_wready  : std_logic := '0';
  -- AXI-Lite Write Response
  signal s_axil_bresp   : std_logic_vector(1 downto 0)  := (others => '0');
  signal s_axil_bvalid  : std_logic := '0';
  signal s_axil_bready  : std_logic := '0';
  -- AXI-Lite Read Address
  signal s_axil_araddr  : std_logic_vector(31 downto 0) := (others => '0');
  signal s_axil_arvalid : std_logic := '0';
  signal s_axil_arready : std_logic := '0';
  -- AXI-Lite Read Data
  signal s_axil_rdata   : std_logic_vector(31 downto 0) := (others => '0');
  signal s_axil_rresp   : std_logic_vector(1 downto 0)  := (others => '0');
  signal s_axil_rvalid  : std_logic := '0';
  signal s_axil_rready  : std_logic := '0';

  -- ── 写寄存器 procedure (VHDL 替代 task) ──
  procedure AXILITE_WR_reg (
    signal clk         : in  std_logic;
    signal awready     : in  std_logic;
    signal wready      : in  std_logic;
    signal bvalid      : in  std_logic;
    signal awaddr      : out std_logic_vector(31 downto 0);
    signal awvalid     : out std_logic;
    signal wdata       : out std_logic_vector(31 downto 0);
    signal wstrb       : out std_logic_vector(3 downto 0);
    signal wvalid      : out std_logic;
    signal bready      : out std_logic;
    constant address   : in  std_logic_vector(31 downto 0);
    constant datain    : in  std_logic_vector(31 downto 0)
  ) is
  begin
    wait until rising_edge(clk);
    awaddr  <= address;
    wdata   <= datain;
    wstrb   <= "1111";
    awvalid <= '1';
    wvalid  <= '1';

    -- AW 通道: 等待 awready
    aw_handshake : process(awready)
    begin
      if awready = '0' then
        awvalid <= '0';
        awaddr  <= (others => '0');
      end if;
    end process;

    -- W 通道: 等待 wready
    w_handshake : process(wready)
    begin
      if wready = '0' then
        wvalid <= '0';
        wdata  <= (others => '0');
        wstrb  <= (others => '0');
      end if;
    end process;

    -- B 通道: 等待 bvalid, 拉高 bready
    b_handshake : process(bvalid)
    begin
      if bvalid = '1' then
        bready <= '1';
        for i in 1 to 2 loop
          wait until rising_edge(clk);
        end loop;
        bready <= '0';
      end if;
    end process;

    report "The AXILITE_WR_reg write address = 32'h" &
           integer'image(to_integer(unsigned(address))) &
           ", data = 32'h" &
           integer'image(to_integer(unsigned(datain)));
    for i in 1 to 3 loop
      wait until rising_edge(clk);
    end loop;
  end procedure;

  -- ── 读寄存器 procedure ──
  procedure AXILITE_RD_reg (
    signal clk         : in  std_logic;
    signal arready     : in  std_logic;
    signal rvalid      : in  std_logic;
    signal rdata       : in  std_logic_vector(31 downto 0);
    signal araddr      : out std_logic_vector(31 downto 0);
    signal arvalid     : out std_logic;
    signal rready      : out std_logic;
    constant address   : in  std_logic_vector(31 downto 0);
    signal   rd_dout   : out std_logic_vector(31 downto 0)
  ) is
  begin
    wait until rising_edge(clk);
    araddr  <= address;
    arvalid <= '1';
    rready  <= '1';

    -- AR 通道
    ar_handshake : process(arready)
    begin
      if arready = '0' then
        arvalid <= '0';
        araddr  <= (others => '0');
      end if;
    end process;

    -- R 通道: 等待 rvalid, 拉低 rready
    r_handshake : process(rvalid)
    begin
      if rvalid = '0' then
        rready <= '0';
      end if;
    end process;

    -- 采样数据
    wait until rising_edge(rvalid);
    rd_dout <= rdata;
    report "The AXILITE_RD_reg read address = 32'h" &
           integer'image(to_integer(unsigned(address))) &
           ", data = 32'h" &
           integer'image(to_integer(unsigned(rdata)));

    for i in 1 to 3 loop
      wait until rising_edge(clk);
    end loop;
  end procedure;

begin

  -- 时钟 100 MHz
  sys_clk <= not sys_clk after 5 ns;

  -- ── 简单 DUT (AXI-Lite Slave Model) ──
  -- 这里只演示 AW/W/AR 通道就绪信号, 实际请接 Vivado 生成的 AXI IP
  awready_proc : process(sys_clk)
  begin
    if rising_edge(sys_clk) then
      if sys_rstn = '0' then
        s_axil_awready <= '0';
        s_axil_wready  <= '0';
        s_axil_arready <= '0';
        s_axil_rvalid  <= '0';
        s_axil_bvalid  <= '0';
      else
        -- 简化: 1 周期后握手
        s_axil_awready <= s_axil_awvalid;
        s_axil_wready  <= s_axil_wvalid;
        s_axil_arready <= s_axil_arvalid;
        s_axil_bvalid  <= s_axil_awready and s_axil_wready;
        s_axil_rvalid  <= s_axil_arready;
        s_axil_bresp   <= "00";
        s_axil_rresp   <= "00";
        s_axil_rdata   <= s_axil_araddr;  -- 回环: 读到的数据 = 地址
      end if;
    end if;
  end process;

  -- ── 仿真流程 ──
  stim : process
    variable rd_data : std_logic_vector(31 downto 0);
  begin
    -- 复位
    sys_rstn <= '0';
    for i in 1 to 10 loop
      wait until rising_edge(sys_clk);
    end loop;
    sys_rstn <= '1';
    for i in 1 to 5 loop
      wait until rising_edge(sys_clk);
    end loop;

    -- 写 0x04 = 0xA5A5A5A5
    AXILITE_WR_reg (
      clk     => sys_clk,
      awready => s_axil_awready,
      wready  => s_axil_wready,
      bvalid  => s_axil_bvalid,
      awaddr  => s_axil_awaddr,
      awvalid => s_axil_awvalid,
      wdata   => s_axil_wdata,
      wstrb   => s_axil_wstrb,
      wvalid  => s_axil_wvalid,
      bready  => s_axil_bready,
      address => std_logic_vector(to_unsigned(16#0000_0004#, 32)),
      datain  => std_logic_vector(to_unsigned(16#A5A5_A5A5#, 32))
    );

    -- 读 0x04
    AXILITE_RD_reg (
      clk     => sys_clk,
      arready => s_axil_arready,
      rvalid  => s_axil_rvalid,
      rdata   => s_axil_rdata,
      araddr  => s_axil_araddr,
      arvalid => s_axil_arvalid,
      rready  => s_axil_rready,
      address => std_logic_vector(to_unsigned(16#0000_0004#, 32)),
      rd_dout => rd_data
    );

    -- 写 0x08 = 0x12345678
    AXILITE_WR_reg (
      clk     => sys_clk,
      awready => s_axil_awready,
      wready  => s_axil_wready,
      bvalid  => s_axil_bvalid,
      awaddr  => s_axil_awaddr,
      awvalid => s_axil_awvalid,
      wdata   => s_axil_wdata,
      wstrb   => s_axil_wstrb,
      wvalid  => s_axil_wvalid,
      bready  => s_axil_bready,
      address => std_logic_vector(to_unsigned(16#0000_0008#, 32)),
      datain  => std_logic_vector(to_unsigned(16#1234_5678#, 32))
    );

    -- 读 0x08
    AXILITE_RD_reg (
      clk     => sys_clk,
      arready => s_axil_arready,
      rvalid  => s_axil_rvalid,
      rdata   => s_axil_rdata,
      araddr  => s_axil_araddr,
      arvalid => s_axil_arvalid,
      rready  => s_axil_rready,
      address => std_logic_vector(to_unsigned(16#0000_0008#, 32)),
      rd_dout => rd_data
    );

    for i in 1 to 20 loop
      wait until rising_edge(sys_clk);
    end loop;
    report "Simulation finished" severity note;
    std.env.stop;
  end process;

end architecture sim;
'''


# ═══════════════════════════════════════════════════════════════
# 9. 高级语法: 2D 数组 + 循环 + fork..join
# ═══════════════════════════════════════════════════════════════
_SYNTAX_VERILOG = '''\
// Module  : syntax_demo
// Created : auto-generated
// 功能    : Verilog 高级语法 - 2D 数组、for/while/repeat/do、fork..join

`timescale 1ns / 1ps

module syntax_demo ();

  reg clk = 0;
  always #5 clk = ~clk;

  // ── 1) 2D 数组 (packed / unpacked) ──
  reg [7:0]  mem_packed   [0:15];
  reg [3:0]  mem_2d       [0:3][0:7];      // 4x8 个 4bit
  reg [7:0]  image [0:7][0:7];             // 8x8 灰度图
  integer    matrix [0:2][0:2];            // 3x3 整数矩阵

  initial begin
    $display("=== 2D 数组初始化 ===");
    for (int i = 0; i < 4; i++) begin
      for (int j = 0; j < 8; j++) begin
        mem_2d[i][j] = i * 8 + j;
      end
    end
    $display("mem_2d[2][5] = %0d", mem_2d[2][5]);

    foreach (image[i, j]) image[i][j] = 0;

    for (int r = 0; r < 3; r++)
      for (int c = 0; c < 3; c++)
        matrix[r][c] = (r == c) ? 1 : 0;
  end

  // ── 2) 循环语句 ──
  reg [7:0] data;
  initial begin
    $display("\\n=== for 循环 ===");
    for (int i = 0; i < 8; i++)
      $display("for i=%0d, 2**i=%0d", i, 2**i);

    $display("\\n=== while 循环 ===");
    data = 8'd1;
    while (data != 8'd0) begin
      $display("while data=%0d", data);
      data = data << 1;
    end

    $display("\\n=== repeat 循环 ===");
    repeat (5) $display("repeat tick");

    $display("\\n=== do..while (SystemVerilog) ===");
    data = 0;
    do begin
      $display("do data=%0d", data);
      data = data + 1;
    end while (data < 3);
  end

  // ── 3) fork..join 并行块 ──
  reg [7:0] q_a, q_b, q_c;

  task parallel_demo;
  begin
    $display("\\n=== fork..join (并行) ===");
    $display("start: t=%0t", $time);

    fork
      begin
        #10;
        q_a = 8'haa;
        $display("A done: t=%0t, q_a=0x%h", $time, q_a);
      end
      begin
        #20;
        q_b = 8'hbb;
        $display("B done: t=%0t, q_b=0x%h", $time, q_b);
      end
      begin
        repeat (5) @(posedge clk);
        q_c = 8'hcc;
        $display("C done: t=%0t, q_c=0x%h", $time, q_c);
      end
    join

    $display("end: t=%0t", $time);
  end
  endtask

  initial begin
    #50;
    parallel_demo();
    $finish;
  end

  initial begin
    $dumpfile("syntax_demo.vcd");
    $dumpvars(0, syntax_demo);
  end

  // ═══════════════════════════════════════════════════════
  // ── 4) generate + genvar (模块化例化/结构化硬件) ──
  // ═══════════════════════════════════════════════════════

  // (a) generate for — 多实例例化
  // 例: 8 个 LED 独立闪烁, 每个 blink 周期不同
  genvar gi;
  generate
    for (gi = 0; gi < 8; gi = gi + 1) begin : g_led_blink
      reg [23:0] cnt;
      always @(posedge clk) cnt <= cnt + gi + 1;  // 计数速度不同
      wire blink = cnt[23];                       // 翻转位
      // 假设有 8 个 LED, 这里只例化示意
      // led_module u_led (.blink(blink), .idx(gi));
    end
  endgenerate

  // (b) generate for — 寄存器数组选择
  wire [7:0] data_in_arr  [0:7];
  wire [7:0] data_out_arr [0:7];
  generate
    for (genvar i = 0; i < 8; i++) begin : g_buf
      // 8 个独立的 8bit 缓冲
      reg [7:0] buf;
      always @(posedge clk) buf <= data_in_arr[i];
      assign data_out_arr[i] = buf;
    end
  endgenerate

  // (c) generate if — 条件例化 (按参数选不同实现)
  parameter MODE = 0;  // 0: fast, 1: slow
  generate
    if (MODE == 0) begin : g_fast
      assign data_out_arr[0] = data_in_arr[0];  // 直通
    end else begin : g_slow
      reg [7:0] slow_buf;
      always @(posedge clk) slow_buf <= data_in_arr[0];
      assign data_out_arr[0] = slow_buf;
    end
  endgenerate

  // (d) generate case — 多选一例化
  parameter WIDTH = 4;
  generate
    case (WIDTH)
      1: assign data_out_arr[1] = data_in_arr[1][0];
      2: assign data_out_arr[1] = data_in_arr[1][1:0];
      4: assign data_out_arr[1] = data_in_arr[1];
      8: assign data_out_arr[1] = data_in_arr[1];
      default: assign data_out_arr[1] = '0;
    endcase
  endgenerate

endmodule
'''

_SYNTAX_VHDL = '''\
-- Module  : syntax_demo
-- Created : auto-generated
-- 功能    : VHDL 高级语法 - 2D 数组、loop 循环、并发 process

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity syntax_demo is
end entity syntax_demo;

architecture sim of syntax_demo is
  signal clk : std_logic := '0';

  type mem_2d_t is array (0 to 3, 0 to 7) of std_logic_vector(3 downto 0);
  signal mem_2d : mem_2d_t;
  type image_t is array (0 to 7, 0 to 7) of integer;
  signal image  : image_t;
  type matrix_t is array (0 to 2, 0 to 2) of integer;
  signal matrix : matrix_t := (others => (others => 0));
begin
  clk <= not clk after 5 ns;

  -- 1) 2D 数组初始化
  process
  begin
    for i in 0 to 3 loop
      for j in 0 to 7 loop
        mem_2d(i, j) <= std_logic_vector(to_unsigned(i * 8 + j, 4));
      end loop;
    end loop;

    for r in 0 to 2 loop
      for c in 0 to 2 loop
        if r = c then
          matrix(r, c) <= 1;
        else
          matrix(r, c) <= 0;
        end if;
      end loop;
    end loop;

    report "matrix(1,1) = " & integer'image(matrix(1, 1));
    wait;
  end process;

  -- 2) loop 循环
  process
    variable data : integer;
  begin
    for i in 0 to 7 loop
      report "for i=" & integer'image(i);
    end loop;

    data := 1;
    while data < 256 loop
      report "while data=" & integer'image(data);
      data := data * 2;
    end loop;
    wait;
  end process;

  -- 3) 并发 process (类似 fork..join)
  process_10ns : process
  begin
    wait for 10 ns;
    report "A done (10ns)";
  end process;

  process_20ns : process
  begin
    wait for 20 ns;
    report "B done (20ns)";
  end process;

  process_clk : process
    variable cnt : integer := 0;
  begin
    while cnt < 5 loop
      wait until rising_edge(clk);
      cnt := cnt + 1;
    end loop;
    report "C done (5 clocks)";
    wait;
  end process;

end architecture sim;
'''


# ═══════════════════════════════════════════════════════════════
# 10. 延时计数 (ms / us / ns 精度)
# ═══════════════════════════════════════════════════════════════
_DELAY_VERILOG = '''\
// Module  : delay_counter
// Created : auto-generated
// 功能    : 可配置延时计数器 (ms / us / ns 三种精度)
//           典型应用: 状态机延时、LED 闪烁、外设上电时序

`timescale 1ns / 1ps

module delay_counter #(
    parameter CLK_FREQ = 50_000_000   // 50 MHz
) (
    input        clk,
    input        rst_n,
    input        start,         // 启动一次延时
    input  [31:0] delay_us,     // 延时值 (微秒), 0 = 不延时
    input  [31:0] delay_ms,     // 延时值 (毫秒), 0 = 不延时
    input  [31:0] delay_ns,     // 延时值 (纳秒), 0 = 不延时
    output reg   done          // 延时完成 (单脉冲)
);

    // 各级分频
    localparam [31:0] CNT_NS = CLK_FREQ / 100_000_000;  // ns 计数
    localparam [31:0] CNT_US = CLK_FREQ / 1_000_000;    // us 计数
    localparam [31:0] CNT_MS = CLK_FREQ / 1_000;        // ms 计数

    reg [31:0] cnt = 0;
    reg        busy = 0;
    reg [1:0]  phase = 0;  // 0=ns, 1=us, 2=ms
    reg [31:0] target = 0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt   <= 0;
            busy  <= 0;
            done  <= 0;
            phase <= 0;
            target<= 0;
        end else begin
            done <= 0;
            if (start && !busy) begin
                // 优先级: ns > us > ms (先做小延时)
                if (delay_ns > 0) begin
                    phase  <= 0;
                    target <= delay_ns * CNT_NS;
                    busy   <= 1;
                end else if (delay_us > 0) begin
                    phase  <= 1;
                    target <= delay_us * CNT_US;
                    busy   <= 1;
                end else if (delay_ms > 0) begin
                    phase  <= 2;
                    target <= delay_ms * CNT_MS;
                    busy   <= 1;
                end
            end else if (busy) begin
                if (cnt >= target - 1) begin
                    cnt   <= 0;
                    done  <= 1;
                    busy  <= 0;
                end else cnt <= cnt + 1;
            end
        end
    end

endmodule

// ── 使用示例 ──
// wire done;
// delay_counter #(.CLK_FREQ(50_000_000)) u_dly (
//     .clk      (sys_clk),
//     .rst_n    (sys_rstn),
//     .start    (start_pulse),
//     .delay_us (32'd100),     // 100us
//     .delay_ms (32'd0),
//     .delay_ns (32'd0),
//     .done     (done)
// );
'''

_DELAY_VHDL = '''\
-- Module  : delay_counter
-- Created : auto-generated
-- 功能    : 可配置延时计数器 (ms / us / ns)

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity delay_counter is
  generic (CLK_FREQ : integer := 50_000_000);
  port (
    clk      : in  std_logic;
    rst_n    : in  std_logic;
    start    : in  std_logic;
    delay_us : in  unsigned(31 downto 0);
    delay_ms : in  unsigned(31 downto 0);
    delay_ns : in  unsigned(31 downto 0);
    done     : out std_logic
  );
end entity delay_counter;

architecture rtl of delay_counter is
  constant CNT_NS : integer := CLK_FREQ / 100_000_000;
  constant CNT_US : integer := CLK_FREQ / 1_000_000;
  constant CNT_MS : integer := CLK_FREQ / 1_000;
  signal cnt   : unsigned(31 downto 0) := (others => '0');
  signal busy  : std_logic := '0';
  signal target: unsigned(31 downto 0) := (others => '0');
begin
  process(clk)
  begin
    if rising_edge(clk) then
      if rst_n = '0' then
        cnt <= (others => '0'); busy <= '0'; done <= '0';
      else
        done <= '0';
        if start = '1' and busy = '0' then
          if delay_ns > 0 then
            target <= to_unsigned(delay_ns * CNT_NS, 32);
            busy <= '1';
          elsif delay_us > 0 then
            target <= to_unsigned(delay_us * CNT_US, 32);
            busy <= '1';
          elsif delay_ms > 0 then
            target <= to_unsigned(delay_ms * CNT_MS, 32);
            busy <= '1';
          end if;
        elsif busy = '1' then
          if cnt >= target - 1 then
            cnt <= (others => '0'); done <= '1'; busy <= '0';
          else cnt <= cnt + 1;
          end if;
        end if;
      end if;
    end if;
  end process;
end architecture rtl;
'''


# ═══════════════════════════════════════════════════════════════
# 11. VHDL package 包 (类型 / 常量 / 函数)
# ═══════════════════════════════════════════════════════════════
# VHDL 才有 package 概念; Verilog 用 `include + parameter
_VHDL_PKG_VERILOG = '''\
// Module  : common_pkg_inc
// Created : auto-generated
// 功能    : Verilog 公共定义 (用 include 文件代替 package)
//           Verilog/SV 没有 package 概念, 用 include 共享

// 文件: common_pkg.vh
`ifndef COMMON_PKG_VH
`define COMMON_PKG_VH

// 时钟频率参数
`ifndef CLK_FREQ
`define CLK_FREQ 50_000_000
`endif

// 全局常量
`define TRUE         1'b1
`define FALSE        1'b0
`define MAX_BYTE     8'hFF
`define MAX_SHORT    16'hFFFF
`define MAX_WORD     32'hFFFF_FFFF

// 状态编码 (用 `define 模拟 VHDL enum)
`define ST_IDLE      3'd0
`define ST_START     3'd1
`define ST_RUN       3'd2
`define ST_DONE      3'd3
`define ST_ERROR     3'd4

// 数据位宽
`define ADDR_W       32
`define DATA_W       32
`define STRB_W       (`DATA_W / 8)

// 函数: 对数
function integer log2(input integer value);
  integer i;
  begin
    log2 = 0;
    for (i = value - 1; i > 1; i = i >> 1)
      log2 = log2 + 1;
  end
endfunction

`endif
'''

_VHDL_PKG_VHDL = '''\
-- Module  : common_pkg
-- Created : auto-generated
-- 功能    : VHDL package 标准写法 - 类型 / 常量 / 函数 / 别名
--           推荐放在 src/ 或工程根目录, 各模块 use work.common_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package common_pkg is

  -- ── 全局常量 ──
  constant CLK_FREQ   : integer := 50_000_000;
  constant CLK_PERIOD : time    := 20 ns;
  constant BAUD_115200: integer := 115200;
  constant VERSION    : string  := "FPGA Toolbox v2.0";

  -- ── 全局类型 ──
  type state_t is (ST_IDLE, ST_START, ST_RUN, ST_DONE, ST_ERROR);

  type reg_addr_t is array (0 to 15) of std_logic_vector(31 downto 0);
  -- 8x8 灰度图
  type image_t is array (0 to 7, 0 to 7) of std_logic_vector(7 downto 0);
  -- AXI 数据类型
  type axil_data_t is record
    addr : std_logic_vector(31 downto 0);
    data : std_logic_vector(31 downto 0);
    strb : std_logic_vector(3 downto 0);
    resp : std_logic_vector(1 downto 0);
  end record;

  -- ── 别名 ──
  alias reg_addr is std_logic_vector(31 downto 0);
  alias byte_t   is std_logic_vector(7 downto 0);

  -- ── 函数 ──
  -- log2: 求对数 (e.g. log2(8) = 3)
  function log2 (n : integer) return integer;
  -- 求最大公约数
  function gcd (a, b : integer) return integer;
  -- 把 std_logic 转为 boolean
  function to_bool (s : std_logic) return boolean;
  -- 十六进制字符串转 std_logic_vector
  function hex_to_slv (hex : string; width : positive) return std_logic_vector;

end package common_pkg;

package body common_pkg is

  function log2 (n : integer) return integer is
    variable v : integer := n;
    variable r : integer := 0;
  begin
    while v > 1 loop
      v := v / 2;
      r := r + 1;
    end loop;
    return r;
  end function;

  function gcd (a, b : integer) return integer is
    variable x, y, t : integer;
  begin
    x := a; y := b;
    while y /= 0 loop
      t := y;
      y := x mod y;
      x := t;
    end loop;
    return x;
  end function;

  function to_bool (s : std_logic) return boolean is
  begin
    return s = '1';
  end function;

  function hex_to_slv (hex : string; width : positive) return std_logic_vector is
    variable result : std_logic_vector(width - 1 downto 0) := (others => '0');
    variable hex_val : integer := 0;
    variable i : integer;
  begin
    -- 解析 hex 字符串 (e.g. "A5" -> 0xA5)
    for i in hex'range loop
      case hex(i) is
        when '0' to '9' => hex_val := hex_val * 16 + character'pos(hex(i)) - character'pos('0');
        when 'A' to 'F' => hex_val := hex_val * 16 + character'pos(hex(i)) - character'pos('A') + 10;
        when 'a' to 'f' => hex_val := hex_val * 16 + character'pos(hex(i)) - character'pos('a') + 10;
        when others => null;
      end case;
    end loop;
    result := std_logic_vector(to_unsigned(hex_val, width));
    return result;
  end function;

end package body common_pkg;


-- ── 使用示例 ──
library ieee;
use ieee.std_logic_1164.all;
use work.common_pkg.all;   -- 使用包

entity use_pkg_demo is
  port (
    clk : in std_logic;
    state_o : out state_t    -- 使用包里的枚举类型
  );
end entity use_pkg_demo;

architecture rtl of use_pkg_demo is
  signal cnt : std_logic_vector(log2(CLK_FREQ) - 1 downto 0);  -- 使用 log2 函数
begin
  process(clk)
  begin
    if rising_edge(clk) then
      cnt <= std_logic_vector(unsigned(cnt) + 1);
      -- 状态机: 用包里的 ST_IDLE / ST_RUN
      if unsigned(cnt) = 100 then
        state_o <= ST_RUN;
      end if;
    end if;
  end process;
end architecture rtl;
'''


# ═══════════════════════════════════════════════════════════════
# 模板数据库 (含 AXI-Lite + 高级语法)
# ═══════════════════════════════════════════════════════════════
TEMPLATES = [
    ('tb',         'Testbench 基础模板',     _TB_VERILOG,         _TB_VHDL),
    ('gmii2rgmii', 'GMII -> RGMII (1G PHY)', _GMII2RGMII_VERILOG, _GMII2RGMII_VHDL),
    ('uart',       'UART 串口收发',          _UART_VERILOG,       _UART_VHDL),
    ('iic',        'I2C 控制器',             _IIC_VERILOG,        _IIC_VHDL),
    ('debug',      'Debug 示例 (ILA)',       _DEBUG_VERILOG,      _DEBUG_VHDL),
    ('fsm',        '三段式状态机',           _FSM_VERILOG,        _FSM_VHDL),
    ('wdt',        '看门狗 (Watchdog)',      _WDT_VERILOG,        _WDT_VHDL),
    ('axilite',    'AXI-Lite 寄存器读写',    _AXILITE_WR_VERILOG, _AXILITE_WR_VHDL),
    ('syntax',     '高级语法 (2D/循环/fork/genvar)', _SYNTAX_VERILOG, _SYNTAX_VHDL),
    ('delay',      '延时计数 (ms/us/ns)',    _DELAY_VERILOG,      _DELAY_VHDL),
    ('vhdl_pkg',   'VHDL package 包写法',    _VHDL_PKG_VERILOG,   _VHDL_PKG_VHDL),
]
