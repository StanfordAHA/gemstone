from gemstone.generator.generator import *
import magma


class _Child(Generator):
    def __init__(self, width):
        super().__init__()
        self.add_ports(
            port0_=magma.In(magma.Bits[width + 1]),
            port0=magma.Out(magma.Bits[width + 1]),
        )

        self.wire(self.ports.port0_, self.ports.port0)

    def name(self):
        return "Child"


class _Gen(Generator):
    def __init__(self, width):
        super().__init__()
        self.add_ports(
            port0=magma.In(magma.Bits[width + 1]),
            port1=magma.In(magma.Bits[width + 1]),
            port2=magma.Out(magma.Bits[width + 1]),
        )
        self.child = _Child(width)

        self.wire(self.ports.port0, self.child.ports.port0_)
        self.wire(self.ports.port1, self.child.ports.port0)

    def name(self):
        return "TestGen"


def test_remove_port():
    gen = _Gen(16)
    assert len(gen.wires) == 2
    # now remove it
    gen.remove_port("port0")
    assert "port0" not in gen.ports
    assert len(gen.wires) == 1


def test_port_connections():
    gen = _Gen(16)
    assert gen.ports.port0._connections == [gen.child.ports.port0_]
    gen.remove_wire(gen.ports.port0, gen.child.ports.port0_)
    assert gen.ports.port0._connections == []
