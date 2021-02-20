import abc
import functools


class MultipleFinalizationError(Exception):
    def __init__(self):
        super().__init__("Can not call finalize() multiple times")


class PostFinalizationError(Exception):
    def __init__(self):
        super().__init__("Can not call method after finalization")


def disallow_post_finalization(fn):

    @functools.wraps(fn)
    def _wrapped(this, *args, **kwargs):
        if this.finalized:
            raise PostFinalizationError()
        return fn(*args, **kwargs)

    return _wrapped


class Finalizable(abc.ABC):
    def __init__(self):
        self._finalized = False

    @property
    def finalized(self):
        return self._finalized

    @abc.abstractmethod
    def _finalize(self):
        raise NotImplementedError()

    def finalize(self, *args, **kwargs):
        if self._finalized:
            raise MultipleFinalizationError()
        ret = self._finalize(*args, **kwargs)
        self._finalized = True
        return ret
