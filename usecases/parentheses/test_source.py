import pytest  # noqa: F401
from source import generate_parentheses


def test_generate_parentheses():
    assert generate_parentheses(3) == ["((()))", "(()())", "(())()", "()(())", "()()()"]
    assert generate_parentheses(1) == ["()"]
