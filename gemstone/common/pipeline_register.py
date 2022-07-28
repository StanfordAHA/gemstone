import magma
from ..generator.generator import Generator


@magma.cache_definition
def _generate_pipeline_register(T):

    class _PipelineRegister(magma.Circuit):
        name = f"PipelineRegister"
        ports = {
            "clk": magma.In(magma.Clock),
            "I": magma.In(T),
            "O": magma.Out(T),
        }
        io = magma.IO(**ports)

        reg = magma.Register(T)()
        magma.wire(io.clk, reg.CLK)
        magma.wire(io.I, reg.I)
        magma.wire(reg.O, io.O)

    return _PipelineRegister


class PipelineRegister(Generator):
    def __init__(self, T, name=None):
        super().__init__(name)

        self.T = T.undirected_t

        self.add_ports(
            clk=magma.In(magma.Clock),
            I=magma.In(self.T),
            O=magma.Out(self.T),
        )

    def circuit(self):
        return _generate_pipeline_register(self.T)

    def name(self):
        return f"PipelineRegister"
