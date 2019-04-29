from gemstone.common.transform import *
from gemstone.generator import Const
import magma
import fault
import tempfile


class Child1(Generator):
    CONST = 1

    def __init__(self, width):
        super().__init__()

        self.add_ports(
            port0=magma.In(magma.Bits[width]),
            port1=magma.Out(magma.Bits[width]),
        )

        add_ = FromMagma(mantle.DefineAdd(width))
        self.wire(self.ports["port0"], add_.ports.I0)
        self.wire(Const(self.CONST), add_.ports.I1)
        self.wire(self.ports["port1"], add_.ports.O)

    def name(self):
        return "Child1"


class Child2(Generator):
    CONST = 2

    def __init__(self, width):
        super().__init__()

        self.add_ports(
            port0=magma.In(magma.Bits[width]),
            port1=magma.Out(magma.Bits[width]),
        )

        add_ = FromMagma(mantle.DefineMul(width))
        self.wire(self.ports["port0"], add_.ports.I0)
        self.wire(Const(self.CONST), add_.ports.I1)
        self.wire(self.ports["port1"], add_.ports.O)

    def name(self):
        return "Child2"


class Child3(Generator):
    def __init__(self, width):
        super().__init__()

        child_2_const = 2

        self.add_ports(
            port0=magma.In(magma.Bits[width + 1]),
            port1=magma.Out(magma.Bits[width + 1]),
        )

        add_ = FromMagma(mantle.DefineAdd(width))
        self.wire(self.ports["port0"], add_.ports.I0)
        self.wire(Const(child_2_const), add_.ports.I1)
        self.wire(self.ports["port1"], add_.ports.O)

    def name(self):
        return "Child3"


class Child4(Generator):
    def __init__(self, width):
        super().__init__()

        self.add_ports(
            port0=magma.In(magma.Bits[width]),
            port2=magma.In(magma.Bits[width]),
            port1=magma.Out(magma.Bits[width]),
        )

        add_ = FromMagma(mantle.DefineMul(width))
        self.wire(self.ports["port0"], add_.ports.I0)
        self.wire(self.ports["port2"], add_.ports.I1)
        self.wire(self.ports["port1"], add_.ports.O)

    def name(self):
        return "Child4"


class Parent(Generator):
    def __init__(self, width):
        super().__init__()
        self.add_ports(
            port0=magma.In(magma.Bits[width]),
            port1=magma.Out(magma.Bits[width])
        )

        self.child = Child1(width)
        self.wire(self.ports.port0, self.child.ports.port0)
        self.wire(self.ports.port1, self.child.ports.port1)

    def name(self):
        return "Parent"


def test_remove_simple():
    width = 16
    num_inputs = 10

    parent = Parent(width)
    new_child = Child3(width)
    try:
        # try to replace one with different interface
        replace(parent, parent.child, new_child)
        assert False
    except AssertionError:
        pass
    new_child = Child2(width)
    replace(parent, parent.child, new_child)

    circuit = parent.circuit()
    tester = fault.Tester(circuit)
    inputs = [fault.random.random_bv(width) for _ in range(num_inputs)]
    for i in range(num_inputs):
        tester.poke(circuit.port0, inputs[i])
        tester.eval()
        tester.expect(circuit.port1, inputs[i] * Child2.CONST)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])


def test_remove_complex():
    width = 16
    num_inputs = 10

    parent = Parent(width)

    # we want to group child1 and child2 together to replace parent.child
    new_child1 = Child1(width)
    new_child2 = Child2(width)
    parent.wire(new_child1.ports.port1, new_child2.ports.port0)
    replace(parent, parent.child, [new_child1, new_child2])

    circuit = parent.circuit()
    tester = fault.Tester(circuit)
    inputs = [fault.random.random_bv(width) for _ in range(num_inputs)]
    for i in range(num_inputs):
        tester.poke(circuit.port0, inputs[i])
        tester.eval()
        tester.expect(circuit.port1, (inputs[i] + Child1.CONST) * Child2.CONST)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])


def test_remove_complex_ignore():
    width = 16
    num_inputs = 10
    # 42 is the answer to everything
    const = 42

    parent = Parent(width)

    # we want to group child1 and child2 together to replace parent.child
    new_child1 = Child1(width)
    new_child4 = Child4(width)
    parent.wire(new_child1.ports.port1, new_child4.ports.port0)
    replace(parent, parent.child, [new_child1, new_child4],
            ignored_ports=[new_child4.ports.port2])
    # we have to wire this port by ourselves
    parent.wire(new_child4.ports.port2, Const(const))

    circuit = parent.circuit()
    tester = fault.Tester(circuit)
    inputs = [fault.random.random_bv(width) for _ in range(num_inputs)]
    for i in range(num_inputs):
        tester.poke(circuit.port0, inputs[i])
        tester.eval()
        tester.expect(circuit.port1, (inputs[i] + Child1.CONST) * const)

    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
