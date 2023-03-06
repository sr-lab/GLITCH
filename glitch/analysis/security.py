import os
import re
import json
import configparser
from urllib.parse import urlparse
from glitch.analysis.rules import Error, RuleVisitor

from glitch.repr.inter import *
from glitch.tech import Tech


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
        SecurityVisitor.__PROFILE = json.loads(config['security']['profile'])
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
        SecurityVisitor.__FILE_COMMANDS = json.loads(config['security']['file_commands'])
        SecurityVisitor.__DOWNLOAD_COMMANDS = json.loads(config['security']['download_commands'])
        self._load_data_files()

    @staticmethod
    def _load_data_files():
        def load_file(file: str) -> list[str]:
            folder_path = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(folder_path, file)) as f:
                content = f.readlines()
                return [c.strip() for c in content]

        SecurityVisitor.__OFFICIAL_IMAGES = load_file("official_docker_images")
        SecurityVisitor.__OBSOLETE_COMMANDS = load_file("obsolete_commands")

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file)

        for item in SecurityVisitor.__FILE_COMMANDS:
            if item not in au.type:
                continue
            for a in au.attributes:
                if a.name == "mode" and re.search(r'(?:^0?777$)|(?:(?:^|(?:ugo)|o|a)\+[rwx]{3})', a.value):
                    errors.append(Error('sec_full_permission_filesystem', au, file, repr(a)))

        if au.type in SecurityVisitor.__OBSOLETE_COMMANDS:
            errors.append(Error('sec_obsolete_command', au, file, repr(au)))

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
            if re.match(r'[_A-Za-z0-9$\/\.\[\]-]*{text}\b'.format(text=item), name) and not has_variable and \
                    name not in SecurityVisitor.__PROFILE:
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

    def check_unitblock(self, u: UnitBlock) -> list[Error]:
        errors = super().check_unitblock(u)

        missing_integrity_checks = {}
        for au in u.atomic_units:
            result = self.check_integrity_check(au, u.path)
            if result:
                missing_integrity_checks[result[0]] = result[1]
                continue

            if file := SecurityVisitor.check_has_checksum(au):
                if file in missing_integrity_checks:
                    del missing_integrity_checks[file]

        errors += missing_integrity_checks.values()

        if self.tech == Tech.docker and 'Dockerfile' not in u.name:
            image = u.name.split(":")
            if image[0] not in SecurityVisitor.__OFFICIAL_IMAGES:
                errors.append(Error('sec_non_official_image', u, u.path, repr(u)))

        return errors

    @staticmethod
    def check_integrity_check(au: AtomicUnit, path: str) -> tuple[str, Error] | None:
        for item in SecurityVisitor.__DOWNLOAD:
            if not re.search(r'(http|https|www)[^ ,]*\.{text}'.format(text=item), au.name):
                continue
            if SecurityVisitor.__has_integrity_check(au.attributes):
                return None
            return os.path.basename(au.name), Error('sec_no_int_check', au, path, repr(au))

        for a in au.attributes:
            value = a.value.strip().lower() if isinstance(a.value, str) else repr(a.value).strip().lower()

            for item in SecurityVisitor.__DOWNLOAD:
                if not re.search(r'(http|https|www)[^ ,]*\.{text}'.format(text=item), value):
                    continue
                if SecurityVisitor.__has_integrity_check(au.attributes):
                    return None
                return os.path.basename(a.value), Error('sec_no_int_check', au, path, repr(a))
        return None

    @staticmethod
    def check_has_checksum(au: AtomicUnit) -> str | None:
        if au.type not in SecurityVisitor.__CHECKSUM:
            return None
        if any(d in au.name for d in SecurityVisitor.__DOWNLOAD):
            return os.path.basename(au.name)

        for a in au.attributes:
            value = a.value.strip().lower() if isinstance(a.value, str) else repr(a.value).strip().lower()
            if any(d in value for d in SecurityVisitor.__DOWNLOAD):
                return os.path.basename(au.name)
        return None

    @staticmethod
    def __has_integrity_check(attributes: list[Attribute]) -> bool:
        for attr in attributes:
            name = attr.name.strip().lower()
            if any([check in name for check in SecurityVisitor.__CHECKSUM]):
                return True
