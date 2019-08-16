import magma
import mantle
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma
from ..generator.const import Const
from .collections import DotDict
from ..generator.port_reference import PortReferenceBase
from .mux_wrapper import MuxWrapper
from .zext_wrapper import ZextWrapper


def ConfigurationType(addr_width, data_width):
    return magma.Tuple(config_addr=magma.Bits[addr_width],
                       config_data=magma.Bits[data_width],
                       read=magma.Bits[1],
                       write=magma.Bits[1]
                       )


class Configurable(Generator):
    def __init__(self, config_addr_width, config_data_width):
        super().__init__()

        self.registers = DotDict()

        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width

        self.read_config_data_mux: MuxWrapper = None

        # Ports for reconfiguration.
        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            read_config_data=magma.Out(magma.Bits[config_data_width]),
        )

    def add_config(self, name, width):
        if name in self.registers:
            raise ValueError(f"{name} is already a register")
        register = ConfigRegister(width, True, name=name)
        self.registers[name] = register

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)

    def _setup_config(self):
        # Sort the registers by it's name. this will be the order of config addr
        # index.
        config_names = list(self.registers.keys())
        config_names.sort()
        for idx, config_name in enumerate(config_names):
            reg = self.registers[config_name]
            # Set the configuration registers.
            reg.set_addr(idx)
            reg.set_addr_width(self.config_addr_width)
            reg.set_data_width(self.config_data_width)

            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        def _zext(port, old_width, new_width):
            if old_width == new_width:
                return port
            zext = ZextWrapper(old_width, new_width)
            self.wire(port, zext.ports.I)
            return zext.ports.O

        # read_config_data output.
        num_config_reg = len(config_names)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg,
                                                   self.config_data_width)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX.
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)

            for idx, config_name in enumerate(config_names):
                reg = self.registers[config_name]
                zext_out = _zext(reg.ports.O, reg.width, self.config_data_width)
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        elif num_config_reg == 1:
            config_name = config_names[0]
            reg = self.registers[config_name]
            zext_out = _zext(reg.ports.O, reg.width, self.config_data_width)
            self.wire(zext_out, self.ports.read_config_data)


class ConfigRegister(Generator):
    def __init__(self, width, use_config_en=False, name=None):
        super().__init__(name)

        self.width = width
        self.use_config_en = use_config_en

        self.addr = None
        self.global_addr = None
        self.addr_width = None
        self.data_width = None

        T = magma.Bits[self.width]

        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            O=magma.Out(T),
        )
        if self.use_config_en:
            self.add_ports(config_en=magma.In(magma.Bit))

        self.reg = FromMagma(mantle.DefineRegister(width,
                                                   has_ce=True,
                                                   has_async_reset=True))



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
        self.add_port("config_addr", magma.In(magma.Bits[self.addr_width]))

    def set_data_width(self, data_width):
        self.data_width = data_width
        self.add_port("config_data", magma.In(magma.Bits[self.data_width]))

    def circuit(self):
        eq = FromMagma(mantle.DefineEQ(self.addr_width))
        eq.instance_name = "EQ_ADDR"
        self.wire(self.ports.config_addr, eq.ports.I0)
        self.wire(Const(self.addr), eq.ports.I1)
        if self.use_config_en:
            and_ = FromMagma(mantle.DefineAnd(2))
            and_.instance_name = "AND_ADDR"
            self.wire(self.ports.config_en, and_.ports.I0)
            self.wire(eq.ports.O, and_.ports.I1)
            self.wire(and_.ports.O, self.reg.ports.CE)
        else:
            self.wire(eq.ports.O, self.reg.ports.CE)

        self.wire(self.reg.ports.O, self.ports.O)
        self.wire(self.reg.ports.CLK, self.ports.clk)
        self.wire(self.reg.ports.ASYNCRESET, self.ports.reset)
        self.wire(self.ports.config_data[0:self.width], self.reg.ports.I)

        return super(ConfigRegister, self).circuit()

    def name(self):
        return f"ConfigRegister"\
            f"_{self.width}"\
            f"_{self.addr_width}"\
            f"_{self.data_width}"\
            f"_{self.addr}"
