from typing import Dict, Optional, Union, List, Any
from abc import ABC, abstractmethod
from glitch.tech import Tech
from glitch.repr.inter import *

ErrorValue = Dict[Tech | str, Dict[str, str] | str]
ErrorDict = Dict[str, ErrorValue]


class Error:
    ERRORS: ErrorDict = {
        "security": {
            "sec_https": "Use of HTTP without TLS - The developers should always favor the usage of HTTPS. (CWE-319)",
            "sec_susp_comm": "Suspicious comment - Comments with keywords such as TODO HACK or FIXME may reveal problems possibly exploitable. (CWE-546)",
            "sec_def_admin": "Admin by default - Developers should always try to give the least privileges possible. Admin privileges may indicate a security problem. (CWE-250)",
            "sec_empty_pass": "Empty password - An empty password is indicative of a weak password which may lead to a security breach. (CWE-258)",
            "sec_weak_crypt": "Weak Crypto Algorithm - Weak crypto algorithms should be avoided since they are susceptible to security issues. (CWE-326 | CWE-327)",
            "sec_hard_secr": "Hard-coded secret - Developers should not reveal sensitive information in the source code. (CWE-798)",
            "sec_hard_pass": "Hard-coded password - Developers should not reveal sensitive information in the source code. (CWE-259)",
            "sec_hard_user": "Hard-coded user - Developers should not reveal sensitive information in the source code. (CWE-798)",
            "sec_invalid_bind": "Invalid IP address binding - Binding to the address 0.0.0.0 allows connections from every possible network which might be a security issues. (CWE-284)",
            "sec_no_int_check": "No integrity check - The content of files downloaded from the internet should be checked. (CWE-353)",
            "sec_no_default_switch": "Missing default case statement - Not handling every possible input combination might allow an attacker to trigger an error for an unhandled value. (CWE-478)",
            "sec_full_permission_filesystem": "Full permission to the filesystem - Files should not have full permissions to every user. (CWE-732)",
            "sec_obsolete_command": "Use of obsolete command or function - Avoid using obsolete or deprecated commands and functions. (CWE-477)",
            Tech.docker: {
                "sec_non_official_image": "Use of non-official Docker image - Use of non-official images should be avoided or taken into careful consideration. (CWE-829)",
            },
            Tech.terraform: {
                "sec_integrity_policy": "Integrity Policy - Image tag is prone to be mutable or integrity monitoring is disabled. (CWE-471)",
                "sec_ssl_tls_policy": "SSL/TLS/mTLS Policy - Developers should use SSL/TLS/mTLS protocols and their secure versions. (CWE-326)",
                "sec_dnssec": "Use of DNS without DNSSEC - Developers should favor the usage of DNSSEC while using DNS. (CWE-350)",
                "sec_public_ip": "Associated Public IP address - Associating Public IP addresses allows connections from public internet. (CWE-1327)",
                "sec_access_control": "Insecure Access Control - Developers should be aware of possible unauthorized access. (CWE-284)",
                "sec_authentication": "Disabled/Weak Authentication - Developers should guarantee that authentication is enabled. (CWE-287 | CWE-306)",
                "sec_missing_encryption": "Missing Encryption - Developers should ensure encryption of sensitive and critical data. (CWE-311)",
                "sec_firewall_misconfig": "Firewall Misconfiguration - Developers should favor the usage of a well configured waf. (CWE-693)",
                "sec_threats_detection_alerts": "Missing Threats Detection/Alerts - Developers should enable threats detection and alerts when it is possible. (CWE-693)",
                "sec_weak_password_key_policy": "Weak Password/Key Policy - Developers should favor the usage of strong password/key requirements and configurations. (CWE-521).",
                "sec_sensitive_iam_action": "Sensitive Action by IAM - Developers should use the principle of least privilege when defining IAM policies. (CWE-284)",
                "sec_key_management": "Key Management - Developers should use well configured Customer Managed Keys (CMK) for encryption. (CWE-1394)",
                "sec_network_security_rules": "Network Security Rules - Developers should enforce that only secure network rules are being used. (CWE-923)",
                "sec_permission_iam_policies": "Permission of IAM Policies - Developers should be aware of unwanted permissions of IAM policies. (CWE-732 | CWE-284)",
                "sec_logging": "Logging - Logs should be enabled and securely configured to help monitoring and preventing security problems. (CWE-223 | CWE-778)",
                "sec_attached_resource": "Attached Resource - Ensure that Route53 A records point to resources part of your account rather than just random IP addresses. (CWE-200)",
                "sec_versioning": "Versioning - Ensure that versioning is enabled so that users can retrieve and restore previous versions.",
                "sec_naming": "Naming - Ensure storage accounts adhere to the naming rules and every security groups and rules have a description. (CWE-1099 | CWE-710)",
                "sec_replication": "Replication - Ensure that cross-region replication is enabled to allow copying objects across S3 buckets.",
            },
        },
        "design": {
            "design_imperative_abstraction": "Imperative abstraction - The presence of imperative statements defies the purpose of IaC declarative languages.",
            "design_unnecessary_abstraction": "Unnecessary abstraction - Blocks should contain declarations or statements, otherwise they are unnecessary.",
            "implementation_long_statement": "Long statement - Long statements may decrease the readability and maintainability of the code.",
            "implementation_improper_alignment": "Improper alignment - The developers should try to follow the languages' style guides. These style guides define how the attributes in an atomic unit should be aligned. The developers should also avoid the use of tabs.",
            "implementation_too_many_variables": "Too many variables - The existence of too many variables in a single IaC script may reveal that the script is being used for too many purposes.",
            "design_duplicate_block": "Duplicate block - Duplicates blocks may reveal a missing abstraction.",
            "implementation_unguarded_variable": "Unguarded variable - Variables should be guarded for readability and maintainability of the code.",
            "design_avoid_comments": "Avoid comments - Comments may lead to bad code or be used as a way to justify bad code.",
            "design_long_resource": "Long Resource - Long resources may decrease the readability and maintainability of the code.",
            "design_multifaceted_abstraction": "Multifaceted Abstraction - Each block should only specify the properties of a single piece of software.",
            "design_misplaced_attribute": "Misplaced attribute - The developers should try to follow the languages' style guides. These style guides define the expected attribute order.",
        },
    }

    ALL_ERRORS: Dict[str, str] = {}

    @staticmethod
    def agglomerate_errors() -> None:
        def aux_agglomerate_errors(
            key: Tech | str, errors: Union[str, ErrorDict, ErrorValue, Dict[str, str]]
        ) -> None:
            if isinstance(errors, dict):
                for k, v in errors.items():
                    aux_agglomerate_errors(k, v)
            elif isinstance(key, str):
                Error.ALL_ERRORS[key] = errors

        aux_agglomerate_errors("", Error.ERRORS)

    def __init__(
        self, code: str, el: Any, path: str, repr: str, opt_msg: Optional[str] = None
    ) -> None:
        self.code: str = code
        self.el = el
        self.path = path
        self.repr = repr
        self.opt_msg = opt_msg

        if isinstance(self.el, CodeElement):
            self.line = self.el.line
        else:
            self.line = -1

    def to_csv(self) -> str:
        repr = self.repr.split("\n")[0].strip()
        if self.opt_msg:
            return f"{self.path},{self.line},{self.code},{repr},{self.opt_msg}"
        else:
            return f"{self.path},{self.line},{self.code},{repr},-"

    def __repr__(self) -> str:
        with open(self.path) as f:
            line = (
                f.readlines()[self.line - 1].strip()
                if self.line != -1
                else self.repr.split("\n")[0]
            )
            if self.opt_msg:
                line += f"\n-> {self.opt_msg}"
            return (
                f"{self.path}\nIssue on line {self.line}: {Error.ALL_ERRORS[self.code]}\n"
                + f"{line}\n"
            )

    def __hash__(self):
        return hash((self.code, self.path, self.line, self.opt_msg))

    def __eq__(self, other: Any):
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.code == other.code
            and self.path == other.path
            and self.line == other.line
        )


Error.agglomerate_errors()


class RuleVisitor(ABC):
    def __init__(self, tech: Tech) -> None:
        super().__init__()
        self.tech = tech
        self.code = None

    def check(self, code: Project | Module | UnitBlock) -> List[Error]:
        self.code = code
        if isinstance(code, Project):
            return self.check_project(code)
        elif isinstance(code, Module):
            return self.check_module(code)
        else:
            return self.check_unitblock(code, code.path)

    def check_element(self, c: CodeElement, file: str) -> list[Error]:
        if isinstance(c, AtomicUnit):
            return self.check_atomicunit(c, file)
        elif isinstance(c, Dependency):
            return self.check_dependency(c, file)
        elif isinstance(c, Attribute):
            return self.check_attribute(c, file)
        elif isinstance(c, Variable):
            return self.check_variable(c, file)
        elif isinstance(c, ConditionalStatement):
            return self.check_condition(c, file)
        elif isinstance(c, Comment):
            return self.check_comment(c, file)
        elif isinstance(c, dict):
            errors: List[Error] = []
            for k, v in c.items():  # type: ignore
                errors += self.check_element(k, file) + self.check_element(v, file)  # type: ignore
            return errors
        else:
            return []

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        pass

    @abstractmethod
    def config(self, config_path: str):
        pass

    def check_project(self, p: Project) -> list[Error]:
        errors: List[Error] = []
        for m in p.modules:
            errors += self.check_module(m)

        for u in p.blocks:
            errors += self.check_unitblock(u, u.path)

        return errors

    def check_module(self, m: Module) -> list[Error]:
        errors: List[Error] = []
        for u in m.blocks:
            errors += self.check_unitblock(u, u.path)

        return errors

    def check_unitblock(self, u: UnitBlock, file: str) -> list[Error]:
        errors: List[Error] = []
        for au in u.atomic_units:
            errors += self.check_atomicunit(au, file)
        for c in u.comments:
            errors += self.check_comment(c, file)
        for v in u.variables:
            errors += self.check_variable(v, file)
        for ub in u.unit_blocks:
            errors += self.check_unitblock(ub, file)
        for a in u.attributes:
            errors += self.check_attribute(a, file)
        for s in u.statements:
            errors += self.check_element(s, file)

        return errors

    def check_atomicunit(self, au: AtomicUnit, file: str) -> list[Error]:
        errors: List[Error] = []
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

    def check_condition(self, c: ConditionalStatement, file: str) -> list[Error]:
        errors: List[Error] = []

        for s in c.statements:
            errors += self.check_element(s, file)

        return errors

    @abstractmethod
    def check_comment(self, c: Comment, file: str) -> list[Error]:
        pass


Error.agglomerate_errors()


class SmellChecker(ABC):
    def __init__(self) -> None:
        self.code: Optional[Project | UnitBlock | Module] = None

    @abstractmethod
    def check(self, element: CodeElement, file: str) -> list[Error]:
        pass
