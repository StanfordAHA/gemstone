import magma
import mantle
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma
from .collections import DotDict
from ..generator.port_reference import PortReferenceBase
from .mux_wrapper import MuxWrapper
from .zext_wrapper import ZextWrapper
from .slice_wrapper import SliceWrapper


@magma.cache_definition
def _generate_config_register(width, addr, addr_width,
                              data_width, use_config_en):
    T = magma.Bits[width]

    class _ConfigRegister(magma.Circuit):
        name = f"ConfigRegister_{width}_{addr_width}_{data_width}_{addr}"
        ports = {
            "clk": magma.In(magma.Clock),
            "reset": magma.In(magma.AsyncReset),
            "O": magma.Out(T),
            "config_addr": magma.In(magma.Bits[addr_width]),
            "config_data": magma.In(magma.Bits[data_width]),
        }
        if use_config_en:
            ports["config_en"] = magma.In(magma.Bit)
        io = magma.IO(**ports)

        reg = mantle.Register(width,
                              has_ce=True,
                              has_async_reset=True)
        magma.wire(io.clk, reg.CLK)
        ce = (io.config_addr == magma.bits(addr, addr_width))
        magma.wire(io.reset, reg.ASYNCRESET)
        if use_config_en:
            ce = ce & io.config_en
        magma.wire(io.config_data[0:width], reg.I)
        magma.wire(magma.enable(ce), reg.CE)
        magma.wire(reg.O, io.O)

    return _ConfigRegister


def ConfigurationType(addr_width, data_width):
    return magma.Product.from_fields("ConfigurationType",
                                     dict(config_addr=magma.Bits[addr_width],
                                          config_data=magma.Bits[data_width],
                                          read=magma.Bits[1],
                                          write=magma.Bits[1]))


class Configurable(Generator):
    def __init__(self, config_addr_width, config_data_width, double_buffer=False):
        super().__init__()

        self.__registers = []
        self.__register_cache = {}
        self.__register_map = {}
        self.registers = DotDict()

        self.config_addr_width = config_addr_width
        self.config_data_width = config_data_width

        self.read_config_data_mux: MuxWrapper = None

        self.double_buffer = double_buffer
        self.double_buffer_map = {}

        # Ports for reconfiguration.
        self.add_ports(
            clk=magma.In(magma.Clock),
            reset=magma.In(magma.AsyncReset),
            read_config_data=magma.Out(magma.Bits[config_data_width]),
        )

        if double_buffer:
            # add extra ports to deal with double buffer
            self.add_ports(
                config_db=magma.In(magma.Bit),
                use_db=magma.In(magma.Bit)
            )

    def add_config(self, name, width):
        if name in self.registers:
            raise ValueError(f"{name} is already a register")
        self.__register_cache[name] = width
        # ideally we should create create the slice wrapper here. since at
        # this point we don't know the exact size, we need to able to resize
        # the port later. however, the framework is not set up to do runtime
        # changes on port width, so we need to be creative here
        # 1. we create a full sized slice wrapper
        # 2. remove the input port
        # 3. later on when we actually create the registers, resize the input
        slice_wrapper = SliceWrapper(self.config_data_width, 0, width,
                                     name=name)
        slice_wrapper.ports.pop("I")
        self.registers[name] = slice_wrapper

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)

    def get_reg_info(self, name):
        return self.__register_map[name]

    def __create_register(self, working_set):
        reg_width = working_set[-1][-1]
        assert reg_width <= self.config_data_width, \
            f"register width ({reg_width} is larger than config " \
            f"addr width ({self.config_data_width}"
        # create a register
        idx = len(self.__registers)
        reg = ConfigRegister(reg_width, True, name=f"config_reg_{idx}")
        self.__registers.append(reg)
        if self.double_buffer:
            reg_db = ConfigRegister(reg_width, True, name=f"config_reg_{idx}_db")
            # set the reg map
            self.double_buffer_map[reg.instance_name] = reg_db
        else:
            reg_db = None

        reg.set_addr(idx)
        reg.set_addr_width(self.config_addr_width)
        reg.set_data_width(self.config_data_width)

        if self.double_buffer:
            reg_db.set_addr(idx)
            reg_db.set_addr_width(self.config_addr_width)
            reg_db.set_data_width(self.config_data_width)

        if self.double_buffer:
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.reset, reg.ports.reset)
            self.wire(self.ports.config.config_addr, reg_db.ports.config_addr)
            self.wire(self.ports.config.config_data, reg_db.ports.config_data)
            self.wire(self.ports.reset, reg_db.ports.reset)
        else:
            self.wire(self.ports.config.config_addr, reg.ports.config_addr)
            self.wire(self.ports.config.config_data, reg.ports.config_data)
            self.wire(self.ports.config.write[0], reg.ports.config_en)
            self.wire(self.ports.reset, reg.ports.reset)

        if self.double_buffer:
            # create a 2-1 MUX, could have been an one-liner in SV
            mux_select = MuxWrapper(2, reg_width, f"{reg.instance_name}_db_sel_{idx}")
            self.wire(mux_select.ports.S[0], self.ports.use_db)
            # set it up in such way that if use_db is 0 (default), we will use the normal reg
            self.wire(mux_select.ports.I[0], reg.ports.O)
            self.wire(mux_select.ports.I[1], reg_db.ports.O)
            reg_out = mux_select.ports.O
        else:
            reg_out = reg.ports.O

        for name, lo, hi in working_set:
            # need to create a slice
            slice_wrapper = self.registers[name]
            slice_wrapper.base_width = reg_width
            slice_wrapper.lo = lo
            slice_wrapper.hi = hi
            slice_wrapper.add_ports(I=magma.In(magma.Bits[reg_width]))
            self.wire(reg_out, slice_wrapper.ports.I)
            # create map
            self.__register_map[name] = (idx, lo, hi)

        working_set.clear()

    def get_config_data(self, name, value):
        idx, lo, hi = self.__register_map[name]
        width = hi - lo
        assert value < (1 << width)
        return idx, value << lo

    def get_reg_idx(self, name):
        return self.__register_map[name][0]

    def _setup_config(self):
        # Sort the registers by it's name. this will be the order of config addr
        # index.
        # notice that we also do register packing, where small registers will
        # be packed together to fit in the config addr size, which in most case,
        # is 32
        reg_addr_offset = 0
        working_set = []
        config_names = list(self.__register_cache.keys())
        config_names.sort()
        for config_name in config_names:
            reg_width = self.__register_cache[config_name]
            # try fit into the word boundrary
            if reg_width + reg_addr_offset > self.config_data_width:
                # we need to create a register based on the working set
                # create the reg
                self.__create_register(working_set)
                reg_addr_offset = 0

            lo = reg_addr_offset
            hi = reg_addr_offset + reg_width
            working_set.append((config_name, lo, hi))
            reg_addr_offset += reg_width

        if working_set:
            self.__create_register(working_set)

        if self.double_buffer and self.__registers:
            not_gate = FromMagma(mantle.DefineInvert(1))
            and_gate = FromMagma(mantle.DefineAnd(2))
            and_gate_db = FromMagma(mantle.DefineAnd(2))
            # use a NOT gate
            self.wire(self.ports.config_db, not_gate.ports.I[0])
            # use an AND gate
            self.wire(and_gate.ports.I0, not_gate.ports.O[0])
            self.wire(and_gate.ports.I1, self.ports.config.write[0])
            self.wire(and_gate_db.ports.I0, self.ports.config_db)
            self.wire(and_gate_db.ports.I1, self.ports.config.write[0])

            for reg in self.__registers:
                reg_db = self.double_buffer_map[reg.instance_name]
                # connect register config_en
                self.wire(and_gate.ports.O, reg.ports.config_en)
                # connect db register config_en
                self.wire(and_gate_db.ports.O, reg_db.ports.config_en)

        def _zext(port, old_width, new_width):
            if old_width == new_width:
                return port
            zext = ZextWrapper(old_width, new_width)
            self.wire(port, zext.ports.I)
            return zext.ports.O

        # read_config_data output.
        num_config_reg = len(self.__registers)
        if num_config_reg > 1:
            self.read_config_data_mux = MuxWrapper(num_config_reg,
                                                   self.config_data_width)
            sel_bits = self.read_config_data_mux.sel_bits
            # Wire up config_addr to select input of read_data MUX.
            self.wire(self.ports.config.config_addr[:sel_bits],
                      self.read_config_data_mux.ports.S)
            self.wire(self.read_config_data_mux.ports.O,
                      self.ports.read_config_data)

            for idx, reg in enumerate(self.__registers):
                # we need to create a mux to select read config as well
                if self.double_buffer:
                    mux = MuxWrapper(2, reg.width, f"read_data_mux_db_{idx}")
                    self.wire(mux.ports.S[0], self.ports.config_db)
                    self.wire(mux.ports.I[0], reg.ports.O)
                    reg_db = self.double_buffer_map[reg.instance_name]
                    self.wire(mux.ports.I[1], reg_db.ports.O)
                    reg_out = mux.ports.O
                else:
                    reg_out = reg.ports.O
                zext_out = _zext(reg_out, reg.width, self.config_data_width)
                self.wire(zext_out, self.read_config_data_mux.ports.I[idx])
        elif num_config_reg == 1:
            reg = self.__registers[0]
            if self.double_buffer:
                mux = MuxWrapper(2, reg.width, f"read_data_mux_db")
                self.wire(mux.ports.S[0], self.ports.config_db)
                self.wire(mux.ports.I[0], reg.ports.O)
                reg_db = self.double_buffer_map[reg.instance_name]
                self.wire(mux.ports.I[1], reg_db.ports.O)
                reg_out = mux.ports.O
            else:
                reg_out = reg.ports.O
            zext_out = _zext(reg_out, reg.width, self.config_data_width)
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
        return _generate_config_register(self.width, self.addr, self.addr_width,
                                         self.data_width, self.use_config_en)

    def name(self):
        return f"ConfigRegister"\
            f"_{self.width}"\
            f"_{self.addr_width}"\
            f"_{self.data_width}"\
            f"_{self.addr}"
