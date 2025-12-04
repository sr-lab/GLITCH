import re
from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import *
from glitch.analysis.expr_checkers.string_checker import StringChecker
from typing import List
from shlex import split as shsplit


class InvalidBind(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        check_invalid = StringChecker(
            lambda s: re.match(r"(?:https?://|^)0.0.0.0", s) is not None
        )
        check_ipv6 = StringChecker(lambda s: s in {"*", "::"})

        if isinstance(element, KeyValue) and (
            check_invalid.check(element.value)
            or (element.name == "ip" and check_ipv6.check(element.value))
            or (
                element.name in SecurityVisitor.IP_BIND_COMMANDS
                and (
                    (isinstance(element.value, Boolean) and element.value.value == True)
                    or check_ipv6.check(element.value)
                )
            )
        ):
            return [Error("sec_invalid_bind", element, file, repr(element))]

        if isinstance(element, KeyValue) and isinstance(element.value, String):
            #HACK: splits a string in command parts as for complete commmands invocations the regex wasn't
            #  matching on full command invocations that included a reference to "0.0.0.0" or the its http/s variants 
            for part in shsplit(element.value.value):
                if check_invalid.str_check(part):
                    return [Error("sec_invalid_bind", element, file, repr(element))]
        return []
