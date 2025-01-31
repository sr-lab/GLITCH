from abc import ABC
from enum import Enum
from dataclasses import dataclass
from typing import List, Union, Dict, Any, ClassVar


@dataclass
class ElementInfo:
    line: int
    column: int
    end_line: int
    end_column: int
    code: str
    sketched: ClassVar[int] = -1

    @staticmethod
    def from_code_element(element: "CodeElement") -> "ElementInfo":
        return ElementInfo(
            element.line,
            element.column,
            element.end_line,
            element.end_column,
            element.code,
        )

    @staticmethod
    def get_sketched() -> "ElementInfo":
        info = ElementInfo(
            ElementInfo.sketched,
            ElementInfo.sketched,
            ElementInfo.sketched,
            ElementInfo.sketched,
            "",
        )
        ElementInfo.sketched -= 1
        return info


class CodeElement(ABC):
    def __init__(self, info: ElementInfo | None = None) -> None:
        if info is not None:
            self.line: int = info.line
            self.column: int = info.column
            self.end_line: int = info.end_line
            self.end_column: int = info.end_column
            self.code: str = info.code
        else:
            self.line: int = -33550336
            self.column: int = -33550336
            self.end_line: int = -33550336
            self.end_column: int = -33550336
            self.code: str = ""

    def __hash__(self) -> int:
        return (
            hash(self.line)
            * hash(self.column)
            * hash(self.end_line)
            * hash(self.end_column)
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CodeElement):
            return False
        return self.line == o.line and self.column == o.column

    def __str__(self) -> str:
        return self.__repr__()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ir_type": self.__class__.__name__,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "code": self.code,
        }


# TODO: as dict for expr and values
@dataclass
class Expr(CodeElement, ABC):
    def __init__(self, info: ElementInfo) -> None:
        super().__init__(info)

    def __hash__(self) -> int:
        return (
            hash(self.line)
            * hash(self.column)
            * hash(self.end_line)
            * hash(self.end_column)
        )

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CodeElement):
            return False
        return self.line == o.line and self.column == o.column


@dataclass
class Value(Expr, ABC):
    def __init__(self, info: ElementInfo, value: Any) -> None:
        super().__init__(info)
        self.value = value

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CodeElement):
            return False
        return (
            self.line == o.line
            and self.column == o.column
            and self.end_line == o.end_line
            and self.end_column == o.end_column
        )

    def __hash__(self) -> int:
        return (
            hash(self.line)
            * hash(self.column)
            * hash(self.end_line)
            * hash(self.end_column)
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "value": self.value,
        }


class String(Value):
    def __init__(self, value: str, info: ElementInfo) -> None:
        super().__init__(info, value)


class Integer(Value):
    def __init__(self, value: int, info: ElementInfo) -> None:
        super().__init__(info, value)


class Complex(Value):
    def __init__(self, value: complex, info: ElementInfo) -> None:
        super().__init__(info, value)


class Float(Value):
    def __init__(self, value: float, info: ElementInfo) -> None:
        super().__init__(info, value)


class Boolean(Value):
    def __init__(self, value: bool, info: ElementInfo) -> None:
        super().__init__(info, value)


class Null(Value):
    def __init__(self, info: ElementInfo | None = None) -> None:
        if info is None:
            # Let's hope there are no files with 2**32 lines lol
            info = ElementInfo(2**32, 2**32, 2**32, 2**32, "")
        super().__init__(info, None)


class Hash(Value):
    def __init__(self, value: Dict[Expr, Expr], info: ElementInfo) -> None:
        super().__init__(info, value)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "value": [
                {"key": k.as_dict(), "value": v.as_dict()}
                for k, v in self.value.items()
            ],
        }


class Array(Value):
    def __init__(self, value: List[Expr], info: ElementInfo) -> None:
        super().__init__(info, value)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "value": [v.as_dict() for v in self.value],
        }


class VariableReference(Value):
    def __init__(self, value: str, info: ElementInfo) -> None:
        super().__init__(info, value)


class FunctionCall(Expr):
    def __init__(self, name: str, args: List[Expr], info: ElementInfo) -> None:
        super().__init__(info)
        self.name: str = name
        self.args: List[Expr] = args


class MethodCall(Expr):
    def __init__(
        self, receiver: Expr, method: str, args: List[Expr], info: ElementInfo
    ) -> None:
        super().__init__(info)
        self.receiver: Expr = receiver
        self.method: str = method
        self.args: List[Expr] = args

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "receiver": self.receiver.as_dict(),
            "method": self.method,
            "args": [a.as_dict() for a in self.args],
        }


class UnaryOperation(Expr, ABC):
    def __init__(self, info: ElementInfo, expr: Expr) -> None:
        super().__init__(info)
        self.expr = expr


class Not(UnaryOperation):
    def __init__(self, info: ElementInfo, expr: Expr) -> None:
        super().__init__(info, expr)


class Minus(UnaryOperation):
    def __init__(self, info: ElementInfo, expr: Expr) -> None:
        super().__init__(info, expr)


class BinaryOperation(Expr, ABC):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info)
        self.left = left
        self.right = right

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CodeElement):
            return False
        return (
            self.line == o.line
            and self.column == o.column
            and self.end_line == o.end_line
            and self.end_column == o.end_column
        )

    def __hash__(self) -> int:
        return (
            hash(self.line)
            * hash(self.column)
            * hash(self.end_line)
            * hash(self.end_column)
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "left": self.left.as_dict(),
            "right": self.right.as_dict(),
            "type": self.__class__.__name__.lower(),
        }


class Or(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class And(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Sum(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Equal(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class NotEqual(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class LessThan(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class LessThanOrEqual(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class GreaterThan(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class GreaterThanOrEqual(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class In(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Subtract(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Multiply(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Divide(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Modulo(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Power(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class RightShift(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class LeftShift(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Access(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class BitwiseAnd(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class BitwiseOr(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class BitwiseXor(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Assign(BinaryOperation):
    def __init__(self, info: ElementInfo, left: Expr, right: Expr) -> None:
        super().__init__(info, left, right)


class Block(CodeElement):
    def __init__(self) -> None:
        CodeElement.__init__(self)
        self.statements: List[CodeElement] = []

    def add_statement(self, statement: CodeElement) -> None:
        self.statements.append(statement)

    def set_element_info(self, info: ElementInfo) -> None:
        self.line = info.line
        self.column = info.column
        self.end_line = info.end_line
        self.end_column = info.end_column
        self.code = info.code

    @staticmethod
    def __as_dict_statement(
        stat: Dict[str, Any] | List[Any] | CodeElement | str
    ) -> Any:
        if isinstance(stat, CodeElement):
            return stat.as_dict()
        elif isinstance(stat, dict):
            for key, value in stat.items():
                stat[key] = Block.__as_dict_statement(value)
            return stat
        elif isinstance(stat, list):
            return [Block.__as_dict_statement(s) for s in stat]
        else:
            return stat

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "statements": [
                Block.__as_dict_statement(s) for s in self.statements  # type: ignore
            ],
        }


class ConditionalStatement(Block, Expr):
    class ConditionType(Enum):
        IF = 1
        SWITCH = 2

    def __init__(
        self,
        condition: Expr,
        type: "ConditionalStatement.ConditionType",
        is_default: bool = False,
    ) -> None:
        Block.__init__(self)
        self.condition: Expr = condition
        self.else_statement: ConditionalStatement | None = None
        self.is_default = is_default
        self.type = type

    def __repr__(self) -> str:
        return self.code.strip().split("\n")[0]

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "condition": self.condition.as_dict(),
            "type": self.type.name,
            "is_default": self.is_default,
            "else_statement": (
                self.else_statement.as_dict() if self.else_statement else None
            ),
        }


class Comment(CodeElement):
    def __init__(self, content: str) -> None:
        super().__init__()
        self.content: str = content

    def __repr__(self) -> str:
        return self.content

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "content": self.content,
        }


class KeyValue(CodeElement):
    def __init__(self, name: str, value: Expr, info: ElementInfo) -> None:
        super().__init__(info)
        self.name: str = name
        self.value: Expr = value

    def __repr__(self) -> str:
        return self.code

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.name,
            "value": self.value.as_dict(),
        }


class Variable(KeyValue):
    def __init__(self, name: str, value: Expr, info: ElementInfo) -> None:
        super().__init__(name, value, info)


class Attribute(KeyValue):
    def __init__(self, name: str, value: Expr, info: ElementInfo) -> None:
        super().__init__(name, value, info)


class AtomicUnit(Block):
    def __init__(self, name: Expr, type: str) -> None:
        super().__init__()
        self.name: Expr = name
        self.type: str = type
        self.attributes: List[Attribute] = []

    def add_attribute(self, a: Attribute) -> None:
        self.attributes.append(a)

    def __repr__(self) -> str:
        return f"{self.name} {self.type}"

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.name.as_dict(),
            "type": self.type,
            "attributes": [a.as_dict() for a in self.attributes],
        }


class Dependency(CodeElement):
    def __init__(self, names: List[str]) -> None:
        super().__init__()
        self.names: List[str] = names

    def __repr__(self) -> str:
        return ",".join(self.names)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "names": self.names,
        }


class UnitBlockType(str, Enum):
    script = "script"
    tasks = "tasks"
    vars = "vars"
    block = "block"
    function = "function"
    definition = "definition"
    unknown = "unknown"


class UnitBlock(Block):
    def __init__(self, name: str, type: UnitBlockType) -> None:
        super().__init__()
        self.dependencies: list[Dependency] = []
        self.comments: list[Comment] = []
        self.variables: list[Variable] = []
        self.atomic_units: list[AtomicUnit] = []
        self.unit_blocks: list["UnitBlock"] = []
        self.attributes: list[Attribute] = []
        self.name: str | None = name
        self.path: str = ""
        self.type: UnitBlockType = type

    def __repr__(self) -> str:
        return self.name if self.name is not None else ""

    def add_dependency(self, d: Dependency) -> None:
        self.dependencies.append(d)

    def add_comment(self, c: Comment) -> None:
        self.comments.append(c)

    def add_variable(self, v: Variable) -> None:
        self.variables.append(v)

    def add_atomic_unit(self, a: AtomicUnit) -> None:
        self.atomic_units.append(a)

    def add_unit_block(self, u: "UnitBlock") -> None:
        self.unit_blocks.append(u)

    def add_attribute(self, a: Attribute) -> None:
        self.attributes.append(a)

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "dependencies": [d.as_dict() for d in self.dependencies],
            "comments": [c.as_dict() for c in self.comments],
            "variables": [v.as_dict() for v in self.variables],
            "atomic_units": [a.as_dict() for a in self.atomic_units],
            "unit_blocks": [u.as_dict() for u in self.unit_blocks],
            "attributes": [a.as_dict() for a in self.attributes],
            "name": self.name,
            "path": self.path,
            "type": self.type,
        }


class File:
    def __init__(self, name: str) -> None:
        self.name: str = name

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
        }


class Folder:
    def __init__(self, name: str) -> None:
        self.content: List[Union["Folder", File]] = []
        self.name: str = name

    def add_folder(self, folder: "Folder") -> None:
        self.content.append(folder)

    def add_file(self, file: File) -> None:
        self.content.append(file)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content": [c.as_dict() for c in self.content],
        }


class Module:
    def __init__(self, name: str, path: str) -> None:
        self.name: str = name
        self.path: str = path
        self.blocks: list[UnitBlock] = []
        self.modules: list[Module] = []
        self.folder: Folder = Folder(name)

    def __repr__(self) -> str:
        return self.name

    def add_block(self, u: UnitBlock) -> None:
        self.blocks.append(u)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "blocks": [b.as_dict() for b in self.blocks],
            "modules": [m.as_dict() for m in self.modules],
            "folder": self.folder.as_dict(),
        }


class Project:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.modules: list[Module] = []
        self.blocks: list[UnitBlock] = []

    def __repr__(self) -> str:
        return self.name

    def add_module(self, m: Module) -> None:
        self.modules.append(m)

    def add_block(self, u: UnitBlock) -> None:
        self.blocks.append(u)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "modules": [m.as_dict() for m in self.modules],
            "blocks": [b.as_dict() for b in self.blocks],
        }
