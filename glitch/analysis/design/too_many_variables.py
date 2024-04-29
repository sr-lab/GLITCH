from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.repr.inter import *


class TooManyVariables(DesignSmellChecker):
    def __count_variables(self, vars: List[KeyValue]) -> int:
        count = 0
        for var in vars:
            if isinstance(var.value, type(None)):
                count += self.__count_variables(var.keyvalues)
            else:
                count += 1
        return count

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, UnitBlock) and element.type != UnitBlockType.vars:
            # The UnitBlock should not be of type vars, because these files are supposed to only
            # have variables
            if (
                self.__count_variables(element.variables) / max(len(self.code_lines), 1) > 0.3  # type: ignore
            ):
                return [
                    Error(
                        "implementation_too_many_variables",
                        element,
                        file,
                        repr(element),
                    )
                ]
        return []
