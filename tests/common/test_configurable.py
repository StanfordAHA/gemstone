import magma
import tempfile
import shutil
from gemstone.common.configurable import Configurable, ConfigurationType
from gemstone.common.testers import BasicTester
from gemstone.common.mux_wrapper_aoi import AOIMuxWrapper


class PassThroughConfig(Configurable):
    def __init__(self):
        super(PassThroughConfig, self).__init__(32, 32)
        self.add_config("test1", 32)
        self.add_config("test2", 32, pass_through=True)
        self.add_port("In", magma.In(magma.Bits[32]))
        self.wire(self.registers["test2"].ports.I, self.ports.In)

        self.add_ports(
            config=magma.In(ConfigurationType(32, 32)))

    def name(self):
        return "TestPassThrough"


def test_pass_through_config():
    config = PassThroughConfig()
    config.finalize()
    circuit = config.circuit()

    tester = BasicTester(circuit, circuit.clk, circuit.reset)
    tester.poke(circuit.In, 42)
    tester.eval()
    tester.config_read(1)
    tester.expect(circuit.read_config_data, 42)

    with tempfile.TemporaryDirectory() as tempdir:
        files = AOIMuxWrapper.get_sv_files()
        for file in files:
            shutil.copy(file, tempdir)
        tester.compile_and_run(target="verilator",
                               directory=tempdir,
                               magma_output="coreir-verilog",
                               flags=["-Wno-fatal"])


if __name__ == "__main__":
    test_pass_through_config()
