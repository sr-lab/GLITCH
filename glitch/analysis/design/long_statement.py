from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.repr.inter import UnitBlockType
from glitch.repr.inter import *


class LongStatementSmell(DesignSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, UnitBlock) and element.type != UnitBlockType.block:
            for i, line in enumerate(self.code_lines):
                if len(line) > 140:
                    error = Error("implementation_long_statement", element, element.path, line)
                    error.line = i + 1
                    errors.append(error)
        
        return errors