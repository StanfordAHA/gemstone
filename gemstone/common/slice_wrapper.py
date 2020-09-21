import magma
from ..generator.generator import Generator


@magma.cache_definition
def _generate_slice_wrapper(base_width, lo, hi, name_):
    class _SliceWrapper(magma.Circuit):
        name = name_
        io = magma.IO(
            I=magma.In(magma.Bits[base_width]),
            O=magma.Out(magma.Bits[hi - lo]),
        )
        magma.wire(io.I[lo:hi], io.O)
    return _SliceWrapper


class SliceWrapper(Generator):
    def __init__(self, base_width, lo, hi, name=None):
        super().__init__()

        self.base_width = base_width
        self.lo = lo
        self.hi = hi
        self.width = hi - lo

        self.__name = name

        self.add_ports(
            I=magma.In(magma.Bits[self.base_width]),
            O=magma.Out(magma.Bits[self.hi - lo]),
        )

    def circuit(self):
        return _generate_slice_wrapper(self.base_width, self.lo, self.hi,
                                       self.name())

    def name(self):
        if self.__name is None:
            return f"SliceWrapper_{self.base_width}_{self.lo}_{self.hi}"
        else:
            return self.__name
