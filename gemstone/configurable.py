import functools

import magma as m

from gemstone.common import disallow_post_finalization, Finalizable
from gemstone.config_register import ConfigRegister


@functools.lru_cache(maxsize=None)
def _configuration_type(addr_width, data_width):
    fields = dict(config_addr=m.Bits[addr_width],
                  config_data=m.Bits[data_width], read=m.Bit, write=m.Bit)
    return magm.Product.from_fields("ConfigurationType", fields)


class _RegisterSet(Finalizable):
    def __init__(self, addr_width, data_width):
        self._addr_width = addr_width
        self._data_width = data_width
        self._staged_register_widths = {}

    @property
    def addr_width(self):
        return self._addr_width

    @property
    def data_width(self):
        return self._data_width

    @disallow_post_finalization
    def add_register(self, name, width):
        try:
            self._staged_register_widths[name]
            raise Exception(f"{name} is already a register")
        except KeyError:
            pass
        self._staged_register_widths[name] = width

    def _finalize(self):
        registers = []
        memory_map = {}
        current_width = 0
        # Iteration (and therefore address assignment) order is based on
        # ascending name of register. Individual registers are packed into
        # maximally sized registers (given this iteration order).
        for name in sorted(self._staged_register_widths.keys()):
            width = self._staged_register_widths[name]
            if width + current_width > self._data_width:
                index = len(registers)
                ckt = ConfigRegister(
                    current_width, index, self._addr_width, self._data_width)
                registers.append(ckt(name=f"config_reg_{index}"))
            new_width = current_width + width
            memory_map[name] = (len(registers), current_width, new_width)
            current_width = new_width
        values = {}
        for name, (idx, lo, hi) in memory_map.items():
            values[name] = registers[idx].O[lo:hi]
        self._registers = registers
        self._memory_map = memory_map
        self._values = values

    def registers(self):
        return self._registers.copy()

    def get_memory_map(self, name):
        return self._memory_map[name]

    def get_value(self, name):
        return self._values[name]


class Configurable(m.CircuitBuilder):
    def __init__(self, name, addr_width, data_width):
        super().__init__(name)
        self.add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
            config=_configuration_type(addr_width, data_width),
            read_config_data=m.Out(m.Bits[data_width]),
        )
        self._register_set = _RegisterSet(addr_width, data_width)

    def add_config(self, name, width):
        self._register_set.add_register(name, width)

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)

    def get_reg_info(self, name):
        return self._register_set.get_memory_map(name)

    def get_config_data(self, name, value):
        idx, lo, hi = self.get_reg_info(name)
        width = hi - lo
        assert value < (1 << width)
        return idx, value << lo

    def get_reg_idx(self, name):
        idx, _, _ = self.get_reg_info(name)

    def _config(self):
        return self._port("config")

    def _read_config_data(self):
        return self._port("read_config_data")

    def _finalize(self):
        self._register_set.finalize()
        registers = self._register_set.registers() 
        config = self._config()
        for reg in registers:
            reg.config_addr @= config.config_addr
            reg.config_data @= config.config_data
            reg.config_en @= config.write
        read_config_data = self._read_config_data()
        data_width = len(read_config_data)
        # Connect read_config_data based on the number of actual hardware
        # registers (not the number of logical registers).
        if len(registers) < 1:
            data = m.bits(0, data_width)
        elif len(registers) == 1:
            data = registers[0].O
        else:
            outputs = [m.zext_to(reg.O, data_width) for reg in registers]
            sel = config.config_addr[:m.clog2(len(outputs))]
            data = m.mux(outputs, sel)
        read_config_data @= m.zext_to(data, read_config_data)
