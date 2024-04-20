from typing import Optional, List
from glitch.analysis.rules import SmellChecker
from glitch.tech import Tech


class DesignSmellChecker(SmellChecker):
    def __init__(self) -> None:
        super().__init__()
        self.code_lines: List[str] = []
        self.variables_names: List[str] = []

    @staticmethod
    def tech() -> Optional[Tech]:
        return None

    @staticmethod
    def ignore_techs() -> List[Tech]:
        return []
