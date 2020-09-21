import magma as m
import tempfile
from gemstone.common.dummy_core_magma import DummyCore
from gemstone.common.util import check_files_equal


def test_instance_name_tile():
    core = DummyCore()
    circuit = core.circuit()
    print(str(circuit.instances))
    assert str(circuit.instances) == '[config_reg_0 = ConfigRegister_32_8_32_0(name="config_reg_0"), dummy_1_inst0 = dummy_1(), config_reg_1 = ConfigRegister_32_8_32_1(name="config_reg_1"), dummy_2_inst0 = dummy_2(), MuxWrapper_2_32_inst0 = MuxWrapper_2_32()]'  # noqa
    with tempfile.TemporaryDirectory() as tempdir:
        m.compile(f"{tempdir}/core", circuit, output="coreir-verilog")
        assert check_files_equal(f"{tempdir}/core.v",
                                 "tests/generator/gold/core_instance_name.v")
