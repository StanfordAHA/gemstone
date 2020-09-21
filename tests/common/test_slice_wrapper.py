import pytest
import random
import tempfile
import fault
from gemstone.common.slice_wrapper import SliceWrapper


@pytest.mark.parametrize("lo,hi", [(5, 10), (10, 11)])
def test_slice_wrapper(lo, hi):
    width = 32
    slice_wrapper = SliceWrapper(width, lo, hi)
    slice_wrapper_circuit = slice_wrapper.circuit()

    tester = fault.Tester(slice_wrapper_circuit)
    for _ in range(10):
        value = random.randint(0, (1 << width) - 1)
        expected_value = (value >> lo) & ((1 << hi) - 1)
        tester.poke(slice_wrapper_circuit.I, value)
        tester.eval()
        tester.expect(slice_wrapper_circuit.O, expected_value)
    with tempfile.TemporaryDirectory() as tempdir:
        tester.compile_and_run(target="verilator",
                               directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
