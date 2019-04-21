from generator.from_verilog import FromVerilog
from .PDConfig import PDCGRAConfig
from generator.generator import Generator
import os
from typing import List
from power_domain.PDConfig import PDCGRAConfig
from canal.circuit import InterconnectConfigurable
from gemstone.common.configurable import Configurable, ConfigurationType
import magma


class PowerDomain(InterconnectConfigurable):
    def __init__(self,config_addr_width: int,
                 config_data_width: int):
        super().__init__(config_addr_width, config_data_width)
        self.config = PDCGRAConfig() 
        # ps
        self.add_config(self.config.ps_config_name, 1)
        self.add_ports(
                 config=magma.In(ConfigurationType(config_addr_width,
                                                   config_data_width)),
        )
        self._setup_config()

    def name(self):
        return "PowerDomain"


def add_pd_tile(tile, config: PDCGRAConfig):
    """This is a pass to add power domain to a particular tile. You need
    to add this pass before calling finalize()"""
    # add a new feature to the tile
    pd_feature = PowerDomain(config, tile.config_addr_width,
                             tile.config_data_width)
    tile.add_feature(pd_feature)


class PowerDomain2(InterconnectConfigurable):
    def __init__(self,config_addr_width: int,
                 config_data_width: int):
        self.config = PDCGRAConfig()
        self.add_ps_config_register(PDCGRAConfig)

    # Add a config register - PS
    def add_ps_config_register(self, PDCGRAConfig):
        self.Params = PDCGRAConfig()
        self.reg_name = self.Params.ps_config_name
        self.idx = self.Params.cfg_reg_addr_ps
        self.add_config_register()


    # Add a config register
    def add_config_register(self):
        # Add corresponding config register.
        self.add_config(self.reg_name, 1)
        self.registers[self.reg_name].set_addr(self.idx)
        self.registers[self.reg_name].set_addr_width(8)
        self.registers[self.reg_name].set_data_width(32)
        self.wire(
            self.ports.config.config_addr[24:32],
            self.registers[self.reg_name].ports.config_addr)
        self.wire(
            self.ports.config.config_data,
            self.registers[self.reg_name].ports.config_data)
        self.wire(
            self.ports.config.write[0],
            self.registers[self.reg_name].ports.config_en)
        self.wire(
            self.ports.reset,
            self.registers[self.reg_name].ports.reset)

    def name(self):
        return "PowerDomain"
