from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.analysis.checkers.transverse_checker import TransverseChecker
from glitch.repr.inter import *


class TooManyVariables(DesignSmellChecker):
    class CountVariablesChecker(TransverseChecker):
        def __init__(self) -> None:
            self.variables: set[Variable] = set()
            self.count = 0

        def check_keyvalue(self, element: KeyValue) -> bool:
            if isinstance(element, Variable) and element not in self.variables:
                self.variables.add(element)
                self.count += 1
            return False

    def __count_variables(self, element: CodeElement) -> int:
        count = 0

        if isinstance(element, Block) or isinstance(element, BlockExpr):
            for child in element.statements:
                count += self.__count_variables(child)

        if isinstance(element, UnitBlock):
            count += len(element.variables)
        elif (
            isinstance(element, ConditionalStatement)
            and element.else_statement is not None
        ):
            count += self.__count_variables(element.else_statement)
        elif isinstance(element, Variable):
            count += 1

        return count

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if (
            isinstance(element, UnitBlock) 
            and element.type in [UnitBlockType.unknown, UnitBlockType.script, UnitBlockType.tasks]
        ):
            # The UnitBlock should not be of type vars, because these files are supposed to only
            # have variables
            checker = self.CountVariablesChecker()
            checker.check(element)
            if checker.count / max(len(self.code_lines), 1) > 0.3:  # type: ignore
                return [
                    Error(
                        "implementation_too_many_variables",
                        element,
                        file,
                        repr(element),
                    )
                ]
        return []
