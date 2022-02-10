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

module ConfigRegister_32_32_32_0 (
    input clk,
    input reset,
    output [31:0] O,
    input [31:0] config_addr,
    input [31:0] config_data
);
wire [31:0] Register_inst0_O;
wire [31:0] const_0_32_out;
wire magma_Bits_32_eq_inst0_out;
Register Register_inst0 (
    .I(config_data),
    .O(Register_inst0_O),
    .CE(magma_Bits_32_eq_inst0_out),
    .CLK(clk),
    .ASYNCRESET(reset)
);
coreir_const #(
    .value(32'h00000000),
    .width(32)
) const_0_32 (
    .out(const_0_32_out)
);
coreir_eq #(
    .width(32)
) magma_Bits_32_eq_inst0 (
    .in0(config_addr),
    .in1(const_0_32_out),
    .out(magma_Bits_32_eq_inst0_out)
);
assign O = Register_inst0_O;
endmodule

