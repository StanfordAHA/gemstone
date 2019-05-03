import magma
from .from_magma import *


class FromVerilog(FromMagma):
    def __init__(self, filename, target_modules=None, type_map={}):
        underlying = magma.DefineFromVerilogFile(filename, target_modules,
                                                 type_map, shallow=True)[0]
        super().__init__(underlying)
