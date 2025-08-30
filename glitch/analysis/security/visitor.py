import os
import re
import json
import glitch
import configparser
from urllib.parse import urlparse, parse_qs
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker
from nltk.tokenize import WordPunctTokenizer  # type: ignore
from typing import Tuple, List, Optional

from glitch.tech import Tech
from glitch.repr.inter import *
from glitch.analysis.expr_checkers.string_checker import StringChecker
from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.security.smell_checker import SecuritySmellChecker


class SecurityVisitor(RuleVisitor):
    __URL_REGEX = r"^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([_\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$"

    class NonOfficialImageSmell(SmellChecker):
        def check(self, element: CodeElement, file: str) -> List[Error]:
            return []

    class DockerNonOfficialImageSmell(SmellChecker):
        def check(self, element: CodeElement, file: str) -> List[Error]:
            if (
                not isinstance(element, UnitBlock)
                or element.name is None
                or "Dockerfile" in element.name
            ):
                return []
            image = element.name.split(":")
            all_official_imgs = SecurityVisitor.DOCKER_OFFICIAL_IMAGES + SecurityVisitor.DEPRECATED_OFFICIAL_DOCKER_IMAGES
            if image[0] not in all_official_imgs:
                return [Error("sec_non_official_image", element, file, repr(element))]
            return []

    def __init__(self, tech: Tech) -> None:
        super().__init__(tech)

        self.checkers: List[SecuritySmellChecker] = []
        for child in SecuritySmellChecker.__subclasses__():
            self.checkers.append(child())

        if tech == Tech.terraform:
            for child in TerraformSmellChecker.__subclasses__():
                self.checkers.append(child())

        if tech == Tech.docker:
            self.non_off_img = SecurityVisitor.DockerNonOfficialImageSmell()
        else:
            self.non_off_img = SecurityVisitor.NonOfficialImageSmell()

    @staticmethod
    def get_name() -> str:
        return "security"

    def config(self, config_path: str) -> None:
        config = configparser.ConfigParser()
        config.read(config_path)
        SecurityVisitor.WRONG_WORDS = json.loads(config["security"]["suspicious_words"])
        SecurityVisitor.PASSWORDS = json.loads(config["security"]["passwords"])
        SecurityVisitor.USERS = json.loads(config["security"]["users"])
        SecurityVisitor.PROFILE = json.loads(config["security"]["profile"])
        SecurityVisitor.SECRETS = json.loads(config["security"]["secrets"])
        SecurityVisitor.MISC_SECRETS = json.loads(config["security"]["misc_secrets"])
        SecurityVisitor.ROLES = json.loads(config["security"]["roles"])
        SecurityVisitor.DOWNLOAD = json.loads(config["security"]["download_extensions"])
        SecurityVisitor.SSH_DIR = json.loads(config["security"]["ssh_dirs"])
        SecurityVisitor.ADMIN = json.loads(config["security"]["admin"])
        SecurityVisitor.CHECKSUM = json.loads(config["security"]["checksum"])
        SecurityVisitor.CRYPT = json.loads(config["security"]["weak_crypt"])
        SecurityVisitor.CRYPT_WHITELIST = json.loads(
            config["security"]["weak_crypt_whitelist"]
        )
        SecurityVisitor.URL_WHITELIST = json.loads(
            config["security"]["url_http_white_list"]
        )
        SecurityVisitor.SECRETS_WHITELIST = json.loads(
            config["security"]["secrets_white_list"]
        )
        SecurityVisitor.SENSITIVE_DATA = json.loads(
            config["security"]["sensitive_data"]
        )
        SecurityVisitor.SECRET_ASSIGN = json.loads(
            config["security"]["secret_value_assign"]
        )
        SecurityVisitor.GITHUB_ACTIONS = json.loads(
            config["security"]["github_actions_resources"]
        )

        if self.tech == Tech.terraform:
            SecurityVisitor.INTEGRITY_POLICY = json.loads(
                config["security"]["integrity_policy"]
            )
            SecurityVisitor.HTTPS_CONFIGS = json.loads(
                config["security"]["ensure_https"]
            )
            SecurityVisitor.SSL_TLS_POLICY = json.loads(
                config["security"]["ssl_tls_policy"]
            )
            SecurityVisitor.DNSSEC_CONFIGS = json.loads(
                config["security"]["ensure_dnssec"]
            )
            SecurityVisitor.PUBLIC_IP_CONFIGS = json.loads(
                config["security"]["use_public_ip"]
            )
            SecurityVisitor.POLICY_KEYWORDS = json.loads(
                config["security"]["policy_keywords"]
            )
            SecurityVisitor.ACCESS_CONTROL_CONFIGS = json.loads(
                config["security"]["insecure_access_control"]
            )
            SecurityVisitor.AUTHENTICATION = json.loads(
                config["security"]["authentication"]
            )
            SecurityVisitor.POLICY_ACCESS_CONTROL = json.loads(
                config["security"]["policy_insecure_access_control"]
            )
            SecurityVisitor.POLICY_AUTHENTICATION = json.loads(
                config["security"]["policy_authentication"]
            )
            SecurityVisitor.MISSING_ENCRYPTION = json.loads(
                config["security"]["missing_encryption"]
            )
            SecurityVisitor.CONFIGURATION_KEYWORDS = json.loads(
                config["security"]["configuration_keywords"]
            )
            SecurityVisitor.ENCRYPT_CONFIG = json.loads(
                config["security"]["encrypt_configuration"]
            )
            SecurityVisitor.FIREWALL_CONFIGS = json.loads(
                config["security"]["firewall"]
            )
            SecurityVisitor.MISSING_THREATS_DETECTION_ALERTS = json.loads(
                config["security"]["missing_threats_detection_alerts"]
            )
            SecurityVisitor.PASSWORD_KEY_POLICY = json.loads(
                config["security"]["password_key_policy"]
            )
            SecurityVisitor.KEY_MANAGEMENT = json.loads(
                config["security"]["key_management"]
            )
            SecurityVisitor.NETWORK_SECURITY_RULES = json.loads(
                config["security"]["network_security_rules"]
            )
            SecurityVisitor.PERMISSION_IAM_POLICIES = json.loads(
                config["security"]["permission_iam_policies"]
            )
            SecurityVisitor.GOOGLE_IAM_MEMBER = json.loads(
                config["security"]["google_iam_member_resources"]
            )
            SecurityVisitor.LOGGING = json.loads(config["security"]["logging"])
            SecurityVisitor.GOOGLE_SQL_DATABASE_LOG_FLAGS = json.loads(
                config["security"]["google_sql_database_log_flags"]
            )
            SecurityVisitor.POSSIBLE_ATTACHED_RESOURCES = json.loads(
                config["security"]["possible_attached_resources_aws_route53"]
            )
            SecurityVisitor.VERSIONING = json.loads(config["security"]["versioning"])
            SecurityVisitor.NAMING = json.loads(config["security"]["naming"])
            SecurityVisitor.REPLICATION = json.loads(config["security"]["replication"])

        SecurityVisitor.FILE_COMMANDS = json.loads(config["security"]["file_commands"])
        SecurityVisitor.SHELL_RESOURCES = json.loads(
            config["security"]["shell_resources"]
        )
        SecurityVisitor.IP_BIND_COMMANDS = json.loads(
            config["security"]["ip_binding_commands"]
        )
        SecurityVisitor.OBSOLETE_COMMANDS = self._load_data_file("obsolete_commands")
        SecurityVisitor.DOCKER_OFFICIAL_IMAGES = self._load_data_file(
            "official_docker_images"
        )

        SecurityVisitor.DEPRECATED_OFFICIAL_DOCKER_IMAGES = self._load_data_file(
            "deprecated_official_docker_images"
        )
        SecurityVisitor.LOG_AGGREGATORS_AND_COLLECTORS = self._load_data_file(
            "log_collectors_and_aggregators"
        )
        SecurityVisitor.DANGEROUS_IMAGE_TAGS = self._load_data_file(
            "dangerous_image_tags"
        )
        SecurityVisitor.DOCKER_LOG_DRIVERS = self._load_data_file("docker_log_drivers")
        SecurityVisitor.API_GATEWAYS = self._load_data_file("api_gateways")

    @staticmethod
    def _load_data_file(file: str) -> List[str]:
        folder_path = os.path.dirname(os.path.realpath(glitch.__file__))
        with open(os.path.join(folder_path, "files", file)) as f:
            content = f.readlines()
            return [c.strip() for c in content]

    def check_atomicunit(self, au: AtomicUnit, file: str) -> List[Error]:
        errors = super().check_atomicunit(au, file)

        # for item in SecurityVisitor.__FILE_COMMANDS:
        #     if item not in au.type:
        #         continue
        #     for a in au.attributes:
        #         values = [a.value]
        #         for value in values:
        #             if not isinstance(value, str):
        #                 continue
        #             if a.name in ["mode", "m"] and re.search(
        #                 r"(?:^0?777$)|(?:(?:^|(?:ugo)|o|a)\+[rwx]{3})", value
        #             ):
        #                 errors.append(
        #                     Error("sec_full_permission_filesystem", a, file, repr(a))
        #                 )

        # for attribute in au.attributes:
        #     if (
        #         au.type in SecurityVisitor.__GITHUB_ACTIONS
        #         and attribute.name == "plaintext_value"
        #     ):
        #         errors.append(Error("sec_hard_secr", attribute, file, repr(attribute)))

        # if au.type in SecurityVisitor.__OBSOLETE_COMMANDS:
        #     errors.append(Error("sec_obsolete_command", au, file, repr(au)))
        # elif any(au.type.endswith(res) for res in SecurityVisitor.__SHELL_RESOURCES):
        #     for attr in au.attributes:
        #         if (
        #             isinstance(attr.value, str)
        #             and attr.value.split(" ")[0] in SecurityVisitor.__OBSOLETE_COMMANDS
        #         ):
        #             errors.append(Error("sec_obsolete_command", attr, file, repr(attr)))
        #             break

        for checker in self.checkers:
            checker.code = self.code
            errors += checker.check(au, file)

        # if self.__is_http_url(au.name):
        #     errors.append(Error("sec_https", au, file, repr(au)))
        # if self.__is_weak_crypt(au.type, au.name):
        #     errors.append(Error("sec_weak_crypt", au, file, repr(au)))

        return errors

    def check_dependency(self, d: Dependency, file: str) -> List[Error]:
        return []

    def __check_keyvalue(self, c: KeyValue, file: str) -> List[Error]:
        errors: List[Error] = []

        # check https/tls/ssl in Hash values

        ssl_checker = StringChecker(lambda x: self.__is_http_url(x))
        weak_crypt_checker = StringChecker(lambda x: self.__is_weak_crypt(x, ""))

        if isinstance(c.value, Hash):
            pairs_to_check = [c.value.value]

            while pairs_to_check:
                for _, v in pairs_to_check[0].items():
                    if ssl_checker.check(v):
                        errors.append(Error("sec_https", v, file, repr(v)))
                    if weak_crypt_checker.check(v):
                        errors.append(Error("sec_weak_crypt", v, file, repr(v)))
                    if isinstance(v, Hash):
                        pairs_to_check.append(v.value)

                pairs_to_check.pop(0)

        elif isinstance(c.value, Array):
            for x in c.value.value:
                if ssl_checker.check(x):
                    errors.append(Error("sec_https", x, file, repr(x)))
                if weak_crypt_checker.check(x):
                    errors.append(Error("sec_weak_crypt", x, file, repr(x)))

        else:
            if ssl_checker.check(c.value):
                errors.append(Error("sec_https", c, file, repr(c)))
            if weak_crypt_checker.check(c.value):
                errors.append(Error("sec_weak_crypt", c, file, repr(c)))

        c.name = c.name.strip().lower()

        # if isinstance(c.value, type(None)):
        #     for child in c.keyvalues:
        #         errors += self.check_element(child, file)
        #     return errors
        # elif isinstance(c.value, str):  # type: ignore
        #     c.value = c.value.strip().lower()
        # else:
        #     errors += self.check_element(c.value, file)
        #     c.value = repr(c.value)

        # if self.__is_http_url(c.value):
        #     errors.append(Error("sec_https", c, file, repr(c)))

        # if self.__is_weak_crypt(c.value, c.name):
        #     errors.append(Error("sec_weak_crypt", c, file, repr(c)))

        # for check in SecurityVisitor.__CHECKSUM:
        #     if check in c.name and (c.value == "no" or c.value == "false"):
        #         errors.append(Error("sec_no_int_check", c, file, repr(c)))
        #         break

        # def get_au(
        #     c: Project | Module | UnitBlock | None, name: str, type: str
        # ) -> AtomicUnit | None:
        #     if isinstance(c, Project):
        #         module_name = os.path.basename(os.path.dirname(file))
        #         for m in c.modules:
        #             if m.name == module_name:
        #                 return get_au(m, name, type)
        #     elif isinstance(c, Module):
        #         for ub in c.blocks:
        #             au = get_au(ub, name, type)
        #             if au is not None:
        #                 return au
        #     elif isinstance(c, UnitBlock):
        #         for au in c.atomic_units:
        #             if au.type == type and au.name == name:
        #                 return au
        #     return None

        # def get_module_var(
        #     c: Project | Module | UnitBlock | None, name: str
        # ) -> Variable | None:
        #     if isinstance(c, Project):
        #         module_name = os.path.basename(os.path.dirname(file))
        #         for m in c.modules:
        #             if m.name == module_name:
        #                 return get_module_var(m, name)
        #     elif isinstance(c, Module):
        #         for ub in c.blocks:
        #             var = get_module_var(ub, name)
        #             if var is not None:
        #                 return var
        #     elif isinstance(c, UnitBlock):
        #         for var in c.variables:
        #             if var.name == name:
        #                 return var
        #     return None

        # # only for terraform
        # var = None
        # if c.has_variable and self.tech == Tech.terraform:
        #     value = re.sub(r"^\${(.*)}$", r"\1", c.value)
        #     if value.startswith(
        #         "var."
        #     ):  # input variable (atomic unit with type variable)
        #         au = get_au(self.code, value.strip("var."), "variable")
        #         if au != None:
        #             for attribute in au.attributes:
        #                 if attribute.name == "default":
        #                     var = attribute
        #     elif value.startswith("local."):  # local value (variable)
        #         var = get_module_var(self.code, value.strip("local."))

        # for item in SecurityVisitor.__MISC_SECRETS:
        #     if (
        #         re.match(
        #             r"([_A-Za-z0-9$-]*[-_]{text}([-_].*)?$)|(^{text}([-_].*)?$)".format(
        #                 text=item
        #             ),
        #             c.name,
        #         )
        #         and len(c.value) > 0
        #         and not c.has_variable
        #     ):
        #         errors.append(Error("sec_hard_secr", c, file, repr(c)))

        # for item in SecurityVisitor.__SENSITIVE_DATA:
        #     if item.lower() in c.name:
        #         for item_value in SecurityVisitor.__SECRET_ASSIGN:
        #             if item_value in c.value.lower():
        #                 errors.append(Error("sec_hard_secr", c, file, repr(c)))
        #                 if "password" in item_value:
        #                     errors.append(Error("sec_hard_pass", c, file, repr(c)))

        for checker in self.checkers:
            checker.code = self.code
            errors += checker.check(c, file)

        return errors

    def check_attribute(self, a: Attribute, file: str) -> list[Error]:
        return self.__check_keyvalue(a, file)

    def check_variable(self, v: Variable, file: str) -> list[Error]:
        return self.__check_keyvalue(v, file)

    def check_comment(self, c: Comment, file: str) -> List[Error]:
        errors: List[Error] = []
        lines = c.content.split("\n")
        stop = False
        for word in SecurityVisitor.WRONG_WORDS:
            for line in lines:
                tokenizer = WordPunctTokenizer()
                tokens = tokenizer.tokenize(line.lower())  # type: ignore
                if word in tokens:
                    errors.append(Error("sec_susp_comm", c, file, line))
                    stop = True
            if stop:
                break
        return errors

    def check_condition(self, c: ConditionalStatement, file: str) -> List[Error]:
        errors = super().check_condition(c, file)
        if c.type != ConditionalStatement.ConditionType.SWITCH:
            return errors

        condition = c
        has_default = False

        while condition != None:
            if condition.is_default:
                has_default = True
                break
            condition = condition.else_statement

        if not has_default:
            return errors + [Error("sec_no_default_switch", c, file, repr(c))]

        return errors

    def check_unitblock(self, u: UnitBlock, file: str) -> List[Error]:
        errors = super().check_unitblock(u, file)

        # Missing integrity check changed to unit block since in Docker the integrity check is not an attribute of the
        # atomic unit but can be done on another atomic unit inside the same unit block.
        missing_integrity_checks = {}
        for au in u.atomic_units:
            result = self.check_integrity_check(au, file)
            if result is not None and result[0] is None:
                errors.append(result[1])
                continue
            if result is not None:
                missing_integrity_checks[result[0]] = result[1]
                continue
            f = SecurityVisitor.check_has_checksum(au)
            if f is not None:
                if f in missing_integrity_checks:
                    del missing_integrity_checks[f]

        errors += missing_integrity_checks.values()
        errors += self.non_off_img.check(u, file)

        for checker in self.checkers:
            checker.code = self.code
            errors += checker.check(u, file)

        return errors

    @staticmethod
    def check_integrity_check(
        au: AtomicUnit, path: str
    ) -> Optional[Tuple[str | None, Error]]:
        for item in SecurityVisitor.DOWNLOAD:
            if not isinstance(au.name, str):
                continue

            if not re.search(
                r"(http|https|www)[^ ,]*\.{text}".format(text=item), au.name
            ):
                continue
            if SecurityVisitor.__has_integrity_check(au.attributes):
                return None
            return os.path.basename(au.name), Error(
                "sec_no_int_check", au, path, repr(au)
            )

        for a in au.attributes:
            value = (
                a.value.strip().lower()
                if isinstance(a.value, str)
                else repr(a.value).strip().lower()
            )

            # Nomad integrity check
            if a.name == "artifact" and isinstance(a.value, Hash):
                found_checksum = False

                for k, v in a.value.value.items():
                    if (
                        isinstance(k, String)
                        and k.value == "options"
                        and isinstance(v, Hash)
                    ):
                        for _k, _ in v.value.items():
                            if isinstance(_k, String) and _k.value == "checksum":
                                found_checksum = True
                                break
                    elif (
                        isinstance(k, String)
                        and k.value == "source"
                        and isinstance(v, String)
                    ):
                        # artifact uses https://github.com/hashicorp/go-getter
                        parsed_source = urlparse(v.value)  # type: ignore
                        checksum = parse_qs(parsed_source.query).get("checksum", [])  # type: ignore
                        if checksum:
                            found_checksum = True
                if not found_checksum:
                    return (None, Error("sec_no_int_check", a, path, repr(a)))  # type: ignore

            for item in SecurityVisitor.DOWNLOAD:
                if not re.search(
                    r"(http|https|www)[^ ,]*\.{text}".format(text=item), value
                ):
                    continue
                if SecurityVisitor.__has_integrity_check(au.attributes):
                    return None
                return os.path.basename(a.value), Error(  # type: ignore
                    "sec_no_int_check", au, path, repr(a)
                )  # type: ignore

        return None

    @staticmethod
    def check_has_checksum(au: AtomicUnit) -> Optional[str]:
        # if au.type not in SecurityVisitor.CHECKSUM or au.name is None:
        #     return None
        # if any(d in au.name for d in SecurityVisitor.DOWNLOAD):
        #     return os.path.basename(au.name)

        # for a in au.attributes:
        #     value = (
        #         a.value.strip().lower()
        #         if isinstance(a.value, str)
        #         else repr(a.value).strip().lower()
        #     )
        #     if any(d in value for d in SecurityVisitor.DOWNLOAD):
        #         return os.path.basename(au.name)
        return None

    @staticmethod
    def __has_integrity_check(attributes: List[Attribute]) -> bool:
        # for attr in attributes:
        #     name = attr.name.strip().lower()
        #     if any([check in name for check in SecurityVisitor.__CHECKSUM]):
        #         return True
        return False

    @staticmethod
    def __is_http_url(value: str | None) -> bool:
        if value is None:
            return False

        if (
            re.match(SecurityVisitor.__URL_REGEX, value)
            and ("http" in value or "www" in value)
            and "https" not in value
        ):
            return True
        try:
            parsed_url = urlparse(value)
            return (
                parsed_url.scheme == "http"
                and parsed_url.hostname not in SecurityVisitor.URL_WHITELIST
            )
        except ValueError:
            return False

    @staticmethod
    def __is_weak_crypt(value: str, name: str | None) -> bool:
        if name is None:
            return False

        if any(crypt in value for crypt in SecurityVisitor.CRYPT):
            whitelist = any(
                word in name or word in value
                for word in SecurityVisitor.CRYPT_WHITELIST
            )
            return not whitelist
        return False


# NOTE: in the end of the file to avoid circular import
# Imports all the classes defined in the __init__.py file
from glitch.analysis.terraform import *
from glitch.analysis.security import *
