from gemstone.generator.const import Const, Generator
import magma as m


def test_eq():
    const1 = Const(1)
    const1_ = Const(1)
    assert const1 == const1_
    const2 = Const(2)
    assert const2 != const1

    s = set()
    s.add(const1)
    s.add(const1_)
    assert len(s) == 1


def test_wire():
    class Gen(Generator):
        def __init__(self):
            super().__init__()
            self.add_ports(in1=m.In(m.Bits[1]),
                           in2=m.In(m.Bits[1]))
            self.wire(self.ports.in1, Const(1))

        def name(self):
            return "Test"

    gen = Gen()
    assert len(gen.wires) == 1
    gen.remove_wire(gen.ports.in1, Const(1))
    assert len(gen.wires) == 0
