from abc import ABC
from glitch.analysis.rules import ExprChecker

from glitch.repr.inter import (
    Array,
    BinaryOperation,
    ConditionalStatement,
    FunctionCall,
    Hash,
    MethodCall,
    UnaryOperation,
)


class TransverseChecker(ExprChecker, ABC):
    def check_array(self, expr: Array) -> bool:
        for v in expr.value:
            if self.check(v):
                return True
        return False

    def check_hash(self, expr: Hash) -> bool:
        for k, v in expr.value.items():
            if self.check(k) or self.check(v):
                return True
        return False

    def check_function_call(self, expr: FunctionCall) -> bool:
        for arg in expr.args:
            if self.check(arg):
                return True
        return False

    def check_method_call(self, expr: MethodCall) -> bool:
        if self.check(expr.receiver):
            return True
        for arg in expr.args:
            if self.check(arg):
                return True
        return False

    def check_unary_operation(self, expr: UnaryOperation) -> bool:
        return self.check(expr.expr)

    def check_binary_operation(self, expr: BinaryOperation) -> bool:
        return self.check(expr.left) or self.check(expr.right)

    def check_conditional_statement(self, expr: ConditionalStatement) -> bool:
        return self.check(expr.condition) or (
            expr.else_statement is not None and self.check(expr.else_statement)
        )
