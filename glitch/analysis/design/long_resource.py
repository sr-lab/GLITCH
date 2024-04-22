from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.analysis.design.visitor import DesignVisitor
from glitch.repr.inter import *


class TooManyVariables(DesignSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, AtomicUnit) and element.type in DesignVisitor.EXEC:
            lines = 0
            for attr in element.attributes:
                for line in attr.code.split("\n"):
                    if line.strip() != "":
                        lines += 1

            if lines > 7:
                return [Error("design_long_resource", element, file, repr(element))]

        return []
