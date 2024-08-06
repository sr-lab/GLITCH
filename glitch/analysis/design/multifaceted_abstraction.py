from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.analysis.design.visitor import DesignVisitor
from glitch.repr.inter import *
from glitch.analysis.expr_checkers.string_checker import StringChecker


class MultifacetedAbstraction(DesignSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        checker = StringChecker(
            lambda s: "&&" in s or ";" in s or "|" in s
        )
        if isinstance(element, AtomicUnit) and element.type in DesignVisitor.EXEC:
            if checker.check(element.name):
                return [
                    Error(
                        "design_multifaceted_abstraction", element, file, repr(element)
                    )
                ]
            else:
                for attribute in element.attributes:
                    if checker.check(attribute.value):
                        return [
                            Error(
                                "design_multifaceted_abstraction",
                                element,
                                file,
                                repr(element),
                            )
                        ]

        return []
