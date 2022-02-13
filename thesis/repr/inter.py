from attr import attributes

class Comment:
    content: str

    def __init__(self, content: str) -> None:
        self.content = content

    def print(self, tab) -> str:
        return (tab * "\t") + self.content

class Variable:
    name: str
    value: str

    def __init__(self, name: str, value: str) -> None:
        self.name = name
        self.value = value

    def print(self, tab) -> str:
        return (tab * "\t") + self.name + "->" + self.value

class Attribute:
    name: str
    value: str

    def __init__(self, name: str, value: str) -> None:
        self.name = name
        self.value = value

    def print(self, tab) -> str:
        return (tab * "\t") + self.name + "->" + self.value

class AtomicUnit:
    name: str
    attributes: list[Attribute] = []

    def __init__(self, name: str) -> None:
        self.name = name

    def add_attribute(self, a: Attribute) -> None:
        self.attributes.append(a)

    def print(self, tab) -> str:
        res = (tab * "\t") + self.name + "\n"

        for attribute in self.attributes:
            res += attribute.print(tab + 1) + "\n"

        return res

class UnitBlock:
    name: str
    dependencies: list['UnitBlock'] = []
    comments: list[Comment] = []
    variables: list[Variable] = []
    atomic_units: list[AtomicUnit] = []

    def __init__(self, name: str) -> None:
        self.name = name

    def add_dependency(self, u: 'UnitBlock') -> None:
        self.dependencies.append(u)

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
            res += (tab * "\t") + "\t\t" + dependency.name

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

class Module:
    name: str
    blocks: list[UnitBlock] = []

    def __init__(self, name) -> None:
        self.name = name

    def add_block(self, u: UnitBlock) -> None:
        self.blocks.append(u)

    def __repr__(self) -> str:
        res = self.name + "\n"

        for block in self.blocks:
            res += block.print(1)

        return res