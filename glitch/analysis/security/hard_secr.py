import re
from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import *
from glitch.analysis.expr_checkers.string_checker import StringChecker
from glitch.analysis.expr_checkers.var_checker import VariableChecker
from typing import List


class HardcodedSecret(SecuritySmellChecker):
    def __check_pair(
        self, element: CodeElement, name: Expr, value: Expr, file: str
    ) -> List[Error]:
        errors: List[Error] = []
        var_checker = VariableChecker()

        whitelist_checker = StringChecker(
            lambda s: any(
                [
                    s.lower() == w
                    for w in SecurityVisitor.SECRETS_WHITELIST + SecurityVisitor.PROFILE
                ]
            )
        )

        for item in (
            SecurityVisitor.PASSWORDS + SecurityVisitor.SECRETS + SecurityVisitor.USERS
        ):
            secr_checker = StringChecker(
                lambda s: (
                    re.match(r"[_A-Za-z0-9$\/\.\[\]-]*{text}\b".format(text=item), s)
                    is not None
                )
                or (
                    re.match(
                        r"[_A-Za-z0-9$\/\.\[\]-]*{text}\b".format(text=item.upper()), s
                    )
                    is not None
                )
            )
            if secr_checker.check(name) and not whitelist_checker.check(name):
                if not var_checker.check(value):
                    if (
                        item in SecurityVisitor.PASSWORDS
                        and isinstance(value, String)
                        and len(value.value) == 0
                    ):
                        errors.append(
                            Error("sec_empty_pass", element, file, repr(element))
                        )
                        break

                    errors.append(Error("sec_hard_secr", element, file, repr(element)))
                    if item in SecurityVisitor.PASSWORDS:
                        errors.append(
                            Error("sec_hard_pass", element, file, repr(element))
                        )
                    elif item in SecurityVisitor.USERS:
                        errors.append(
                            Error("sec_hard_user", element, file, repr(element))
                        )
                    break

        id_rsa_checker = StringChecker(lambda s: len(s) > 0 and "/id_rsa" in s)
        for item in SecurityVisitor.SSH_DIR:
            ssh_dir_checker = StringChecker(lambda s: item.lower() in s)
            if ssh_dir_checker.check(name):
                if id_rsa_checker.check(value):
                    errors.append(Error("sec_hard_secr", element, file, repr(element)))

        return errors

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, KeyValue) and not isinstance(element.value, Hash):
            errors += self.__check_pair(
                element,
                String(element.name, ElementInfo(-1, -1, -1, -1, "")),
                element.value,
                file,
            )
        elif isinstance(element, KeyValue) and isinstance(element.value, Hash):
            for key, value in element.value.value.items():
                errors += self.__check_pair(element, key, value, file)

        return errors
