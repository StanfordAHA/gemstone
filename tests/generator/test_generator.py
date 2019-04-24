from gemstone.generator.generator import *
import magma


def test_remove_port():
    width = 16

    class Gen(Generator):
        def __init__(self):
            super().__init__()
            self.add_ports(
                port0=magma.In(magma.Bits[width + 1]),
                port1=magma.Out(magma.Bits[width + 1]),
            )

            self.wire(self.ports.port0, self.ports.port1)

        def name(self):
            return "TestGen"

    gen = Gen()
    assert len(gen.wires) == 1
    # now remove it
    gen.remove_port(gen.ports.port0)
    assert "port0" not in gen.ports
    assert len(gen.wires) == 0
