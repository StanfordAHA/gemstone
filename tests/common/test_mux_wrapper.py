import pytest
from random import randint
import tempfile
from hwtypes import BitVector
import fault
import fault.random
import magma
from gemstone.common.mux_wrapper import MuxWrapper


@pytest.mark.parametrize('height,width', [(randint(2, 10), randint(1, 32))
                                          for _ in range(5)])
def test_mux_wrapper(height, width):
    """
    Test that the mux wrapper circuit works as expected. Specifically, we
    initialize a mux with random height and width, and check that the output is
    as expected for select in range [0, height).

    Note that we do not check the behavior with sel >= height, because this is
    undefined behavior.
    """
    mux = MuxWrapper(height, width)
    assert mux.height == height
    assert mux.width == width
    assert mux.name() == f"MuxWrapper_{height}_{width}"

    mux_circuit = mux.circuit()
    tester = fault.Tester(mux_circuit)
    inputs = [fault.random.random_bv(width) for _ in range(height)]
    for i, input_ in enumerate(inputs):
        tester.poke(mux_circuit.I[i], input_)
    for i in range(height):
        tester.poke(mux_circuit.S, BitVector[mux.sel_bits](i))
        tester.eval()
        tester.expect(mux_circuit.O, inputs[i])
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])


def test_pass_through_mux_wrapper():
    height = 1
    width = 16
    mux = MuxWrapper(height, width)
    assert mux.height == height
    assert mux.width == width
    assert mux.name() == f"MuxWrapper_{height}_{width}"

    mux_circuit = mux.circuit()
    tester = fault.Tester(mux_circuit)
    input_ = fault.random.random_bv(width)
    tester.poke(mux_circuit.I[0], input_)
    tester.eval()
    tester.expect(mux_circuit.O, input_)
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
