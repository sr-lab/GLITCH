from abc import ABC
from enum import Enum
from typing import List, Union, Dict, Any


class CodeElement(ABC):
    def __init__(self) -> None:
        self.line: int = -1
        self.column: int = -1
        self.code: str = ""

    def __hash__(self) -> int:
        return hash(self.line) * hash(self.column)

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
            "code": self.code,
        }


class Block(CodeElement):
    def __init__(self) -> None:
        super().__init__()
        self.statements: List[CodeElement] = []

    def add_statement(self, statement: "ConditionalStatement") -> None:
        self.statements.append(statement)

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


class ConditionalStatement(Block):
    class ConditionType(Enum):
        IF = 1
        SWITCH = 2

    def __init__(
        self,
        condition: str,
        type: "ConditionalStatement.ConditionType",
        is_default: bool = False,
    ) -> None:
        super().__init__()
        self.condition: str = condition
        self.else_statement: ConditionalStatement | None = None
        self.is_default = is_default
        self.type = type

    def __repr__(self) -> str:
        return self.code.strip().split("\n")[0]

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "condition": self.condition,
            "type": self.type.name,
            "is_default": self.is_default,
            "else_statement": self.else_statement.as_dict()
            if self.else_statement
            else None,
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
    def __init__(self, name: str, value: str | None, has_variable: bool) -> None:
        self.name: str = name
        self.value: str | None = value
        self.has_variable: bool = has_variable
        self.keyvalues: List[KeyValue] = []

    def __repr__(self) -> str:
        value = repr(self.value).split("\n")[0]
        if value == "None":
            return f"{self.name}:{value}:{self.keyvalues}"
        else:
            return f"{self.name}:{value}"

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.name,
            # FIXME: In Puppet code, the value can be a ConditionalStatement or a dict.
            # The types need to be fixed.
            "value": self.value if not isinstance(self.value, CodeElement) else self.value.as_dict(),  # type: ignore
            "has_variable": self.has_variable,
            "keyvalues": [kv.as_dict() for kv in self.keyvalues],
        }


class Variable(KeyValue):
    def __init__(self, name: str, value: str | None, has_variable: bool) -> None:
        super().__init__(name, value, has_variable)


class Attribute(KeyValue):
    def __init__(self, name: str, value: str | None, has_variable: bool) -> None:
        super().__init__(name, value, has_variable)


class AtomicUnit(Block):
    def __init__(self, name: str | None, type: str) -> None:
        super().__init__()
        self.name: str | None = name
        self.type: str = type
        self.attributes: list[Attribute] = []

    def add_attribute(self, a: Attribute) -> None:
        self.attributes.append(a)

    def __repr__(self) -> str:
        return f"{self.name} {self.type}"

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.name,
            "type": self.type,
            "attributes": [a.as_dict() for a in self.attributes],
        }


class Dependency(CodeElement):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name

    def __repr__(self) -> str:
        return self.name

    def as_dict(self) -> Dict[str, Any]:
        return {
            **super().as_dict(),
            "name": self.name,
        }


class UnitBlockType(str, Enum):
    script = "script"
    tasks = "tasks"
    vars = "vars"
    block = "block"
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
