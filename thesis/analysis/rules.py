import re
from thesis.repr.inter import *
from abc import ABC, abstractmethod

class Error():
    msg: str
    el: CodeElement
    path: str

    def __init__(self, msg: str, el: CodeElement, path: str) -> None:
        self.msg: str = msg
        self.el: CodeElement = el
        self.path = path

    def __repr__(self) -> str:
        with open(self.path) as f:
            return self.path + "\nIssue on line " + \
                str(self.el.line) + ": " + self.msg + \
                    "\n" + f.readlines()[self.el.line - 1].strip() + "\n"

class RuleVisitor(ABC):
    @abstractmethod
    def check_module(self, m: Module) -> list[Error]:
        pass

    @abstractmethod
    def check_unitblock(self, u: UnitBlock) -> list[Error]:
        pass

    @abstractmethod
    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        pass

    @abstractmethod
    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        pass

    @abstractmethod
    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        pass

    @abstractmethod
    def check_variable(self, v: Variable, file: str) -> list[Error]:
        pass

    @abstractmethod
    def check_comment(self, c: Comment, file: str) -> list[Error]:
        pass

# FIXME we may want to look to the improvements made to these detections
class SecurityVisitor(RuleVisitor):
    URL_REGEX = r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)' \
        '?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'
    WRONG_WORDS = ['bug', 'debug', 'todo', 'to-do', 'to_do', 'fix',
        'issue', 'problem', 'solve', 'hack', 'ticket', 'later', 'incorrect', 'fixme']
    PASSWORDS = ["pass", "password", "pwd"]
    USERS = ["user", "usr"]
    SECRETS = ["uuid", "key", "crypt", "secret", "certificate", "id"
        "cert", "token", "ssh_key", "rsa", "ssl"]

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

        return errors

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = []
        for a in au.attributes:
            errors += self.check_attribute(a, file)

        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        pass

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        errors = []
        name = a.name.strip().lower()
        value = a.value.strip().lower()

        if (re.match(SecurityVisitor.URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
            errors.append(Error("We should prefer the usage of https instead of http.", a, file))
        elif re.match(r'^0.0.0.0', value):
            errors.append(Error("Invalid IP address binding.", a, file))
        elif value.startswith('sha1') or value.startswith('md5'):
            errors.append(Error("Weak Crypto Algorithm.", a, file))
        elif (name in SecurityVisitor.PASSWORDS or name in SecurityVisitor.USERS) \
                and 'admin' in value:
            errors.append(Error("Admin by default.", a, file))
        elif name in SecurityVisitor.PASSWORDS and len(value) == 0:
            errors.append(Error("Empty password.", a, file))
        elif ((name in SecurityVisitor.PASSWORDS or name in SecurityVisitor.SECRETS)
                and len(value) > 0):
            errors.append(Error("Hard-coded secret.", a, file))

        return errors

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        errors = []
        name = v.name.strip().lower()
        value = v.value.strip().lower()

        if (re.match(SecurityVisitor.URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
            errors.append(Error("We should prefer the usage of https instead of http.", v, file))
        elif re.match(r'^0.0.0.0', value):
            errors.append(Error("Invalid IP address binding.", v, file))
        elif value.startswith('sha1') or value.startswith('md5'):
            errors.append(Error("Weak Crypto Algorithm.", v, file))
        elif (name in SecurityVisitor.PASSWORDS or name in SecurityVisitor.USERS) \
                and 'admin' in value:
            errors.append(Error("Admin by default.", v, file))
        elif name in SecurityVisitor.PASSWORDS and len(value) == 0:
            errors.append(Error("Empty password.", v, file))
        elif ((name in SecurityVisitor.PASSWORDS or name in SecurityVisitor.SECRETS)
                and len(value) > 0):
            errors.append(Error("Hard-coded secret.", v, file))

        return errors

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors = []
        for word in SecurityVisitor.WRONG_WORDS:
            if word in c.content.lower():
                errors.append(Error("Suspicious word in comment", c, file))
                break
        return errors