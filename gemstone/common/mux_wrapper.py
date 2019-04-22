import magma
import mantle
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma


@magma.cache_definition
def _generate_mux_wrapper(height, width):
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
                mux = mantle.DefineMux(height, width)()
                for i in range(height):
                    magma.wire(io.I[i], mux.interface.ports[f"I{i}"])
                mux_in = io.S if sel_bits > 1 else io.S[0]
                magma.wire(mux_in, mux.S)
                magma.wire(mux.O, io.O)

    return _MuxWrapper


class MuxWrapper(Generator):
    def __init__(self, height, width, name=None):
        super().__init__(name)

        self.height = max(height, 1)
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

        self.sel_bits = magma.bitutils.clog2(self.height)

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
