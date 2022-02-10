from abc import ABC, abstractmethod, ABCMeta
from ordered_set import OrderedSet
import warnings
from ..common.collections import DotDict
from .port_reference import *

import magma as m


__DEBUG_MODE = True
_generator_cache = {}


def clear_generator_cache():
    _generator_cache.clear()


def set_debug_mode(value: bool = True):
    global __DEBUG_MODE
    assert value in {True, False}
    __DEBUG_MODE = value


def get_debug_mode():
    return __DEBUG_MODE


def _hash_wire(old_hash, connection):
    return old_hash ^ (~(hash(connection[0]) ^ hash(connection[1]))) << 16


import uuid


class GeneratorMeta(ABCMeta):
    def __new__(metacls, name, bases, dct):
        if bases and Generator in bases:
            if "circuit" in dct:
                print ("found circuit", dct["circuit"])
        return super().__new__(metacls, name, bases, dct)


class Generator(metaclass=GeneratorMeta):
    def __init__(self, name=None):
        """
        name: Set this parameter to override default name for instance
        """
        self._builder = m.CircuitBuilder(name=name)

    @property
    def context(self):
        return self._builder.context

    @abstractmethod
    def name(self):
        raise NotImplementedError()

    def add_port(self, name, T):
        self._builder._add_port(name, T)

    def remove_port(self, port_name: str):
        raise NotImplementedError()

    def add_ports(self, **kwargs):
        for name, T in kwargs.items():
            self.add_port(name, T)

    def wire(self, port0, port1):
        m.wire(port0, port1)

    def remove_wire(self, port0, port1):
        m.unwire(port0, port1)

    def decl(self):
        raise NotImplementedError()

    def children(self):
        raise NotImplementedError()

    def circuit(self):
        self.finalize()
        self._builder._name = self.name()
        self._builder.finalize()
        return self._builder._defn
