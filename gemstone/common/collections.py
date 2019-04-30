from collections import UserDict


# TODO(rsetaluri): Instead of this custom class we should rely on:
# https://github.com/drgrib/dotmap.
class DotDict(UserDict):
    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, key):
        return self.data[key]


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self))
