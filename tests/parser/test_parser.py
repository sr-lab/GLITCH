import unittest
from typing import Any, Type
from glitch.repr.inter import Expr, Value, BinaryOperation


class TestParser(unittest.TestCase):
    def _check_value(
        self,
        obtained: Expr,
        type: Type[Expr],
        value: Any,
        line: int,
        column: int,
        end_line: int,
        end_column: int,
    ):
        assert isinstance(obtained, type)
        if isinstance(obtained, Value):
            assert obtained.value == value
        assert obtained.line == line
        assert obtained.column == column
        assert obtained.end_line == end_line
        assert obtained.end_column == end_column

    def _check_binary_operation(
        self,
        obtained: Expr,
        type: Type[BinaryOperation],
        left: Expr,
        right: Expr,
        line: int,
        column: int,
        end_line: int,
        end_column: int,
    ):
        assert isinstance(obtained, BinaryOperation)
        assert isinstance(obtained, type)
        assert obtained.left == left
        assert obtained.right == right
        assert obtained.line == line
        assert obtained.column == column
        assert obtained.end_line == end_line
        assert obtained.end_column == end_column
