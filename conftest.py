import pytest
from magma import clear_cachedFunctions
import magma.backend.coreir_
from gemstone.generator import clear_generator_cache


@pytest.fixture(autouse=True)
def magma_test():
    clear_cachedFunctions()
    magma.backend.coreir_.__reset_context()
    clear_generator_cache()
