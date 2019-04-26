import magma
from ..generator.generator import Generator
import math


@magma.cache_definition
def _generate_mux_wrapper(height, width, muxtype):
    if (muxtype):
        # 1-bit extra for the constant
        sel_bits = magma.bitutils.clog2(height + 1)
    else:
        sel_bits = magma.bitutils.clog2(height)
    T = magma.Bits[width]

    class _MuxWrapper(magma.Circuit):
        name = f"MuxWrapper_{height}_{width}"
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
                if (muxtype):
                    f = open("mux_aoi_const.sv", "w")
                    # 1-bit extra for the constant
                    num_sel = math.ceil(math.log(height + 1, 2))
                else:
                    f = open("mux_aoi.sv", "w")
                    num_sel = math.ceil(math.log(height, 2))
                num_inputs = math.pow(2, num_sel)

                f.write("module mux ( \n")

                for i in range(height):
                    f.write(f'\tinput logic  [{width-1} : 0] I{i}, \n')
                if num_sel == 1:
                    f.write(f'input logic S, \n')
                else:
                    f.write(f'\tinput logic  [{num_sel-1} : 0] S ,\n')
                f.write(f'\toutput logic [{width-1} : 0] O); \n')

                f.write(f'\t\nlogic  [{int(num_inputs)-1} : 0] out_sel;\n')

                f.write(f'\nprecoder_{width}_{height} u_precoder ( \n')
                f.write('\t.S(S), \n')
                f.write('\t.out_sel(out_sel)); \n')

                f.write(f'\nmux_logic_{width}_{height} u_mux_logic ( \n')
                for i in range(height):
                    f.write(f'\t.I{i} (I{i}),\n')
                f.write(f'\t.out_sel(out_sel), \n')
                f.write(f'\t.O(O)); \n')

                f.write(f'\nendmodule \n')

                f.write(f'\nmodule precoder_{width}_{height} ( \n')
                f.write(f'\tinput logic  [{num_sel-1} : 0] S ,\n')
                f.write(f'\toutput logic  [{int(num_inputs)-1} : 0] out_sel );'
                        f'\n')

                f.write(f'\nalways_comb begin: mux_sel \n')
                f.write(f'\tcase (S) \n')
                for i in range(height):
                    data = format(int(math.pow(2, int(i))),
                                  'b').zfill(int(num_inputs))
                    data0 = format(int(math.pow(2, int(height))),
                                   'b').zfill(int(num_inputs))
                    f.write(f'\t\t{num_sel}\'d{i}    :   '
                            f'out_sel = {int(num_inputs)}\'b{data}; \n')
                if (muxtype):
                    f.write(f'\t\t{num_sel}\'d{height}    :'
                            f'   out_sel = {int(num_inputs)}\'b{data0}; \n')
                f.write(f'\t\tdefault :   out_sel = {int(num_inputs)}\'b0; '
                        f'\n''')
                f.write(f'\tendcase \n')
                f.write(f'end \n')
                f.write(f'\nendmodule \n')

                f.write(f'\nmodule mux_logic_{width}_{height} ( \n')
                f.write(f'\tinput logic  [{int(num_inputs)-1} : 0] out_sel,\n')
                for i in range(height):
                    f.write(f'\tinput logic  [{width-1} : 0] I{i}, \n')
                f.write(f'\toutput logic [{width-1} : 0] O); \n')

                f.write(f'\nalways_comb begin: out_sel_logic \n')
                f.write(f'\tcase (out_sel) \n')
                for i in range(height):
                    data = format(int(math.pow(2, int(i))),
                                  'b').zfill(int(num_inputs))

                    f.write(f'\t\t{int(num_inputs)}\'b{data}    :   O = I{i};'
                            f'\n')
                if (muxtype):
                    data = format(int(math.pow(2, int(height))),
                                  'b').zfill(int(num_inputs))
                    f.write(f'\t\t{int(num_inputs)}\'b{data}    :   O = 0; \n')
                f.write(f'\t\tdefault :   O = 0; \n''')
                f.write(f'\tendcase \n')
                f.write(f'end \n')

                f.write("endmodule \n")
                f.close()
                if (muxtype):
                    mux = magma.DefineFromVerilogFile("./mux_aoi_const.sv",
                                                      target_modules=["mux"])[0]()
                else:
                    mux = magma.DefineFromVerilogFile("./mux_aoi.sv",
                                                      target_modules=["mux"])[0]()
                for i in range(height):
                    magma.wire(io.I[i], mux.interface.ports[f"I{i}"])
                mux_in = io.S if sel_bits > 1 else io.S[0]
                magma.wire(mux_in, mux.S)
                magma.wire(mux.O, io.O)

    return _MuxWrapper


class AOIMuxWrapperCommon(Generator):
    def __init__(self, height, width, muxtype, name=None):
        super().__init__(name)

        self.height = height
        self.width = width
        self.muxtype = muxtype

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

        if (muxtype):
            # 1-bit extra for the constant
            self.sel_bits = magma.bitutils.clog2(self.height + 1)
        else:
            self.sel_bits = magma.bitutils.clog2(self.height)
        self.add_ports(
            I=magma.In(magma.Array[self.height, T]),
            S=magma.In(magma.Bits[self.sel_bits]),
            O=magma.Out(T),
        )

    def circuit(self):
        return _generate_mux_wrapper(self.height, self.width, self.muxtype)

    def name(self):
        return f"MuxWrapperAOI_{self.height}_{self.width}_WithConst_{self.muxtype}"
