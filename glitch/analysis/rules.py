from glitch.tech import Tech
from glitch.repr.inter import *
from abc import ABC, abstractmethod

class Error():
    ERRORS = {
        'security': {
            'sec_https': "Use of HTTP without TLS - The developers should always favor the usage of HTTPS. (CWE-319)",
            'sec_susp_comm': "Suspicious comment - Comments with keywords such as TODO HACK or FIXME may reveal problems possibly exploitable. (CWE-546)",
            'sec_def_admin': "Admin by default - Developers should always try to give the least privileges possible. Admin privileges may indicate a security problem. (CWE-250)",
            'sec_empty_pass': "Empty password - An empty password is indicative of a weak password which may lead to a security breach. (CWE-258)",
            'sec_weak_crypt': "Weak Crypto Algorithm - Weak crypto algorithms should be avoided since they are susceptible to security issues. (CWE-326 | CWE-327)",
            'sec_hard_secr': "Hard-coded secret - Developers should not reveal sensitive information in the source code. (CWE-798)",
            'sec_hard_pass': "Hard-coded password - Developers should not reveal sensitive information in the source code. (CWE-259)",
            'sec_hard_user': "Hard-coded user - Developers should not reveal sensitive information in the source code. (CWE-798)",
            'sec_invalid_bind': "Invalid IP address binding - Binding to the address 0.0.0.0 allows connections from every possible network which might be a security issues. (CWE-284)",
            'sec_no_int_check': "No integrity check - The content of files downloaded from the internet should be checked. (CWE-353)",
            'sec_no_default_switch': "Missing default case statement - Not handling every possible input combination might allow an attacker to trigger an error for an unhandled value. (CWE-478)"
        },
        'design': {
            'design_imperative_abstraction': "Imperative abstraction - The presence of imperative statements defies the purpose of IaC declarative languages.",
            'design_unnecessary_abstraction': "Unnecessary abstraction - Blocks should contain declarations or statements, otherwise they are unnecessary.",
            'implementation_long_statement': "Long statement - Long statements may decrease the readability and maintainability of the code.",
            'implementation_improper_alignment': "Improper alignment - The developers should try to follow the languages' style guides. These style guides define how the attributes in an atomic unit should be aligned. The developers should also avoid the use of tabs.",
            'implementation_too_many_variables': "Too many variables - The existence of too many variables in a single IaC script may reveal that the script is being used for too many purposes.",
            'design_duplicate_block': "Duplicate block - Duplicates blocks may reveal a missing abstraction.",
            'implementation_unguarded_variable': "Unguarded variable - Variables should be guarded for readability and maintainability of the code.",
            'design_avoid_comments': "Avoid comments - Comments may lead to bad code or be used as a way to justify bad code.",
            'design_long_resource': "Long Resource - Long resources may decrease the readability and maintainability of the code.",
            'design_multifaceted_abstraction': "Multifaceted Abstraction - Each block should only specify the properties of a single piece of software.",
            'design_misplaced_attribute': "Misplaced attribute - The developers should try to follow the languages' style guides. These style guides define the expected attribute order."
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
        repr = self.repr.split('\n')[0].strip()
        return f"{self.path},{self.line},{self.code},{repr}"

    def __repr__(self) -> str:
        with open(self.path) as f:
            line = f.readlines()[self.line - 1].strip() if self.line != -1 else self.repr.split('\n')[0]
            return \
                f"{self.path}\nIssue on line {self.line}: {Error.ALL_ERRORS[self.code]}\n" + \
                    f"{line}\n" 

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
