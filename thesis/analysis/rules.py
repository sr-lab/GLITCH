import re
from thesis.repr.inter import *
from abc import ABC, abstractmethod

class Error():
    __ERRORS = {
        'sec_https': "We should prefer the usage of https instead of http.",
        'sec_susp_comm': "Suspicious word in comment",
        'sec_def_admin': "Admin by default.",
        'sec_empty_pass': "Empty password.",
        'sec_weak_crypt': "Weak Crypto Algorithm.",
        'sec_hard_secr': "Hard-coded secret.",
        'sec_invalid_bind': "Invalid IP address binding."
    }

    code: str
    el: CodeElement
    path: str

    def __init__(self, code: str, el: CodeElement, path: str) -> None:
        self.code: str = code
        self.el: CodeElement = el
        self.path = path

    def __repr__(self) -> str:
        with open(self.path) as f:
            return self.path + "\nIssue on line " + \
                str(self.el.line) + ": " + Error.__ERRORS[self.code] + \
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
        return []

    def __check_keyvalue(self, c: CodeElement, name: str, value: str, file: str):
        errors = []
        name = name.strip().lower()
        value = value.strip().lower()

        if (re.match(SecurityVisitor.URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
            errors.append(Error('sec_https', c, file))
        elif re.match(r'^0.0.0.0', value):
            errors.append(Error('sec_invalid_bind', c, file))
        elif value.startswith('sha1') or value.startswith('md5'):
            errors.append(Error('sec_weak_crypt', c, file))
        elif (name in SecurityVisitor.PASSWORDS or name in SecurityVisitor.USERS) \
                and 'admin' in value:
            errors.append(Error('sec_def_admin', c, file))
        elif name in SecurityVisitor.PASSWORDS and len(value) == 0:
            errors.append(Error('sec_empty_pass', c, file))
        elif ((name in SecurityVisitor.PASSWORDS or name in SecurityVisitor.SECRETS)
                and len(value) > 0):
            errors.append(Error('sec_hard_secr', c, file))

        return errors

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return self.__check_keyvalue(a, a.name, a.value, file)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return self.__check_keyvalue(v, v.name, v.value, file)

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors = []
        for word in SecurityVisitor.WRONG_WORDS:
            if word in c.content.lower():
                errors.append(Error('sec_susp_comm', c, file))
                break
        return errors