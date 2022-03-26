import re
from thesis.repr.inter import *
from abc import ABC, abstractmethod
from urllib.parse import urlparse

class Error():
    __ERRORS = {
        'sec_https': "We should prefer the usage of https instead of http.",
        'sec_susp_comm': "Suspicious word in comment",
        'sec_def_admin': "Admin by default.",
        'sec_empty_pass': "Empty password.",
        'sec_weak_crypt': "Weak Crypto Algorithm.",
        'sec_hard_secr': "Hard-coded secret.",
        'sec_hard_pass': "Hard-coded password.",
        "sec_hard_user": "Hard-coded user.",
        'sec_invalid_bind': "Invalid IP address binding.",
        'sec_no_int_check': "No integrity check."
    }

    code: str
    el: CodeElement
    path: str
    repr: str

    def __init__(self, code: str, el: CodeElement, path: str, repr: str) -> None:
        self.code: str = code
        self.el: CodeElement = el
        self.path = path
        self.repr = repr

    def to_csv(self) -> str:
        return f"{self.path},{self.el.line},{self.code},{self.repr.strip()}"

    def __repr__(self) -> str:
        with open(self.path) as f:
            return \
                f"{self.path}\nIssue on line {self.el.line}: {Error.__ERRORS[self.code]}\n" + \
                    f"{f.readlines()[self.el.line - 1].strip()}\n" 

    def __hash__(self):
        return hash((self.code, self.path, self.el.line))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.code == other.code and self.path == other.path and\
                    self.el.line == other.el.line

class RuleVisitor(ABC):
    def check(self, code) -> list[Error]:
        if isinstance(code, Project):
            return self.check_project(code)
        elif isinstance(code, Module):
            return self.check_module(code)
        elif isinstance(code, UnitBlock):
            return self.check_unitblock(code)

    @abstractmethod
    def check_project(self, p: Project) -> list[Error]:
        pass

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
    __URL_REGEX = r'^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'
    __WRONG_WORDS = ['bug', 'debug', 'todo', 'to-do', 'to_do', 'fix',
            'issue', 'problem', 'solve', 'hack', 'ticket', 'later', 'incorrect', 'fixme']
    __PASSWORDS = ['pass', 'pwd', 'password', 'passwd', 'passno', 'pass-no', 'pass_no' ]
    __USERS = ['root', 'user', 'uname', 'username', 'user-name', 'user_name',
            'owner-name', 'owner_name', 'owner', 'admin', 'login', 'userid', 'loginid']
    __SECRETS = ["uuid", "crypt", "secret", "certificate", "token", "ssh_key", 
            "rsa", 'auth_token',  'authetication_token','auth-token', 'authentication-token',
            'md5', 'ssl_content', 'ca_content', 'ssl-content', 'ca-content', 'ssh_key_content', 
            'ssh-key-content', 'ssh_key_public', 'ssh-key-public', 'ssh_key_private', 
            'ssh-key-private', 'ssh_key_public_content', 'ssh_key_private_content', 
            'ssh-key-public-content', 'ssh-key-private-content']
    __MISC = ['key', 'id', 'cert']
    __ROLES = ["role"]
    __DOWNLOAD = ['iso', 'tar', 'tar.gz', 'tar.bzip2', 'zip', 
            'rar', 'gzip', 'gzip2', 'deb', 'rpm', 'sh', 'run', 'bin']
    __SSH_DIR = ['source', 'destination', 'path', 'directory', 
        'src', 'dest', 'file']

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

        return errors

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = []
        for a in au.attributes:
            errors += self.check_attribute(a, file)

        # Check integrity check
        for a in au.attributes:
            value = a.value.strip().lower()
            for item in SecurityVisitor.__DOWNLOAD:
                if re.match(r'(http|https|www)[_\-a-zA-Z0-9:\/.]*{text}$'
                        .format(text = item), value):
                    integrity_check = False
                    for other in au.attributes:
                        name = other.name.strip().lower()
                        if 'checksum' in name or 'gpg' in name:
                            integrity_check = True
                            break

                    if not integrity_check:
                        errors.append(Error('sec_no_int_check', a, file, repr(a)))

                    break

        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

    # FIXME attribute and variables need to have superclass
    def __check_keyvalue(self, c: CodeElement, name: str, 
            value: str, has_variable: bool, file: str):
        errors = []
        name = name.split('.')[-1].strip().lower()
        value = value.strip().lower()

        try:
            for v in value.split(' '):
                if v.startswith(('"', "'")) and v.endswith(('"', "'")):
                    v = v[1:-1]

                if (re.match(SecurityVisitor.__URL_REGEX, v) and
                    ('http' in v or 'www' in v) and 'https' not in v) or \
                        (urlparse(v).scheme == 'http'):
                    errors.append(Error('sec_https', c, file, repr(c)))
        except:
            # The url is not valid
            pass

        if re.match(r'^0.0.0.0', value):
            errors.append(Error('sec_invalid_bind', c, file, repr(c)))
        if value.startswith('sha1') or value.startswith('md5'):
            errors.append(Error('sec_weak_crypt', c, file, repr(c)))
        if (name in SecurityVisitor.__ROLES or name in SecurityVisitor.__USERS) \
                and 'admin' in value:
            errors.append(Error('sec_def_admin', c, file, repr(c)))
        if (('gpgcheck' in name or 'get_checksum' in name) \
                and (value == 'no' or value == 'false')):
            errors.append(Error('sec_no_int_check', c, file, repr(c)))

        for item in (SecurityVisitor.__PASSWORDS + 
                SecurityVisitor.__SECRETS + SecurityVisitor.__USERS):
            if (re.match(r'[_A-Za-z0-9\/\.\[\]-]*{text}\b'.format(text=item), name)):
                if (len(value) > 0 and not has_variable):
                    errors.append(Error('sec_hard_secr', c, file, repr(c)))

                    if (item in SecurityVisitor.__PASSWORDS):
                        errors.append(Error('sec_hard_pass', c, file, repr(c)))
                    elif (item in SecurityVisitor.__USERS):
                        errors.append(Error('sec_hard_user', c, file, repr(c)))
                    break
                elif (item in SecurityVisitor.__PASSWORDS and len(value) == 0):
                    errors.append(Error('sec_empty_pass', c, file, repr(c)))
                    break

        for item in SecurityVisitor.__SSH_DIR:
            if item.lower() in name:
                if len(value) > 0 and '/id_rsa' in value:
                    errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__MISC:
            if (re.match(r'[_A-Za-z0-9-]*{text}[-_]*$'.format(text=item), name) 
                    and len(value) > 0 and not has_variable):
                errors.append(Error('sec_hard_secr', c, file, repr(c)))

        return errors

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return self.__check_keyvalue(a, a.name, a.value, a.has_variable, file)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return self.__check_keyvalue(v, v.name, v.value, v.has_variable, file) #FIXME

    def check_comment(self, c: Comment, file: str) -> list[Error]:
        errors = []
        lines = c.content.split('\n')
        stop = False
        for word in SecurityVisitor.__WRONG_WORDS:
            for line in lines:
                if word in line.lower():
                    errors.append(Error('sec_susp_comm', c, file, line))
                    stop = True
            if stop:
                break
        return errors