import re
from glitch.analysis.rules import Error
from glitch.analysis.security.smell_checker import SecuritySmellChecker
from glitch.analysis.security.visitor import SecurityVisitor
from glitch.repr.inter import CodeElement, KeyValue
from glitch.analysis.expr_checkers.string_checker import StringChecker
from glitch.analysis.expr_checkers.var_checker import VariableChecker
from typing import List


class AdminByDefault(SecuritySmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, KeyValue):
            var_checker = VariableChecker()

            for item in SecurityVisitor.ROLES + SecurityVisitor.USERS:
                if re.match(r"[_A-Za-z0-9$\/\.\[\]-]*{text}\b".format(text=item), element.name):
                    if not var_checker.check(element.value):
                        for admin in SecurityVisitor.ADMIN:
                            str_checker = StringChecker(lambda s: admin in s)
                            if str_checker.check(element.value):
                                return [Error("sec_def_admin", element, file, repr(element))]
                            
        return []
