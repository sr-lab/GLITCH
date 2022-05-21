from glitch.tech import Tech
from glitch.repr.inter import *
from abc import ABC, abstractmethod

class Error():
    ERRORS = {
        'security': {
            'sec_https': "Use of HTTP without TLS",
            'sec_susp_comm': "Suspicious comment",
            'sec_def_admin': "Admin by default",
            'sec_empty_pass': "Empty password",
            'sec_weak_crypt': "Weak Crypto Algorithm",
            'sec_hard_secr': "Hard-coded secret",
            'sec_hard_pass': "Hard-coded password",
            'sec_hard_user': "Hard-coded user",
            'sec_invalid_bind': "Invalid IP address binding",
            'sec_no_int_check': "No integrity check",
            'sec_no_default_switch': "Missing default case statement"
        },
        'design': {
            'design_imperative_abstraction': "Imperative abstraction",
            'design_unnecessary_abstraction': "Unnecessary abstraction",
            'implementation_long_statement': "Long statement",
            'implementation_improper_alignment': "Improper alignment",
            'implementation_too_many_variables': "Too many variables",
            'design_duplicate_block': "Duplicate block",
            'implementation_unguarded_variable': "Unguarded variable",
            'design_avoid_comments': "Avoid comments",
            'design_multifaceted_abstraction': "Multifaceted Abstraction",
            'design_misplaced_attribute': "Misplaced attribute"
        }
    }

    ALL_ERRORS = {}

    @staticmethod
    def agglomerate_errors():
        for error_list in Error.ERRORS.values():
            for k,v in error_list.items():
                Error.ALL_ERRORS[k] = v

    def __init__(self, code: str, el, path: str, repr: str) -> None:
        self.code: str = code
        self.el = el
        self.path = path
        self.repr = repr

        if isinstance(self.el, CodeElement):
            self.line = self.el.line
        else:
            self.line = -1

    def to_csv(self) -> str:
        return f"{self.path},{self.line},{self.code},{self.repr.strip()}"

    def __repr__(self) -> str:
        with open(self.path) as f:
            return \
                f"{self.path}\nIssue on line {self.line}: {Error.ALL_ERRORS[self.code]}\n" + \
                    f"{f.readlines()[self.line - 1].strip()}\n" 

    def __hash__(self):
        return hash((self.code, self.path, self.line))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.code == other.code and self.path == other.path and\
                    self.line == other.line

Error.agglomerate_errors()

class RuleVisitor(ABC):
    def __init__(self, tech: Tech) -> None:
        super().__init__()
        self.tech = tech

    def check(self, code) -> list[Error]:
        if isinstance(code, Project):
            return self.check_project(code)
        elif isinstance(code, Module):
            return self.check_module(code)
        elif isinstance(code, UnitBlock):
            return self.check_unitblock(code)

    def check_element(self, c, file: str) -> list[Error]:
        if isinstance(c, AtomicUnit):
            return self.check_atomicunit(c, file)
        elif isinstance(c, Dependency):
            return self.check_dependency(c, file)
        elif isinstance(c, Attribute):
            return self.check_attribute(c, file)
        elif isinstance(c, Variable):
            return self.check_variable(c, file)
        elif isinstance(c, ConditionStatement):
            return self.check_condition(c, file)
        elif isinstance(c, Comment):
            return self.check_comment(c, file)
        elif isinstance(c, dict):
            errors = []
            for k, v in c.items():
                errors += self.check_element(k, file) + self.check_element(v, file)
            return errors
        else:
            return []

    @abstractmethod
    def get_name() -> str:
        pass

    @abstractmethod
    def config(self, config_path: str):
        pass

    def check_project(self, p: Project) -> list[Error]:
        errors = []
        for m in p.modules:
            errors += self.check_module(m)

        for u in p.blocks:
            errors += self.check_unitblock(u)

        return errors

    def check_module(self, m: Module) -> list[Error]:
        errors = []
        for u in m.blocks:
            errors += self.check_unitblock(u)

        return errors

    def check_unitblock(self, u: UnitBlock) -> list[Error]:
        errors = []
        for au in u.atomic_units:
            errors += self.check_atomicunit(au, u.path)
        for c in u.comments:
            errors += self.check_comment(c, u.path)
        for v in u.variables:
            errors += self.check_variable(v, u.path)
        for ub in u.unit_blocks:
            errors += self.check_unitblock(ub)
        for a in u.attributes:
            errors += self.check_attribute(a, u.path)
        for s in u.statements:
            errors += self.check_element(s, u.path)

        return errors

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = []
        for a in au.attributes:
            errors += self.check_attribute(a, file)

        for s in au.statements:
            errors += self.check_element(s, file)

        return errors

    @abstractmethod
    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        pass

    @abstractmethod
    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        pass

    @abstractmethod
    def check_variable(self, v: Variable, file: str) -> list[Error]:
        pass

    def check_condition(self, c: ConditionStatement, file: str) -> list[Error]:
        errors = []

        for s in c.statements:
            errors += self.check_element(s, file)

        return errors

    @abstractmethod
    def check_comment(self, c: Comment, file: str) -> list[Error]:
        pass
Error.agglomerate_errors()
class SmellChecker(ABC):
    @abstractmethod
    def check(self, element, file: str) -> list[Error]:
        pass