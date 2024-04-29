import re
from typing import List
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.analysis.design.visitor import DesignVisitor
from glitch.repr.inter import *


class UnguardedVariable(DesignSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if (
            isinstance(element, UnitBlock)
            and DesignVisitor.VAR_REFER_SYMBOL is not None
        ):
            # FIXME could be improved if we considered strings as part of the model
            for i, l in enumerate(self.code_lines):
                for tuple in re.findall(
                    r"(\'([^\\]|(\\(\n|.)))*?\')|(\"([^\\]|(\\(\n|.)))*?\")", l
                ):
                    for string in (tuple[0], tuple[4]):
                        for var in (
                            self.variables_names + DesignVisitor.DEFAULT_VARIABLES
                        ):
                            if (DesignVisitor.VAR_REFER_SYMBOL + var) in string[1:-1]:
                                error = Error(
                                    "implementation_unguarded_variable",
                                    element,
                                    file,
                                    string,
                                )
                                error.line = i + 1
                                errors.append(error)

        return errors
