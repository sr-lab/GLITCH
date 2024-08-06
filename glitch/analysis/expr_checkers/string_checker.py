from glitch.analysis.expr_checkers.transverse_checker import TransverseChecker
from typing import Callable

from glitch.repr.inter import String


class StringChecker(TransverseChecker):
    def __init__(self, str_check: Callable[[str], bool]) -> None:
        self.str_check = str_check

    def check_string(self, expr: String) -> bool:
        return self.str_check(expr.value)