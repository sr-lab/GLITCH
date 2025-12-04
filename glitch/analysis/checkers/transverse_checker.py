from abc import ABC
from glitch.analysis.rules import Checker

from glitch.repr.inter import (
    Array,
    BinaryOperation,
    ConditionalStatement,
    FunctionCall,
    Hash,
    MethodCall,
    UnaryOperation,
    BlockExpr,
    Undef,
    KeyValue,
    Block,
    AtomicUnit,
    UnitBlock,
)


class TransverseChecker(Checker, ABC):
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
        return self.check_block(expr) or self.check(expr.condition) or (
            expr.else_statement is not None and self.check(expr.else_statement)
        )

    def check_blockexpr(self, element: BlockExpr) -> bool:
        for stmt in element.statements:
            if self.check(stmt):
                return True
        return False

    def check_undef(self, expr: Undef) -> bool:
        return False

    def check_keyvalue(self, element: KeyValue) -> bool:
        return self.check(element.value)

    def check_block(self, element: Block) -> bool:
        if isinstance(element, UnitBlock):
            for stmt in element.variables:
                if self.check(stmt):
                    return True
            for stmt in element.atomic_units:
                if self.check(stmt):
                    return True
            for stmt in element.unit_blocks:
                if self.check(stmt):
                    return True

        for stmt in element.statements:
            if self.check(stmt):
                return True
        return False

    def check_atomicunit(self, element: AtomicUnit) -> bool:
        if self.check(element.name):
            return True
        for attr in element.attributes:
            if self.check(attr):
                return True
        return self.check_block(element)