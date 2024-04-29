from typing import List, Tuple, Set
from glitch.analysis.rules import Error
from glitch.analysis.design.smell_checker import DesignSmellChecker
from glitch.repr.inter import *


class UnguardedVariable(DesignSmellChecker):
    def __get_line(self, i: int, lines: List[Tuple[int, int]]):
        for j, line in lines:
            if i < j:
                return line
        raise RuntimeError("Line not found")

    def check(self, element: CodeElement, file: str) -> List[Error]:
        errors: List[Error] = []

        if isinstance(element, UnitBlock) and element.type != UnitBlockType.block:
            lines: List[Tuple[int, int]] = []
            all_code, code = "".join(self.code_lines), ""
            current_line = 1
            i = 0
            for c in all_code:
                if c == "\n":
                    lines.append((i, current_line))
                    current_line += 1
                elif not c.isspace():
                    code += c
                    i += 1
            lines.append((i, current_line))

            blocks: Dict[int, List[int]] = {}
            for i in range(len(code) - 150):
                hash = code[i : i + 150].__hash__()
                if hash not in blocks:
                    blocks[hash] = [i]
                else:
                    blocks[hash].append(i)

            # Note: changing the structure to a set instead of a list increased the speed A LOT
            checked: Set[int] = set()
            for _, value in blocks.items():
                if len(value) >= 2:
                    for i in value:
                        if i not in checked:
                            line = self.__get_line(i, lines)
                            error = Error(
                                "design_duplicate_block",
                                element,
                                file,
                                self.code_lines[line - 1],
                            )
                            error.line = line
                            errors.append(error)
                            checked.update(range(i, i + 150))

        return errors
