import magma
import mantle
from ..generator.generator import Generator
from .collections import DotDict
from ..generator.port_reference import PortReferenceBase


@magma.cache_definition
def _generate_config_register(width, addr, addr_width,
                              data_width, use_config_en):
    T = magma.Bits(width)

    class _ConfigRegister(magma.Circuit):
        name = f"ConfigRegister_{width}_{addr_width}_{data_width}_{addr}"
        IO = [
            "clk", magma.In(magma.Clock),
            "reset", magma.In(magma.AsyncReset),
            "O", magma.Out(T),
            "config_addr", magma.In(magma.Bits(addr_width)),
            "config_data", magma.In(magma.Bits(data_width)),
        ]
        if use_config_en:
            IO.extend(["config_en", magma.In(magma.Bit)])

        @classmethod
        def definition(io):
            reg = mantle.Register(width,
                                  has_ce=True,
                                  has_async_reset=True)
            magma.wire(io.clk, reg.CLK)
            ce = (io.config_addr == magma.bits(addr, addr_width))
            magma.wire(io.reset, reg.ASYNCRESET)
            if use_config_en:
                ce = ce & io.config_en
            magma.wire(io.config_data[0:width], reg.I)
            magma.wire(ce, reg.CE)
            magma.wire(reg.O, io.O)

    return _ConfigRegister


def ConfigurationType(addr_width, data_width):
    return magma.Tuple(config_addr=magma.Bits(addr_width),
                       config_data=magma.Bits(data_width),
                       read=magma.Bits(1),
                       write=magma.Bits(1)
                       )


class Configurable(Generator):
    def __init__(self):
        super().__init__()

        self.registers = DotDict()

    def add_config(self, name, width):
        if name in self.registers:
            raise ValueError(f"{name} is already a register")
        register = ConfigRegister(width, True, name=name)
        self.registers[name] = register

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)


class ConfigRegister(Generator):
    def __init__(self, width, use_config_en=False, name=None):
        super().__init__(name)

        self.width = width
        self.use_config_en = use_config_en

        self.addr = None
        self.global_addr = None
        self.addr_width = None
        self.data_width = None

        T = magma.Bits(self.width)

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            O=magma.Out(T),
        )
        if self.use_config_en:
            self.add_ports(config_en=magma.In(magma.Bit))

    # TODO(rsetaluri): Implement this.
    def write(self, value):
        raise NotImplementedError()

    # TODO(rsetaluri): Implement this.
    def read(self):
        raise NotImplementedError()

    def set_addr(self, addr):
        self.addr = addr

    def set_global_addr(self, global_addr):
        self.global_addr = global_addr

    def set_addr_width(self, addr_width):
        self.addr_width = addr_width
        self.add_port("config_addr", magma.In(magma.Bits(self.addr_width)))

    def set_data_width(self, data_width):
        self.data_width = data_width
        self.add_port("config_data", magma.In(magma.Bits(self.data_width)))

    def circuit(self):
        return _generate_config_register(self.width, self.addr, self.addr_width,
                                         self.data_width, self.use_config_en)

    def name(self):
        return f"ConfigRegister"\
            f"_{self.width}"\
            f"_{self.addr_width}"\
            f"_{self.data_width}"\
            f"_{self.addr}"
