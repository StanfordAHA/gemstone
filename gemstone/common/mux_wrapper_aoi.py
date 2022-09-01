import os.path

import magma
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma
import math
import enum
import glob


@enum.unique
class AOIMuxType(enum.Enum):
    Regular = enum.auto()
    Const = enum.auto()
    RegularReadyValid = enum.auto()
    ConstReadyValid = enum.auto()


@magma.cache_definition
def _generate_mux_wrapper(height, width, mux_type: AOIMuxType):
    sel_bits = magma.bitutils.clog2(height)
    T = magma.Bits[width]

    class _MuxWrapper(magma.Circuit):
        coreir_metadata = {"inline_single_instance": False}
        in_height = max(1, height)
        verilog_str = ""

        if mux_type == mux_type.Const or mux_type == mux_type.ConstReadyValid:
            # 1-bit extra for the constant
            num_sel = math.ceil(math.log(height + 1, 2))
            num_ops = math.ceil((height + 1) / 2)
        else:
            num_sel = math.ceil(math.log(height, 2))
            num_ops = math.ceil(height / 2)
        num_inputs = int(math.pow(2, num_sel))

        ports = {
            "I": magma.In(magma.Array[in_height, T]),
            "O": magma.Out(T),
        }
        ready_valid = mux_type == mux_type.RegularReadyValid or mux_type == mux_type.ConstReadyValid
        if ready_valid:
            # add ready valid ports
            bits = magma.Bits[in_height]
            ports["ready_in"] = magma.In(magma.Bit)
            ports["ready_out"] = magma.Out(magma.Bit)
            ports["valid_in"] = magma.In(bits)
            ports["valid_out"] = magma.Out(magma.Bit)

        if height > 1:
            ports["S"] = magma.In(magma.Bits[sel_bits])
            ports["out_sel"] = magma.Out(magma.Bits[num_inputs])

        io = magma.IO(**ports)

        name = "mux_aoi"
        if ready_valid:
            name += "_ready_valid"
        if mux_type == mux_type.Const or mux_type == mux_type.ConstReadyValid:
            name += "_const"
        name += f"_{height}_{width}"

        if height <= 1:
            magma.wire(io.I[0], io.O)
        else:
            # ======= MUX MODULE =========

            verilog_str += f"module {name} ( \n"
            verilog_str += f'\tinput logic  [{width-1} : 0] I[{height-1}:0], \n'
            if num_sel == 1:
                verilog_str += f'input logic S, \n'
            else:
                verilog_str += f'\tinput logic  [{num_sel-1} : 0] S ,\n'
            if ready_valid:
                verilog_str += f'\tinput logic ready_in,\n'
                verilog_str += f'\toutput logic ready_out,\n'
                verilog_str += f'\tinput logic [{height-1}:0]  valid_in,\n'
                verilog_str += f'\toutput logic valid_out,\n'
            verilog_str += f'\toutput logic  [{int(num_inputs)-1} : 0] out_sel,\n'
            verilog_str += f'\toutput logic [{width-1} : 0] O); \n'

            # Intermediate Signals
            for i in range(num_ops):
                verilog_str += f'\tlogic  [{int(width)-1} : 0] O_int{i};\n'
            if ready_valid:
                verilog_str += f'\tlogic [{num_ops - 1}:0] valid_out_temp;\n'

            # PRECODER INSTANTIATION #
            verilog_str += f'\nprecoder_{width}_{height} u_precoder ( \n'
            verilog_str += '\t.S(S), \n'
            verilog_str += '\t.out_sel(out_sel)); \n'

            # MUX_LOGIC INSTANTIATION #
            verilog_str += f'\nmux_logic_{width}_{height} u_mux_logic ( \n'
            for i in range(height):
                verilog_str += f'\t.I{i} (I[{i}]),\n'
            verilog_str += f'\t.out_sel(out_sel),'
            if ready_valid:
                verilog_str += f'\n\t.valid_in(valid_in),\n\t.valid_out(valid_out_temp),\n'
            for i in range(num_ops - 1):
                verilog_str += f'\t.O{i}(O_int{i}), \n'
            verilog_str += f'\t.O{num_ops-1}(O_int{num_ops-1})); \n'

            # OR Logic
            verilog_str += f'\tassign O = (  '
            for i in range(num_ops - 1):
                verilog_str += f'\tO_int{i} | '
            verilog_str += f'\tO_int{num_ops-1} '
            verilog_str += f'\t); \n'

            if ready_valid:
                verilog_str += f'\tassign ready_out = ready_in;\n'
                verilog_str += f'\tassign valid_out = |valid_out_temp;\n'

            verilog_str += f'\nendmodule \n'

            # ======== PRECODER MODULE ========
            verilog_str += f'\nmodule precoder_{width}_{height} (\n'
            verilog_str += f'\tinput logic  [{num_sel-1} : 0] S ,\n'
            verilog_str += f'\toutput logic  [{int(num_inputs)-1} : 0] out_sel );\n'    # noqa

            verilog_str += f'\nalways_comb begin: mux_sel\n'
            verilog_str += f'\tcase (S) \n'
            for i in range(height):
                data = format(int(math.pow(2, int(i))),
                              'b').zfill(int(num_inputs))
                data0 = format(int(math.pow(2, int(height))),
                               'b').zfill(int(num_inputs))
                verilog_str += f'\t\t{num_sel}\'d{i}    :   out_sel = {int(num_inputs)}\'b{data};\n'   # noqa
            if mux_type == AOIMuxType.Const or mux_type == AOIMuxType.ConstReadyValid:
                verilog_str += f'\t\t{num_sel}\'d{height}    :   out_sel = {int(num_inputs)}\'b{data0};\n'    # noqa
            verilog_str += f'\t\tdefault :   out_sel = {int(num_inputs)}\'b0;\n'
            verilog_str += f'\tendcase \n'
            verilog_str += f'end \n'
            verilog_str += f'\nendmodule \n'

            # ======== MUX_LOGIC MODULE ========
            verilog_str += f'\nmodule mux_logic_{width}_{height} ( \n'
            verilog_str += f'\tinput logic  [{int(num_inputs)-1} : 0] out_sel,\n'   # noqa
            for i in range(height):
                verilog_str += f'\tinput logic  [{width-1} : 0] I{i}, \n'
            if ready_valid:
                verilog_str += f'\tinput logic [{height - 1}:0] valid_in,\n'
                verilog_str += f'\toutput logic [{num_ops - 1}:0] valid_out,\n'
            for i in range(num_ops - 1):
                verilog_str += f'\toutput logic  [{width-1} : 0] O{i}, \n'
            verilog_str += f'\toutput logic  [{width-1} : 0] O{num_ops-1}); \n'

            for j in range(width):
                for i in range(math.floor(height / 2)):
                    verilog_str += f'\tSC7P5T_AO22X0P5_SSC14R inst_{i}_{j} ( \n'
                    verilog_str += f'\t.A1(out_sel[{i*2}]), \n'
                    verilog_str += f'\t.A2(I{i*2}[{j}]), \n'
                    verilog_str += f'\t.B1(out_sel[{i*2+1}]), \n'
                    verilog_str += f'\t.B2(I{i*2+1}[{j}]), \n'
                    verilog_str += f'\t.Z(O{i}[{j}])); \n'
                if height % 2 != 0:
                    if mux_type != mux_type.Const and mux_type != mux_type.ConstReadyValid:
                        verilog_str += f'\tSC7P5T_AN2X0P5_SSC14R inst_and_{j} ( \n'
                        verilog_str += f'\t.A(out_sel[{i*2+2}]), \n'
                        verilog_str += f'\t.B(I{i*2+2}[{j}]), \n'
                        verilog_str += f'\t.Z(O{i+1}[{j}])); \n'
                    else:
                        verilog_str += f'\tSC7P5T_AO22X0P5_SSC14R inst_{i+1}_{j} ( \n'
                        verilog_str += f'\t.A1(out_sel[{i*2+2}]), \n'
                        verilog_str += f'\t.A2(I{i*2+2}[{j}]), \n'
                        verilog_str += f'\t.B1(out_sel[{i*2+3}]), \n'
                        verilog_str += f'\t.B2(1\'b0), \n'
                        verilog_str += f'\t.Z(O{i+1}[{j}])); \n'
                else:
                    if mux_type == mux_type.Const or mux_type == mux_type.ConstReadyValid:
                        verilog_str += f'\tSC7P5T_AN2X0P5_SSC14R inst_and_{j} ( \n'
                        verilog_str += f'\t.A(out_sel[{i*2+2}]), \n'
                        verilog_str += f'\t.B(1\'b0), \n'
                        verilog_str += f'\t.Z(O{i+1}[{j}])); \n'

            # for the constant ready-valid
            if mux_type == mux_type.ConstReadyValid:
                for i in range(math.floor(height / 2)):
                    verilog_str += f'\tSC7P5T_AO22X0P5_SSC14R inst_{i}_valid ( \n'
                    verilog_str += f'\t.A1(out_sel[{i*2}]), \n'
                    verilog_str += f'\t.A2(valid_in[{i*2}]), \n'
                    verilog_str += f'\t.B1(out_sel[{i*2+1}]), \n'
                    verilog_str += f'\t.B2(valid_in[{i*2+1}]), \n'
                    verilog_str += f'\t.Z(valid_out[{i}])); \n'

                if height % 2 != 0:
                    verilog_str += f'\tSC7P5T_AO22X0P5_SSC14R inst_{i + 1}_valid ( \n'
                    verilog_str += f'\t.A1(out_sel[{i * 2 + 2}]), \n'
                    verilog_str += f'\t.A2(valid_in[{i * 2 + 2}]), \n'
                    verilog_str += f'\t.B1(out_sel[{i * 2 + 3}]), \n'
                    verilog_str += f'\t.B2(1\'b0), \n'
                    verilog_str += f'\t.Z(valid_out[{i + 1}])); \n'
            verilog_str += "endmodule \n"

    _MuxWrapper.verilogFile = _MuxWrapper.verilog_str

    return _MuxWrapper


class AOIMuxWrapper(Generator):
    def __init__(self, height, width, mux_type: AOIMuxType = AOIMuxType.Regular, name=None):
        super().__init__(name)

        self.height = max(1, height)
        self.width = width
        self.mux_type: AOIMuxType = mux_type

        T = magma.Bits[self.width]

        # In the case that @height <= 1, we make this circuit a simple
        # pass-through circuit.
        if self.height <= 1:
            self.add_ports(
                I=magma.In(magma.Array[1, T]),
                O=magma.Out(T),
            )
            self.sel_bits = 0
            return

        if mux_type == AOIMuxType.Const:
            assert magma.bitutils.clog2(height) == \
                magma.bitutils.clog2(height + 1)
        self.sel_bits = magma.bitutils.clog2(height)
        self.add_ports(
            I=magma.In(magma.Array[self.height, T]),
            S=magma.In(magma.Bits[self.sel_bits]),
            O=magma.Out(T),
        )


        if mux_type == AOIMuxType.RegularReadyValid or mux_type == AOIMuxType.ConstReadyValid:
            bits = magma.Bits[self.height]
            self.add_ports(
                ready_in=magma.In(magma.Bit),
                ready_out= magma.Out(bits),
                valid_in= magma.In(bits),
                valid_out= magma.Out(magma.Bit)
            )

            if self.height > 1:
                num_inputs = int(math.pow(2, magma.bitutils.clog2(height)))
                self.add_port("out_sel", magma.Out(magma.Bits[num_inputs]))


    def circuit(self):
        return _generate_mux_wrapper(self.height, self.width, self.mux_type)

    def name(self):
        return f"MuxWrapperAOI_{self.height}_{self.width}_{self.mux_type.name}"

    @staticmethod
    def get_sv_files():
        root_dir = os.path.abspath(__file__)
        for i in range(3):
            root_dir = os.path.dirname(root_dir)
        rtl_dir = os.path.join(root_dir, "tests", "common", "rtl", "*.sv")
        return glob.glob(rtl_dir)
