import magma
from ..generator.generator import Generator


@magma.cache_definition
def _generate_zext_wrapper(in_width, out_width):
    diff = out_width - in_width

    class _ZextWrapper(magma.Circuit):
        name = f"ZextWrapper_{in_width}_{out_width}"
        io = magma.IO(
            I=magma.In(magma.Bits[in_width]),
            O=magma.Out(magma.Bits[out_width]),
        )

        @classmethod
        def definition(io):
            magma.wire(magma.zext(io.I, diff), io.O)

    return _ZextWrapper


class ZextWrapper(Generator):
    def __init__(self, in_width, out_width):
        super().__init__()

        if out_width <= in_width:
            raise ValueError(f"output width must be greater than input width "
                             f"(output width = {out_width}, input width = "
                             f"{in_width})")

        self.in_width = in_width
        self.out_width = out_width

        self.add_ports(
            I=magma.In(magma.Bits[self.in_width]),
            O=magma.Out(magma.Bits[self.out_width]),
        )

    def circuit(self):
        return _generate_zext_wrapper(self.in_width, self.out_width)

    def name(self):
        return f"ZextWrapper_{self.in_width}_{self.out_width}"
