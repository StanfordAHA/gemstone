from abc import ABC, abstractmethod
from ordered_set import OrderedSet
import warnings
import magma
from ..common.collections import DotDict
from .port_reference import *


__DEBUG_MODE = True


def set_debug_mode(value: bool = True):
    global __DEBUG_MODE
    assert value in {True, False}
    __DEBUG_MODE = value


def get_debug_mode():
    return __DEBUG_MODE


class Generator(ABC):
    __cache = {}

    def __init__(self, name=None):
        """
        name: Set this parameter to override default name for instance
        """
        self.ports = DotDict()
        self.wires = []
        self.instance_name = name
        # use class name as a hash init
        self.__hash = hash(self.__class__.__name__)

    @abstractmethod
    def name(self):
        pass

    def add_port(self, name, T):
        if get_debug_mode() and name in self.ports:
            raise ValueError(f"{name} is already a port")
        port_ref = PortReference(self, name, T)
        self.ports[name] = port_ref
        self.__hash ^= hash(port_ref)

    def remove_port(self, port_name: str):
        # first remove it from self.ports
        assert port_name in self.ports
        port_ref = self.ports[port_name]
        # due to the property of xor, the hash will go back to the original one
        self.__hash ^= hash(port_ref)
        self.ports.pop(port_name)
        # then remove any wires connected with it. due to port cloning
        # the only thing won't change is the port name
        wires_to_remove = set()
        for conn1, conn2 in self.wires:
            if conn1._name == port_name and conn1.owner() == self:
                wires_to_remove.add((conn1, conn2))
            elif conn2._name == port_name and conn2.owner() == self:
                wires_to_remove.add((conn1, conn2))
        for conn1, conn2 in wires_to_remove:
            self.remove_wire(conn1, conn2)

    def add_ports(self, **kwargs):
        for name, T in kwargs.items():
            self.add_port(name, T)

    def __hash_wire(self, connection):
        self.__hash ^= (~(hash(connection[0]) ^ hash(connection[1]))) << 16

    def set_hash(self, new_hash_value):
        self.__hash = new_hash_value

    def __hash__(self):
        return self.__hash

    def wire(self, port0, port1):
        if not get_debug_mode():
            connection = self.__sort_ports(port0, port1)
            self.wires.append(connection)
            self.__hash_wire(connection)
        else:
            assert isinstance(port0, PortReferenceBase)
            assert isinstance(port1, PortReferenceBase)
            connection = self.__sort_ports(port0, port1)
            if connection not in self.wires:
                self.wires.append(connection)
                self.__hash_wire(connection)
            else:
                warnings.warn(f"skipping duplicate connection: "
                              f"{port0.qualified_name()}, "
                              f"{port1.qualified_name()}")

    def remove_wire(self, port0, port1):
        assert isinstance(port0, PortReferenceBase)
        assert isinstance(port1, PortReferenceBase)
        connection = self.__sort_ports(port0, port1)
        if connection in self.wires:
            self.wires.remove(connection)
            self.__hash_wire(connection)

    def decl(self):
        io = []
        for name, port in self.ports.items():
            io += [name, port.base_type()]
        return io

    def children(self):
        children = OrderedSet()
        for ports in self.wires:
            for port in ports:
                if port.owner() == self:
                    continue
                children.add(port.owner())
        return children

    def circuit(self):
        if self.__hash in Generator.__cache:
            return Generator.__cache[self.__hash]

        children = self.children()
        circuits = {}
        for child in children:
            circuits[child] = child.circuit()

        class _Circ(magma.Circuit):
            name = self.name()
            IO = self.decl()

            @classmethod
            def definition(io):
                instances = {}
                for child in children:
                    kwargs = {}
                    if child.instance_name:
                        kwargs["name"] = child.instance_name
                    instances[child] = circuits[child](**kwargs)
                instances[self] = io
                for port0, port1 in self.wires:
                    inst0 = instances[port0.owner()]
                    inst1 = instances[port1.owner()]
                    wire0 = port0.get_port(inst0)
                    wire1 = port1.get_port(inst1)
                    magma.wire(wire0, wire1)

        Generator.__cache[self.__hash] = _Circ

        return _Circ

    def __sort_ports(self, port0, port1):
        if id(port0) < id(port1):
            return (port0, port1)
        else:
            return (port1, port0)
