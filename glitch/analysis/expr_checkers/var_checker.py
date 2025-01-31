from glitch.analysis.expr_checkers.transverse_checker import TransverseChecker
from glitch.repr.inter import VariableReference


class VariableChecker(TransverseChecker):
    def check_var_reference(self, expr: VariableReference) -> bool:
        return True
