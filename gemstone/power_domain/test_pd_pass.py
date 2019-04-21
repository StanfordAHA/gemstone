import magma
from top.top_magma import CGRA
from generator.from_verilog import FromVerilog
from top.PDConfig import PDCGRAConfig

width = 2
height = 2
cgra = CGRA(width=2, height=2)
Params = PDCGRAConfig()


def add_power_domains(cgra, PDCGRAConfig):
    for x in range(width):
        for y in range(height):
            tile = cgra.interconnect.tile_circuits[(x, y)]
            if (Params.en_power_domains == 1 and x >= Params.pd_bndry_loc):
                tile = cgra.interconnect.tile_circuits[(x, y)]
                tile.column_labels = "SD"
                # Add PS Config Register
                tile.add_ps_config_register(PDCGRAConfig)
            else:
                tile.column_labels = "AON"
    return cgra

def test_top_pd_magma():
    cgra_pd = add_power_domains(cgra, PDCGRAConfig)
    cgra_pd_circ = cgra_pd.circuit()
    magma.compile("cgra_pd", cgra_pd_circ, output="coreir-verilog")
