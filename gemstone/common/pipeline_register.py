import magma
from ..generator.generator import Generator
from ..generator.from_magma import FromMagma
from .collections import DotDict
from ..generator.port_reference import PortReferenceBase
from .mux_wrapper_aoi import AOIMuxWrapper
from .zext_wrapper import ZextWrapper
from .slice_wrapper import SliceWrapper


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

        self.T = T

        self.add_ports(
            clk=magma.In(magma.Clock),
            O=magma.In(T),
            O=magma.Out(T),
        )

    def circuit(self):
        return _generate_pipeline_register(T)

    def name(self):
        return f"PipelineRegister"
