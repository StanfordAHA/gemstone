import functools

import magma as m

from gemstone.common import disallow_post_finalization, Finalizable
from gemstone.config_register import ConfigRegister


@functools.lru_cache(maxsize=None)
def _configuration_type(addr_width, data_width):
    fields = dict(config_addr=m.In(m.Bits[addr_width]),
                  config_data=m.In(m.Bits[data_width]),
                  read=m.In(m.Bit), write=m.In(m.Bit))
    return m.Product.from_fields("ConfigurationType", fields)


class _RegisterFinalizer(Finalizable):
    def __init__(self, max_width, inst_callback):
        super().__init__()
        self._max_width = max_width
        self._inst_callback = inst_callback
        self._registers = []
        self._memory_map = {}
        self._current_width = 0

    @property
    def registers(self):
        return self._registers.copy()

    @property
    def memory_map(self):
        return self._memory_map.copy()

    def _finalize_register(self):
        index = len(self._registers)
        reg = self._inst_callback(width=self._current_width, addr=index)
        self._registers.append(reg)
        self._current_width = 0

    @disallow_post_finalization
    def consume(self, name, width):
        if self._current_width + width > self._max_width:
            self._finalize_register()
        new_width = self._current_width + width
        self._memory_map[name] = (
            len(self._registers), self._current_width, new_width)
        self._current_width = new_width

    def _finalize(self):
        if not (self._current_width > 0):
            return
        self._finalize_register()


class _RegisterSet(Finalizable):
    def __init__(self, addr_width, data_width):
        super().__init__()
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

        def _inst_callback(width, addr):
            ckt = ConfigRegister(width, addr, self._addr_width,
                                 self._data_width, use_config_en=True)
            return ckt(name=f"config_reg_{addr}")

        finalizer = _RegisterFinalizer(
            max_width=self._data_width, inst_callback=_inst_callback)
        # Iteration (and therefore address assignment) order is based on
        # ascending name of register. Individual registers are packed into
        # maximally sized registers (given this iteration order).
        for name in sorted(self._staged_register_widths.keys()):
            width = self._staged_register_widths[name]
            finalizer.consume(name, width)
        finalizer.finalize()
        self._registers = finalizer.registers
        self._memory_map = finalizer.memory_map
        self._values = {}
        for name, (idx, lo, hi) in self._memory_map.items():
            self._values[name] = self._registers[idx].O[lo:hi]

    def registers(self):
        return self._registers.copy()

    def get_memory_map(self, name):
        return self._memory_map[name]

    def get_value(self, name):
        return self._values[name]


class Configurable(m.CircuitBuilder):
    def __init__(self, name, addr_width, data_width):
        super().__init__(name)
        self._add_ports(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
            config=_configuration_type(addr_width, data_width),
            read_config_data=m.Out(m.Bits[data_width]),
        )
        self.__register_set = _RegisterSet(addr_width, data_width)
        self.__values = {}

    def add_config(self, name, width):
        self.__register_set.add_register(name, width)
        self.__values[name] = m.Bits[width]()

    def add_configs(self, **kwargs):
        for name, width in kwargs.items():
            self.add_config(name, width)

    def get_reg_info(self, name):
        return self.__register_set.get_memory_map(name)

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

    def _get_value(self, name):
        return self.__values[name]

    @m.builder_method
    def _finalize(self):
        self.__register_set.finalize()
        registers = self.__register_set.registers()
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
            # NOTE(rsetaluri): data_width - 1 is hack due to magma's zext.
            data = m.bits(0, data_width - 1)
        elif len(registers) == 1:
            data = registers[0].O
        else:
            outputs = [m.zext_to(reg.O, data_width) for reg in registers]
            sel = config.config_addr[:m.clog2(len(outputs))]
            data = m.mux(outputs, sel)
        read_config_data @= m.zext_to(data, len(read_config_data))
        # Drive place-holders for values.
        for name, value in self.__values.items():
            value @= self.__register_set.get_value(name)
