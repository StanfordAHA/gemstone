import magma
from .core import ConfigurableCore
from .configurable import ConfigurationType
from .mux_with_default import MuxWithDefaultWrapper


class DummyCore(ConfigurableCore):
    def __init__(self):
        super().__init__(8, 32)

        self.add_ports(
            data_in_16b=magma.In(magma.Bits[16]),
            data_out_16b=magma.Out(magma.Bits[16]),
            data_in_1b=magma.In(magma.Bits[1]),
            data_out_1b=magma.Out(magma.Bits[1]),
            config=magma.In(ConfigurationType(8, 32)),
        )

        # Dummy core just passes inputs through to outputs
        self.wire(self.ports.data_in_16b, self.ports.data_out_16b)
        self.wire(self.ports.data_in_1b, self.ports.data_out_1b)

        # Add some config registers
        self.add_configs(
            dummy_1=32,
            dummy_2=32
        )

    def finalize(self):
        self._setup_config()

    def get_config_bitstream(self, instr):
        raise NotImplementedError()

    def instruction_type(self):
        raise NotImplementedError()

    def inputs(self):
        return [self.ports.data_in_1b, self.ports.data_in_16b]

    def outputs(self):
        return [self.ports.data_out_1b, self.ports.data_out_16b]

    def eval_model(self, **kargs):
        # kargs is str -> int
        value_16 = kargs["data_in_16b"] if "data_in_16b" in kargs else 0
        value_1 = kargs["data_in_1b"] if "data_in_1b" in kargs else 0
        return {"data_out_16b": value_16,
                "data_out_1b": value_1}

    def name(self):
        return "DummyCore"


class ReadyValidCore(ConfigurableCore):
    def __init__(self):
        super().__init__(8, 32)

        bit_in = magma.BitIn
        bit_out = magma.BitOut
        self.add_ports(
            data_in_16b=magma.In(magma.Bits[16]),
            data_out_16b=magma.Out(magma.Bits[16]),
            data_in_16b_ready=bit_out,
            data_in_16b_valid=bit_in,
            data_out_16b_ready=bit_in,
            data_out_16b_valid=bit_out,
            data_in_16b_comb=magma.In(magma.Bits[16])
        )

        self.remove_port("read_config_data")
        self.remove_port("reset")

        # Dummy core just passes inputs through to outputs
        self.wire(self.ports.data_in_16b, self.ports.data_out_16b)
        self.wire(self.ports.data_in_16b_ready, self.ports.data_out_16b_ready)
        self.wire(self.ports.data_in_16b_valid, self.ports.data_out_16b_valid)

    def get_config_bitstream(self, instr):
        raise NotImplementedError()

    def instruction_type(self):
        raise NotImplementedError()

    def inputs(self):
        return [self.ports.data_in_16b, self.ports.data_in_16b_comb]

    def outputs(self):
        return [self.ports.data_out_16b]

    def eval_model(self, **kargs):
        pass

    def combinationa_ports(self):
        return [self.ports.data_in_16b_comb]

    def name(self):
        return "ReadyValidCore"
