import magma as m

from gemstone.common.configurable import ConfigRegister
from gemstone.generator.generator import Generator


# class Wrapper(Generator):
#     def __init__(self):


reg = ConfigRegister(32)
reg.set_addr_width(32)
reg.set_data_width(32)
reg.set_addr(0)
ckt = reg.circuit()

m.compile(ckt.name, ckt, output="coreir-verilog")
