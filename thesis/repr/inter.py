from abc import ABC

class CodeElement(ABC):
    line: int
    column: int

    def __init__(self) -> None:
        self.line, self.column = -1, -1

class Comment(CodeElement):
    content: str

    def __init__(self, content: str) -> None:
        super().__init__()
        self.content = content

    def __repr__(self) -> str:
        return self.content

    def print(self, tab) -> str:
        return (tab * "\t") + self.content + ' (on line ' + str(self.line) + ')'

class Variable(CodeElement):
    name: str
    value: str

    def __init__(self, name: str, value: str) -> None:
        super().__init__()
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        value = self.value.split('\n')[0]
        return f"{self.name}:{value}"

    def print(self, tab) -> str:
        return (tab * "\t") + self.name + "->" + self.value + \
            " (on line " + str(self.line) + ")"

class Attribute(CodeElement):
    name: str
    value: str

    def __init__(self, name: str, value: str) -> None:
        super().__init__()
        self.name = name
        self.value = value

    def __repr__(self) -> str:
        value = self.value.split('\n')[0]
        return f"{self.name}:{value}"

    def print(self, tab) -> str:
        return (tab * "\t") + self.name + "->" + self.value.replace('\n', '') + \
            " (on line " + str(self.line) + ")"

class AtomicUnit(CodeElement):
    name: str
    type: str
    attributes: list[Attribute]

    def __init__(self, name: str, type: str) -> None:
        super().__init__()
        self.name = name
        self.type = type
        self.attributes = []

    def add_attribute(self, a: Attribute) -> None:
        self.attributes.append(a)

    def __repr__(self) -> str:
        return f"{self.name} {self.type}"

    def print(self, tab) -> str:
        res = ((tab * "\t") + self.type + ' ' + self.name + " (on line " 
                + str(self.line) + ")\n")

        for attribute in self.attributes:
            res += attribute.print(tab + 1) + "\n"
        res = res[:-1]

        return res

class Dependency(CodeElement):
    name: str

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def print(self, tab) -> str:
        return (tab * "\t") + self.name + " (on line " + str(self.line) + ")"

class UnitBlock:
    name: str
    dependencies: list[Dependency]
    comments: list[Comment]
    variables: list[Variable]
    atomic_units: list[AtomicUnit]
    path: str

    def __init__(self, name: str) -> None:
        self.dependencies = []
        self.comments = []
        self.variables = []
        self.atomic_units = []
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def add_dependency(self, d: Dependency) -> None:
        self.dependencies.append(d)

    def add_comment(self, c: Comment) -> None:
        self.comments.append(c)

    def add_variable(self, v: Variable) -> None:
        self.variables.append(v)

    def add_atomic_unit(self, a: AtomicUnit) -> None:
        self.atomic_units.append(a)

    def print(self, tab) -> str:
        res = (tab * "\t") + self.name + "\n"
        
        res += (tab * "\t") + "\tdependencies:\n"
        for dependency in self.dependencies:
            res += dependency.print(tab + 2) + "\n"

        res += (tab * "\t") + "\tcomments:\n"
        for comment in self.comments:
            res += comment.print(tab + 2) + "\n"

        res += (tab * "\t") + "\tvariables:\n"
        for variable in self.variables:
            res += variable.print(tab + 2) + "\n"

        res += (tab * "\t") + "\tatomic units:\n"
        for atomic in self.atomic_units:
            res += atomic.print(tab + 2) + "\n"

        return res

class File:
    name: str

    def __init__(self, name) -> None:
        self.name = name

    def print(self, tab) -> str:
        return (tab * "\t") + self.name

class Folder:
    name: str
    content: list

    def __init__(self, name) -> None:
        self.content = []
        self.name = name

    def add_folder(self, folder: 'Folder') -> None:
        self.content.append(folder)

    def add_file(self, file: File) -> None:
        self.content.append(file)

    def print(self, tab) -> str:
        res = (tab * "\t") + self.name + "\n"

        for c in self.content:
            res += c.print(tab + 1) + "\n"
        res = res[:-1]

        return res

class Module:
    name: str
    blocks: list[UnitBlock]
    folder: Folder

    def __init__(self, name) -> None:
        self.name = name
        self.blocks = []
        self.folder = Folder(name)

    def __repr__(self) -> str:
        return self.name

    def add_block(self, u: UnitBlock) -> None:
        self.blocks.append(u)

    def print(self, tab) -> str:
        res = (tab * "\t") + self.name + "\n"

        res += (tab * "\t") + "\tblocks:\n"
        for block in self.blocks:
            res += block.print(tab + 2)

        res += (tab * "\t") + "\tfile structure:\n"
        res += self.folder.print(tab + 2)

        return res

class Project:
    modules: list[Module]
    blocks: list[UnitBlock]
    name: str

    def __init__(self, name) -> None:
        self.name = name
        self.modules = []
        self.blocks = []

    def __repr__(self) -> str:
        return self.name

    def add_module(self, m: Module):
        self.modules.append(m)
    
    def add_block(self, u: UnitBlock):
        self.blocks.append(u)

    def print(self, tab) -> str:
        res = self.name + "\n"

        res += (tab * "\t") + "\tmodules:\n"
        for module in self.modules:
            res += module.print(tab + 2)

        res += (tab * "\t") + "\tblocks:\n"
        for block in self.blocks:
            res += block.print(tab + 2)

        return res