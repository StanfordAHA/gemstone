import magma
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma


@magma.cache_definition
def _generate_mux_wrapper(height, width):
    sel_bits = magma.bitutils.clog2(height)
    T = magma.Bits[width]

    class _MuxWrapper(magma.Circuit):
        name = f"MuxWrapper_{height}_{width}"
        in_height = max(1, height)

        ports = {
            "I": magma.In(magma.Array[in_height, T]),
            "O": magma.Out(T),
        }
        if height > 1:
            ports["S"] = magma.In(magma.Bits[sel_bits])

        io = magma.IO(**ports)

        if height <= 1:
            magma.wire(io.I[0], io.O)
        else:
            mux = magma.Mux(height, magma.Bits[width])()
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

            self.sel_bits = 0
            return

        self.sel_bits = magma.bitutils.clog2(self.height)

        self.add_ports(
            I=magma.In(magma.Array[self.height, T]),
            S=magma.In(magma.Bits[self.sel_bits]),
            O=magma.Out(T),
        )

    def circuit(self):
        return _generate_mux_wrapper(self.height, self.width)

    def name(self):
        return f"MuxWrapper_{self.height}_{self.width}"
