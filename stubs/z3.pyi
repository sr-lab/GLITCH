from typing import List

class CheckSatResult: ...

sat: CheckSatResult

class Z3PPObject: ...
class AstRef(Z3PPObject): ...
class FuncDeclRef(AstRef): ...

class ModelRef(Z3PPObject):
    def __getitem__(self, idx: AstRef) -> FuncDeclRef: ...

class ExprRef(AstRef):
    def __eq__(self, __value: object) -> BoolRef: ...  # type: ignore

class BoolRef(ExprRef): ...

class ArithRef(ExprRef):
    def __ge__(self, __value: object) -> BoolRef: ...

class IntNumRef(ArithRef): ...
class SeqRef(ExprRef): ...
class Context: ...
class Tactic: ...
class Probe: ...

class Solver:
    def __init__(
        self,
        solver: Solver | None = None,
        ctx: Context | None = None,
        logFile: str | None = None,
    ) -> None: ...
    def add(self, *args: Z3PPObject) -> None: ...
    def push(self) -> None: ...
    def pop(self) -> None: ...
    def check(self) -> CheckSatResult: ...
    def model(self) -> ModelRef: ...

def If(
    a: Probe | Z3PPObject, b: Z3PPObject, c: Z3PPObject, ctx: Context | None = None
) -> ExprRef: ...
def StringVal(s: str, ctx: Context | None = None) -> SeqRef: ...
def String(name: str, ctx: Context | None = None) -> SeqRef: ...
def Int(name: str, ctx: Context | None = None) -> ArithRef: ...
def IntVal(val: int, ctx: Context | None = None) -> IntNumRef: ...
def Bool(name: str, ctx: Context | None = None) -> BoolRef: ...
def And(*args: Z3PPObject | List[Z3PPObject]) -> BoolRef: ...
def Or(*args: Z3PPObject | List[Z3PPObject]) -> BoolRef: ...
def Not(a: Z3PPObject) -> BoolRef: ...
def Sum(*args: Z3PPObject | int | List[Z3PPObject | int]) -> ArithRef: ...
