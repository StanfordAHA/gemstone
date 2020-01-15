module coreir_ult #(parameter width = 1) (input [width-1:0] in0, input [width-1:0] in1, output out);
  assign out = in0 < in1;
endmodule

module coreir_reg_arst #(parameter width = 1, parameter arst_posedge = 1, parameter clk_posedge = 1, parameter init = 1) (input clk, input arst, input [width-1:0] in, output [width-1:0] out);
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

module coreir_mux #(parameter width = 1) (input [width-1:0] in0, input [width-1:0] in1, input sel, output [width-1:0] out);
  assign out = sel ? in1 : in0;
endmodule

module coreir_eq #(parameter width = 1) (input [width-1:0] in0, input [width-1:0] in1, output out);
  assign out = in0 == in1;
endmodule

module coreir_const #(parameter width = 1, parameter value = 1) (output [width-1:0] out);
  assign out = value;
endmodule

module corebit_and (input in0, input in1, output out);
  assign out = in0 & in1;
endmodule

module commonlib_muxn__N2__width32 (input [31:0] in_data_0, input [31:0] in_data_1, input [0:0] in_sel, output [31:0] out);
wire [31:0] _join_out;
coreir_mux #(.width(32)) _join(.in0(in_data_0), .in1(in_data_1), .out(_join_out), .sel(in_sel[0]));
assign out = _join_out;
endmodule

module Mux2xOutBits32 (input [31:0] I0, input [31:0] I1, output [31:0] O, input S);
wire [31:0] coreir_commonlib_mux2x32_inst0_out;
commonlib_muxn__N2__width32 coreir_commonlib_mux2x32_inst0(.in_data_0(I0), .in_data_1(I1), .in_sel(S), .out(coreir_commonlib_mux2x32_inst0_out));
assign O = coreir_commonlib_mux2x32_inst0_out;
endmodule

module Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32 (input ASYNCRESET, input CE, input CLK, input [31:0] I, output [31:0] O);
wire [31:0] enable_mux_O;
wire [31:0] value_out;
Mux2xOutBits32 enable_mux(.I0(value_out), .I1(I), .O(enable_mux_O), .S(CE));
coreir_reg_arst #(.arst_posedge(1'b1), .clk_posedge(1'b1), .init('h00000000), .width(32)) value(.arst(ASYNCRESET), .clk(CLK), .in(enable_mux_O), .out(value_out));
assign O = value_out;
endmodule

module Mux2x32 (input [31:0] I0, input [31:0] I1, output [31:0] O, input S);
wire [31:0] coreir_commonlib_mux2x32_inst0_out;
commonlib_muxn__N2__width32 coreir_commonlib_mux2x32_inst0(.in_data_0(I0), .in_data_1(I1), .in_sel(S), .out(coreir_commonlib_mux2x32_inst0_out));
assign O = coreir_commonlib_mux2x32_inst0_out;
endmodule

module MuxWrapper_2_32 (input [31:0] I_0, input [31:0] I_1, output [31:0] O, input [0:0] S);
wire [31:0] Mux2x32_inst0_O;
Mux2x32 Mux2x32_inst0(.I0(I_0), .I1(I_1), .O(Mux2x32_inst0_O), .S(S[0]));
assign O = Mux2x32_inst0_O;
endmodule

module MuxWithDefaultWrapper_2_32_8_0 (input [0:0] EN, input [31:0] I_0, input [31:0] I_1, output [31:0] O, input [7:0] S);
wire [31:0] MuxWrapper_2_32_inst0_O;
wire [31:0] MuxWrapper_2_32_inst1_O;
wire and_inst0_out;
wire [31:0] const_0_32_out;
wire [7:0] const_2_8_out;
wire coreir_ult8_inst0_out;
MuxWrapper_2_32 MuxWrapper_2_32_inst0(.I_0(I_0), .I_1(I_1), .O(MuxWrapper_2_32_inst0_O), .S(S[0]));
MuxWrapper_2_32 MuxWrapper_2_32_inst1(.I_0(const_0_32_out), .I_1(MuxWrapper_2_32_inst0_O), .O(MuxWrapper_2_32_inst1_O), .S(and_inst0_out));
corebit_and and_inst0(.in0(coreir_ult8_inst0_out), .in1(EN[0]), .out(and_inst0_out));
coreir_const #(.value('h00000000), .width(32)) const_0_32(.out(const_0_32_out));
coreir_const #(.value(8'h02), .width(8)) const_2_8(.out(const_2_8_out));
coreir_ult #(.width(8)) coreir_ult8_inst0(.in0(S), .in1(const_2_8_out), .out(coreir_ult8_inst0_out));
assign O = MuxWrapper_2_32_inst1_O;
endmodule

module ConfigRegister_32_8_32_1 (output [31:0] O, input clk, input [7:0] config_addr, input [31:0] config_data, input config_en, input reset);
wire [31:0] Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0_O;
wire [7:0] const_1_8_out;
wire magma_Bit_and_inst0_out;
wire magma_Bits_8_eq_inst0_out;
Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32 Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0(.ASYNCRESET(reset), .CE(magma_Bit_and_inst0_out), .CLK(clk), .I(config_data), .O(Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0_O));
coreir_const #(.value(8'h01), .width(8)) const_1_8(.out(const_1_8_out));
corebit_and magma_Bit_and_inst0(.in0(magma_Bits_8_eq_inst0_out), .in1(config_en), .out(magma_Bit_and_inst0_out));
coreir_eq #(.width(8)) magma_Bits_8_eq_inst0(.in0(config_addr), .in1(const_1_8_out), .out(magma_Bits_8_eq_inst0_out));
assign O = Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0_O;
endmodule

module ConfigRegister_32_8_32_0 (output [31:0] O, input clk, input [7:0] config_addr, input [31:0] config_data, input config_en, input reset);
wire [31:0] Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0_O;
wire [7:0] const_0_8_out;
wire magma_Bit_and_inst0_out;
wire magma_Bits_8_eq_inst0_out;
Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32 Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0(.ASYNCRESET(reset), .CE(magma_Bit_and_inst0_out), .CLK(clk), .I(config_data), .O(Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0_O));
coreir_const #(.value(8'h00), .width(8)) const_0_8(.out(const_0_8_out));
corebit_and magma_Bit_and_inst0(.in0(magma_Bits_8_eq_inst0_out), .in1(config_en), .out(magma_Bit_and_inst0_out));
coreir_eq #(.width(8)) magma_Bits_8_eq_inst0(.in0(config_addr), .in1(const_0_8_out), .out(magma_Bits_8_eq_inst0_out));
assign O = Register_has_ce_True_has_reset_False_has_async_reset_True_has_async_resetn_False_type_Bits_n_32_inst0_O;
endmodule

module DummyCore (input clk, input [7:0] config_config_addr, input [31:0] config_config_data, input [0:0] config_read, input [0:0] config_write, input [15:0] data_in_16b, input [0:0] data_in_1b, output [15:0] data_out_16b, output [0:0] data_out_1b, output [31:0] read_config_data, input reset);
wire [31:0] MuxWithDefaultWrapper_2_32_8_0_inst0_O;
wire [31:0] dummy_1_O;
wire [31:0] dummy_2_O;
MuxWithDefaultWrapper_2_32_8_0 MuxWithDefaultWrapper_2_32_8_0_inst0(.EN(config_read), .I_0(dummy_1_O), .I_1(dummy_2_O), .O(MuxWithDefaultWrapper_2_32_8_0_inst0_O), .S(config_config_addr));
ConfigRegister_32_8_32_0 dummy_1(.O(dummy_1_O), .clk(clk), .config_addr(config_config_addr), .config_data(config_config_data), .config_en(config_write[0]), .reset(reset));
ConfigRegister_32_8_32_1 dummy_2(.O(dummy_2_O), .clk(clk), .config_addr(config_config_addr), .config_data(config_config_data), .config_en(config_write[0]), .reset(reset));
assign data_out_16b = data_in_16b;
assign data_out_1b = data_in_1b;
assign read_config_data = MuxWithDefaultWrapper_2_32_8_0_inst0_O;
endmodule

