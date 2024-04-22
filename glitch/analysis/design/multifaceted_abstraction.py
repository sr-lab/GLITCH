from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.analysis.design.visitor import DesignVisitor
from glitch.repr.inter import *


class TooManyVariables(DesignSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, AtomicUnit) and element.type in DesignVisitor.EXEC:
            if isinstance(element.name, str) and (
                "&&" in element.name or ";" in element.name or "|" in element.name
            ):
                return [
                    Error(
                        "design_multifaceted_abstraction", element, file, repr(element)
                    )
                ]
            else:
                for attribute in element.attributes:
                    value = repr(attribute.value)
                    if "&&" in value or ";" in value or "|" in value:
                        return [
                            Error(
                                "design_multifaceted_abstraction",
                                element,
                                file,
                                repr(element),
                            )
                        ]

        return []
