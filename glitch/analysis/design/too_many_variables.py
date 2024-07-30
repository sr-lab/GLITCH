from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.repr.inter import *


class TooManyVariables(DesignSmellChecker):
    def __count_variables(self, element: CodeElement) -> int:
        count = 0

        if isinstance(element, Block):
            for child in element.statements:
                count += self.__count_variables(child)

        if isinstance(element, UnitBlock):
            count += len(element.variables)
        elif isinstance(element, ConditionalStatement) and element.else_statement is not None:
            count += self.__count_variables(element.else_statement)
        elif isinstance(element, Variable):
            count += 1

        return count

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, UnitBlock) and element.type != UnitBlockType.vars:
            # The UnitBlock should not be of type vars, because these files are supposed to only
            # have variables
            if (
                self.__count_variables(element) / max(len(self.code_lines), 1) > 0.3  # type: ignore
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
