import magma
from ..generator.generator import Generator
import math
import enum


@enum.unique
class AOIMuxType(enum.Enum):
    Regular = enum.auto()
    Const = enum.auto()


@magma.cache_definition
def _generate_mux_wrapper(height, width, mux_type: AOIMuxType):
    sel_bits = magma.bitutils.clog2(height)
    T = magma.Bits[width]

    class _MuxWrapper(magma.Circuit):
        name = f"MuxWrapperAOIImpl_{height}_{width}"
        in_height = max(1, height)
        IO = [
            "I", magma.In(magma.Array[in_height, T]),
            "O", magma.Out(T),
        ]
        if height > 1:
            IO.extend(["S", magma.In(magma.Bits[sel_bits])])

        @classmethod
        def definition(io):
            if height <= 1:
                magma.wire(io.I[0], io.O)
            else:
                if mux_type == mux_type.Const:
                    # 1-bit extra for the constant
                    num_sel = math.ceil(math.log(height + 1, 2))
                    num_ops = math.ceil((height + 1) / 2)
                else:
                    num_sel = math.ceil(math.log(height, 2))
                    num_ops = math.ceil(height / 2)
                num_inputs = math.pow(2, num_sel)

                # ======= MUX MODULE =========
                verilog = ""
                if mux_type == mux_type.Const:
                    verilog += f"module mux_aoi_const_{height}_{width} ( \n"
                else:
                    verilog += f"module mux_aoi_{height}_{width} ( \n"
                for i in range(height):
                    verilog += f'\tinput logic  [{width-1} : 0] I{i}, \n'
                if num_sel == 1:
                    verilog += f'input logic S, \n'
                else:
                    verilog += f'\tinput logic  [{num_sel-1} : 0] S ,\n'
                verilog += f'\toutput logic [{width-1} : 0] O); \n'

                # Intermediate Signals
                verilog += f'\n\tlogic  [{int(num_inputs)-1} : 0] out_sel;\n'
                for i in range(num_ops):
                    verilog += f'\tlogic  [{int(width)-1} : 0] O_int{i};\n'

                # PRECODER INSTANTIATION #
                verilog += f'\nprecoder_{width}_{height} u_precoder ( \n'
                verilog += '\t.S(S), \n'
                verilog += '\t.out_sel(out_sel)); \n'

                # MUX_LOGIC INSTANTIATION #
                verilog += f'\nmux_logic_{width}_{height} u_mux_logic ( \n'
                for i in range(height):
                    verilog += f'\t.I{i} (I{i}),\n'
                verilog += f'\t.out_sel(out_sel), \n'
                for i in range(num_ops - 1):
                    verilog += f'\t.O{i}(O_int{i}), \n'
                verilog += f'\t.O{num_ops-1}(O_int{num_ops-1})); \n'

                # OR Logic
                verilog += f'\tassign O = (  '
                for i in range(num_ops - 1):
                    verilog += f'\tO_int{i} | '
                verilog += f'\tO_int{num_ops-1} '
                verilog += f'\t); \n'

                verilog += f'\nendmodule \n'

                # ======== PRECODER MODULE ========
                verilog += f'\nmodule precoder_{width}_{height} (\n'
                verilog += f'\tinput logic  [{num_sel-1} : 0] S ,\n'
                verilog += f'\toutput logic  [{int(num_inputs)-1} : 0] out_sel );\n'    # noqa

                verilog += f'\nalways_comb begin: mux_sel\n'
                verilog += f'\tcase (S) \n'
                for i in range(height):
                    data = format(int(math.pow(2, int(i))),
                                  'b').zfill(int(num_inputs))
                    data0 = format(int(math.pow(2, int(height))),
                                   'b').zfill(int(num_inputs))
                    verilog += f'\t\t{num_sel}\'d{i}    :   out_sel = {int(num_inputs)}\'b{data};\n'   # noqa
                if mux_type == AOIMuxType.Const:
                    verilog += f'\t\t{num_sel}\'d{height}    :   out_sel = {int(num_inputs)}\'b{data0};\n'    # noqa
                verilog += f'\t\tdefault :   out_sel = {int(num_inputs)}\'b0;\n'
                verilog += f'\tendcase \n'
                verilog += f'end \n'
                verilog += f'\nendmodule \n'

                # ======== MUX_LOGIC MODULE ========
                verilog += f'\nmodule mux_logic_{width}_{height} ( \n'
                verilog += f'\tinput logic  [{int(num_inputs)-1} : 0] out_sel,\n'   # noqa
                for i in range(height):
                    verilog += f'\tinput logic  [{width-1} : 0] I{i}, \n'
                for i in range(num_ops - 1):
                    verilog += f'\toutput logic  [{width-1} : 0] O{i}, \n'
                verilog += f'\toutput logic  [{width-1} : 0] O{num_ops-1}); \n'

                for j in range(width):
                    for i in range(math.floor(height / 2)):
                        verilog += f'\tAO22D0BWP16P90 inst_{i}_{j} ( \n'
                        verilog += f'\t.A1(out_sel[{i*2}]), \n'
                        verilog += f'\t.A2(I{i*2}[{j}]), \n'
                        verilog += f'\t.B1(out_sel[{i*2+1}]), \n'
                        verilog += f'\t.B2(I{i*2+1}[{j}]), \n'
                        verilog += f'\t.Z(O{i}[{j}])); \n'
                    if (height % 2 != 0):
                        if (mux_type != mux_type.Const):
                            verilog += f'\tAN2D0BWP16P90 inst_and_{j} ( \n'
                            verilog += f'\t.A1(out_sel[{i*2+2}]), \n'
                            verilog += f'\t.A2(I{i*2+2}[{j}]), \n'
                            verilog += f'\t.Z(O{i+1}[{j}])); \n'
                        else:
                            verilog += f'\tAO22D0BWP16P90 inst_{i+1}_{j} ( \n'
                            verilog += f'\t.A1(out_sel[{i*2+2}]), \n'
                            verilog += f'\t.A2(I{i*2+2}[{j}]), \n'
                            verilog += f'\t.B1(out_sel[{i*2+3}]), \n'
                            verilog += f'\t.B2(1\'b0), \n'
                            verilog += f'\t.Z(O{i+1}[{j}])); \n'
                    else:
                        if (mux_type == mux_type.Const):
                            verilog += f'\tAN2D0BWP16P90 inst_and_{j} ( \n'
                            verilog += f'\t.A1(out_sel[{i*2+2}]), \n'
                            verilog += f'\t.A2(1\'b0), \n'
                            verilog += f'\t.Z(O{i+1}[{j}])); \n'
                verilog += "endmodule \n"

                targets = [f"mux_aoi_{height}_{width}"]
                if mux_type == AOIMuxType.Const:
                    targets = [f"mux_aoi_const_{height}_{width}"]
                    Mux = magma.DefineFromVerilog(verilog,
                                                  target_modules=targets)[0]
                else:
                    targets = [f"mux_aoi_{height}_{width}"]
                    Mux = magma.DefineFromVerilog(verilog,
                                                  target_modules=targets)[0]
                mux = Mux()
                for i in range(height):
                    magma.wire(io.I[i], mux.interface.ports[f"I{i}"])
                mux_in = io.S if sel_bits > 1 else io.S[0]
                magma.wire(mux_in, mux.S)
                magma.wire(mux.O, io.O)

    return _MuxWrapper


class AOIMuxWrapper(Generator):
    def __init__(self, height, width, mux_type, name=None):
        super().__init__(name)

        self.height = height
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

    def circuit(self):
        return _generate_mux_wrapper(self.height, self.width, self.mux_type)

    def name(self):
        return f"MuxWrapperAOI_{self.height}_{self.width}_{self.mux_type.name}"
