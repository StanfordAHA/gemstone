import abc
import dataclasses
import typing

import magma as m

from gemstone.common.configurable import Configurable


@dataclasses.dataclass(frozen=True, eq=True)
class PnRTag:
    tag_name: str
    priority_major: int
    priority_minor: int

    def __post_init__(self):
        if len(self.tag_name) != 1:
            raise ValueError("Tag can only be one character")

    def __hash__(self):
        return hash(self.tag_name)


class Core(m.CircuitBuilder):
    _DEFAULT_PRIORITY = 20

    @abc.abstractmethod
    def inputs(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def outputs(self):
        raise NotImplementedError()

    def features(self) -> List[typing.Union["Core", "CoreFeature"]]:
        return [self]

    def pnr_info(self) -> typing.Union[PnRTag, typing.List[PnRTag]]:
        tag = self.name[0]
        priority_major = Core._DEFAULT_PRIORITY
        priority_minor = Core._DEFAULT_PRIORITY
        return PnRTag(tag, priority_major, priority_minor) # can also be a list

    @abc.abstractmethod
    def configure_model(self, instr):
        raise NotImplementedError()

    def eval_model(self, **kargs):
        return {}


class ConfigurableCore(Core, Configurable):
    def __init__(self, name, config_addr_width, config_data_width):
        Core.__init__(self, name)
        Configurable.__init__(self, name, config_addr_width, config_data_width)
        # If set to true, allows skipping reg. compression on this feature
        # during the bitstream generation stage.
        self.skip_compression = False

    @abstractmethod
    def get_config_bitstream(self, instr):
        raise NotImplementedError()

    @abstractmethod
    def instruction_type(self):
        raise NotImplementedError()


class CoreFeature(m.Generator2):
    def __init__(self, parent: Core, index: int):
        self._index = index
        self._parent = parent
        self.name = f"{parent.name}_FEATURE_{index}"
        # If set to true, allows skipping reg. compression on this feature
        # during the bitstream generation stage.
        self.skip_compression = False

    @property
    def parent(self):
        return self._parent

    @property
    def index(self):
        return self._index

    @abc.abstractmethod
    def configure_model(self, instr):
        raise NotImplementedError()

    def eval_model(self, **kwargs):
        return {}
