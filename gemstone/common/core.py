from abc import abstractmethod
from .configurable import Configurable, ConfigurationType
from ..generator.from_magma import FromMagma
from ..generator.generator import Generator
import magma
from typing import List, Union
import mantle


class PnRTag:
    def __init__(self, tag_name: str, priority_major: int,
                 priority_minor: int):
        assert len(tag_name) == 1, "Tag can only be one character"
        self.tag_name = tag_name
        self.priority_major = priority_major
        self.priority_minor = priority_minor

    def __eq__(self, other):
        if not isinstance(other, PnRTag):
            return False
        return self.tag_name == other.tag_name \
            and self.priority_major == self.priority_major \
            and self.priority_minor == self.priority_minor

    def __hash__(self):
        return hash(self.tag_name)


class Core(Generator):
    DEFAULT_PRIORITY = 20
    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass

    def features(self) -> List[Union["Core", "CoreFeature"]]:
        return [self]

    def pnr_info(self) -> Union[PnRTag, List[PnRTag]]:
        tag = self.name()[0]
        priority_major = self.DEFAULT_PRIORITY
        priority_minor = self.DEFAULT_PRIORITY
        # this can be a list as well
        return PnRTag(tag, priority_major, priority_minor)

    def configure_model(self, instr):
        pass

    def eval_model(self, **kargs):
        return {}


class ConfigurableCore(Core, Configurable):
    def __init__(self, config_addr_width, config_data_width):
        Core.__init__(self)
        Configurable.__init__(self, config_addr_width, config_data_width)

    @abstractmethod
    def get_config_bitstream(self, instr):
        pass

    @abstractmethod
    def instruction_type(self):
        pass


class CoreFeature(Generator):
    def __init__(self,
                 parent_core: "Core",
                 index: int):
        super().__init__()

        self.__index = index
        self.__parent = parent_core

    def name(self):
        return f"{self.__parent.name()}_FEATURE_{self.__index}"

    def parent(self):
        return self.__parent

    def index(self):
        return self.__index

    def configure_model(self, instr):
        pass

    def eval_model(self, **kargs):
        return {}
