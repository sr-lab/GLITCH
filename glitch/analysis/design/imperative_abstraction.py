from typing import List, Tuple
from glitch.analysis.rules import Error
from glitch.analysis.design.visitor import DesignVisitor
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.repr.inter import *


class ImperativeAbstraction(DesignSmellChecker):
    def __count_atomic_units(self, ub: UnitBlock) -> Tuple[int, int]:
        count_resources = len(ub.atomic_units)
        count_execs = 0
        for au in ub.atomic_units:
            if au.type in DesignVisitor.EXEC:
                count_execs += 1

        for unitblock in ub.unit_blocks:
            resources, execs = self.__count_atomic_units(unitblock)
            count_resources += resources
            count_execs += execs

        return count_resources, count_execs

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, UnitBlock):
            total_resources, total_execs = self.__count_atomic_units(element)
            if total_execs > 2 and (total_execs / total_resources) > 0.20:
                return [
                    Error(
                        "design_imperative_abstraction",
                        element,
                        file,
                        repr(element),
                    )
                ]
        return []
