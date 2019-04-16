import magma
import mantle
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma
from ..generator.from_verilog import FromVerilog
import math

@magma.cache_definition
def _generate_mux_wrapper(height, width):
    sel_bits = magma.bitutils.clog2(height+1) #1-bit extra for the constant 
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
                f = open("mux_aoi_const.sv", "w")
                num_sel = math.ceil(math.log(height+1,2)) #1-bit extra for the constant 
                num_inputs = math.pow(2, num_sel)
                
                f.write("module mux ( \n")
                
                for i in range(height):
                   f.write(f'\tinput logic  [{width-1} : 0] I{i}, \n')
                if num_sel==1:
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
                f.write(f'\toutput logic  [{int(num_inputs)-1} : 0] out_sel );\n')
                
                f.write(f'\nalways_comb begin: mux_sel \n')
                f.write(f'\tcase (S) \n')
                for i in range(height):
                    data = format(int(math.pow(2,int(i))), 'b').zfill(int(num_inputs))
                    data0 = format(0, 'b').zfill(int(num_inputs))
                    f.write(f'\t\t{num_sel}\'d{i}    :   out_sel = {int(num_inputs)}\'b{data}; \n')
                f.write(f'\t\t{num_sel}\'d{i+1}    :   out_sel = {int(num_inputs)}\'b{data0}; \n')
                f.write(f'\t\tdefault :   out_sel = {int(num_inputs)}\'b0; \n''')
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
                    #data =  bin(int(math.pow(2,int(i))))
                    data = format(int(math.pow(2,int(i))), 'b').zfill(int(num_inputs))
                    
                    f.write(f'\t\t{int(num_inputs)}\'b{data}    :   O = I{i}; \n')
                data = format(int(math.pow(2,int(i+1))), 'b').zfill(int(num_inputs))
                f.write(f'\t\t{int(num_inputs)}\'b{data}    :   O = 0; \n')
                f.write(f'\t\tdefault :   O = 0; \n''')
                f.write(f'\tendcase \n')
                f.write(f'end \n')
                
                f.write("endmodule \n")
                f.close()
                #gen_aoimux()
                #mux = FromVerilog("./mux.sv") 
                #mux = FromVerilog("./mux.sv", target_modules=["mux"]) 
                mux = magma.DefineFromVerilogFile("./mux_aoi_const.sv", target_modules=["mux"])[0]()
                #mux = magma.DefineFromVerilogFile("./mux.sv", target_modules=["mux"])[0]
                #mux = mantle.DefineMux(height, width)()
                for i in range(height):
                    magma.wire(io.I[i], mux.interface.ports[f"I{i}"])
                mux_in = io.S if sel_bits > 1 else io.S[0]
                magma.wire(mux_in, mux.S)
                magma.wire(mux.O, io.O)
        
    return _MuxWrapper


class AOIConstMuxWrapper(Generator):
    def __init__(self, height, width, name=None):
        super().__init__(name)

        self.height = height
        self.width = width

        T = magma.Bits[self.width]

        # In the case that @height <= 1, we make this circuit a simple
        # pass-through circuit.
        if self.height <= 1:
            self.add_ports(
                I=magma.In(magma.Array[1, T]),
                O=magma.Out(T),
            )
            #self.wire(self.ports.I[0], self.ports.O)
            self.sel_bits = 0
            return

        #MuxCls = mantle.DefineMux(self.height, self.width)
        #self.mux = FromMagma(MuxCls)

        self.sel_bits = magma.bitutils.clog2(self.height+1) #1-bit extra for the constant  

        self.add_ports(
            I=magma.In(magma.Array[self.height, T]),
            S=magma.In(magma.Bits[self.sel_bits]),
            O=magma.Out(T),
        )

        #for i in range(self.height):
        #    self.wire(self.ports.I[i], self.mux.ports[f"I{i}"])
        #mux_in = self.ports.S if self.sel_bits > 1 else self.ports.S[0]
        #self.wire(mux_in, self.mux.ports.S)
        #self.wire(self.mux.ports.O, self.ports.O)

    def circuit(self):
        return _generate_mux_wrapper(self.height, self.width)

    def name(self):
        return f"MuxWrapper_{self.height}_{self.width}"
