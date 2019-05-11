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
    if mux_type == mux_type.Const:
        # 1-bit extra for the constant
        sel_bits = magma.bitutils.clog2(height + 1)
    else:
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
                    f = open("mux_aoi_const.sv", "w")
                    # 1-bit extra for the constant
                    num_sel = math.ceil(math.log(height + 1, 2))
                    num_ops = math.ceil((height+1)/2)
                else:
                    f = open("mux_aoi.sv", "w")
                    num_sel = math.ceil(math.log(height, 2))
                    num_ops = math.ceil(height/2)
                num_inputs = math.pow(2, num_sel)

                # ======= MUX MODULE =========
                if mux_type == mux_type.Const:
                    f.write(f"module mux_aoi_const_{height}_{width} ( \n")
                else:
                    f.write(f"module mux_aoi_{height}_{width} ( \n")
                for i in range(height):
                    f.write(f'\tinput logic  [{width-1} : 0] I{i}, \n')
                if num_sel == 1:
                    f.write(f'input logic S, \n')
                else:
                    f.write(f'\tinput logic  [{num_sel-1} : 0] S ,\n')
                f.write(f'\toutput logic [{width-1} : 0] O); \n')

                # Intermediate Signals
                f.write(f'\n\tlogic  [{int(num_inputs)-1} : 0] out_sel;\n')
                for i in range(num_ops): 
                    f.write(f'\tlogic  [{int(width)-1} : 0] O_int{i};\n')
                
                # PRECODER INSTANTIATION # 
                f.write(f'\nprecoder_{width}_{height} u_precoder ( \n')
                f.write('\t.S(S), \n')
                f.write('\t.out_sel(out_sel)); \n')

                # MUX_LOGIC INSTANTIATION #
                f.write(f'\nmux_logic_{width}_{height} u_mux_logic ( \n')
                for i in range(height):
                    f.write(f'\t.I{i} (I{i}),\n')
                f.write(f'\t.out_sel(out_sel), \n')
                for i in range(num_ops-1):
                    f.write(f'\t.O{i}(O_int{i}), \n')
                f.write(f'\t.O{num_ops-1}(O_int{num_ops-1})); \n')

                # OR Logic
                f.write(f'\tassign O = (  ')
                for i in range(num_ops - 1):
                    f.write(f'\tO_int{i} | ')
                f.write(f'\tO_int{num_ops-1} ')
                f.write(f'\t); \n')    

                f.write(f'\nendmodule \n')

                # ======== PRECODER MODULE ========
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
                if mux_type == AOIMuxType.Const:
                    f.write(f'\t\t{num_sel}\'d{height}    :'
                            f'   out_sel = {int(num_inputs)}\'b{data0}; \n')
                f.write(f'\t\tdefault :   out_sel = {int(num_inputs)}\'b0; '
                        f'\n''')
                f.write(f'\tendcase \n')
                f.write(f'end \n')
                f.write(f'\nendmodule \n')

                # ======== MUX_LOGIC MODULE ========
                f.write(f'\nmodule mux_logic_{width}_{height} ( \n')
                f.write(f'\tinput logic  [{int(num_inputs)-1} : 0] out_sel,\n')
                for i in range(height):
                    f.write(f'\tinput logic  [{width-1} : 0] I{i}, \n')
                for i in range(num_ops - 1):
                    f.write(f'\toutput logic  [{width-1} : 0] O{i}, \n')
                f.write(f'\toutput logic  [{width-1} : 0] O{num_ops-1}); \n') 

                for j in range(width):
                    for i in range(math.floor(height / 2)):
                        f.write(f'\tAO22D0BWP16P90 inst_{i}_{j} ( \n')
                        f.write(f'\t.A1(out_sel[{i*2}]), \n')
                        f.write(f'\t.A2(I{i*2}[{j}]), \n')
                        f.write(f'\t.B1(out_sel[{i*2+1}]), \n')
                        f.write(f'\t.B2(I{i*2+1}[{j}]), \n')
                        f.write(f'\t.Z(O{i}[{j}])); \n')
                    if (height % 2 != 0):
                        if (mux_type != mux_type.Const):
                            f.write(f'\tAN2D0BWP16P90 inst_and_{j} ( \n')
                            f.write(f'\t.A1(out_sel[{i*2+2}]), \n')
                            f.write(f'\t.A2(I{i*2+2}[{j}]), \n')
                            f.write(f'\t.Z(O{i+1}[{j}])); \n')
                        else:
                            f.write(f'\tAO22D0BWP16P90 inst_{i+1}_{j} ( \n')
                            f.write(f'\t.A1(out_sel[{i*2+2}]), \n')
                            f.write(f'\t.A2(I{i*2+2}[{j}]), \n')
                            f.write(f'\t.B1(out_sel[{i*2+3}]), \n')
                            f.write(f'\t.B2(1\'b0), \n')
                            f.write(f'\t.Z(O{i+1}[{j}])); \n')
                    else:
                        if (mux_type == mux_type.Const):
                            f.write(f'\tAN2D0BWP16P90 inst_and_{j} ( \n')
                            f.write(f'\t.A1(out_sel[{i*2+2}]), \n')
                            f.write(f'\t.A2(1\'b0), \n')
                            f.write(f'\t.Z(O{i+1}[{j}])); \n')
                
                f.write("endmodule \n")
                f.close()
                targets = [f"mux_aoi_{height}_{width}"]
                if mux_type == AOIMuxType.Const:
                    targets = [f"mux_aoi_const_{height}_{width}"]
                    Mux = magma.DefineFromVerilogFile("./mux_aoi_const.sv",
                                                      target_modules=targets,
                                                      shallow=True)[0]
                else:
                    targets = [f"mux_aoi_{height}_{width}"]
                    Mux = magma.DefineFromVerilogFile("./mux_aoi.sv",
                                                      target_modules=targets,
                                                      shallow=True)[0]
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
        return _generate_mux_wrapper(self.height, self.width, self.mux_type)

    def name(self):
        return f"MuxWrapperAOI_{self.height}_{self.width}_{self.mux_type.name}"
