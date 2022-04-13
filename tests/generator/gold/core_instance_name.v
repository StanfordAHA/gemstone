module mantle_wire__typeBit8 (
    input [7:0] in,
    output [7:0] out
);
assign out = in;
endmodule

module dummy_2 (
    input [31:0] I,
    output [31:0] O
);
assign O = I;
endmodule

module dummy_1 (
    input [31:0] I,
    output [31:0] O
);
assign O = I;
endmodule

module coreir_reg_arst #(
    parameter width = 1,
    parameter arst_posedge = 1,
    parameter clk_posedge = 1,
    parameter init = 1
) (
    input clk,
    input arst,
    input [width-1:0] in,
    output [width-1:0] out
);
  reg [width-1:0] outReg;
  wire real_rst;
  assign real_rst = arst_posedge ? arst : ~arst;
  wire real_clk;
  assign real_clk = clk_posedge ? clk : ~clk;
  always @(posedge real_clk, posedge real_rst) begin
    if (real_rst) outReg <= init;
    else outReg <= in;
  end
  assign out = outReg;
endmodule

module coreir_mux #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    input sel,
    output [width-1:0] out
);
  assign out = sel ? in1 : in0;
endmodule

module coreir_eq #(
    parameter width = 1
) (
    input [width-1:0] in0,
    input [width-1:0] in1,
    output out
);
  assign out = in0 == in1;
endmodule

module coreir_const #(
    parameter width = 1,
    parameter value = 1
) (
    output [width-1:0] out
);
  assign out = value;
endmodule

module corebit_and (
    input in0,
    input in1,
    output out
);
  assign out = in0 & in1;
endmodule

module commonlib_muxn__N2__width32 (
    input [31:0] in_data [1:0],
    input [0:0] in_sel,
    output [31:0] out
);
wire [31:0] _join_out;
coreir_mux #(
    .width(32)
) _join (
    .in0(in_data[0]),
    .in1(in_data[1]),
    .sel(in_sel[0]),
    .out(_join_out)
);
assign out = _join_out;
endmodule

module Mux2xBits32 (
    input [31:0] I0,
    input [31:0] I1,
    input S,
    output [31:0] O
);
wire [31:0] coreir_commonlib_mux2x32_inst0_out;
wire [31:0] coreir_commonlib_mux2x32_inst0_in_data [1:0];
assign coreir_commonlib_mux2x32_inst0_in_data[1] = I1;
assign coreir_commonlib_mux2x32_inst0_in_data[0] = I0;
commonlib_muxn__N2__width32 coreir_commonlib_mux2x32_inst0 (
    .in_data(coreir_commonlib_mux2x32_inst0_in_data),
    .in_sel(S),
    .out(coreir_commonlib_mux2x32_inst0_out)
);
assign O = coreir_commonlib_mux2x32_inst0_out;
endmodule

module Register (
    input [31:0] I,
    output [31:0] O,
    input CE,
    input CLK,
    input ASYNCRESET
);
wire [31:0] enable_mux_O;
wire [31:0] reg_PR32_inst0_out;
Mux2xBits32 enable_mux (
    .I0(reg_PR32_inst0_out),
    .I1(I),
    .S(CE),
    .O(enable_mux_O)
);
coreir_reg_arst #(
    .arst_posedge(1'b1),
    .clk_posedge(1'b1),
    .init(32'h00000000),
    .width(32)
) reg_PR32_inst0 (
    .clk(CLK),
    .arst(ASYNCRESET),
    .in(enable_mux_O),
    .out(reg_PR32_inst0_out)
);
assign O = reg_PR32_inst0_out;
endmodule

module MuxWrapper_2_32 (
    input [31:0] I [1:0],
    output [31:0] O,
    input [0:0] S
);
wire [31:0] Mux2xBits32_inst0_O;
Mux2xBits32 Mux2xBits32_inst0 (
    .I0(I[0]),
    .I1(I[1]),
    .S(S[0]),
    .O(Mux2xBits32_inst0_O)
);
assign O = Mux2xBits32_inst0_O;
endmodule

module ConfigRegister_32_8_32_1 (
    input clk,
    input reset,
    output [31:0] O,
    input [7:0] config_addr,
    input [31:0] config_data,
    input config_en
);
wire [31:0] Register_inst0_O;
wire [7:0] const_1_8_out;
wire magma_Bit_and_inst0_out;
wire magma_Bits_8_eq_inst0_out;
Register Register_inst0 (
    .I(config_data),
    .O(Register_inst0_O),
    .CE(magma_Bit_and_inst0_out),
    .CLK(clk),
    .ASYNCRESET(reset)
);
coreir_const #(
    .value(8'h01),
    .width(8)
) const_1_8 (
    .out(const_1_8_out)
);
corebit_and magma_Bit_and_inst0 (
    .in0(magma_Bits_8_eq_inst0_out),
    .in1(config_en),
    .out(magma_Bit_and_inst0_out)
);
coreir_eq #(
    .width(8)
) magma_Bits_8_eq_inst0 (
    .in0(config_addr),
    .in1(const_1_8_out),
    .out(magma_Bits_8_eq_inst0_out)
);
assign O = Register_inst0_O;
endmodule

module ConfigRegister_32_8_32_0 (
    input clk,
    input reset,
    output [31:0] O,
    input [7:0] config_addr,
    input [31:0] config_data,
    input config_en
);
wire [31:0] Register_inst0_O;
wire [7:0] const_0_8_out;
wire magma_Bit_and_inst0_out;
wire magma_Bits_8_eq_inst0_out;
Register Register_inst0 (
    .I(config_data),
    .O(Register_inst0_O),
    .CE(magma_Bit_and_inst0_out),
    .CLK(clk),
    .ASYNCRESET(reset)
);
coreir_const #(
    .value(8'h00),
    .width(8)
) const_0_8 (
    .out(const_0_8_out)
);
corebit_and magma_Bit_and_inst0 (
    .in0(magma_Bits_8_eq_inst0_out),
    .in1(config_en),
    .out(magma_Bit_and_inst0_out)
);
coreir_eq #(
    .width(8)
) magma_Bits_8_eq_inst0 (
    .in0(config_addr),
    .in1(const_0_8_out),
    .out(magma_Bits_8_eq_inst0_out)
);
assign O = Register_inst0_O;
endmodule

module DummyCore (
    input clk,
    input [7:0] config_config_addr,
    input [31:0] config_config_data,
    input [0:0] config_read,
    input [0:0] config_write,
    input [15:0] data_in_16b,
    input [0:0] data_in_1b,
    output [15:0] data_out_16b,
    output [0:0] data_out_1b,
    output [31:0] read_config_data,
    input reset
);
wire [31:0] MuxWrapper_2_32_inst0_O;
wire [31:0] config_reg_0_O;
wire [31:0] config_reg_1_O;
wire [31:0] dummy_1_inst0_O;
wire [31:0] dummy_2_inst0_O;
wire [7:0] self_config_config_addr_out;
wire [31:0] MuxWrapper_2_32_inst0_I [1:0];
assign MuxWrapper_2_32_inst0_I[1] = config_reg_1_O;
assign MuxWrapper_2_32_inst0_I[0] = config_reg_0_O;
MuxWrapper_2_32 MuxWrapper_2_32_inst0 (
    .I(MuxWrapper_2_32_inst0_I),
    .O(MuxWrapper_2_32_inst0_O),
    .S(self_config_config_addr_out[0:0])
);
wire [7:0] config_reg_0_config_addr;
assign config_reg_0_config_addr = {self_config_config_addr_out[7],self_config_config_addr_out[6],self_config_config_addr_out[5],self_config_config_addr_out[4],self_config_config_addr_out[3],self_config_config_addr_out[2],self_config_config_addr_out[1],self_config_config_addr_out[0:0]};
ConfigRegister_32_8_32_0 config_reg_0 (
    .clk(clk),
    .reset(reset),
    .O(config_reg_0_O),
    .config_addr(config_reg_0_config_addr),
    .config_data(config_config_data),
    .config_en(config_write[0])
);
wire [7:0] config_reg_1_config_addr;
assign config_reg_1_config_addr = {self_config_config_addr_out[7],self_config_config_addr_out[6],self_config_config_addr_out[5],self_config_config_addr_out[4],self_config_config_addr_out[3],self_config_config_addr_out[2],self_config_config_addr_out[1],self_config_config_addr_out[0:0]};
ConfigRegister_32_8_32_1 config_reg_1 (
    .clk(clk),
    .reset(reset),
    .O(config_reg_1_O),
    .config_addr(config_reg_1_config_addr),
    .config_data(config_config_data),
    .config_en(config_write[0])
);
dummy_1 dummy_1_inst0 (
    .I(config_reg_0_O),
    .O(dummy_1_inst0_O)
);
dummy_2 dummy_2_inst0 (
    .I(config_reg_1_O),
    .O(dummy_2_inst0_O)
);
mantle_wire__typeBit8 self_config_config_addr (
    .in(config_config_addr),
    .out(self_config_config_addr_out)
);
assign data_out_16b = data_in_16b;
assign data_out_1b = data_in_1b;
assign read_config_data = MuxWrapper_2_32_inst0_O;
endmodule

