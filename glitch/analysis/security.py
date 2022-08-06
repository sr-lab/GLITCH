import re
import json
import configparser
from urllib.parse import urlparse
from glitch.analysis.rules import Error, RuleVisitor

from glitch.repr.inter import *


class SecurityVisitor(RuleVisitor):
    __URL_REGEX = r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"

    @staticmethod
    def get_name() -> str:
        return "security"

    def config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path)
        SecurityVisitor.__WRONG_WORDS = json.loads(config['security']['suspicious_words'])
        SecurityVisitor.__PASSWORDS = json.loads(config['security']['passwords'])
        SecurityVisitor.__USERS = json.loads(config['security']['users'])
        SecurityVisitor.__SECRETS = json.loads(config['security']['secrets'])
        SecurityVisitor.__MISC_SECRETS = json.loads(config['security']['misc_secrets'])
        SecurityVisitor.__ROLES = json.loads(config['security']['roles'])
        SecurityVisitor.__DOWNLOAD = json.loads(config['security']['download_extensions'])
        SecurityVisitor.__SSH_DIR = json.loads(config['security']['ssh_dirs'])
        SecurityVisitor.__ADMIN = json.loads(config['security']['admin'])
        SecurityVisitor.__CHECKSUM = json.loads(config['security']['checksum'])
        SecurityVisitor.__CRYPT = json.loads(config['security']['weak_crypt'])
        SecurityVisitor.__CRYPT_WHITELIST = json.loads(config['security']['weak_crypt_whitelist'])
        SecurityVisitor.__URL_WHITELIST = json.loads(config['security']['url_http_white_list'])

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file)
        # Check integrity check
        for a in au.attributes:
            if isinstance(a.value, str): value = a.value.strip().lower()
            else: value = repr(a.value).strip().lower()

            for item in SecurityVisitor.__DOWNLOAD:
                if re.search(r'(http|https|www)[^ ,]*\.{text}'.format(text = item), value):
                    integrity_check = False
                    for other in au.attributes:
                        name = other.name.strip().lower()
                        if any([check in name for check in SecurityVisitor.__CHECKSUM]):
                            integrity_check = True
                            break

                    if not integrity_check:
                        errors.append(Error('sec_no_int_check', au, file, repr(a)))

                    break

        return errors

    def check_dependency(self, d: Dependency, file: str) -> list[Error]:
        return []

    # FIXME attribute and variables need to have superclass
    def __check_keyvalue(self, c: CodeElement, name: str, 
            value: str, has_variable: bool, file: str):
        errors = []
        name = name.split('.')[-1].strip().lower()
        if (isinstance(value, str)):
            value = value.strip().lower()
        else:
            errors += self.check_element(value, file)
            value = repr(value)

        try:
            if (re.match(SecurityVisitor.__URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
                errors.append(Error('sec_https', c, file, repr(c)))

            parsed_url = urlparse(value)
            if parsed_url.scheme == 'http' and \
                    parsed_url.hostname not in SecurityVisitor.__URL_WHITELIST:
                errors.append(Error('sec_https', c, file, repr(c)))
        except:
            # The url is not valid
            pass

        if re.match(r'^0.0.0.0', value):
            errors.append(Error('sec_invalid_bind', c, file, repr(c)))

        for crypt in SecurityVisitor.__CRYPT:
            if crypt in value:
                whitelist = False
                for word in SecurityVisitor.__CRYPT_WHITELIST:
                    if word in name or word in value:
                        whitelist = True
                        break

                if not whitelist:
                    errors.append(Error('sec_weak_crypt', c, file, repr(c)))   

        for check in SecurityVisitor.__CHECKSUM:     
            if (check in name and (value == 'no' or value == 'false')):
                errors.append(Error('sec_no_int_check', c, file, repr(c)))
                break

        for item in (SecurityVisitor.__ROLES + SecurityVisitor.__USERS):
            if (re.match(r'[_A-Za-z0-9$\/\.\[\]-]*{text}\b'.format(text=item), name)):
                if (len(value) > 0 and not has_variable):
                    for admin in SecurityVisitor.__ADMIN:
                        if admin in value:
                            errors.append(Error('sec_def_admin', c, file, repr(c)))
                            break

        for item in (SecurityVisitor.__PASSWORDS + 
                SecurityVisitor.__SECRETS + SecurityVisitor.__USERS):
            if (re.match(r'[_A-Za-z0-9$\/\.\[\]-]*{text}\b'.format(text=item), name) and not has_variable):
                errors.append(Error('sec_hard_secr', c, file, repr(c)))

                if (item in SecurityVisitor.__PASSWORDS):
                    errors.append(Error('sec_hard_pass', c, file, repr(c)))
                elif (item in SecurityVisitor.__USERS):
                    errors.append(Error('sec_hard_user', c, file, repr(c)))

                if (item in SecurityVisitor.__PASSWORDS and len(value) == 0):
                    errors.append(Error('sec_empty_pass', c, file, repr(c)))
                    
                break

        for item in SecurityVisitor.__SSH_DIR:
            if item.lower() in name:
                if len(value) > 0 and '/id_rsa' in value:
                    errors.append(Error('sec_hard_secr', c, file, repr(c)))

        for item in SecurityVisitor.__MISC_SECRETS:
            if (re.match(r'([_A-Za-z0-9$-]*[-_]{text}([-_].*)?$)|(^{text}([-_].*)?$)'.format(text=item), name) 
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

    def check_condition(self, c: ConditionStatement, file: str) -> list[Error]:
        errors = super().check_condition(c, file)

        condition = c
        has_default = False

        while condition != None:
            if condition.is_default:
                has_default = True
                break
            condition = condition.else_statement

        if not has_default:
            return errors + [Error('sec_no_default_switch', c, file, repr(c))]

        return errors
