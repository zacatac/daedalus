import random
import pytest  # noqa: F401
from .failrandom import add


def test_add():
    assert add(2, 3) == random.randint(1, 100)
    assert add(-1, 1) == random.randint(1, 100)
