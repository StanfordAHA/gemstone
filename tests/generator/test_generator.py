from gemstone.generator.generator import *
import magma


def test_remove_port():
    width = 16

    class Child(Generator):
        def __init__(self):
            super().__init__()
            self.add_ports(
                port0_=magma.In(magma.Bits[width + 1]),
                port0=magma.Out(magma.Bits[width + 1]),
            )

            self.wire(self.ports.port0_, self.ports.port0)

        def name(self):
            return "Child"

    class Gen(Generator):
        def __init__(self):
            super().__init__()
            self.add_ports(
                port0=magma.In(magma.Bits[width + 1]),
                port1=magma.In(magma.Bits[width + 1]),
                port2=magma.Out(magma.Bits[width + 1]),
            )
            child = Child()

            self.wire(self.ports.port0, child.ports.port0_)
            self.wire(self.ports.port1, child.ports.port0)

        def name(self):
            return "TestGen"

    gen = Gen()
    assert len(gen.wires) == 2
    # now remove it
    gen.remove_port("port0")
    assert "port0" not in gen.ports
    assert len(gen.wires) == 1
