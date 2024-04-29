from typing import List, Optional
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.tech import Tech
from glitch.repr.inter import *


class ImproperAlignmentTabs(DesignSmellChecker):
    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, UnitBlock):
            errors: List[Error] = []
            for i, line in enumerate(self.code_lines):
                if "\t" in line:
                    error = Error(
                        "implementation_improper_alignment",
                        element,
                        file,
                        repr(element),
                    )
                    error.line = i + 1
                    errors.append(error)
            return errors
        return []


class ImproperAlignment(DesignSmellChecker):
    @staticmethod
    def ignore_techs() -> List[Tech]:
        return [Tech.puppet, Tech.ansible]

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if isinstance(element, AtomicUnit):
            identation = None
            for a in element.attributes:
                first_line = a.code.split("\n")[0]
                curr_id = len(first_line) - len(first_line.lstrip())

                if identation is None:
                    identation = curr_id
                elif identation != curr_id:
                    return [
                        Error(
                            "implementation_improper_alignment",
                            element,
                            file,
                            repr(element),
                        )
                    ]

            return []
        return []


class PuppetImproperAlignment(DesignSmellChecker):
    def __init__(self):
        self.cached_file = ""
        self.lines = []

    @staticmethod
    def tech() -> Optional[Tech]:
        return Tech.puppet

    def check(self, element: CodeElement, file: str) -> List[Error]:
        if not isinstance(element, AtomicUnit) and not isinstance(element, UnitBlock):
            return []

        if self.cached_file != file:
            with open(file, "r") as f:
                self.lines = f.readlines()
                self.cached_file = file
        lines = self.lines

        longest = 0
        longest_ident = 0
        longest_split = ""
        for a in element.attributes:
            if len(a.name) > longest and "=>" in a.code:
                longest = len(a.name)
                split = lines[a.line - 1].split("=>")[0]
                longest_ident = len(split)
                longest_split = split
        if longest_split == "":
            return []
        elif len(longest_split) - 1 != len(longest_split.rstrip()):
            return [
                Error(
                    "implementation_improper_alignment",
                    element,
                    file,
                    repr(element),
                )
            ]

        for a in element.attributes:
            first_line = lines[a.line - 1]
            cur_arrow_column = len(first_line.split("=>")[0])
            if cur_arrow_column != longest_ident:
                return [
                    Error(
                        "implementation_improper_alignment",
                        element,
                        file,
                        repr(element),
                    )
                ]

        return []
