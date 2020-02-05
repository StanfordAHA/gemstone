import magma
from .from_magma import *


class FromVerilog(FromMagma):
    def __init__(self, filename, target_modules=None, type_map={}):
        underlying = magma.DefineFromVerilogFile(filename,
                                                 target_modules=target_modules,
                                                 type_map=type_map)[0]
        super().__init__(underlying)
