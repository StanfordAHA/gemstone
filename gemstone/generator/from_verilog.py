import magma
from .from_magma import *


class FromVerilog(FromMagma):
    def __init__(self, filename, target_modules=None):
        underlying = magma.DefineFromVerilogFile(filename, target_modules=target_modules)[0]
        super().__init__(underlying)
