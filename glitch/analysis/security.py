import os
import re
import json
import configparser
from urllib.parse import urlparse

import glitch
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker

from glitch.repr.inter import *
from glitch.tech import Tech


class SecurityVisitor(RuleVisitor):
    __URL_REGEX = r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"

    class NonOfficialImageSmell(SmellChecker):
        def check(self, element, file: str) -> list[Error]:
            return []

    class DockerNonOfficialImageSmell(SmellChecker):
        def __init__(self, official_images: list[str]):
            super().__init__()
            self.off_images = official_images

        def check(self, element, file: str) -> list[Error]:
            if not isinstance(element, UnitBlock) or "Dockerfile" in element.name:
                return []
            image = element.name.split(":")
            if image[0] not in self.off_images:
                return [Error('sec_non_official_image', element, file, repr(element))]
            return []

    def __init__(self, tech: Tech) -> None:
        super().__init__(tech)

        if tech == Tech.docker:
            self.non_off_img = SecurityVisitor.DockerNonOfficialImageSmell(
                self._load_data_file('official_docker_images'))
        else:
            self.non_off_img = SecurityVisitor.NonOfficialImageSmell()

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
        SecurityVisitor.__SHELL_RESOURCES = json.loads(config['security']['shell_resources'])
        SecurityVisitor.__OBSOLETE_COMMANDS = self._load_data_file("obsolete_commands")

    @staticmethod
    def _load_data_file(file: str) -> list[str]:
        folder_path = os.path.dirname(os.path.realpath(glitch.__file__))
        with open(os.path.join(folder_path, "files", file)) as f:
            content = f.readlines()
            return [c.strip() for c in content]

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors = super().check_atomicunit(au, file)

        for item in SecurityVisitor.__FILE_COMMANDS:
            if item not in au.type:
                continue
            for a in au.attributes:
                if a.name == "mode" and re.search(r'(?:^0?777$)|(?:(?:^|(?:ugo)|o|a)\+[rwx]{3})', a.value):
                    errors.append(Error('sec_full_permission_filesystem', a, file, repr(a)))

        if au.type in SecurityVisitor.__OBSOLETE_COMMANDS:
            errors.append(Error('sec_obsolete_command', au, file, repr(au)))
        elif any(au.type.endswith(res) for res in SecurityVisitor.__SHELL_RESOURCES):
            for attr in au.attributes:
                if isinstance(attr.value, str) and attr.value.split(" ")[0] in SecurityVisitor.__OBSOLETE_COMMANDS:
                    errors.append(Error('sec_obsolete_command', attr, file, repr(attr)))

        if self.__is_http_url(au.name):
            errors.append(Error('sec_https', au, file, repr(au)))
        if self.__is_weak_crypt(au.type, au.name):
            errors.append(Error('sec_weak_crypt', au, file, repr(au)))

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

        if self.__is_http_url(value):
            errors.append(Error('sec_https', c, file, repr(c)))

        if re.match(r'^0.0.0.0', value):
            errors.append(Error('sec_invalid_bind', c, file, repr(c)))

        if self.__is_weak_crypt(value, name):
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

        """
        Missing integrity check changed to unit block since in Docker the integrity check is not an attribute of the
        atomic unit but can be done on another atomic unit inside the same unit block.
        """
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
        errors += self.non_off_img.check(u, u.path)

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

    @staticmethod
    def __is_http_url(value: str) -> bool:
        if (re.match(SecurityVisitor.__URL_REGEX, value) and
                ('http' in value or 'www' in value) and 'https' not in value):
            return True
        parsed_url = urlparse(value)
        return parsed_url.scheme == 'http' and \
                parsed_url.hostname not in SecurityVisitor.__URL_WHITELIST

    @staticmethod
    def __is_weak_crypt(value: str, name: str) -> bool:
        if any(crypt in value for crypt in SecurityVisitor.__CRYPT):
            whitelist = any(word in name or word in value for word in SecurityVisitor.__CRYPT_WHITELIST)
            return not whitelist
        return False
