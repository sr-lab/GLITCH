import os
import json
import glitch
import configparser
from glitch.analysis.rules import Error, RuleVisitor, SmellChecker
from nltk.tokenize import WordPunctTokenizer  # type: ignore
from typing import List, Type, Dict

from glitch.tech import Tech
from glitch.repr.inter import *

from glitch.analysis.terraform.smell_checker import TerraformSmellChecker
from glitch.analysis.security.smell_checker import SecuritySmellChecker


class SecurityVisitor(RuleVisitor):

    class NonOfficialImageSmell(SmellChecker):
        def check(self, element: CodeElement, file: str) -> List[Error]:
            return []

    def __init__(self, tech: Tech, fallback: set[str]) -> None:
        super().__init__(tech)
        
        SECURITY_CHECKER_ERRORS: Dict[Type[SecuritySmellChecker], List[str]] = {}

        from glitch.analysis.terraform.access_control import TerraformAccessControl
        from glitch.analysis.terraform.attached_resource import TerraformAttachedResource
        from glitch.analysis.terraform.authentication import TerraformAuthentication
        from glitch.analysis.terraform.dns_policy import TerraformDnsWithoutDnssec
        from glitch.analysis.terraform.firewall_misconfig import TerraformFirewallMisconfig
        from glitch.analysis.terraform.http_without_tls import TerraformHttpWithoutTls
        from glitch.analysis.terraform.integrity_policy import TerraformIntegrityPolicy
        from glitch.analysis.terraform.key_management import TerraformKeyManagement
        from glitch.analysis.terraform.logging import TerraformLogging
        from glitch.analysis.terraform.missing_encryption import TerraformMissingEncryption
        from glitch.analysis.terraform.naming import TerraformNaming
        from glitch.analysis.terraform.network_policy import TerraformNetworkSecurityRules
        from glitch.analysis.terraform.permission_iam_policies import TerraformPermissionIAMPolicies
        from glitch.analysis.terraform.public_ip import TerraformPublicIp
        from glitch.analysis.terraform.replication import TerraformReplication
        from glitch.analysis.terraform.sensitive_iam_action import TerraformSensitiveIAMAction
        from glitch.analysis.terraform.ssl_tls_policy import TerraformSslTlsPolicy
        from glitch.analysis.terraform.threats_detection import TerraformThreatsDetection
        from glitch.analysis.terraform.versioning import TerraformVersioning
        from glitch.analysis.terraform.weak_password_key_policy import TerraformWeakPasswordKeyPolicy

        TERRAFORM_CHECKER_ERRORS: Dict[Type[TerraformSmellChecker], str] = {
            TerraformAccessControl: "sec_access_control",
            TerraformAttachedResource: "sec_attached_resource",
            TerraformAuthentication: "sec_authentication",
            TerraformDnsWithoutDnssec: "sec_dnssec",
            TerraformFirewallMisconfig: "sec_firewall_misconfig",
            TerraformHttpWithoutTls: "sec_https",
            TerraformIntegrityPolicy: "sec_integrity_policy",
            TerraformKeyManagement: "sec_key_management",
            TerraformLogging: "sec_logging",
            TerraformMissingEncryption: "sec_missing_encryption",
            TerraformNaming: "sec_naming",
            TerraformNetworkSecurityRules: "sec_network_security_rules",
            TerraformPermissionIAMPolicies: "sec_permission_iam_policies",
            TerraformPublicIp: "sec_public_ip",
            TerraformReplication: "sec_replication",
            TerraformSensitiveIAMAction: "sec_sensitive_iam_action",
            TerraformSslTlsPolicy: "sec_ssl_tls_policy",
            TerraformThreatsDetection: "sec_threats_detection_alerts",
            TerraformVersioning: "sec_versioning",
            TerraformWeakPasswordKeyPolicy: "sec_weak_password_key_policy"
        }

        self.checkers: List[SmellChecker] = []

        for child in SecuritySmellChecker.__subclasses__():
            error_name = SECURITY_CHECKER_ERRORS.get(child, [])

            if not any(name in fallback for name in error_name):
                continue
            
            self.checkers.append(child())

        if tech == Tech.terraform:
            # Some Terraform checkers handle Terraform-specific patterns that complement
            # generic Rego checks for the same smell code. These should always run.
            ALWAYS_RUN_CHECKERS = {TerraformHttpWithoutTls}
            
            for child in TerraformSmellChecker.__subclasses__():
                error_name = TERRAFORM_CHECKER_ERRORS.get(child)

                if error_name is None:
                    continue
                
                # Run if: smell is in fallback (no Rego) OR checker is in always-run list
                if error_name not in fallback and child not in ALWAYS_RUN_CHECKERS:
                    continue
                
                self.checkers.append(child())

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

    @staticmethod
    def _load_data_file(file: str) -> List[str]:
        folder_path = os.path.dirname(os.path.realpath(glitch.__file__))
        with open(os.path.join(folder_path, "files", file)) as f:
            content = f.readlines()
            return [c.strip() for c in content]

    def check_atomicunit(self, au: AtomicUnit, file: str) -> List[Error]:
        errors = super().check_atomicunit(au, file)

        for checker in self.checkers:
            checker.code = self.code
            errors += checker.check(au, file)

        return errors

    def check_dependency(self, d: Dependency, file: str) -> List[Error]:
        return []

    def __check_keyvalue(self, c: KeyValue, file: str) -> List[Error]:
        errors: List[Error] = []
        c.name = c.name.strip().lower()

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
        return errors

    def check_condition(self, c: ConditionalStatement, file: str) -> List[Error]:
        errors = super().check_condition(c, file)
        return errors

    def check_unitblock(self, u: UnitBlock, file: str) -> List[Error]:
        errors = super().check_unitblock(u, file)
        errors += self.non_off_img.check(u, file)

        return errors

# NOTE: in the end of the file to avoid circular import
# Imports all the classes defined in the __init__.py file
from glitch.analysis.terraform import *
from glitch.analysis.security import *