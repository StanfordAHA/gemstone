import tempfile
import glob
import shutil
import os
import pytest
from random import randint, choice
import tempfile
from hwtypes import BitVector
import fault
import fault.random
from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper, AOIMuxType


@pytest.mark.parametrize('height,width', [(randint(2, 10), randint(1, 32))
                                          for _ in range(5)])
def test_aoi_mux_wrapper(height, width):
    """
    Test that the mux wrapper circuit works as expected. Specifically, we
    initialize a mux with random height and width, and check that the output is
    as expected for select in range [0, height).

    Note that we do not check the behavior with sel >= height, because this is
    undefined behavior.
    """
    mux = AOIMuxWrapper(height, width, AOIMuxType.Regular)
    assert mux.height == height
    assert mux.width == width
    assert mux.name() == \
        f"MuxWrapperAOI_{height}_{width}_{AOIMuxType.Regular.name}"

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
        for aoi_mux in glob.glob("tests/common/rtl/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])


# Keyi: the height cannot be 2^n
@pytest.mark.parametrize('height,width', [(choice([3, 5, 6, 7, 9]),
                                           randint(1, 32))
                                          for _ in range(5)])
def test_aoi_const_mux_wrapper(height, width):
    """
    Test that the mux wrapper circuit works as expected. Specifically, we
    initialize a mux with random height and width, and check that the output is
    as expected for select in range [0, height).

    Note that we do not check the behavior with sel > height, because this is
    undefined behavior.
    """
    mux = AOIMuxWrapper(height, width, AOIMuxType.Const)
    assert mux.width == width
    assert mux.name() == \
        f"MuxWrapperAOI_{height}_{width}_{AOIMuxType.Const.name}"

    mux_circuit = mux.circuit()
    tester = fault.Tester(mux_circuit)
    inputs = [fault.random.random_bv(width) for _ in range(height + 1)]
    for i, input_ in enumerate(inputs[:height]):
        tester.poke(mux_circuit.I[i], input_)
    for i in range(height + 1):
        tester.poke(mux_circuit.S, BitVector[mux.sel_bits](i))
        tester.eval()
        if i < height:
            tester.expect(mux_circuit.O, inputs[i])
        else:
            tester.expect(mux_circuit.O, 0)

    with tempfile.TemporaryDirectory() as tempdir:
        for aoi_mux in glob.glob("tests/common/rtl/*.sv"):
            shutil.copy(aoi_mux, tempdir)
        tester.compile_and_run(directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])
