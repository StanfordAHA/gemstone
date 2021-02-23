import magma as m


class ConfigRegister(m.Generator2):
    def __init__(self, width, addr, addr_width, data_width,
                 use_config_en=False):
        self.addr = addr
        self.name = f"ConfigRegister_{width}_{addr_width}_{data_width}_{addr}"
        self.io = m.IO(
            clk=m.In(m.Clock),
            reset=m.In(m.AsyncReset),
            O=m.Out(m.Bits[width]),
            config_addr=m.In(m.Bits[addr_width]),
            config_data=m.In(m.Bits[data_width]),
        )
        if use_config_en:
            self.io += m.IO(config_en=m.In(m.Bit))
        reg = m.Register(T=m.Bits[width],
                         reset_type=m.AsyncReset,
                         has_enable=True)()
        ce = (self.io.config_addr == addr)
        if use_config_en:
            ce = ce & self.io.config_en
        self.io.O @= reg(I=self.io.config_data[:width], CE=ce)
